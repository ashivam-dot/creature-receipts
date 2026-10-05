# History's Last Hours: script and episode rules

Channel: **History's Last Hours** (@HistorysLastHours), true stories of history's tragedies (lost cities, doomed
voyages and expeditions, fallen empires, ignored warnings, and the few who survived), in American English for a
US audience. Every claim has at least two reputable sites behind it. Promise: the human story of one real
disaster in 17 to 35 seconds, told with weight and sourced. Only events at least 75 years old. Space belongs to
the sister channel Universe Receipts: no space topics here.

Before writing, read `strategy/LEARNINGS.md`: what's working on this channel, what isn't, and the numbers
each new Short should beat. Apply every proven rule in it.

## Deliverables per episode

Folder: `content/episodes/<id>/` (ids are `ep001`, `ep002`, ...).

1. `short.yaml`: the spec the renderer reads (schema below).
2. `research.md`: a claims table. Each factual claim in the narration gets one row: claim, at least two
   independent reputable sources (URLs), and confidence. Add notes on disputed details and how the script
   handles them. End with a line `Better than the last: ...` naming the learning or improvement this
   episode applies and where.

## Script rules

- **Length:** 55–72 spoken words (about 22–31 seconds in the Kokoro am_fenrir read at 1.15x), 6–8 beats, one short sentence per beat. The
  breakout history Shorts of 2026 run 17–27 seconds; a Short watched to the end and replayed is the one the
  feed pushes. Cut every word that doesn't move the story.
- **Hook (beat 1):** 12 words or fewer, literally true and concrete, opening inside the moment of the story
  on its most gripping fact: "The lookouts on the Titanic had no binoculars."; "At noon, the mountain above
  Pompeii split open." No "Did you know", "You might think", "Imagine", "What if", or "Many believe", no
  greeting, no channel name, no question the Short can't answer. Never graphic in the hook, the on-screen
  hook, or the title (no beheadings, severed heads, corpses, blood, or torture): YouTube shows graphic Shorts
  to fewer people, so open on the people, the place, the stakes, or the decision.
  Name the place, ship, or event in the hook or beat 2, so search and the first frame agree.
- **Structure:** the writer is given one of five structures, the one the recent episodes used least:
  `story` (hook, context, 2–3 escalating beats, a twist), `myth_vs_fact` (what most people believe, then the
  evidence beat by beat, ending on the true fact), `countdown` (the last ordinary moment, then the signs and
  hours in order until it struck), `mystery` (something that made no sense, the clues in the order they were
  found, then the answer), or `warning` (the disaster, the warning someone gave, why it was ignored, and the
  price). Follow the one given; each still ends on a line that loops to the first.
- **Twist:** the detail a curious viewer is least likely to already know. For a famous event (the Titanic,
  Pompeii), build the Short around its least-known true detail rather than the story everyone has seen:
  reviewers score a well-told but well-known story 3 on payoff.
- **Loop:** the last line is a complete sentence on its own that echoes the hook's image or question, so
  replaying the hook feels like the next line ("Nobody in the city looked up at the mountain that morning." /
  "At noon, the mountain above Pompeii split open."). Never end on a dangling "because", "when", "until", or
  "that": the reviewer scores it 2 or 3 as jarring.
- **Clarity:** one idea per beat. After the hook, tell events in the order they happened. Introduce each
  person the first time with who they are ("Captain Edward Smith"), and name at most 2 people in a Short.
  Don't open a beat with "he", "she", "they", or "it" unless the previous beat named who or what that is.
  Each line should name something a picture can show (a person, a ship, a city, a building, a document) or a
  date, number, or quote a title card can show.
- **On-screen hook:** `hook_text` is 2–6 words shown over beat 1 from its first frame. It adds to the spoken
  hook (a time, a number, the stakes) without repeating it or giving away the payoff: "18 MINUTES TO SINK",
  "THE KEY NOBODY HAD".
- **Truth:** every claim must carry exact quotes matched against the fetched text of at least two independent
  reputable sources (museums, national archives, universities, the Smithsonian, Britannica, established history publications such as History
  Extra or World History Encyclopedia, peer-reviewed journals, established newspapers). Disputed details and
  legends are left out or attributed ("according to one account", "historians think"). The script must preserve
  a source's uncertainty; it cannot strengthen correlation into cause or describe a survivor as the only one
  without evidence. Never invent quotes,
  numbers, names, or dates. Death tolls are stated as the sources give them, with "about", "at least", or
  "estimated" kept, and a range when they disagree.
