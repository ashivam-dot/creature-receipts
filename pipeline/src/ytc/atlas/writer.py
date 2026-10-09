"""Write an Atlas script from its dataset: the model sees only the data summary and the publisher's own definition
of the indicator, and every number it says must be one the data supports."""

from __future__ import annotations

import logging
import re
import statistics

import requests

from .. import llm
from . import geo
from .data import Dataset, get
from .draw import short_name
from .episode import AtlasEpisode

log = logging.getLogger(__name__)

WORDS = (60, 110)
# Spoken words (numbers as said) that fit 44 s at the narrator's natural 2.55 words a second, plus the few that
# film.narrate's capped speed-up still says clearly; past that the speech check fails the Short.
SPOKEN_MAX = 118
BEATS = (6, 9)
TRIES = 6
MIN_COUNTRIES = 100
# Places with data that the map can't draw (tiny islands) are left out of what the writer may point at: the main
# landmass must span this much of the projected map (about 5 pixels across on the world view).
MIN_SIDE = 0.025

PROMPT = """You write 30 to 45 second YouTube Shorts for "Atlas in Numbers", a cinematic data channel. The picture
is a photoreal 3D globe that flies to each country you name, then real photos of that country with its flag and
value on screen; comparisons split the screen, rankings rise as a panel of flags. Your words carry the story: one
dataset, one surprising contrast, told like a sharp documentary narrator. Every claim comes from the data below; the
audience is curious adults worldwide.

TOPIC: {topic}
ANGLE: {angle}
FORMAT: {format}
DATASET: {label} ({unit}), {source}, {year}. {count} countries and territories are on the globe.
OFFICIAL DEFINITION (the only allowed basis for any "what it measures" line):
{definition}

DATA SUMMARY (values already rounded the way you may say them):
{summary}

Write {beats_min}-{beats_max} beats, {words_min}-{words_max} words in total, as JSON. Numbers take long to say
("3,947" is six spoken words): at most {spoken_max} words as spoken, so use only the numbers the story needs.
How a great Atlas script works:
- Beat 1 is the hook while the globe spins: a concrete contrast in at most 16 words that makes people stay, true by
  the data, e.g. "Every square kilometre of Bangladesh holds 1,333 people. In Australia, it's 4." Use the exact
  metric (subscriptions are not phones; basic water is not safe water). No "Did you know", no "Most people think",
  no question as the first beat.
- Then tell it as a story with a turn: the extreme, its opposite, a surprise (a famous country that isn't where
  people expect, or India or the USA when the data makes them interesting), and a payoff. Each country beat names
  its country and says its value, then makes the number felt: a contrast with another country, or a ratio from
  COMPARISONS ("377 times", said exactly as listed, in a beat that names both countries).
- Use one "group" beat to put 2 or 3 countries side by side (the screen splits between their photos).
- Never describe the map's colours or legend, and never say "among these countries", "measures", "reaches" or "with
  data": say the number plainly ("Japan: 340.", "Niger has 6.1.").
- You may add one short line on what is counted, only from the official definition, if it makes the number clearer.
  Never invent causes, history, or opinions.
- The last beat is a short question to the viewer that loops back to the hook (e.g. "Where does your country land?").
- Every beat adds something new: never repeat a number in the very next beat. No report-speak ("records",
  "registers", "standing at", "holding rank", "ranks 21st globally", "India's value"): talk like a person and
  name the thing ("2.3 times the food Burundi has").
- The beats of a finished script for another dataset, for their rhythm only (its numbers are not yours; ISO codes
  go only in "isos", never in "text"):
  {{"shot": "world", "isos": ["BGD", "AUS"], "text": "Every square kilometre of Bangladesh holds 1,333 people. In Australia, it's 4."}}
  {{"shot": "country", "isos": ["BGD"], "text": "Bangladesh is the most crowded big country on Earth. Fields, rivers and cities, all shared."}}
  {{"shot": "country", "isos": ["AUS"], "text": "Those same 1,333 people, in Australia, would spread across 377 square kilometres."}}
  {{"shot": "group", "isos": ["IND", "CHN"], "text": "India and China, the giants, aren't the most crowded. India has 488. China, just 150."}}
  {{"shot": "rank", "isos": ["MNG", "AUS", "CAN", "RUS"], "text": "The emptiest big countries? Mongolia, Australia, Canada and Russia, all under 10."}}
  {{"shot": "country", "isos": ["JPN"], "text": "And Japan, famous for its crowds, has 340. A quarter of Bangladesh."}}
  {{"shot": "card", "text": "Where does your country land?"}}
- Write every number as digits exactly as in the summary ("178", "3.2", "1.15 billion"). Never write numbers as
  words, not even "two worlds" or "three times"; rephrase instead ("a world apart"). Never round differently. Definition thresholds may quote the official definition exactly; never use
  a definition threshold as a country's measured value. A country's value goes only in
  a beat whose isos include that country.
- Put each country name directly before its own value; do not use shared lists followed by "respectively".
- Say a negative value as a fall without the minus sign: "-1.8%" becomes "shrinking by 1.8%" or "down 1.8%".
- These are latest available observations, not a time series. Never claim a trend over time: no "every year", "each year", "always", "more than
  ever", "for decades". "Shrinking by 1.8% a year" is fine; it states the rate.
- The "why" line is plain English a 12-year-old follows; no jargon such as "exponential", "de facto", "per capita".
- Plain spoken English, short punchy sentences, "you" is fine, no emojis, no hashtags in the beats, no politics or war.
- Shots: "world" (the spinning globe; list in isos the countries the beat names, up to 2), "country" (one iso: the
  globe dives to it, then its photos), "group" (2-3 isos side by side), "rank" (3-6 isos shown as a panel of flags
  and bars; the best way to show a top or bottom list, listed in the order you say them), or "card" for the last
  beat only. Use "rank" for exactly one middle beat when the FORMAT is rank_ladder, and at most once otherwise.
  Use only ISO codes from the summary.
- opening_options: propose 3 distinct factual openings, strongest first for clarity and curiosity, each with text
  (at most 16 words) and hook_text (2-5 words). Preserve the exact metric and universe. Never optimize by overclaiming.
- title: at most 60 characters, a concrete claim with a number, no clickbait punctuation, no emoji.
- hook_text: 2-5 words in capitals shown on screen over beat 1, adding to (not repeating) the spoken hook.
- card_lines: 2 short lines for the end card: a 2-4 word question, then the dataset label.
{feedback}"""

