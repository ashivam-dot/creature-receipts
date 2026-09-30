# Days of Odd: script and episode rules

Channel: **Days of Odd** (@DaysOfOdd), strange-but-true history Shorts in English for a US audience.
Promise: one true, surprising story from history in under a minute, told well and sourced.

Before writing, read `strategy/LEARNINGS.md`: what's working on this channel, what isn't, and the numbers
each new Short should beat. Apply every proven rule in it.

## Deliverables per episode

Folder: `content/episodes/<id>/` (ids are `ep001`, `ep002`, ...).

1. `short.yaml`: the spec the renderer reads (schema below).
2. `research.md`: a claims table. Each factual claim in the narration gets one row: claim, at least two
   independent reputable sources (URLs), and confidence. Add notes on disputed details and how the script
   handles them. End with a line `Better than the last: ...` naming the learning or improvement this
   episode applies and where (for example, "hook states the twist in 9 words, per the rule on first-2-second
   surprises").

## Script rules

- **Length:** 105–135 spoken words (about 40–50 seconds), 6–9 beats, one or two short sentences per beat.
- **Hook (beat 1):** a concrete, surprising statement of 12 words or fewer. No "Did you know", no greeting,
  no channel name. Open inside the story.
- **Shape:** hook, then context, 2–3 escalating beats, a twist or payoff, and a last line that flows back
  into the first line so the Short loops cleanly.
- **Clarity:** one idea per beat. After the hook, tell events in the order they happened. Introduce each
  person the first time with who they are ("16-year-old Elsie Wright"), and name at most 3 people in a Short.
  Don't open a beat with "he", "she", or "they" unless the previous beat named that person. Each line should
  name something a picture can show (a person, place, object, or document) or a date, number, or quote a
  title card can show.
- **On-screen hook:** `hook_text` is 2–6 words shown over beat 1. It adds to the spoken hook (a number, a
  place, the stakes) without repeating it or giving away the payoff: "20,000 EMUS VS. MACHINE GUNS".
- **Truth:** every claim must be supported by at least two independent reputable sources (encyclopedias,
  museums, universities, national archives, established newspapers or history publications). Disputed
  details are either left out or attributed ("according to one account"). Never invent quotes, numbers,
  names, or dates. Prefer understatement to exaggeration.
- **Tone:** curious, vivid, warm. No gore, no graphic injury or death, no mocking victims, no present-day
  politics, no medical, legal, or financial advice.
- **Language:** American English. Years as digits (the narrator reads "1518" as "fifteen eighteen").
  Big numbers as digits with commas ("20,000"). Avoid abbreviations the narrator might misread.
- **Originality:** write the story from the sources in your own words. Don't paraphrase another creator's
  script or video.

## Metadata rules

- **Title:** 60 characters or fewer, accurate, curiosity-driven. At most one word in capitals, no emojis,
  no false promises.
- **Description:** 1–2 plain sentences. The pipeline appends sources and image credits from `sources`
  and the asset manifest.
- **Hashtags:** exactly 3: `#history`, then 2 specific ones.
- **Tags:** 4–8 plain keywords.
- **Series:** one of `Wait, That Happened?`, `History's Luckiest People`, `History's Unluckiest People`,
  `Hoaxes That Fooled Everyone`, `Trials You Won't Believe`, `Bad Ideas That Seemed Good`,
  `History Got It Wrong`. Spell it exactly: each live Short is added to the playlist with that name.
- **synthetic_media:** `false` unless a beat uses a realistic AI image of a real person or event.

## Visual rules

The studio picks pictures itself (`pick.py`). For each beat the writer gives:

- `visual`: the ideal picture as an archive would caption it (subject, kind of picture, year), 15 words or fewer.
- `subjects`: 0–3 exact English Wikipedia article titles for what that picture shows, most specific first. They
  lead to the subject's own picture on Wikidata, its Commons category, files tagged as depicting it, and period
  categories for places ("San Francisco in the 1870s").
- `year`: when the beat takes place (0 if it has no time), so modern photos are kept out of historical beats.
- `queries`: 2–3 Commons keyword searches.
- `card`: a title card for when no picture fits: `dateline` (a date and place), `fact` (a number or a short
  fact), or `quote` (words quoted in the claims, exactly), using only the beat's text and claims; `none`
  otherwise. At most 2 cards are used per Short, never for the hook.

Candidates are ranked by how well they match `visual` (SigLIP, on the CPU), the model picks from the best six per
beat and marks the subject, a quick second look flags clear problems, and a beat with no fitting picture gets
its card, or an earlier picture reframed. A tall picture fills the screen; a wide, square, or small one is
shown whole as a framed print over a blurred copy of itself; a beat of about 3 seconds or more cuts to a
close-up of the part the line names.

Pictures are public domain, CC0, or CC BY (credited in the description); never CC BY-SA, NC, or ND. Flickr
Commons scans marked "no known copyright restrictions" are used only when dated before 1931.

In a spec written by hand, each beat's visual comes from public-domain or openly licensed archives via the
pipeline, at least 1,200 px on the long side:
  - `commons`: Wikimedia Commons, auto-filtered to public domain, CC0, or CC BY.
  - `met`: The Met, CC0.
  - `aic`: Art Institute of Chicago, CC0.
  - `nasa`: NASA images.
  - `url`: a picture already chosen, with `url` (the file to fetch) and `credit` (source, title, credit,
    license, url of its page); 600 px is enough, as it's then shown as a card.
  - `card`: a designed title card, `card: {kind: dateline, big: "November 1932", small: "Campion, Western Australia"}`.
  - `color`: a plain gradient, as a last resort.
- `query` must name the exact subject so the search hits the right image (for example
  `Great Emu War 1932 Meredith`, not `bird war`). Period-accurate images beat generic ones.
- Each source takes its best-ranked result, so the same query always gives the same image. To get a
  different one, change the query. On Commons, `intitle:"words from the file name"` pins a single file.
- `met` and `aic` only take an artwork whose title, artist, date, or subject tags contain most of the query's
  subject words, so give them short subject queries (`Monet Stacks of Wheat`). The Met's own search is weak;
  its images are also on Commons with "MET" in the file name (`intitle:"Warming pan" MET`).
- Always give `fallbacks` in a sensible order, ending with `color`.
- Vary `motion` across beats: `zoom_in`, `zoom_out`, `pan_left`, `pan_right`, `pan_up`, `pan_down`.
- The vertical crop keeps the middle of a tall image. To keep another part, set `focus_x` (0 is the
  left edge, 1 the right) or `focus_y` (0 is the top, 1 the bottom). `box: [left, top, right, bottom]` (0 to 1)
  marks the part a close-up cuts to. Changing only `motion`, the focus, or the box keeps the image already
  downloaded.
- Avoid images showing corpses, wounds, executions, or nudity.
- Don't use the same image for two beats, except that the loop line may return to the hook's image with
  `visual: {reuse: 1, motion: zoom_out}`.

## Sound rules

- `sfx: whoosh` on up to 3 scene changes, `pop` on up to 2 punchlines, `riser` once before the twist,
  otherwise `none`. No music.

## Spec schema (short.yaml)

```yaml
id: ep001
title: "Australia declared war on emus. The emus won."
series: "Wait, That Happened?"
description: |
  In 1932 Australia sent soldiers with machine guns after 20,000 emus. It did not go to plan.
sources:
  - https://www.britannica.com/...
  - https://www.nationalgeographic.com/...
hashtags: ["#history", "#emuwar", "#australia"]
tags: [great emu war, emus, australia history, 1932]
voice: {voice: af_heart, speed: 1.05}
hook_text: "20,000 EMUS VS. MACHINE GUNS"
beats:
  - text: In 1932, Australia sent soldiers with machine guns to fight emus.
    emphasis: [emus]
    sfx: whoosh
    visual: {source: commons, query: Great Emu War 1932, fallbacks: [aic, color], motion: zoom_in}
  - text: It began in November 1932, near Campion in Western Australia.
    emphasis: [November 1932]
    visual: {source: card, card: {kind: dateline, big: November 1932, small: "Campion, Western Australia"}}
```

`emphasis` words must appear in that beat's text; use 1–2 per beat, single words or short phrases.

## Render and check

From `<repo root>/pipeline`:

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
wrong, write it as `[word](/phonemes/)` using that alphabet (`[Formosus](/fɔɹmˈOsəs/)`), re-render, and note
it in `research.md`. Other spellings of a correctly spoken name and skipped short words are normal. It also writes one frame per beat to
`content/episodes/<id>/work/frames/`. Look at every frame. If an image is wrong, off-topic, low quality,
or has distracting burned-in text, change that beat's `query` or `source` and re-render; a changed visual
is fetched again automatically. Aim for 40–50 seconds.
