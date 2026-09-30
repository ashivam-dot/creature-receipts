# Adapting the studio to a new niche

The kit is the Days of Odd studio with that channel's identity replaced by placeholders (Kit Channel,
@KitChannel, `kit-channel`, `kit-owner/kit-channel`). The code doesn't care what the niche is, except in
the places marked `NICHE:`. Those are prompts, rules, and templates that describe strange-but-true
history. The full list is at the end of this file, generated when the kit was built.

1. `python3 kit/configure.py ...` sets the identity, the series, the first hashtag, and the launch date.
   It's mechanical and can be run again.
2. Rewrite each `NICHE:` spot for the new niche, then delete its marker line.
3. Write the strategy documents and seed the calendar.
4. Make the brand.
5. Run `python3 kit/verify.py --stage adapted` until it passes. Then make the first Short (START-HERE,
   Phase 4) and let its scores and the owner's reaction drive another round.

## What the machinery assumes

Keep these unless you change the code knowingly.

- **Topics come through Wikipedia.** Research (`research.gather`) reads the topic's English Wikipedia
  articles, the pages they cite, and web search results. The model builds a claims table from those texts
  alone, and a claim counts only when two different sites state it. A topic with fewer than 8 such claims
  is dropped. The daily routine asks for new topics with an exact Wikipedia title and checks that the
  article exists (`auto.add_topics`), and it takes the backlog's most-read articles first (`auto.demand`).
  So every topic needs an English Wikipedia article and some reputable coverage.
- **The script's shape is enforced** (`writer.problems`): 6 to 9 beats, 105 to 135 spoken words, a hook of
  12 words or fewer that opens inside the story, a title of 60 characters or fewer, exactly 3 hashtags
  with the channel's own first, and a last line that runs back into the first so the Short loops.
- **Pictures are found by subject** (`sources.gather`). Each beat names what it shows as English Wikipedia
  titles; Wikidata and Commons give that subject's own picture, its category, and files depicting it.
  Keyword searches and Openverse, Wellcome Collection, the Met, and the Art Institute of Chicago fill in.
  Only public domain, CC0, and CC BY pictures come back (with credits written into the description).
  SigLIP scores the matches (`rank.py`), the model picks (`pick.py`), and a second look vetoes clear
  mistakes. A beat with no good picture becomes a title card (a date, a number, or a quote).
- **Voice:** Kokoro-82M, `af_heart`, American English (`studio.VOICE`). Kokoro's other English voices
  include `af_bella`, `af_nicole`, `am_michael`, `am_fenrir`, and `bf_emma`. `uv run --no-sync ytc phonemes
  "<text>"` shows how the narrator will say something.
- **The quality gate** (`studio.REVIEW_PROMPT`): hook, clarity, payoff, visuals, and loop, each scored 1 to
  5. Anything under 4 gets up to two rounds of fixes, then the Short is rejected. `ytc check` separately
  enforces 35 to 58 seconds, -14 LUFS loudness, and a speech check with faster-whisper.
- **Publishing:** US Eastern slots (`publish.SLOTS`, `publish.AUDIENCE_TZ`), 2 or 3 a day depending on
  stock. Buffer's free queue holds 10 posts, and the studio keeps up to 42 finished Shorts waiting.
- **Time zone:** reports, alerts, and the daily routine's hour use IST (`IST` in `auto.py`, `studio.py`,
  and `monitor/monitor.py`), and the schedules are set around Gemini's quota reset. If the owner isn't in
  India, everything still works; only the times shown are in IST.

## Rewriting the NICHE spots