SCHEMA = {
    "type": "object",
    "properties": {
        "opening_options": {"type": "array", "items": {"type": "object", "properties": {
            "text": {"type": "string"}, "hook_text": {"type": "string"}}, "required": ["text", "hook_text"]}},
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
    "required": ["title", "hook_text", "description", "card_lines", "beats", "opening_options"],
}


def definition(ds_spec: dict) -> str:
    """The publisher's own note on what the indicator measures (World Bank `sourceNote`), or the topic's note."""
    if ds_spec.get("kind") == "worldbank":
        try:
            meta = get(f"https://api.worldbank.org/v2/indicator/{ds_spec['indicator']}",
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

    add(f"Countries and territories with data on the map: {len(vals)}", len(vals))
    add(f"Year: {ds.year_label}", *sorted(set(ds.years.values())))
    if ep_scale.get("kind") == "threshold":
        at = ep_scale["at"]
        above = [k for k, v in vals.items() if v >= at]
        add(f"Countries/territories at or above {at:g}: {len(above)} of {len(vals)}", len(above), at)
        add(f"Countries/territories below {at:g}: {len(vals) - len(above)}", len(vals) - len(above))
    median = statistics.median(vals.values())
    add(f"Median country: {_say(median, fmt)}", _say(median, fmt))
    lines.append(f"Top 12 of the {len(shown)} countries big enough to see on the map (iso, name, value):")
    for k, v in ranked[:12]:
        add(f"  {k} {names[k]}: {_say(v, fmt)} (year {ds.years[k]})", _say(v, fmt), iso=k)
    lines.append("Bottom 8:")
    for k, v in ranked[-8:]:
        add(f"  {k} {names[k]}: {_say(v, fmt)} (year {ds.years[k]})", _say(v, fmt), iso=k)
    every = sorted(vals.items(), key=lambda kv: kv[1], reverse=True)
    for label, (k, _) in (("highest", every[0]), ("lowest", every[-1])):
        if k in shown:
            lines.append(f"{names[k]} is the {label} of all {len(vals)} with data, so 'the world's {label}' is true of it.")
        else:
            lines.append(f"The true {label} is {names[k]}, too small to show. Never call another country the "
                         f"world's {label} or 'the fastest/most/least'; say 'one of the {label}' or compare instead.")
    lines.append(f"Notable countries (rank among the {len(shown)}):")
    for k in NOTABLE:
        if k in shown:
            rank = 1 + [x for x, _ in ranked].index(k)
            add(f"  {k} {names[k]}: {_say(vals[k], fmt)} (rank {rank}; year {ds.years[k]})", _say(vals[k], fmt), rank, iso=k)
    pairs = comparisons(shown, ranked, fmt)
    if pairs:
        lines.append("COMPARISONS (already computed; a ratio may be said only as written, in a beat naming both):")
        for a, b, text in pairs:
            lines.append(f"  {names[a]} has {text} times {names[b]}'s value")
            for f in _forms(text):
                owners.setdefault(f, set()).update({a, b})
    for n in range(1, 13):
        allowed.update(_forms(n))
    allowed.update({"100", "hundred", str(len(shown))})
    # Measurement definitions can contain numeric thresholds (e.g. broadband's 256 kbit/s).
    # Semantic review still binds their meaning; these are not country values.
    for token in _NUMBER.findall(ds.definition or ""):
        allowed.update(_forms(token))
    return "\n".join(lines), allowed, owners


NOTABLE = ("IND", "USA", "CHN", "GBR", "BRA", "NGA", "JPN", "DEU", "PAK", "IDN", "RUS", "AUS", "CAN", "MEX")


def ratio_text(r: float) -> str:
    """How a ratio is said: whole above 10 ("377"), one decimal below ("2.5"), never "3.0"."""
    return f"{r:,.0f}" if r >= 10 else f"{r:.1f}".removesuffix(".0")


def comparisons(shown: dict[str, float], ranked: list[tuple[str, float]], fmt: str,
                limit: int = 16) -> list[tuple[str, str, str]]:
    """(bigger iso, smaller iso, ratio text) for the pairs a script is most likely to contrast: the extremes and the
    notable countries. Only pairs whose displayed values are within 3% of the data, so the ratio said is also the
    one a viewer gets from the numbers on screen."""
    def shown_value(iso: str) -> float | None:
        m = _NUMBER.search(_say(shown[iso], fmt))
        if not m:
            return None
        d = float(m.group(0).replace(",", ""))
        return d if shown[iso] and abs(d - abs(shown[iso])) <= 0.03 * abs(shown[iso]) else None

    extremes = [k for k, _ in ranked[:3]] + [k for k, _ in ranked[-3:]]
    notable = [k for k in NOTABLE if k in shown and k not in extremes][:6]
    pool = list(dict.fromkeys(extremes + notable))
    out = []
    for i, a in enumerate(pool):
        for b in pool[i + 1:]:
            va, vb = shown_value(a), shown_value(b)
            if va is None or vb is None or va <= 0 or vb <= 0 or "-" in _say(shown[a], fmt) + _say(shown[b], fmt):
                continue
            hi, lo = (a, b) if va >= vb else (b, a)
            r = max(va, vb) / min(va, vb)
            if r < 1.5:
                continue
            # The two extremes first, then an extreme against a famous country, then famous against famous.
            famous = (a in notable) + (b in notable)
            kind = 0 if {a, b} == {ranked[0][0], ranked[-1][0]} else {1: 1, 2: 2}.get(famous, 3)
            out.append((kind, -r, hi, lo, ratio_text(r)))
    out.sort()
    return [(a, b, t) for _, _, a, b, t in out[:limit]]


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


_COLOUR_TALK = re.compile(r"\b(yellow|blue|grey|gray|gold|red|green|orange|purple|pink|brown|colou?r(s|ed)?|legend|"
                          r"shaded)\b", re.I)
_FILLER = re.compile(r"\b(among these (countries|places)|with data|measures|reaches|is mapped|mapped across)\b", re.I)
_REPAIRS = ((re.compile(r"\b(countries|places)( and territories)? with data\b", re.I), r"\1\2"),
            (re.compile(r"\breaches\b", re.I), "hits"),
            (re.compile(r"\b(records|registers)\b", re.I), "has"))
# "3.5 times older" says 3.5 times the age difference, not 3.5 times the age; "times less" has no clear meaning.
_LOOSE_RATIO = re.compile(r"\btimes (older|younger|less|fewer|smaller|lower|cheaper|poorer)\b", re.I)
_REPORT_SPEAK = re.compile(r"\b(standing (as|at)|holding (the )?rank|ranks? \d+(st|nd|rd|th)? (globally|worldwide)|"
                           r"\w+'s value|the value of)\b", re.I)


def spoken_words(text: str) -> int:
    """Words as the narrator says them: "3,947" is six ("three thousand nine hundred forty-seven"), not one."""
    def say(m: re.Match) -> str:
        token = m.group(0).replace(",", "")
        try:
            from num2words import num2words
            return num2words(float(token) if "." in token else int(token)).replace("-", " ").replace(",", "")
        except (ImportError, ValueError, OverflowError):
            return " ".join("x" * (1 + len(token) // 2))
    return len(_NUMBER.sub(say, text).replace(" and ", " ").split())


def strip_codes(text: str, isos: set[str]) -> str:
    """ISO codes copied into the narration ("FIN Finland", "USA USA") are dropped; "USA" alone stays a name."""
    text = re.sub(r"\b([A-Z]{3})\s+(?=[A-Z])", lambda m: "" if m.group(1) in isos and m.group(1) != "USA" else m.group(0),
                  text)
    return re.sub(r"\b(USA|UAE)\s+(?=\1\b|United\b)", "", text)


def plain(text: str) -> str:
    """Fillers with a plain equivalent are repaired here rather than costing a rewrite."""
    for pattern, repl in _REPAIRS:
        text = pattern.sub(repl, text)
    return text


_TREND = re.compile(r"\b(every (single )?year|each year|always|for decades|more than ever)\b", re.I)
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_WORD_NUMBERS = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|"
                           r"fifty|sixty|seventy|eighty|ninety|thousand|million|billion|percent)\b", re.I)


def number_problems(text: str, allowed: set[str], owners: dict[str, set[str]] | None = None,
                    isos: list[str] | None = None, quoted: str = "") -> list[str]:
    """`quoted` is the official definition, whose own words ("two halves") may be quoted as they are."""
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
        if quoted and re.search(rf"\b{word}\b", quoted, re.I):
            continue
        problems.append(f"write '{m.group(0)}' as digits from the summary")
    return problems


def problems(draft: dict, allowed: set[str], owners: dict[str, set[str]], vals: dict[str, float],
             quoted: str = "") -> list[str]:
    out = []
    beats = draft.get("beats", [])
    words = sum(len(b["text"].split()) for b in beats)
    if not BEATS[0] <= len(beats) <= BEATS[1]:
        out.append(f"{len(beats)} beats; write {BEATS[0]}-{BEATS[1]}")
    if not WORDS[0] <= words <= WORDS[1]:
        out.append(f"{words} words; write {WORDS[0]}-{WORDS[1]}")
    if (spoken := sum(spoken_words(b["text"]) for b in beats)) > SPOKEN_MAX:
        out.append(f"{spoken} words as spoken (a number counts as said: '3,947' is 6 words); cut about "
                   f"{spoken - SPOKEN_MAX + 5}: drop a number or a clause")
    if len(draft.get("title", "")) > 60:
        out.append("the title is over 60 characters")
    if beats and beats[0]["shot"] != "world":
        out.append("beat 1 must be a world shot")
    if beats and beats[-1]["shot"] != "card":
        out.append("the last beat must be the card")
    if beats and (n := len(beats[0]["text"].split())) > 16:
        out.append(f"the hook (beat 1 and every opening option) is {n} words; at most 16, shaped like "
                   "'<country> has <value>. In <other country>, it's <value>.'")
    if beats and beats[0]["text"].strip().endswith("?"):
        out.append("the hook must be a statement ending in a full stop, not a question")
    for where, text in [("title", draft.get("title", "")), *((f"beat {i}", b["text"]) for i, b in enumerate(beats, 1))]:
        if loose := _LOOSE_RATIO.search(text):
            out.append(f"{where}: '{loose.group(0)}' misstates a ratio; say 'N times the <measure> of <country>' "
                       "or 'a third of'")
    used = []
    for i, b in enumerate(beats, 1):
        isos = b.get("isos", [])
        used += isos
        if colour := _COLOUR_TALK.search(b["text"]):
            out.append(f"beat {i}: '{colour.group(0)}' describes the map; say the numbers and places instead")
        if filler := _FILLER.search(b["text"]):
            out.append(f"beat {i}: drop the filler '{filler.group(0)}'; say the number plainly")
        if report := _REPORT_SPEAK.search(b["text"]):
            out.append(f"beat {i}: '{report.group(0)}' is report-speak; say it the way a person would")
        repeated = set(_NUMBER.findall(b["text"])) & set(_NUMBER.findall(beats[i - 2]["text"])) if i > 1 else set()
        if again := {n for n in repeated if owners.get(n) or owners.get(n.replace(",", ""))}:
            out.append(f"beat {i}: repeats {', '.join(sorted(again))} from the beat before; add something new")
        if trend := _TREND.search(b["text"]):
            out.append(f"beat {i}: '{trend.group(0)}' claims a trend, but the data is one year")
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
        out += [f"beat {i}: {p}" for p in number_problems(b["text"], allowed, owners,
                    list(vals) if b["shot"] == "world" else isos, quoted)]
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
    feedback = ""
    for attempt in range(1, TRIES + 1):
        prompt = PROMPT.format(topic=topic["topic"], angle=topic.get("angle", ""), format=topic.get("format", "map_reveal"),
                               label=ds.label, unit=ds.unit, source=ds.source, year=ds.year_label, count=len(vals),
                               definition=topic.get("definition_text", "") or "(none given)",
                               summary=summary, beats_min=BEATS[0], beats_max=BEATS[1], words_min=WORDS[0],
                               words_max=WORDS[1], spoken_max=SPOKEN_MAX, feedback=feedback)
        draft = llm.generate(prompt, schema=SCHEMA, temperature=0.7,
                             models=(*llm.FLASH, *llm.FLASH_LITE, *llm.BACKUP_STRONG),
                             purpose=f"atlas script {episode_id}")
        for beat in [*draft.get("beats", []), *draft.get("opening_options", [])]:
            beat["text"] = plain(strip_codes(beat["text"], set(vals)))
        # Bind named country/value clauses to their world-shot callouts instead of wasting a rewrite.
        for beat in draft.get("beats", []):
            if beat["shot"] != "world":
                continue
            isos = beat.setdefault("isos", [])
            for number in _NUMBER.findall(beat["text"]):
                for iso in owners.get(number.replace(",", ""), set()):
                    names = {ds.names.get(iso, ""), geo.world()[iso].name, short_name(geo.world()[iso].name)}
                    if iso not in isos and any(name and re.search(r"\b" + re.escape(name) + r"\b", beat["text"], re.I) for name in names):
                        isos.append(iso)
        # A pair is a comparison, not a ranking. Repair structure without another model call.
        for beat in draft.get("beats", []):
            if beat["shot"] == "rank" and len(beat.get("isos", [])) == 2:
                beat["shot"] = "group"
        # Try the ranked factual openings against the same deterministic contract; render only one.
        import copy
        for option in draft.get("opening_options", [])[:3]:
            candidate = copy.deepcopy(draft)
            candidate["beats"][0]["text"] = option["text"]
            candidate["hook_text"] = option["hook_text"]
            if not problems(candidate, allowed, owners, shown, topic.get("definition_text", "")):
                draft = candidate
                break
        found = problems(draft, allowed, owners, shown, topic.get("definition_text", ""))
        if not found:
            return _episode(draft, topic, episode_id, series)
        log.info("%s draft %d: %s", episode_id, attempt, "; ".join(found))
        feedback = "\nYOUR LAST DRAFT BROKE THESE RULES; FIX ALL OF THEM:\n- " + "\n- ".join(found) + \
                   f"\nLast draft: {draft}"
    raise RuntimeError(f"{episode_id}: no draft passed after {TRIES} tries: {'; '.join(found)[:500]}")


def _episode(draft: dict, topic: dict, episode_id: str, series: str) -> AtlasEpisode:
    # Aggregate totals cover World Bank countries AND territories; repair this terminology deterministically.
    draft["title"] = re.sub(r"\bcountries\b", "places", draft["title"], flags=re.I)
    draft["hook_text"] = re.sub(r"\bcountries\b", "PLACES", draft["hook_text"], flags=re.I)
    draft["description"] = re.sub(r"\bcountries\b(?! and territories)", "countries and territories", draft["description"], flags=re.I)
    beats = []
    for b in draft["beats"]:
        b["text"] = re.sub(r"\b(\d+) countries\b(?! and territories)", r"\1 countries and territories", b["text"], flags=re.I)
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
