"""Write an Atlas script from its dataset: the model sees only the data summary and the publisher's own definition
of the indicator, and every number it says must be one the data supports."""

from __future__ import annotations

import logging
import re
import statistics

import requests

from .. import llm
from . import geo
from .data import Dataset
from .draw import short_name
from .episode import AtlasEpisode

log = logging.getLogger(__name__)

WORDS = (75, 120)
BEATS = (6, 8)
TRIES = 3
MIN_COUNTRIES = 100
# Places with data that the map can't draw (tiny islands) are left out of what the writer may point at: the main
# landmass must span this much of the projected map (about 5 pixels across on the world view).
MIN_SIDE = 0.025

PROMPT = """You write 30 to 45 second YouTube Shorts for "Atlas in Numbers": one world map, one dataset, and the
surprise hidden in it. Every claim comes from the data below; the audience is curious adults worldwide.

TOPIC: {topic}
ANGLE: {angle}
FORMAT: {format}
DATASET: {label} ({unit}), {source}, mostly {year}. {count} countries have data.
{scale_note}
OFFICIAL DEFINITION (the only allowed basis for any "why" or "what it measures" line):
{definition}

DATA SUMMARY (values already rounded the way you may say them):
{summary}

Write {beats_min}-{beats_max} beats, {words_min}-{words_max} words in total, as JSON.
Rules:
- Beat 1 is the hook over the finished world map: a concrete, surprising claim in at most 14 words, phrased so it's
  true by the data. No "Did you know", no "Most people think", no question as the first beat.
- Beat 2 says what the colours mean and one headline count from the summary.
- The middle beats tour 3 or 4 countries that make the point (biggest, smallest, a surprise, and India or the USA
  when the data makes them interesting). Each tour beat names its country and says its value.
- One beat explains WHY or what the number really measures, using only the official definition. If the definition
  gives no reason, explain what is being counted instead. Never invent causes, history, or opinions.
- The last beat is a short question to the viewer that loops back to the hook (e.g. "So where's your country?").
- Write every number as digits exactly as in the summary ("178", "3.2", "1.15 billion"). Never write numbers as
  words. Never round differently. Never add a number the summary doesn't contain. A country's value goes only in
  a beat whose isos include that country.
- Say a negative value as a fall without the minus sign: "-1.8%" becomes "shrinking by 1.8%" or "down 1.8%".
- The "why" line is plain English a 12-year-old follows; no jargon such as "exponential", "de facto", "per capita".
- Plain spoken English, short sentences, no emojis, no hashtags in the beats, no politics or war.
- Shots: "world" (whole map), "country" (iso), "group" (2-3 isos side by side), "rank" (3-6 isos shown as a bar
  chart of their values; the best way to show a top or bottom list), or "card" for the last beat only. Use "rank"
  for exactly one middle beat when the FORMAT is rank_ladder, and at most once otherwise. Use only ISO codes from
  the summary.
- title: at most 60 characters, a concrete claim with a number, no clickbait punctuation, no emoji.
- hook_text: 2-5 words in capitals shown on screen over beat 1, adding to (not repeating) the spoken hook.
- card_lines: 2 short lines for the end card: a 2-4 word question, then the dataset label.
{feedback}"""

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook_text": {"type": "string"},
        "description": {"type": "string"},
        "card_lines": {"type": "array", "items": {"type": "string"}},
        "beats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "shot": {"type": "string", "enum": ["world", "country", "group", "rank", "card"]},
                    "isos": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "shot"],
            },
        },
    },
    "required": ["title", "hook_text", "description", "card_lines", "beats"],
}


def definition(ds_spec: dict) -> str:
    """The publisher's own note on what the indicator measures (World Bank `sourceNote`), or the topic's note."""
    if ds_spec.get("kind") == "worldbank":
        try:
            meta = requests.get(f"https://api.worldbank.org/v2/indicator/{ds_spec['indicator']}",
                                params={"format": "json"}, timeout=60).json()[1][0]
            return (meta.get("sourceNote") or "").strip()[:1500]
        except Exception as err:
            log.warning("no definition for %s: %s", ds_spec.get("indicator"), err)
    return ds_spec.get("definition", "")


