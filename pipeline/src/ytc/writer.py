"""Write an episode from its research: the script and metadata, checked against strategy/SCRIPT-RULES.md."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import yaml

from . import llm

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
SERIES = (
    "Built Different",
    "Deep Sea Files",
    "Back From Extinction",
    "Evolution Got Weird",
    "Nature's Record Breakers",
    "Animal Myths, Busted",
)
HOOK_STYLES = ["statement", "question", "number", "contradiction"]
# Shapes an episode can take. The writer is given the one the recent episodes used least, so the channel never
# settles into one template (YouTube demonetizes "narrated stories with only superficial differences").
STRUCTURES = {
    "story": "hook, context, 2 or 3 escalating beats, then a twist or payoff near the end",
    "myth_vs_fact": "open on what most people believe, then the evidence that overturns it beat by beat, ending on the true fact",
    "scale_ladder": "start from something familiar, then 3 to 5 steps of comparison up (or down) to the astonishing true "
                    "size, speed, age, or number",
    "mystery": "open on something that made no sense, give the clues in the order they were found, then the answer",
    "record": "open on the record itself, then what it beat, the trick or cost behind it, and the surprise nobody expected",
}
# Two scripts sharing this share of their three-word phrases read as the same script with the nouns swapped.
SAME_SCRIPT = 0.25
# A hook whose first this-many words match a recent hook's opens on a template.
SAME_OPENING = 4
RECENT = 40
# Rewrites of a draft that breaks the script rules before the Short is given up; each starts from the draft with
# the fewest problems so far, since a weaker backup model can make a fix worse.
FIX_ROUNDS = 3
SFX = ["none", "whoosh", "pop", "riser"]
CARD_KINDS = ["none", "dateline", "fact", "quote"]
# The longest a title card's lines may be, in characters, so they stay large on a phone.
CARD_BIG = {"dateline": 24, "fact": 28, "quote": 90}
CARD_SMALL = 60
_OVERRIDE = re.compile(r"\[([^\]]+)\]\(/[^)]*/\)")
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF]")

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "hooks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"style": {"type": "string", "enum": HOOK_STYLES}, "text": {"type": "string"}},
                "required": ["style", "text"],
            },
        },
        "hook_style": {"type": "string", "enum": HOOK_STYLES},
        "structure": {"type": "string", "enum": list(STRUCTURES)},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "beats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "emphasis": {"type": "array", "items": {"type": "string"}},
                    "sfx": {"type": "string", "enum": SFX},
                    "pause_after": {"type": "number"},
                    "claims": {"type": "array", "items": {"type": "integer"}},
                    "visual": {"type": "string"},
                    "subjects": {"type": "array", "items": {"type": "string"}},
                    "year": {"type": "integer"},
                    "queries": {"type": "array", "items": {"type": "string"}},
                    "card": {
                        "type": "object",
                        "properties": {"kind": {"type": "string", "enum": CARD_KINDS}, "big": {"type": "string"},
                                       "small": {"type": "string"}},
                        "required": ["kind", "big", "small"],
                    },
                },
                "required": ["text", "emphasis", "sfx", "pause_after", "claims", "visual", "subjects", "year", "queries", "card"],
            },
        },
        "hook_text": {"type": "string"},
        "loop": {"type": "boolean"},
        "better_than_last": {"type": "string"},
    },
    "required": ["hooks", "hook_style", "title", "description", "hashtags", "tags", "beats", "hook_text", "loop",
                 "better_than_last"],
}

PROMPT = """You write Shorts for Creature Receipts (@CreatureReceipts): true, surprising, sourced stories of strange
animals, extreme biology, and deep-sea life, in American English for a US audience. Promise: one true,
jaw-dropping animal story in under a minute, with receipts. Every Short tells a real story (a discovery, an
experiment, a record, a scientist's surprise), never a list of animal facts. No gore, predation close-ups, dead
animals, or animal cruelty, and never health advice.

Episode {id}, series "{series}". Topic: {topic}
Structure: {structure} ({structure_how}). Set structure to "{structure}".

Follow these rules exactly:

{rules}

What the channel has learned so far (apply every proven rule; try to beat the numbers):

{learnings}

Recent episodes, for format and tone only. Don't reuse their wording or structure beat for beat:

{exemplars}

Research. The numbered claims are the only facts you may state; say nothing beyond them.

Story: {story}
Most surprising fact: {angle}
Claims:
{claims}
Disputed (leave out, or attribute "according to one account"):
{disputed}
Visual ideas:
{visuals}

Write the episode:
- hooks: three candidate first lines in different styles, each 12 words or fewer, opening inside the story
  on its most surprising true fact. Use the strongest as beat 1 and name its style in hook_style.
- beats: 6 to 9 beats and 105 to 135 spoken words in total, one or two short sentences each. Follow the
  structure above, and end with a last beat that loops back to beat 1. The twist is the claim a curious viewer is least likely to know already; for a famous subject, build
  the Short around its least-known true detail instead of retelling the familiar story in order.
- The loop: the last beat is a complete, grammatical sentence on its own that echoes beat 1's image or question,
  so replaying beat 1 feels like the natural next line (a last beat "Scientists had declared it extinct for 66
  million years." before a first beat "In 1938, a fisherman hauled up a fish that was supposed to be a fossil.").
  Never end on a dangling
  word such as "because", "when", "until", or "that". Set loop to true when it loops.
- Each beat: claims lists the numbers of the claims it states (the last beat may reuse the hook's);
  emphasis has 1 or 2 words or short phrases copied exactly from that beat's text; sfx is "whoosh" on up to 3
  scene changes, "pop" on up to 2 punchlines, "riser" once just before the twist, otherwise "none";
  pause_after is 0.12, or 0.4 after a punchline.
- Each beat's picture: visual describes the ideal picture the way a field guide, NOAA, or iNaturalist would
  caption the photo (species, behavior, place, year), in 15 words or fewer ("peacock mantis shrimp on a reef,
  Philippines"; "coelacanth swimming off Sodwana Bay, South Africa, 2000"; "NOAA ROV image of a vampire squid,
  Gulf of Mexico"; "Biodiversity Heritage Library plate of a giant squid, 1879"); subjects lists 0 to 3 exact
  English Wikipedia article titles for the species, scientists, places, or events that picture shows, most
  specific first ("Peacock mantis shrimp", "Mantis shrimp", "Coelacanth", "Marjorie Courtenay-Latimer"); year
  is when the beat takes place (0 if it has no time); queries gives 2 or 3 Wikimedia Commons searches for it,
  naming the exact species (common or scientific name).
- Each beat's card: a title card shown instead when no picture fits. kind "dateline" (big: the date, like
  "December 1938"; small: the place or expedition), "fact" (big: a number or a fact of 1 to 3 words from the line,
  like "50 mph punch"; small: a few words explaining it), or "quote" (big: words quoted in the claims, exactly; small:
  who said or wrote them). Use only that beat's text and claims. Use kind "none", with big and small empty, when
  the beat has no date, number, or quote worth a card.
- hook_text: 2 to 6 words on screen over beat 1 that add to the spoken hook without repeating it or giving away
  the payoff ("A FOSSIL THAT SWAM").
- title, description, hashtags, tags: per the metadata rules. The first hashtag is #animals.
- better_than_last: one sentence naming the learning or improvement this episode applies, and where.
"""


def _between(text: str, start: str, end: str | None) -> str:
    begin = text.index(start)
    stop = text.index(end, begin) if end and end in text[begin:] else len(text)
    return text[begin:stop].strip()


def _rules() -> str:
    rules = (ROOT / "strategy" / "SCRIPT-RULES.md").read_text(encoding="utf-8")
    return "\n\n".join(
        [_between(rules, "## Script rules", "## Metadata rules"), _between(rules, "## Metadata rules", "## Visual rules"),
         _between(rules, "## Sound rules", "## Spec schema")]
    )


def _learnings() -> str:
    text = (ROOT / "strategy" / "LEARNINGS.md").read_text(encoding="utf-8")
    return text.split("## Log")[0].strip()


def exemplars(count: int = 2) -> str:
    """The newest scheduled or live specs, trimmed to what shows format and tone."""
    folders = sorted((ROOT / "content" / "episodes").glob("ep*/publish.json"), reverse=True)[:count]
    blocks = []
    for record in folders:
        spec = yaml.safe_load((record.parent / "short.yaml").read_text(encoding="utf-8"))
        beats = [{"text": b["text"], "emphasis": b.get("emphasis", []), "sfx": b.get("sfx", "none")} for b in spec["beats"]]
        blocks.append(yaml.safe_dump({"title": spec["title"], "series": spec.get("series"), "beats": beats},
                                     sort_keys=False, allow_unicode=True, width=120))
    return "\n---\n".join(blocks) or "(none yet)"


def recent_scripts(topic: str | None = None, count: int = RECENT) -> list[dict]:
    """The newest made episodes' scripts (id, structure, spoken beats), leaving out the given topic's own drafts."""
    out = []
    for folder in sorted((ROOT / "content" / "episodes").glob("ep*"), reverse=True):
        try:
            spec = yaml.safe_load((folder / "short.yaml").read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        try:
            meta = json.loads((folder / "script.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        try:
            own = json.loads((folder / "research.json").read_text(encoding="utf-8")).get("topic")
        except (OSError, ValueError):
            own = None
        if topic and own == topic:
            continue
        out.append({"id": folder.name, "structure": meta.get("structure"), "beats": [spoken(b["text"]) for b in spec.get("beats", [])]})
        if len(out) >= count:
            break
    return out


def choose_structure(recent: list[dict]) -> str:
    """The structure the last 8 episodes used least (the first listed on a tie)."""
    used = [r["structure"] for r in recent[:8] if r.get("structure") in STRUCTURES]
    return min(STRUCTURES, key=lambda s: (used.count(s), list(STRUCTURES).index(s)))


def _trigrams(text: str) -> set[tuple[str, ...]]:
    words = _plain_words(text)
    return {tuple(words[i:i + 3]) for i in range(len(words) - 2)}


def sameness(beats: list[str], recent: list[dict]) -> list[str]:
    """Ways a script repeats a recent one: most of its phrasing, or its hook's opening words."""
    found = []
    mine = _trigrams(" ".join(beats))
    opening = _plain_words(beats[0])[:SAME_OPENING] if beats else []
    for other in recent:
        theirs = _trigrams(" ".join(other["beats"]))
        if mine and theirs and len(mine & theirs) / len(mine | theirs) >= SAME_SCRIPT:
            found.append(f"The script reuses much of {other['id']}'s wording; write it fresh in your own words.")
        if len(opening) == SAME_OPENING and other["beats"] and _plain_words(other["beats"][0])[:SAME_OPENING] == opening:
            found.append(f"The hook opens with the same words as {other['id']}'s ({' '.join(opening)}...); open differently.")
    return found[:2]


def spoken(text: str) -> str:
    return _OVERRIDE.sub(r"\1", text)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.,\-]*", spoken(text)))


def _plain_words(text: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)+|[a-z0-9']+", spoken(text).lower().replace(",", ""))


def _card_ok(card: dict, beat: dict, research: dict) -> bool:
    """A title card states nothing its beat and the beat's claims don't: its numbers, and a quote word for word."""
    kind, big, small = card.get("kind"), (card.get("big") or "").strip(), (card.get("small") or "").strip()
    if kind not in CARD_BIG or not big or len(big) > CARD_BIG[kind] or len(small) > CARD_SMALL or _EMOJI.search(big + small):
        return False
    claims = research.get("claims", [])
    cited = " ".join(claims[c - 1]["claim"] for c in beat.get("claims", []) if 1 <= c <= len(claims))
    known = " ".join(_plain_words(f"{beat['text']} {cited}"))
    for number in re.findall(r"\d[\d,.]*", f"{big} {small}"):
        if number.replace(",", "").rstrip(".") not in known.replace(",", ""):
            return False
    if kind == "quote":
        quoted = " ".join(_plain_words(big.strip("\"“”'")))
        return bool(quoted) and quoted in " ".join(_plain_words(" ".join(c["claim"] for c in claims)))
    return True


def normalize(script: dict, research: dict | None = None) -> dict:
    """Fix the mechanical slips (hashtag case, stray emphasis, too many sound effects or tags, a long
    description, missing picture searches, a card or on-screen hook that breaks the rules) without another call."""
    tags = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in script.get("hashtags", [])]
    tags = list(dict.fromkeys(["animals"] + [t for t in tags if t and t != "animals"]))
    if len(tags) >= 3:
        script["hashtags"] = [f"#{t}" for t in tags[:3]]
    script["tags"] = list(dict.fromkeys(t.strip() for t in script.get("tags", []) if isinstance(t, str) and t.strip()))[:8]
    sentences = re.split(r"(?<=[.!?])\s+", (script.get("description") or "").strip())
    script["description"] = " ".join(sentences[:2])
    limits = {"whoosh": 3, "pop": 2, "riser": 1}
    for beat in script.get("beats", []):
        text = spoken(beat["text"]).lower()
        kept = [e for e in beat.get("emphasis", []) if e.lower() in text]
        if kept:
            beat["emphasis"] = kept[:2]
        sfx = beat.get("sfx", "none")
        if sfx in limits:
            limits[sfx] -= 1
            if limits[sfx] < 0:
                beat["sfx"] = "none"
        beat["pause_after"] = min(max(float(beat.get("pause_after", 0.12)), 0.12), 0.6)
        beat["subjects"] = [s.strip() for s in beat.get("subjects") or [] if isinstance(s, str) and s.strip()][:3]
        queries = [q.strip() for q in beat.get("queries") or [] if isinstance(q, str) and q.strip()]
        for extra in (*beat["subjects"], beat.get("visual", "")):
            if len(queries) < 2 and extra and extra not in queries:
                queries.append(extra)
        beat["queries"] = queries[:3]
        try:
            beat["year"] = int(beat.get("year") or 0)
        except (TypeError, ValueError):
            beat["year"] = 0
        card = beat.get("card") or {}
        if card.get("kind", "none") != "none" and not (research and _card_ok(card, beat, research)):
            log.info("dropping a title card that states more than its beat: %s", card)
            beat["card"] = {"kind": "none", "big": "", "small": ""}
    hook_text = " ".join((script.get("hook_text") or "").split())
    hook = set(_plain_words(script["beats"][0]["text"])) if script.get("beats") else set()
    words = _plain_words(hook_text)
    if not 2 <= len(words) <= 6 or len(hook_text) > 40 or _EMOJI.search(hook_text) or sum(w in hook for w in words) > 0.7 * len(words):
        hook_text = ""
    script["hook_text"] = hook_text
    return script


DANGLING_END = r"\b(because|when|until|that|and|but|so|as|while|after|before|if|since|which|with|of|to|the|a)\W*$"


def problems(script: dict, research: dict) -> list[str]:
    """Every way the draft breaks the script rules, as instructions for a rewrite."""
    found = []
    beats = script.get("beats", [])
    total = sum(word_count(b["text"]) for b in beats)
    if not 6 <= len(beats) <= 9:
        found.append(f"Use 6 to 9 beats (you have {len(beats)}).")
    if not 105 <= total <= 135:
        per_beat = ", ".join(f"beat {n}: {word_count(b['text'])}" for n, b in enumerate(beats, start=1))
        change = f"add at least {105 - total}" if total < 105 else f"cut at least {total - 135}"
        found.append(f"Use 105 to 135 spoken words in total (you have {total}): {change} words, aiming for about "
                     f"120, by lengthening or trimming the middle beats rather than the hook. Words now: {per_beat}.")
    if beats:
        hook = spoken(beats[0]["text"])
        if word_count(hook) > 12:
            found.append(f"The hook (beat 1) must be 12 words or fewer (it has {word_count(hook)}: \"{hook}\"); "
                         f"cut at least {word_count(hook) - 12} words and keep its meaning.")
        if re.match(r"\s*(did you know|hey|hi|welcome)", hook, re.I) or "creature receipts" in hook.lower():
            found.append("The hook must open inside the story: no 'Did you know', greeting, or channel name.")
        if re.search(DANGLING_END, spoken(beats[-1]["text"]), re.I):
            found.append("The last beat must be a complete sentence that echoes beat 1, not end on a dangling word "
                         "such as 'because', 'when', 'until', or 'that'.")
    title = script.get("title", "")
    if len(title) > 60:
        found.append(f"The title must be 60 characters or fewer (it has {len(title)}).")
    if _EMOJI.search(title) or len([w for w in re.findall(r"\b[A-Z]{2,}\b", title) if w not in ("US", "UK", "USA", "TV")]) > 1:
        found.append("The title may have at most one word in capitals and no emojis.")
    tags = script.get("hashtags", [])
    if len(tags) != 3 or (tags and tags[0] != "#animals") or any(not re.fullmatch(r"#[a-z0-9]+", t) for t in tags):
        found.append("Give exactly 3 lowercase hashtags with no spaces, the first being #animals.")
    if not 4 <= len(script.get("tags", [])) <= 8:
        found.append("Give 4 to 8 tags.")
    if len(re.findall(r"[.!?](\s|$)", script.get("description", "").strip())) > 2:
        found.append("The description must be 1 or 2 sentences.")
    claim_count = len(research.get("claims", []))
    counts = {s: 0 for s in SFX}
    for number, beat in enumerate(beats, start=1):
        counts[beat.get("sfx", "none")] += 1
        text = spoken(beat["text"]).lower()
        emphasis = beat.get("emphasis", [])
        if not 1 <= len(emphasis) <= 2 or any(e.lower() not in text for e in emphasis):
            found.append(f"Beat {number}: emphasis needs 1 or 2 words or phrases copied exactly from its text.")
        cited = beat.get("claims", [])
        if any(not 1 <= c <= claim_count for c in cited):
            found.append(f"Beat {number}: claims must be numbers from 1 to {claim_count}.")
        if not cited and number != len(beats):
            found.append(f"Beat {number}: list the claims it states; every fact must come from the research.")
        if not 0.1 <= beat.get("pause_after", 0.12) <= 0.6:
            found.append(f"Beat {number}: pause_after must be between 0.12 and 0.6.")
        if not beat.get("queries"):
            found.append(f"Beat {number}: give 2 or 3 Commons queries.")
    if counts["whoosh"] > 3 or counts["pop"] > 2 or counts["riser"] > 1:
        found.append("Use sfx whoosh at most 3 times, pop at most 2, riser at most once.")
    if beats:
        found += sameness([spoken(b["text"]) for b in beats], recent_scripts(research.get("topic")))
    return found


def _claims_listing(research: dict) -> str:
    return "\n".join(f"{n}. {c['claim']} ({c['confidence']})" for n, c in enumerate(research["claims"], start=1))


def write_script(research: dict, episode_id: str, feedback: list[str] | None = None, draft: dict | None = None) -> dict:
    """A script that meets the rules, from the research alone. With a reviewer's feedback on a rendered draft,
    a revision of that draft. Raises if FIX_ROUNDS rewrites can't fix it."""
    structure = (draft or {}).get("structure") if (draft or {}).get("structure") in STRUCTURES else None
    structure = structure or choose_structure(recent_scripts(research.get("topic")))
    prompt = PROMPT.format(
        id=episode_id,
        series=research["series"],
        topic=research["topic"],
        structure=structure,
        structure_how=STRUCTURES[structure],
        rules=_rules(),
        learnings=_learnings(),
        exemplars=exemplars(),
        story=research.get("story", ""),
        angle=research.get("angle", ""),
        claims=_claims_listing(research),
        disputed="\n".join(f"- {d}" for d in research.get("disputed", [])) or "- none",
        visuals="\n".join(f"- {v['subject']}: {'; '.join(v['queries'])}" for v in research.get("visuals", [])),
    )
    if feedback and draft:
        prompt += (
            "\n\nA reviewer watched the render of your draft and asks for these changes:\n"
            + "\n".join(f"- {item}" for item in feedback)
            + "\n\nKeep what works, make these changes within the rules, and return the whole episode again. "
            "Your draft:\n" + json.dumps(draft, indent=1)
        )
    script = llm.generate(prompt, schema=SCRIPT_SCHEMA, purpose=f"{episode_id} script" + (" revision" if feedback else ""))
    best = None
    for attempt in range(FIX_ROUNDS + 1):
        script = normalize(script, research) | {"structure": structure}
        issues = problems(script, research)
        if not issues:
            return script
        if best is None or len(issues) <= len(best[1]):
            best = (script, issues)
        if attempt == FIX_ROUNDS:
            break
        log.info("%s script needs fixes: %s", episode_id, issues)
        script, issues = best
        script = llm.generate(
            prompt + "\n\nYour draft broke these rules:\n" + "\n".join(f"- {i}" for i in issues)
            + "\n\nFix every one, change nothing else, and return the whole episode again. Your draft:\n"
            + json.dumps(script, indent=1),
            schema=SCRIPT_SCHEMA, purpose=f"{episode_id} script fix {attempt + 1}",
        )
    raise RuntimeError(f"{episode_id} script still breaks the rules: {best[1]}")