- **Tone:** grave, vivid, human. Tell it through the people in it: what they saw, decided, and could not
  know. The weight comes from the facts and the people, never from hype. No gore: deaths are stated once,
  plainly, with no description of bodies or suffering. No jokes about the dead, no "they deserved it", no
  blame beyond what the sources state, no present-day politics, and no event whose victims' families are
  still in the news. No false framing ("historians are baffled") and no curses or ghosts presented as real.
- **Language:** American English. Years as digits (the narrator reads "1912" as "nineteen twelve"); "79 AD"
  and "373 BC" for ancient years. Big numbers as digits with commas ("1,198"). Spell out units the narrator
  might misread ("kilometers", not "km"). Check names in other languages ("Herculaneum", "Tenochtitlan",
  "Peshtigo") with `ytc phonemes`.
- **Originality:** write the story from the sources in your own words. Don't paraphrase another creator's
  script or video, and don't retell the same angle as a recent episode: the studio rejects a script that
  reuses much of a recent one's wording or opens with the same four words.

## Metadata rules

- **Title:** 60 characters or fewer, accurate, curiosity-driven, naming the event, place, or ship in about
  the first 40 characters. A question that the Short answers works best ("Why Did No One on the Titanic Have
  Binoculars?", "How Did Pompeii's People Not See It Coming?"). At most one word in capitals and at most one
  emoji, at the very end (😳, 🤯, or ⚠️). No false promises and no "historians are terrified" style bait.
- **Description:** 1–2 plain sentences that name the event in the first sentence. The pipeline appends
  sources and image credits from `sources` and the asset manifest.
- **Hashtags:** exactly 3: `#history`, then 2 specific ones (`#titanic`, `#pompeii`, `#shipwreck`).
- **Tags:** 4–8 plain keywords.
- **Series:** one of `The Last Hours`, `Lost Cities`, `Doomed Expeditions`, `Fallen Empires`, `Warnings Ignored`, `Sole Survivors`. Spell it exactly: each live Short is added to the playlist with that name.
- **synthetic_media:** `false` unless a beat uses a realistic AI image of a real person or event.

## Visual rules

The studio picks pictures itself (`pick.py`). For each beat the writer gives:

- `visual`: the ideal picture as a museum or archive would caption it (subject, kind of picture, year), 15
  words or fewer: "photograph of RMS Titanic leaving Southampton, 1912", "painting of the eruption of
  Vesuvius, 1822", "engraving of the 1755 Lisbon earthquake and tsunami".
- `subjects`: 0–3 exact English Wikipedia article titles for what that picture shows, most specific first
  ("Sinking of the Titanic", "Titanic"). They lead to the subject's own picture on Wikidata, its Commons
  category, and files tagged as depicting it.
- `year`: when the beat takes place (0 if it has no time).
- `queries`: 2–3 Commons keyword searches naming the exact subject (`RMS Titanic Southampton 1912`, not
  `old ship`).
- `card`: a title card for when no picture fits: `dateline` (a date and place), `fact` (a number or a short
  fact), or `quote` (words quoted in the claims, exactly), using only the beat's text and claims; `none`
  otherwise. At most 2 cards are used per Short, never for the hook.

Kinds of pictures, best first: photographs, paintings, engravings, and newspaper pages of the event or its
people from the time; then later paintings of the event when nothing from the time exists; then the ruins,
wreck, or artifacts as they are today for lines about what was found or what remains; then maps. The picture
must show what the line names: a different ship of the same line, a different city, or a look-alike portrait is
wrong even if it's beautiful. Modern stock footage only for a line about a place today or as moving atmosphere
(a dark sea, falling ash, flames) that doesn't contradict the line.

Never: corpses, remains shown as gore, wounds, executions, nudity, or pictures of suffering held on screen; a
story about deaths is shown with the place, the ship, the people alive, a painting, or a card. Never movie
stills, fan art, toys, or AI renderings of real people.

Candidates are ranked by how well they match `visual` (SigLIP, on the CPU), the model picks from the best six per
beat and marks the subject, a quick second look flags clear problems, and a beat with no fitting picture gets
its card, or an earlier picture reframed. A tall picture fills the screen; a wide, square, or small one is
shown whole as a framed print over a blurred copy of itself; a beat of about 3 seconds or more cuts to a
close-up of the part the line names. The hook's picture and `hook_text` are fully on screen from frame 0, with
no fade-in: the swipe-or-stay decision is made in the first second.

Pictures are public domain, CC0, or CC BY (credited in the description); never CC BY-SA, NC, or ND. Most
pictures from before 1931 are public domain, as are US-government photos (Library of Congress, National
Archives, NPS, USGS). Flickr Commons scans marked "no known copyright restrictions" are used only when dated
before 1931.

In a spec written by hand, each beat's visual comes from public-domain or openly licensed archives via the
pipeline, at least 1,200 px on the long side:
  - `commons`: Wikimedia Commons, auto-filtered to public domain, CC0, or CC BY.
  - `nasa`: NASA images (images.nasa.gov), public domain; rarely useful here (an eruption seen from orbit).
  - `met`: The Met, CC0 (paintings, prints, and artifacts).
  - `aic`: Art Institute of Chicago, CC0 (paintings and prints).
  - `url`: a picture already chosen, with `url` (the file to fetch) and `credit` (source, title, credit,
    license, url of its page); 600 px is enough, as it's then shown as a card.
  - `card`: a designed title card, `card: {kind: dateline, big: "April 15, 1912", small: "North Atlantic"}`.
  - `color`: a plain gradient, as a last resort.
- `query` must name the exact subject so the search hits the right image (for example
  `RMS Titanic Southampton 1912`, not `ship`).
- Each source takes its best-ranked result, so the same query always gives the same image. To get a
  different one, change the query. On Commons, `intitle:"words from the file name"` pins a single file.
- `met` and `aic` only take an artwork whose title, artist, date, or subject tags contain most of the query's
  subject words, so give them short subject queries. Their images are also on Commons.
- Always give `fallbacks` in a sensible order, ending with `color`.
- Vary `motion` across beats: `zoom_in`, `zoom_out`, `pan_left`, `pan_right`, `pan_up`, `pan_down`.
- The vertical crop keeps the middle of a tall image. To keep another part, set `focus_x` (0 is the
  left edge, 1 the right) or `focus_y` (0 is the top, 1 the bottom). `box: [left, top, right, bottom]` (0 to 1)
  marks the part a close-up cuts to (a face, a headline, the crow's nest). Changing only `motion`, the focus,
  or the box keeps the image already downloaded.
- Avoid images with large watermarks or burned-in text, and any image that breaks the "Never" list above.
- Don't use the same image for two beats, except that the loop line may return to the hook's image with
  `visual: {reuse: 1, motion: zoom_out}`.

## Sound rules

- `sfx: whoosh` on up to 3 scene changes, `pop` on up to 2 punchlines, `riser` once before the twist,
  otherwise `none`. No music.

## Spec schema (short.yaml)

```yaml
id: ep025
title: "Why Did No One on the Titanic Have Binoculars? 😳"
series: "The Last Hours"
description: |
  The Titanic's lookouts sailed without binoculars, because the key to their locker left the ship with an officer.
sources:
  - https://www.britannica.com/...
  - https://www.encyclopedia-titanica.org/...
hashtags: ["#history", "#titanic", "#shipwreck"]
tags: [titanic, 1912, shipwreck, lookouts]
voice: {voice: af_heart, speed: 1.05}
hook_text: "THE KEY NOBODY HAD"
beats:
  - text: The lookouts on the Titanic had no binoculars.
    emphasis: [no binoculars]
    sfx: whoosh
    visual: {source: commons, query: RMS Titanic Southampton 1912, fallbacks: [met, color], motion: zoom_in}
  - text: On April 14, 1912, they were watching for ice with their bare eyes.
    emphasis: [April 14, 1912]
    visual: {source: card, card: {kind: dateline, big: "April 14, 1912", small: "North Atlantic"}}
```

`emphasis` words must appear in that beat's text; use 1–2 per beat, single words or short phrases.

## Render and check

From `pipeline/`:

```bash
uv run --no-sync ytc make ../content/episodes/<id>/short.yaml
uv run --no-sync ytc check ../content/episodes/<id>/<id>.mp4
```

Keep `--no-sync`: the environment is already installed, and without it every `uv run` re-checks a
GitHub-hosted dependency and waits on other agents' runs, which can stall a command for minutes.

`ytc make` renders on Modal's cloud when `MODAL_TOKEN_ID` is set in `pipeline/.env` and falls back to this
Mac if the cloud fails; add `--where local` or `--where cloud` to force one. Only the Short and the files
under `work/` that `ytc check` and `ytc publish` read are kept; intermediate clips are deleted.

The check prints duration, loudness, and each beat's asset and source, plus `warnings` for anything outside
the limits or any beat that fell back to a gradient; fix every warning. Its `speech.differences` lists where
a speech recognizer heard something other than the script. Check each with
`uv run --no-sync ytc phonemes "<the sentence>"`, which prints the narrator's pronunciation. If a word is
wrong, write it as `[word](/phonemes/)` using that alphabet, re-render, and note it in `research.md`. Other
spellings of a correctly spoken name and skipped short words are normal. It also writes one frame per beat to
`content/episodes/<id>/work/frames/`. Look at every frame. If an image is wrong, off-topic, low quality, or has
distracting burned-in text, change that beat's `query` or `source` and re-render; a changed visual is fetched
again automatically. Aim for 17–27 seconds.