def _say(value: float, fmt: str) -> str:
    text = fmt.format(v=value)
    return text[1:] if text.startswith("-") and not re.search(r"[1-9]", text) else text


def drawable(ds: Dataset) -> dict[str, float]:
    world = geo.world()
    return {k: v for k, v in ds.values.items() if k in world}


def visible(vals: dict[str, float]) -> dict[str, float]:
    world = geo.world()
    out = {}
    for k, v in vals.items():
        x0, y0, x1, y1 = world[k].bbox()
        if max(x1 - x0, y1 - y0) >= MIN_SIDE:
            out[k] = v
    return out


def facts(ds: Dataset, ep_scale: dict, fmt: str) -> tuple[str, set[str], dict[str, set[str]]]:
    """The summary the writer sees, every number it may say, and which countries own each country value (a value
    may only be said in a beat that names one of its owners)."""
    vals = drawable(ds)
    shown = visible(vals)
    names = {k: short_name(geo.world()[k].name) for k in vals}
    ranked = sorted(shown.items(), key=lambda kv: kv[1], reverse=True)
    lines, allowed, owners = [], set(), {}

    def add(text: str, *numbers: float | int | str, iso: str | None = None) -> None:
        lines.append(text)
        for n in numbers:
            forms = _forms(n)
            if iso:
                for f in forms:
                    owners.setdefault(f, set()).add(iso)
            else:
                allowed.update(forms)

    add(f"Countries with data on the map: {len(vals)}", len(vals))
    add(f"Year: {ds.year}", ds.year)
    if ep_scale.get("kind") == "threshold":
        at = ep_scale["at"]
        above = [k for k, v in vals.items() if v >= at]
        add(f"Countries at or above {at:g}: {len(above)} of {len(vals)}", len(above), at)
        add(f"Countries below {at:g}: {len(vals) - len(above)}", len(vals) - len(above))
    median = statistics.median(vals.values())
    add(f"Median country: {_say(median, fmt)}", _say(median, fmt))
    lines.append(f"Top 12 of the {len(shown)} countries big enough to see on the map (iso, name, value):")
    for k, v in ranked[:12]:
        add(f"  {k} {names[k]}: {_say(v, fmt)}", _say(v, fmt), iso=k)
    lines.append("Bottom 8:")
    for k, v in ranked[-8:]:
        add(f"  {k} {names[k]}: {_say(v, fmt)}", _say(v, fmt), iso=k)
    every = sorted(vals.items(), key=lambda kv: kv[1], reverse=True)
    for label, (k, _) in (("highest", every[0]), ("lowest", every[-1])):
        if k in shown:
            lines.append(f"{names[k]} is the {label} of all {len(vals)} with data, so 'the world's {label}' is true of it.")
        else:
            lines.append(f"The true {label} is {names[k]}, too small to show. Never call a country on this map the "
                         f"world's {label} or 'the fastest/most/least'; say 'among these countries' instead.")
    lines.append(f"Notable countries (rank among the {len(shown)}):")
    for k in ("IND", "USA", "CHN", "GBR", "BRA", "NGA", "JPN", "DEU", "PAK", "IDN", "RUS", "AUS", "CAN", "MEX"):
        if k in shown:
            rank = 1 + [x for x, _ in ranked].index(k)
            add(f"  {k} {names[k]}: {_say(vals[k], fmt)} (rank {rank})", _say(vals[k], fmt), rank, iso=k)
    for n in range(1, 13):
        allowed.update(_forms(n))
    allowed.update({"100", "hundred", str(len(shown))})
    return "\n".join(lines), allowed, owners


