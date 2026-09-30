# Creature Receipts: script and episode rules

Channel: **Creature Receipts** (@CreatureReceipts), true, surprising stories of strange animals, extreme
biology, and deep-sea life, in American English for a US audience. Every claim comes with receipts: at least
two reputable sites behind it. Promise: one true, jaw-dropping animal story in under a minute, with receipts.
Space belongs to the sister channel Universe Receipts: no space topics here, and no animals-in-space angles.

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
- **Hook (beat 1):** a curiosity-gap statement of 12 words or fewer that is literally true and concrete: it
  opens a question the rest of the Short answers ("This fish was supposed to be extinct for 66 million
  years."; "A captive giant isopod refused every meal for five years."). No "Did you know", no greeting, no
  channel name, no question the Short can't answer. Open inside the story, and name the animal in the hook or
  beat 2 so search and the first frame agree.
- **Structure:** the writer is given one of five structures, the one the recent episodes used least:
  `story` (hook, context, 2–3 escalating beats, a twist), `myth_vs_fact` (what most people believe, then the
  evidence beat by beat, ending on the true fact), `scale_ladder` (from something familiar up or down 3–5
  steps to the astonishing size, speed, age, or number), `mystery` (something that made no sense, the clues in
  the order they were found, then the answer), or `record` (the record, what it beat, the trick or cost behind
  it, and the surprise nobody expected). Follow the one given; each still ends on a line that loops to the first.
- **Twist:** the fact a curious viewer is least likely to already know. For a famous animal (the axolotl,
  the platypus, the blue whale), build the Short around its least-known true detail rather than listing the
  facts everyone has seen: reviewers score a well-told but well-known story 3 on payoff.
- **Loop:** the last line is a complete sentence on its own that echoes the hook's image or question, so
  replaying the hook feels like the next line ("Fishermen still call it a living fossil." / "This fish was
  supposed to be extinct for 66 million years."). Never end on a dangling "because", "when", "until", or
  "that": the reviewer scores it 2 or 3 as jarring.
- **Clarity:** one idea per beat. After the hook, tell events in the order they happened; for a fact Short,
  build from the familiar to the jaw-dropping. Introduce each person the first time with who they are
  ("museum curator Marjorie Courtenay-Latimer"), and name at most 3 people in a Short. Give the animal's
  common name; add the scientific name only when it's the hook or the joke, and explain any group in a few
  plain words the first time ("a cephalopod, the octopus and squid family"). Don't open a beat with "he",
  "she", "they", or "it" unless the previous beat named that animal or person. Each line should name
  something a picture can show (the animal, a body part, a place, a person, a specimen, a ship) or a date,
  number, or quote a title card can show.
- **On-screen hook:** `hook_text` is 2–6 words shown over beat 1 from its first frame. It adds to the spoken
  hook (a number, a record, the stakes) without repeating it or giving away the payoff: "66 MILLION YEARS
  GONE", "5 YEARS, ZERO MEALS".
- **Truth:** every claim must be supported by at least two independent reputable sources (natural history
  museums, zoos and aquariums, universities, NOAA, USFWS, the IUCN Red List, peer-reviewed journals,
  established science publications such as National Geographic, Smithsonian, Scientific American, or
  Nature's news pages, encyclopedias, established newspapers). Disputed details and open questions are left
  out or attributed ("according to one study", "biologists think"). Never invent quotes, numbers, names, or
  dates. Prefer understatement to exaggeration. A record is stated as the sources state it: "the oldest
  known", "the deepest recorded", never "the oldest ever" when they don't say so.
- **Numbers:** state every number precisely as the sources give it, with its unit, and keep "about", "at
  least", "up to", or "estimated" when the source has it (Greenland shark ages are estimates with wide
  error bars). Don't round up, stack superlatives, or convert units yourself; use a conversion or everyday
  comparison only when it is in the claims.
- **No sensationalism:** no false or unfalsifiable framing: "scientists are baffled", "the most dangerous
  animal alive" unless the sources rank it so, cryptids or monsters presented as real, or doom the sources
  don't state. A hypothesis is called a hypothesis. A myth in "Animal Myths, Busted" is named as a myth and
  then busted with sourced facts.
- **Tone:** curious, wry, precise; the wonder comes from the facts, not from hype. Never cruel: no mocking
  an animal's looks or suffering, no "nature is metal" gore, no jokes about extinction or cruelty. Predation,
  death, and extinction are stated once, plainly, without graphic detail, and the Short moves on to the
  science. Human harm (a shark bite, a venomous sting) is handled with respect and never played for shock. No
  present-day politics, no medical, legal, or financial advice ("in 1992 a book claimed..." is fine; "you
  should..." is not), and never advice on handling or keeping wild animals.
- **Language:** American English. Years as digits (the narrator reads "1938" as "nineteen thirty-eight").
  Big numbers as digits with commas ("13,560") or words for the scale ("66 million years"); never scientific
  notation. Spell out units the narrator might misread ("kilometers", not "km"; "degrees Celsius", not "°C").
  Check scientific and Māori names ("Vampyroteuthis", "takahē", "tuatara") with `ytc phonemes`.
- **Originality:** write the story from the sources in your own words. Don't paraphrase another creator's
  script or video, and don't retell the same angle as a recent episode: the studio rejects a script that
  reuses much of a recent one's wording or opens with the same four words.

## Metadata rules

- **Title:** 60 characters or fewer, accurate, curiosity-driven, with the animal's name in about the first
  40 characters. At most one word in capitals, no emojis, no false promises, no "scientists are terrified"
  style bait.
- **Description:** 1–2 plain sentences that name the animal in the first sentence. The pipeline appends
  sources and image credits from `sources` and the asset manifest.
- **Hashtags:** exactly 3: `#animals`, then 2 specific ones (`#axolotl`, `#deepsea`, `#sharks`).
- **Tags:** 4–8 plain keywords.
- **Series:** one of `Built Different`, `Deep Sea Files`, `Back From Extinction`, `Evolution Got Weird`, `Nature's Record Breakers`, `Animal Myths, Busted`. Spell it exactly: each live Short is added to the playlist with that name.
- **synthetic_media:** `false` unless a beat uses a realistic AI image of a real animal, person, or event.

## Visual rules

The studio picks pictures itself (`pick.py`). For each beat the writer gives:

- `visual`: the ideal picture as a natural history picture library would caption it (species, what it's
  doing, kind of picture, place or year), 15 words or fewer: "Axolotl with external gills in an aquarium,
  photograph", "NOAA photo of a giant isopod on the seafloor", "1887 lithograph plate of a coelacanth".
- `subjects`: 0–3 exact English Wikipedia article titles for what that picture shows, most specific first
  ("Axolotl", "Lake Xochimilco"). Name the species article, not the genus or family, when one exists. They
  lead to the subject's own picture on Wikidata, its Commons category, and files tagged as depicting it.
- `year`: when the beat takes place (0 if it has no time, as for most facts about a living species).
- `queries`: 2–3 Commons keyword searches naming the exact species (common and scientific name:
  `Ambystoma mexicanum axolotl`, not `cute salamander`).
- `card`: a title card for when no picture fits: `dateline` (a date and place), `fact` (a number or a short
  fact), or `quote` (words quoted in the claims, exactly), using only the beat's text and claims; `none`
  otherwise. At most 2 cards are used per Short, never for the hook.

Kinds of pictures, best first: real photos of the exact species, living (iNaturalist research-grade
observations, Wikimedia Commons, NOAA Ocean Exploration and USFWS photos); then museum specimens, skeletons,
and fossils for extinct or rarely seen animals; then natural history plates and illustrations (the
Biodiversity Heritage Library's public-domain plates on Commons) for historical beats or animals never
photographed; then clear diagrams, maps, and range maps. The picture must show the species the line names:
a look-alike (a different shrimp for a mantis shrimp, a squid for a vampire squid, a crocodile for an
alligator) is wrong even if it's beautiful. A related species is used only when the line is about the group,
and then the narration says so. For a person, place, ship, or document, use the real one or a picture from
the time.

Never: dead, injured, bleeding, or dissected animals, carcasses or kills, animals in distress, cruelty,
hunting or trophy photos, gore, or medical close-ups of bites and wounds; a story about a death or an
extinction is shown with the living animal, a museum specimen, a plate, or a card. Never cartoons, toys,
mascots, movie stills, fan art, or AI renderings of real animals. Zoo and aquarium photos are fine when the
animal looks healthy; say "in captivity" when the line depends on it.

Candidates are ranked by how well they match `visual` (SigLIP, on the CPU), the model picks from the best six per
beat and marks the subject, a quick second look flags clear problems, and a beat with no fitting picture gets
its card, or an earlier picture reframed. A tall picture fills the screen; a wide, square, or small one is
shown whole as a framed print over a blurred copy of itself; a beat of about 3 seconds or more cuts to a
close-up of the part the line names. The hook's picture and `hook_text` are fully on screen from frame 0, with
no fade-in: the swipe-or-stay decision is made in the first second.

Pictures are public domain, CC0, or CC BY (credited in the description); never CC BY-SA, NC, or ND. That
means: NOAA, USFWS, NPS, USGS, and other US-government photos (public domain); iNaturalist photos marked CC0
or CC BY (credited to the observer); public-domain plates from the Biodiversity Heritage Library; and
Wikimedia Commons files under those licenses. Many excellent Commons and iNaturalist photos are CC BY-SA or
CC BY-NC and are never used. MBARI and most aquarium press images are copyrighted and never used. Flickr
Commons scans marked "no known copyright restrictions" are used only when dated before 1931.

In a spec written by hand, each beat's visual comes from public-domain or openly licensed archives via the
pipeline, at least 1,200 px on the long side:
  - `commons`: Wikimedia Commons, auto-filtered to public domain, CC0, or CC BY.
  - `nasa`: NASA images (images.nasa.gov), public domain; rarely useful here (Earth-from-orbit views of a
    reef or migration route, never space topics).
  - `met`: The Met, CC0 (natural history prints, animal art, old specimens in art).
  - `aic`: Art Institute of Chicago, CC0 (animal prints and paintings).
  - `url`: a picture already chosen, with `url` (the file to fetch) and `credit` (source, title, credit,
    license, url of its page); 600 px is enough, as it's then shown as a card.
  - `card`: a designed title card, `card: {kind: dateline, big: "Dec 22, 1938", small: "East London, South Africa"}`.
  - `color`: a plain gradient, as a last resort.
- `query` must name the exact subject so the search hits the right image (for example
  `Latimeria chalumnae coelacanth`, not `old fish`). The actual species beats a generic reef or ocean.
- Each source takes its best-ranked result, so the same query always gives the same image. To get a
  different one, change the query. On Commons, `intitle:"words from the file name"` pins a single file.
- `met` and `aic` only take an artwork whose title, artist, date, or subject tags contain most of the query's
  subject words, so give them short subject queries. Their images are also on Commons.
- Always give `fallbacks` in a sensible order, ending with `color`.
- Vary `motion` across beats: `zoom_in`, `zoom_out`, `pan_left`, `pan_right`, `pan_up`, `pan_down`.
- The vertical crop keeps the middle of a tall image. To keep another part, set `focus_x` (0 is the
  left edge, 1 the right) or `focus_y` (0 is the top, 1 the bottom). `box: [left, top, right, bottom]` (0 to 1)
  marks the part a close-up cuts to (the eye, the claw, the lure). Changing only `motion`, the focus, or the
  box keeps the image already downloaded.
- Avoid images with large watermarks or burned-in text, and any image that breaks the "Never" list above.
- Don't use the same image for two beats, except that the loop line may return to the hook's image with
  `visual: {reuse: 1, motion: zoom_out}`.

## Sound rules

- `sfx: whoosh` on up to 3 scene changes, `pop` on up to 2 punchlines, `riser` once before the twist,
  otherwise `none`. No music.

## Spec schema (short.yaml)

```yaml
id: ep001
title: "This fish was 'extinct' for 66 million years"
series: "Back From Extinction"
description: |
  In December 1938 a museum curator in South Africa spotted a coelacanth, a fish known only from fossils, in a fisherman's catch.
sources:
  - https://www.nhm.ac.uk/...
  - https://www.britannica.com/...
hashtags: ["#animals", "#coelacanth", "#livingfossil"]
tags: [coelacanth, living fossil, lazarus taxon, 1938]
voice: {voice: af_heart, speed: 1.05}
hook_text: "66 MILLION YEARS GONE"
beats:
  - text: This fish was supposed to be extinct for 66 million years.
    emphasis: [66 million years]
    sfx: whoosh
    visual: {source: commons, query: Latimeria chalumnae coelacanth, fallbacks: [met, color], motion: zoom_in}
  - text: Then, in December 1938, one turned up in a fisherman's catch in South Africa.
    emphasis: [December 1938]
    visual: {source: card, card: {kind: dateline, big: "Dec 22, 1938", small: "East London, South Africa"}}
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
wrong, write it as `[word](/phonemes/)` using that alphabet (`[axolotl](/ˈæksəlɒtəl/)`), re-render, and note
it in `research.md`. Other spellings of a correctly spoken name and skipped short words are normal. It also writes one frame per beat to
`content/episodes/<id>/work/frames/`. Look at every frame. If an image is wrong, off-topic, low quality,
shows the wrong species, or has distracting burned-in text, change that beat's `query` or `source` and
re-render; a changed visual is fetched again automatically. Aim for 40–50 seconds.
