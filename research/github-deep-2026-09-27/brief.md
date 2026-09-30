# Context for the GitHub deep dive (read this first)

## Our channel and pipeline

Days of Odd (@DaysOfOdd) is a fully automated YouTube Shorts channel: strange-but-true history in American
English for a US audience (examples: the Great Emu War, the BBC spaghetti-harvest hoax, the Cottingley
Fairies, Piltdown Man, Juliane Koepcke). Goal: 100k subscribers and Shorts monetization by 2027-01-04, with no
human in the loop.

Each Short is made end to end by our Python pipeline (`<repo root>/pipeline/src/ytc/`):

1. Research: an LLM gathers sourced claims (a claims table, 2+ reputable sources per claim).
2. Script: 105-135 words, 6-9 beats; hook (12 words or fewer, beat 1), escalation, twist, and a last line that
   loops into the first. Title, description, 3 hashtags, tags, series.
3. Pictures: ONE still per beat. Candidates come from a keyword search of Wikimedia Commons (public domain /
   CC0 / CC BY only, 1,200 px or more); a vision LLM ranks up to 5 candidates per beat plus a shared pool
   of 18 and picks a focus point. Fallback sources are The Met (CC0), Art Institute of Chicago (CC0), NASA,
   then a plain color gradient. An AI-image function (FLUX.1-schnell on Cloudflare Workers AI, free tier)
   exists but is unused.
4. Motion: FFmpeg `zoompan` Ken Burns only (zoom in/out, pan left/right/up/down, max 1.12x), hard cuts
   between beats, no transitions, no overlays, no text other than captions.
5. Voice: Kokoro-82M (`af_heart`), with word timestamps.
6. Captions: libass ASS, word-by-word, 1-2 emphasis words per beat highlighted.
7. Sound: short SFX (whoosh, pop, riser) from a cache; no music; two-pass loudnorm to -14 LUFS.
8. Review: Gemini looks at a contact sheet (one frame per beat) and scores hook, clarity, payoff, visuals
   (1-5). Low scores trigger picture replacement or a rewrite; after the last fix round a Short passes only
   if every score is 4 or more.
9. Publishing: Buffer's free API (official YouTube partner) with Cloudinary hosting. YouTube Data/Analytics
   APIs for stats (read-only).

Where it runs: Modal (CPU containers; $30/month free credit, about $0.12 per Short today; GPUs are allowed
within the credit) and GitHub Actions as a backup. LLMs: Gemini free tier (Flash models; image input OK),
Cursor SDK models as a fallback. Everything must stay free.

## The problem we most need to solve

14 of our 15 rejected Shorts failed on visuals (mean visual score 2.9, against 4.6 for accepted ones): the
picture didn't show what the line says, pictures were from the wrong period, or a beat had no picture at all
(topics with few archive images). Our look is also "static slideshow": one still, a slow zoom, a hard cut.
We want to learn how the best free/open-source Shorts and explainer pipelines solve:

- finding the RIGHT picture for each line (sources, search strategy, verification, ranking);
- beats with no good archive picture (designed shots: title cards, maps, dates, documents, quote cards,
  kinetic typography, diagrams, collage, illustration styles, AI images with honest labelling);
- motion that isn't just zoompan: parallax/2.5D, image-to-video, crops that zoom to a detail, overlays,
  highlights, transitions, grain/grade, pacing (cuts every N seconds, multiple shots per beat);
- retention craft: hooks, pacing rules, on-screen hook text, loop endings, sound design;
- quality gates: automated checks of the rendered video (vision LLM review, frame checks), and feedback loops
  from analytics;
- how they structure prompts, knowledge files, "shot recipes", and agent workflows.

## Hard constraints for anything we adopt

- 100% free: free tiers, open-source, or Modal within the $30/month credit. No paid-only APIs.
- Licenses: code must allow our use (MIT/Apache/BSD fine; AGPL/GPL fine to RUN as a separate tool but not to
  copy code into our repo; "non-commercial" code or model weights are NOT OK because the channel will be
  monetized). Media must be public domain, CC0, or CC BY (with credit). No CC BY-SA/NC/ND media.
- No automated use of youtube.com (no scraping, no yt-dlp, no youtube-transcript-api, no uploads via browser).
  Official YouTube APIs are fine for reading.
- Must run headless in the cloud (Modal Linux containers or GitHub Actions ubuntu runners).
- Realistic AI images of real people/events must be disclosed; our credibility matters (history channel).

## What to return

For each repo you cover, verify on GitHub (not from memory): stars, last push date, license (check the LICENSE
file, not just the badge), and whether it is archived. Then, from READING THE CODE (clone it), not just the
README:

- What it does, as a pipeline (stage by stage), and the key files.
- The specific techniques worth stealing, each with the file path (and line range if useful) and a short
  excerpt or paraphrase of the prompt / algorithm / parameters.
- Where it is clearly better than our pipeline above, and where it is worse or irrelevant.
- How we could adopt it within the constraints: code vs idea, effort (S/M/L), cost on Modal, risks.
- A verdict: ADOPT (code or tool), BORROW IDEA, WATCH, or SKIP, with one line of why.

Write your notes as Markdown to the file path your task names (under
`<repo root>/.scratch/deep/`). Finish with a section "Top insights for Days of Odd" ranking
the 5-10 most valuable, concrete changes for our pipeline.