def _forms(n: float | int | str) -> set[str]:
    """The ways a number may appear in the script: as formatted, and its bare digits."""
    text = str(n)
    out = {text}
    m = re.search(r"-?[\d,]*\.?\d+", text)
    if m:
        # A script says "shrinking by 0.2%" for -0.2%, so the magnitude counts too.
        digits = m.group(0).replace(",", "").lstrip("-")
        out.update({digits, m.group(0).lstrip("-")})
        try:
            f = float(digits)
            if f.is_integer():
                out.add(str(int(f)))
                out.add(f"{int(f):,}")
        except ValueError:
            pass
    return out


_WRONG_COLOUR = re.compile(r"\b(red|green|orange|purple|pink|brown|light blue)\b", re.I)
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_WORD_NUMBERS = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|"
                           r"fifty|sixty|seventy|eighty|ninety|thousand|million|billion|percent)\b", re.I)


def number_problems(text: str, allowed: set[str], owners: dict[str, set[str]] | None = None,
                    isos: list[str] | None = None) -> list[str]:
    problems = []
    owners = owners or {}
    for m in _NUMBER.finditer(text):
        token = m.group(0).rstrip(",").rstrip(".")
        bare = token.replace(",", "")
        if token in allowed or bare in allowed:
            continue
        owned = owners.get(token) or owners.get(bare)
        if not owned:
            problems.append(f"the number {token} isn't in the data summary")
        elif not owned & set(isos or []):
            problems.append(f"{token} is the value of {', '.join(sorted(owned))}; say it only in a beat whose isos "
                            "include that country")
    for m in _WORD_NUMBERS.finditer(text):
        word = m.group(0).lower()
        if word in ("million", "billion", "percent") and re.search(rf"\d\s*{word}", text, re.I):
            continue
        problems.append(f"write '{m.group(0)}' as digits from the summary")
    return problems


def problems(draft: dict, allowed: set[str], owners: dict[str, set[str]], vals: dict[str, float]) -> list[str]:
    out = []
    beats = draft.get("beats", [])
    words = sum(len(b["text"].split()) for b in beats)
    if not BEATS[0] <= len(beats) <= BEATS[1]:
        out.append(f"{len(beats)} beats; write {BEATS[0]}-{BEATS[1]}")
    if not WORDS[0] <= words <= WORDS[1]:
        out.append(f"{words} words; write {WORDS[0]}-{WORDS[1]}")
    if len(draft.get("title", "")) > 60:
        out.append("the title is over 60 characters")
    if beats and beats[0]["shot"] != "world":
        out.append("beat 1 must be a world shot")
    if beats and beats[-1]["shot"] != "card":
        out.append("the last beat must be the card")
    if beats and len(beats[0]["text"].split()) > 14:
        out.append("the hook is over 14 words")
    if beats and beats[0]["text"].strip().endswith("?"):
        out.append("the hook must be a claim, not a question")
    used = []
    for i, b in enumerate(beats, 1):
        isos = b.get("isos", [])
        used += isos
        if colour := _WRONG_COLOUR.search(b["text"]):
            out.append(f"beat {i}: the map has no {colour.group(0)}; name only yellow, dark blue, or grey")
        if re.search(r"(?<![\w.])-\d", b["text"]):
            out.append(f"beat {i}: say a negative value as a fall ('down 1.8%'), without the minus sign")
        for iso in isos:
            if iso not in vals:
                out.append(f"beat {i}: {iso} is too small to see or has no data; pick a country from the summary")
        if b["shot"] == "country" and len(isos) != 1:
            out.append(f"beat {i}: a country shot names exactly one iso")
        if b["shot"] == "group" and not 2 <= len(isos) <= 3:
            out.append(f"beat {i}: a group shot names 2 or 3 isos")
        if b["shot"] == "rank" and not 3 <= len(isos) <= 6:
            out.append(f"beat {i}: a rank shot names 3 to 6 isos")
    if sum(b["shot"] == "rank" for b in beats) > 1:
        out.append("use the rank shot at most once")
    for i, b in enumerate(beats, 1):
        isos = b.get("isos", [])
        out += [f"beat {i}: {p}" for p in number_problems(b["text"], allowed, owners, isos)]
    out += [f"title: {p}" for p in number_problems(draft.get("title", ""), allowed, owners, used)]
    return out


