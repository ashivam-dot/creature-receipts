"""Keep the Atlas topic catalogue stocked without anyone adding topics by hand.

When fewer than MIN_OPEN topics are open, `refill` shortlists World Bank WDI indicators that are ratios (%, per
person, years) and stay clear of the channel's no-go subjects, lets the model pick the ones with the most surprising
maps (told which past Shorts did best), fetches each one's real data, keeps those with enough countries, and has the
model write the topic from the data's actual spread. A topic's colour scale is checked against that data before it
joins strategy/ATLAS-TOPICS.json.
"""

from __future__ import annotations

import json
import logging
import re
import statistics

import requests

from .. import llm
from .data import WB_API, fetch
from .writer import MIN_COUNTRIES, drawable

log = logging.getLogger(__name__)

MIN_OPEN = 12
ADD = 10
SHORTLIST = 24
RATIO = re.compile(r"(%|per |\(years\)|per capita|ratio|rate|share|index|\(days\)|\(hours\))", re.I)
NO_GO = re.compile(
    r"(military|armed|arms |weapon|conflict|battle|war\b|terror|refugee|asylum|homicide|suicide|death|mortality|"
    r"killed|violence|religio|election|parliament|seats held|corruption|tax |\bLCU\b|current US\$|constant|"
    r"\bPPP\b \(constant|atlas method|debt service|IDA|IBRD|HIV|tuberculosis|malaria|AIDS|prisoners|police)", re.I)

PICK = """You choose topics for Atlas in Numbers, a YouTube Shorts channel: one world map coloured by one official
dataset, with a surprising claim, a tour of 3-4 countries and a plain "why". Audience: curious English speakers,
mostly US. Pick the {n} indicators below whose world map would surprise people most and be easiest to grasp in 30
seconds. Prefer everyday life (money, work, homes, food, tech, nature, people, travel). Never pick anything about
war, death, disease, religion, politics or crime. Avoid near-duplicates of the topics already made.

Already made or queued: {done}
{performance}
INDICATORS (id | name):
{rows}

Return the ids, best first."""

PICK_SCHEMA = {"type": "object", "properties": {"ids": {"type": "array", "items": {"type": "string"}}},
               "required": ["ids"]}

SPEC = """Write one topic for Atlas in Numbers (see the channel description: one world map, one official number,
surprising claim, English, no politics or war) from this World Bank indicator and its real data.

Indicator: {id} — {name}
Definition: {note}
Countries with data: {count}; most values are for {year}.
Spread of the values: min {min}, 10th pct {p10}, 25th {p25}, median {p50}, 75th {p75}, 90th {p90}, max {max}.
Highest: {top}
Lowest: {bottom}

Fields:
- topic: a 3-7 word headline for the map.
- angle: one sentence, the surprising thing the data shows (true by the numbers above).
- label: what the colour means, at most 40 characters, e.g. "Share of adults with a bank account".
- unit: the unit, short ("%", "years", "per 1,000 people").
- scale: either a threshold {{"kind": "threshold", "at": X, "labels": [above label, below label]}} when one number
  splits the story (X between the 10th and 90th percentile), or bins {{"kind": "bins", "edges": [4 or 5 ascending
  numbers inside min..max], "labels": [one more label than edges, short]}}.
- value_format: a Python format for one value, e.g. "{{v:.0f}}%", "{{v:.1f}} years", "{{v:,.0f}}".
- hashtags: 3 hashtags starting with #maps or #geography."""

SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"}, "angle": {"type": "string"}, "label": {"type": "string"},
        "unit": {"type": "string"}, "value_format": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "scale": {"type": "object", "properties": {
            "kind": {"type": "string", "enum": ["threshold", "bins"]}, "at": {"type": "number"},
            "edges": {"type": "array", "items": {"type": "number"}},
            "labels": {"type": "array", "items": {"type": "string"}}}, "required": ["kind", "labels"]},
    },
    "required": ["topic", "angle", "label", "unit", "scale", "value_format", "hashtags"],
}