| Where | What it is | What to change |
|---|---|---|
| `pipeline/src/ytc/writer.py`, `PROMPT` | The scriptwriter's prompt | The channel's promise and audience. Replace the history examples (the Cardiff Giant, Elsie Wright, the emus) with examples from the niche that follow the same rules. "The way an archive would caption it" becomes the way a picture library would caption the niche's pictures. Keep the rules, lengths, fields, and the Wikipedia `subjects` and Commons `queries`. |
| `pipeline/src/ytc/research.py`, `PROMPT` | The research brief | The channel description, and the kinds of pictures to suggest (for space: telescope images, spacecraft photos, mission patches, diagrams). |
| `pipeline/src/ytc/research.py`, `TRUSTED` | Sites read first | Add the niche's reputable sources (for space: nasa.gov, esa.int, eso.org, jpl.nasa.gov, space.com, skyandtelescope.org, scientificamerican.com, nature.com). Keep `SKIP` as it is. |
| `pipeline/src/ytc/pick.py`, `PICK_PROMPT` and `VERIFY_PROMPT` | Picture choice and the second look | Replace "a history Short" and the period wording with the niche's. The rule against anachronistic pictures only matters for historical lines. Keep every safety rule: no gore, nudity, big watermarks, or text-only pages. |
| `pipeline/src/ytc/pick.py`, `MODERN_BEFORE` | Penalizes modern color photos in beats set before 1945 | A modern niche can keep it (beats with no year, or a year after 1945, aren't affected), or set it to 0 to switch it off. |
| `pipeline/src/ytc/studio.py`, `REVIEW_PROMPT` | The quality gate | The channel description. Keep the scores, thresholds, and output. |
| `pipeline/src/ytc/auto.py`, the topics prompt in `add_topics` | New topics every day | The channel description, "told with archive pictures", the picture-source hint, and the example topic line ("The Great Molasses Flood (1919)"). Keep the rule about an exact English Wikipedia title. |
| `pipeline/src/ytc/auto.py`, the prompts in `update_learnings` and `weekly_review` | Analytics write-ups | The channel description only. |
| `pipeline/src/ytc/publish.py`, `AUDIENCE_TZ` and `SLOTS` | When Shorts post | Keep US Eastern evenings for a US audience. Change them only with evidence about a different audience. |
| `strategy/SCRIPT-RULES.md` | The rules the writer and reviewer read | Rewrite the channel line, promise, examples, tone, and visual rules for the niche. Keep the section headings exactly: `writer._rules` pulls out "## Script rules", "## Metadata rules", "## Visual rules", "## Sound rules", and "## Spec schema". |
| `strategy/STRATEGY.md`, `strategy/PLAN-100.md` | Templates | Write them for the new channel, section by section, using `reference/days-of-odd/strategy/` as the model. The plan's decision points carry over almost as they are. |
| `strategy/CALENDAR.md` | Topics | At least 40 backlog topics, 6 or more per series, one line each ("Story (year): twist", with a Wikipedia article behind it), plus anniversaries for the next 8 weeks (dates like "Oct 7"). The daily routine adds more on its own. |
| `CHANNEL.md`, `OWNER-CHECKLIST.md` | Templates | Fill them in as the accounts are created. |
| `site/index.html`, `site/privacy.html` | The API app's home page and privacy policy | Describe the new channel. The privacy policy's facts (read-only analytics, playlists, nothing shared) stay the same. |
| `brand/make_brand.py` | Draws the avatar, banner, and watermark | Redesign: a simple, bold mark that reads at 48 px, colors that suit the niche, and a banner from 3 to 6 openly licensed pictures. Credit each one in `brand/CREDITS.md` with its license and link. Write `brand/CHANNEL-COPY.md` (name, handle, tagline, description, keywords), using `reference/days-of-odd/brand/CHANNEL-COPY.md` as the model. |

Once the NICHE spots are rewritten, also read the other lines listed at the end ("Other lines to
review"). They mention history or periods; most are harmless, but a few may need the niche's wording.

## Making the first Shorts good

- Read the first Short's `research.json`: are the claims surprising, and are two sites really behind
  each one? If research keeps coming back thin, the topics are too obscure or the trusted sites are wrong
  for the niche.
- Read `review.json`: the reviewer's notes say what to fix. Fix the cause in the prompts or
  `SCRIPT-RULES.md`, not the thresholds.
- Look at the frames (`content/episodes/<id>/work/frames/`, before `ytc sync` cleans them up): if the
  pictures are weak, improve how the writer names `subjects` and `queries`, and add the niche's
  archives to `TRUSTED` and the prompts.
- Leave `strategy/LEARNINGS.md` alone. The daily routine keeps it up to date from the channel's own
  analytics.

## The NICHE markers (20, generated 2026-09-29)

- `CHANNEL.md:3`: NICHE: fill in the channel's facts below as setup goes (Phases 1 and 2), then delete this line. -->
- `OWNER-CHECKLIST.md:3`: NICHE: fill this in at the end of setup (START-HERE, Phase 6): the dates, what's done, and anything still open. Then delete this line. -->
- `PLAYBOOK.md:3`: NICHE: the first paragraph's niche ("strange-but-true history") and the goal, for the new channel. Then delete this line. -->
- `brand/make_brand.py:25`: NICHE: the brand: redesign the mark, colors, and banner pictures for the niche (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/auto.py:382`: NICHE: the daily topics prompt: the channel, its pictures, and the example topic (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/auto.py:990`: NICHE: the learnings prompt: the channel's description (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/auto.py:1131`: NICHE: the weekly review prompt: the channel's description (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/pick.py:32`: NICHE: modern photos count less in beats set before this year; 0 switches that off (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/pick.py:73`: NICHE: the picture picker: the niche and its kinds of pictures (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/pick.py:107`: NICHE: the picture check: the niche's wording (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/publish.py:32`: NICHE: the audience's time zone, and the posting slots below (SLOTS) (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/research.py:24`: NICHE: the sites read first: add the niche's reputable sources (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/research.py:234`: NICHE: the research brief: the channel, and the kinds of pictures to suggest (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/studio.py:56`: NICHE: the quality gate: the channel's description (kit/NICHE-ADAPTATION.md)
- `pipeline/src/ytc/writer.py:83`: NICHE: the scriptwriter's prompt: the channel's promise, audience, and examples (kit/NICHE-ADAPTATION.md)
- `site/index.html:3`: NICHE: describe the new channel, and add avatar-256.png (the new avatar from brand/out/avatar-800.png, at 256 px), which both pages use as their icon. Then delete this line. -->
- `strategy/CALENDAR.md:13`: NICHE: seed at least 40 backlog topics (6 or more per series) and the anniversaries of the next 8 weeks, then delete this line. -->
- `strategy/PLAN-100.md:3`: NICHE: write the phases, targets, and decision points for the new channel, using reference/days-of-odd/strategy/PLAN-100.md as the model (its decision points carry over almost as they are). Then delete this line. -->
- `strategy/SCRIPT-RULES.md:3`: NICHE: rewrite the channel line, promise, examples, tone, and visual rules for the niche; keep every "## " heading (writer.py reads the rules by them). Then delete this line. -->
- `strategy/STRATEGY.md:3`: NICHE: write this file for the new channel, section by section, using reference/days-of-odd/strategy/STRATEGY.md as the model and research/ for the evidence (cite it). Keep the headings. Then delete this line. -->

## Other lines to review

Lines in the pipeline that mention history, periods, archives, or centuries. Most are about how pictures
are found and are fine for any niche; change only what would steer a new niche wrong.

- `pipeline/src/ytc/auto.py` (11)
  - line 91: `SERIES = ["Wait, That Happened?", "History's Luckiest People", "History's Unluckiest People",`
  - line 92: `"Hoaxes That Fooled Everyone", "Trials You Won't Believe", "Bad Ideas That Seemed Good", "History Got It Wrong`
  - line 383: `"You find topics for Kit Channel, a YouTube Shorts channel of strange-but-true history for a US audience "`
  - line 384: `"(under a minute each, told with archive pictures). Series: " + "; ".join(SERIES) + ".\n\n"`
  - line 388: `"Wikipedia article (give its exact title), and with period pictures likely on Wikimedia Commons. No "`
  - line 441: `"""Actions minutes this calendar month (UTC), from the run history; each job is billed in whole minutes."""`
  - line 444: `for line in (STATUS / "history.jsonl").read_text(encoding="utf-8").splitlines() if (STATUS / "history.jsonl").`
  - line 881: `# Three days back covers every day a new post can land on; all of Buffer's history would cost a request per 50`
  - line 991: `"You keep the learning log of Kit Channel, a Shorts channel of strange-but-true history. From the numbers "`
  - line 1132: `f"Write the week {week} review for Kit Channel, a Shorts channel of strange-but-true history, in plain "`
  - line 1260: `with (STATUS / "history.jsonl").open("a", encoding="utf-8") as fh:`
- `pipeline/src/ytc/pick.py` (18)
  - line 4: `searches), and from other open archives for beats those leave weak. rank.py orders them by how well they match`
  - line 29: `# A beat whose best candidate matches worse than this (0 to 1) also gets candidates from other archives.`
  - line 33: `MODERN_BEFORE = 1945`
  - line 37: `ROUTE_BONUS = {"subject": 0.08, "article": 0.05, "depicts": 0.05, "category": 0.03, "period": 0.02}`
  - line 48: `"route", "original", "source_name", "match", "historical")`
  - line 74: `PICK_PROMPT = """You choose the pictures for a Kit Channel history Short. While each beat of narration plays,`
  - line 85: `event the line names; the same subject or place at the time; a period picture that sets the scene without`
  - line 86: `contradicting the line. Never: an unrelated or anachronistic picture (a modern photo for a historical line),`
  - line 90: `subject or place around that time), "scene" (it only sets the period), or "none".`
  - line 108: `VERIFY_PROMPT = """Check the pictures chosen for a history Short before it is made. Each beat below has its li`
  - line 110: `person, place, or thing than the line is about; it is from the wrong period (a modern photo for a historical`
  - line 112: `isn't about a document; or it is too damaged or blurry to make out. A period picture that sets the scene is ok`
  - line 165: `"""Each candidate's match to every beat, and how likely it's a historical picture."""`
  - line 174: `candidate["historical"] = 0.5`
  - line 177: `candidate["historical"] = scores["historical"][j]`
  - and 3 more
- `pipeline/src/ytc/plates.py` (2)
  - line 50: `"""Slightly muted and warm, so photographs, engravings, and paintings from different archives sit together."""`
  - line 266: `"""The picture without the plain white or black margins many archive scans have (up to 12% a side)."""`
- `pipeline/src/ytc/rank.py` (7)
  - line 4: `It also says how likely each picture is a historical image (an engraving, painting, drawing, or black-and-whit`
  - line 5: `photo) rather than a modern color photo, which catches pictures from the wrong period.`
  - line 22: `HISTORICAL = ("a recent color photo taken with a digital camera", "an old black and white photograph, engravin`
  - line 71: `"""{"match": [[p for each image] for each text], "historical": [p for each image]}; p runs 0 to 1."""`
  - line 76: `ids = torch.tensor([e.ids for e in tokenizer.encode_batch([_canonical(t) for t in [*texts, *HISTORICAL]])])`
  - line 87: `return {"match": match, "historical": era}`
  - line 94: `return {"match": [[] for _ in texts], "historical": []}`
- `pipeline/src/ytc/render.py` (1)
  - line 30: `# One look over pictures from every archive (plates.grade warms and mutes them first): a little contrast, a`
- `pipeline/src/ytc/research.py` (11)
  - line 26: `"britannica.com", "smithsonianmag.com", "si.edu", "history.com", "nationalgeographic.com", "bbc.co.uk",`
  - line 27: `"bbc.com", "loc.gov", "archives.gov", "nps.gov", "nationalarchives.gov.uk", "npr.org", "pbs.org",`
  - line 28: `"nytimes.com", "theguardian.com", "washingtonpost.com", "time.com", "historyextra.com", "atlasobscura.com",`
  - line 30: `"rmg.co.uk", "britishmuseum.org", "metmuseum.org", "historic-uk.com", "history.state.gov",`
  - line 31: `"thecanadianencyclopedia.ca", "historylink.org", "encyclopedia.com", "worldhistory.org", "historynet.com",`
  - line 36: `"jstor.org", "worldcat.org", "archive.org/details", "amazon.", "youtube.com", "twitter.com", "x.com/",`
  - line 61: `"""The site a URL belongs to, looking through web.archive.org copies to the original."""`
  - line 62: `if match := re.match(r"https?://web\.archive\.org/web/[^/]+/(.+)", url):`
  - line 103: `f"A history Short will tell this story: {topic}\n\nName the one or two English Wikipedia articles that "`
  - line 235: `PROMPT = """You research stories for Kit Channel, a YouTube Shorts channel of strange-but-true history for a U`
  - line 254: `- visuals: 8 to 14 things a viewer could see (people, places, objects, documents, period prints,`
- `pipeline/src/ytc/sources.py` (13)
  - line 4: `picture, its Commons category, files tagged as depicting it, and period categories for places ("San Francisco`
  - line 5: `in the 1870s"). Keyword searches, the topic article's own pictures, and other open archives (Openverse,`
  - line 235: `def period_categories(pairs: list[tuple[str, int]]) -> dict[tuple[str, int], list[str]]:`
  - line 237: `Australia", "Strasbourg in the 16th century"), for each (category, year) pair, found in one lookup."""`
  - line 240: `century = _ordinal(year // 100 + 1)`
  - line 241: `for name in (f"{category} in the {year // 10 * 10}s", f"{year} in {category}", f"{category} in the {century} c`
  - line 250: `log.info("period category lookup failed: %s", err)`
  - line 426: `periods = period_categories(pairs) if pairs else {}`
  - line 431: `for category in periods.get((item.get("category"), beat_year(beat) or 0), [])[:2]:`
  - line 432: `add(n, commons_search, f'incategory:"{category}"', "period")`
  - line 444: `order = {"subject": 0, "article": 1, "category": 2, "depicts": 3, "period": 4, "search": 5}`
  - line 457: `"""More candidates from other open archives for beats the Commons routes left weak."""`
  - line 472: `log.info("extra candidates from other archives: %s", {n: len(c) for n, c in out.items()})`
- `pipeline/src/ytc/studio.py` (3)
  - line 58: `history. Judge this rendered Short as a demanding editor would. Below are the script with each beat's timing,`
  - line 70: `- frames: each beat whose frame has a problem (off-topic, anachronistic, gore, nudity, a big watermark,`
  - line 228: `# archives rarely have a picture that shows exactly what every one of nine lines says.`
- `pipeline/src/ytc/visuals.py` (3)
  - line 40: `"about after and before by circa during for from great historic historical history into near new "`
  - line 41: `"of old over the under with century drawing engraving etching illustration image lithograph painting "`
  - line 221: `fields = ("title", "objectName", "artistDisplayName", "culture", "period", "objectDate", "city", "country")`
- `pipeline/src/ytc/writer.py` (10)
  - line 19: `"History's Luckiest People",`
  - line 20: `"History's Unluckiest People",`
  - line 24: `"History Got It Wrong",`
  - line 84: `PROMPT = """You write Shorts for Kit Channel (@KitChannel): strange-but-true history in American English for a`
  - line 85: `US audience. Promise: one true, surprising story from history in under a minute, told well and sourced.`
  - line 123: `- Each beat's picture: visual describes the ideal picture the way an archive would caption it (subject, kind o`
  - line 135: `- title, description, hashtags, tags: per the metadata rules. The first hashtag is #history.`
  - line 204: `tags = list(dict.fromkeys(["history"] + [t for t in tags if t and t != "history"]))`
  - line 266: `if len(tags) != 3 or (tags and tags[0] != "#history") or any(not re.fullmatch(r"#[a-z0-9]+", t) for t in tags)`
  - line 267: `found.append("Give exactly 3 lowercase hashtags with no spaces, the first being #history.")`