def write(topic: dict, ds: Dataset, episode_id: str, series: str = "") -> AtlasEpisode:
    """A checked script for the topic, or RuntimeError after TRIES drafts that break the rules."""
    fmt = topic.get("value_format", "{v:,.0f}")
    scale = topic.get("scale", {"kind": "bins"})
    summary, allowed, owners = facts(ds, scale, fmt)
    vals = drawable(ds)
    if len(vals) < MIN_COUNTRIES:
        raise RuntimeError(f"only {len(vals)} countries have data; an Atlas map needs {MIN_COUNTRIES}")
    shown = visible(vals)
    labels = scale.get("labels") or ["above", "below"]
    scale_note = (f"Colours on the map: yellow = {labels[0]} (at or above {scale['at']:g}), dark blue = {labels[1]}. "
                  "Grey = no data. Name only these colours." if scale.get("kind") == "threshold" else
                  "Colours on the map: dark blue is lowest, through grey-gold, to bright yellow for highest. Grey = no "
                  "data. Name only these colours.")
    feedback = ""
    for attempt in range(1, TRIES + 1):
        prompt = PROMPT.format(topic=topic["topic"], angle=topic.get("angle", ""), format=topic.get("format", "map_reveal"),
                               label=ds.label, unit=ds.unit, source=ds.source, year=ds.year, count=len(vals),
                               scale_note=scale_note, definition=topic.get("definition_text", "") or "(none given)",
                               summary=summary, beats_min=BEATS[0], beats_max=BEATS[1], words_min=WORDS[0],
                               words_max=WORDS[1], feedback=feedback)
        draft = llm.generate(prompt, schema=SCHEMA, temperature=0.7, purpose=f"atlas script {episode_id}")
        found = problems(draft, allowed, owners, shown)
        if not found:
            return _episode(draft, topic, episode_id, series)
        log.info("%s draft %d: %s", episode_id, attempt, "; ".join(found))
        feedback = "\nYOUR LAST DRAFT BROKE THESE RULES; FIX ALL OF THEM:\n- " + "\n- ".join(found) + \
                   f"\nLast draft: {draft}"
    raise RuntimeError(f"{episode_id}: no draft passed after {TRIES} tries: {'; '.join(found)[:500]}")


def _episode(draft: dict, topic: dict, episode_id: str, series: str) -> AtlasEpisode:
    beats = []
    for b in draft["beats"]:
        isos = b.get("isos", [])
        if b["shot"] == "card":
            shot = {"kind": "card", "lines": [*draft["card_lines"][:2]]}
        elif b["shot"] == "country":
            shot = {"kind": "country", "iso": isos[0]}
        elif b["shot"] == "group":
            shot = {"kind": "group", "isos": isos}
        elif b["shot"] == "rank":
            shot = {"kind": "rank", "isos": isos}
        else:
            shot = {"kind": "world", "callouts": isos[:3]}
        beats.append({"text": b["text"].strip(), "shot": shot})
    ds_spec = {k: v for k, v in topic["dataset"].items() if k != "definition"}
    return AtlasEpisode.model_validate({
        "id": episode_id, "title": draft["title"].strip(), "format": topic.get("format", "map_reveal"),
        "series": series, "hook_text": draft["hook_text"].strip().upper(), "description": draft["description"].strip(),
        "hashtags": topic.get("hashtags", ["#maps", "#geography", "#data"]),
        "sources": [topic["source_url"]] if topic.get("source_url") else [],
        "dataset": ds_spec, "scale": topic.get("scale", {}), "value_format": topic.get("value_format", "{v:,.0f}"),
        "beats": beats,
    })