AUDIT = """You fact-check a data channel before it publishes. Below are the highest and lowest values a World Bank
series reports. Official series sometimes carry broken values (a definition change, a unit slip, a survey that
measured something else). Compare each value with what you know about that country.

Indicator: {name}
Definition: {note}
Year: {year}
Highest: {top}
Lowest: {bottom}

List every value that is very likely wrong or not comparable with the others (for example far from the country's
widely reported figure). Return an empty list only if all of them are plausible."""

AUDIT_SCHEMA = {"type": "object", "properties": {"suspect": {"type": "array", "items": {
    "type": "object", "properties": {"country": {"type": "string"}, "why": {"type": "string"}},
    "required": ["country", "why"]}}}, "required": ["suspect"]}


def audit(name: str, note: str, year: int, top: str, bottom: str) -> list[dict]:
    """Extreme values an independent check finds implausible: [{country, why}]."""
    return llm.generate(AUDIT.format(name=name, note=note, year=year, top=top, bottom=bottom),
                        schema=AUDIT_SCHEMA, temperature=0.0, purpose="atlas data audit")["suspect"]


def audit_dataset(ds, name: str, note: str) -> list[dict]:
    vals = drawable(ds)
    ranked = sorted(vals.items(), key=lambda kv: kv[1], reverse=True)
    wide = lambda rows: ", ".join(f"{ds.names.get(k, k)} {v:.3g}" for k, v in rows)  # noqa: E731
    return audit(name, note, ds.year, wide(ranked[:8]), wide(ranked[-8:]))


def indicators() -> list[dict]:
    """WDI indicators that are ratios and not on a no-go subject: [{id, name, note}]."""
    rows = requests.get(f"{WB_API}/source/2/indicators", params={"format": "json", "per_page": 3000},
                        timeout=120).json()[1]
    out = []
    for r in rows:
        name = r.get("name") or ""
        if RATIO.search(name) and not NO_GO.search(name) and not NO_GO.search(r.get("sourceNote") or ""):
            out.append({"id": r["id"], "name": name, "note": (r.get("sourceNote") or "")[:600]})
    return out


def _quantile(sorted_vals: list[float], q: float) -> float:
    return sorted_vals[min(int(q * (len(sorted_vals) - 1) + 0.5), len(sorted_vals) - 1)]


def check(spec: dict, values: list[float]) -> list[str]:
    """Problems with a written topic's scale and format against the real values."""
    out = []
    vals = sorted(values)
    scale = spec["scale"]
    try:
        spec["value_format"].format(v=vals[len(vals) // 2])
    except (KeyError, ValueError, IndexError):
        out.append("value_format doesn't format a number")
    if scale["kind"] == "threshold":
        at = scale.get("at")
        if at is None or not _quantile(vals, 0.1) <= at <= _quantile(vals, 0.9):
            out.append("the threshold isn't between the 10th and 90th percentile")
        if len(scale.get("labels", [])) != 2:
            out.append("a threshold needs 2 labels")
    else:
        edges = scale.get("edges", [])
        if not 3 <= len(edges) <= 6 or edges != sorted(edges) or len(set(edges)) != len(edges):
            out.append("bins need 3-6 ascending edges")
        elif not (vals[0] < edges[0] and edges[-1] < vals[-1]):
            out.append("bin edges must sit inside the data's range")
        if len(scale.get("labels", [])) != len(edges) + 1:
            out.append("bins need one more label than edges")
    if len(spec["label"]) > 44:
        out.append("label over 44 characters")
    return out


def _performance(stats: list[dict]) -> str:
    seen = [s for s in stats if s.get("views") is not None]
    if len(seen) < 3:
        return ""
    seen.sort(key=lambda s: s["views"], reverse=True)
    best = "; ".join(f"{s['title']} ({s['views']} views)" for s in seen[:3])
    worst = "; ".join(f"{s['title']} ({s['views']} views)" for s in seen[-3:])
    return f"Past Shorts that did best: {best}. Did worst: {worst}. Lean towards what did best.\n"


def refill(catalogue: dict, stats: list[dict] | None = None, add: int = ADD) -> list[dict]:
    """New topics appended to the catalogue (in place) when it's running low; [] when it isn't."""
    topics = catalogue["topics"]
    if sum(t.get("status") == "open" for t in topics) >= MIN_OPEN:
        return []
    used = {t["dataset"].get("indicator") for t in topics}
    pool = [r for r in indicators() if r["id"] not in used]
    by_id = {r["id"]: r for r in pool}
    done = "; ".join(t["topic"] for t in topics)
    picked = llm.generate(PICK.format(n=SHORTLIST, done=done, performance=_performance(stats or []),
                                      rows="\n".join(f"{r['id']} | {r['name']}" for r in pool)),
                          schema=PICK_SCHEMA, temperature=0.4, purpose="atlas topics")["ids"]
    added = []
    number = max((int(t["id"][1:]) for t in topics if re.fullmatch(r"t\d+", t["id"])), default=0)
    for ind in [by_id[i] for i in picked if i in by_id]:
        if len(added) >= add:
            break
        base = {"kind": "worldbank", "indicator": ind["id"], "label": ind["name"][:44], "unit": "",
                "source": "World Bank", "min_year": 2019}
        try:
            ds = fetch(base)
        except Exception as err:
            log.info("skip %s: %s", ind["id"], err)
            continue
        vals = drawable(ds)
        if len(vals) < MIN_COUNTRIES:
            continue
        ranked = sorted(vals.items(), key=lambda kv: kv[1], reverse=True)
        s = sorted(vals.values())
        fmt = lambda v: f"{v:.3g}"  # noqa: E731
        top = ", ".join(f"{ds.names.get(k, k)} {fmt(v)}" for k, v in ranked[:5])
        bottom = ", ".join(f"{ds.names.get(k, k)} {fmt(v)}" for k, v in ranked[-5:])
        if suspect := audit_dataset(ds, ind["name"], ind["note"]):
            log.info("skip %s, implausible values: %s", ind["id"],
                     "; ".join(f"{s['country']}: {s['why']}" for s in suspect))
            continue
        spec = None
        feedback = ""
        for _ in range(2):
            answer = llm.generate(SPEC.format(
                id=ind["id"], name=ind["name"], note=ind["note"], count=len(vals), year=ds.year,
                min=fmt(s[0]), p10=fmt(_quantile(s, 0.1)), p25=fmt(_quantile(s, 0.25)), p50=fmt(statistics.median(s)),
                p75=fmt(_quantile(s, 0.75)), p90=fmt(_quantile(s, 0.9)), max=fmt(s[-1]),
                top=top, bottom=bottom) + feedback,
                schema=SPEC_SCHEMA, temperature=0.5, purpose=f"atlas topic {ind['id']}")
            if not (found := check(answer, s)):
                spec = answer
                break
            feedback = "\nYOUR LAST ANSWER HAD THESE PROBLEMS; FIX THEM:\n- " + "\n- ".join(found)
        if spec is None:
            continue
        number += 1
        scale = {k: v for k, v in spec["scale"].items() if k in ("kind", "at", "edges", "labels")}
        topic = {"id": f"t{number:03d}", "topic": spec["topic"].strip(), "angle": spec["angle"].strip(),
                 "format": "rank_ladder" if number % 3 == 0 else "map_reveal",
                 "dataset": {**base, "label": spec["label"].strip(), "unit": spec["unit"].strip()},
                 "scale": scale, "value_format": spec["value_format"],
                 "hashtags": [h if h.startswith("#") else f"#{h}" for h in spec["hashtags"][:3]],
                 "source_url": f"https://data.worldbank.org/indicator/{ind['id']}", "status": "open",
                 "added_by": "refill"}
        topics.append(topic)
        added.append(topic)
        log.info("new topic %s: %s (%s)", topic["id"], topic["topic"], ind["id"])
    return added
