# Tools radar

Updated every Sunday by the weekly review (`PLAYBOOK.md`, step 9). Adopt a tool only if it is clearly better in
a test we ran, allows commercial use, is maintained (a push in the last 3 months, not archived), and runs on
Modal or this Mac for free. Record each check below with its date.

## Current stack

| Job | Tool | License | Since |
|---|---|---|---|
| Narration | Kokoro-82M, voice `af_heart` | Apache-2.0 | Day 0 |
| Captions | Kokoro word timestamps, burned in with libass | Apache-2.0, ISC | Day 0 |
| Images | Entity-first: Wikipedia articles, Wikidata (image, Commons category, "depicts"), Wikimedia Commons, then Openverse, Wellcome Collection, The Met, Art Institute of Chicago (`sources.py`) | PD, CC0, CC BY | 2026-09-28 (Commons, Met, AIC since Day 0) |
| Picture ranking | SigLIP `google/siglip-base-patch16-224` through transformers, on Modal (`rank_pictures`) | Apache-2.0 | 2026-09-28 |
| Designed shots | Title cards and plates drawn with Pillow (`plates.py`); fonts Anton, Montserrat, DM Serif Display | HPND; OFL | 2026-09-28 |
| Render | FFmpeg on Modal, or on the GitHub runner when Modal's credit is used up | LGPL/GPL | Day 0 |
| Running it | Modal cron (`studio_run`, 4 runs a day) starting Modal workers; GitHub Actions `studio` workflow as backup | free plans | 2026-09-27 |
| Research, scripts, image picks, review | Gemini free tier: six Flash models, then Gemma 4 31B (`gemma-4-31b-it`, same project) for small prompts, then Flash-Lite for research and picks; the review uses Flash only; Cursor agent models last | Gemini API terms; Gemma Apache-2.0; Cursor terms | 2026-09-28 (Gemini-first since 2026-09-27) |
| Publishing | Buffer API (scheduled), Cloudinary hosting | free plans | Day 0 |
| Analytics and playlists | YouTube Data and Analytics APIs | Google API terms | Day 0 |
| Speech check | faster-whisper `small.en` on Modal, diffed against the script after Whisper's own normalizer | MIT | Day 0 |

## Candidates

| Candidate | For | Status | Next step |
|---|---|---|---|
| Chatterbox (Resemble AI) | more expressive narration | not tested | Blind test against `af_heart` in week 2 (confirm the weights' license first) |
| Pocket TTS | narration on CPU | not tested | Same blind test (MIT code, CC BY weights) |
| Gemini Flash TTS | narration | not tested | Same blind test (check the free tier's terms allow commercial use) |
| Real-ESRGAN | upscaling genuine archive photos under 1,200 px | reviewed 2026-09-27: BSD-3 weights, repo idle since 2024 | Only if card photos look soft after Phase 1 of the picture plan: vendor `realesr-general-x4v3` (a 69-line network), use it only past 1.3x magnification, never on faces or text |
| On-screen hook text | first-2-second retention | adopted 2026-09-28 (`hook_text`, Anton in a box over beat 1) | Compare first-3-second retention before and after in the weekly review |
| Tighter pacing | retention | partly adopted 2026-09-28: beats of 2.8 s or more cut to a close-up | Trim Kokoro's padding between beats |
| Entity-first Commons search (Wikidata items, categories, "depicts") | the right picture per beat | adopted 2026-09-28 (tested 2026-09-27: 948 usable files against 137 on 38 beats) | Watch the visuals score |
| SigLIP ViT-B/16 | ranking candidates before Gemini sees them | adopted 2026-09-28 (transformers, not open_clip; same weights family) | none |
| Openverse and Wellcome Collection APIs | more CC0, PD and CC BY pictures | adopted 2026-09-28 for weak beats | none |
| Gemma 4 31B on the Gemini API | free capacity once the Flash quota is spent | adopted 2026-09-28 (16,000 input tokens a minute; see `free-llm-providers-2026-09-28.md`) | Track how many Shorts it drafts and how they score |
| Cloudflare Workers AI, Mistral free mode, Groq | more free LLM capacity | reviewed 2026-09-28, not adopted | Each needs the owner to sign up; next if Gemini's free tier shrinks |
| FLUX.2 klein 4B (Cloudflare, or self-hosted on Modal) | generated pictures | reviewed 2026-09-28, not adopted | Only if designed cards hurt retention (`free-image-generation-2026-09-28.md`) |
| HyperFrames | designed shots: maps, datelines, documents, counters | reviewed, not yet run on Modal | Phase 2 spike: 3 templates on Modal, measure time and cost |
| BiRefNet_lite, Depth Anything V2 Small | 2.5D parallax on wide scenes | reviewed | Picture plan, Phase 2 item 12 |
| Wan 2.2 image-to-video with LightX2V distills | motion in paintings | watch | Only once a Short can carry the synthetic-media label through Buffer |

## YouTube features to adopt when we can

| Feature | Status (2026-09-26) | Blocker | Plan |
|---|---|---|---|
| Shorts Series (seasons and episodes, "watch series" button) | Announced Sep 23, rolling out; one report says Partner Program channels only | Studio only, no API yet | Check Studio's Content tab weekly and the Data API release notes. When possible, turn the series playlists into Shorts Series |
| Video A/B testing of up to three cuts | Arrives 2027 | Studio only | Use for hook tests once it can be run without automating Studio |
| Image posts in the Shorts feed | Live on phones | No API for posts | Revisit if the API or Buffer adds posts |
| Related-video link on each Short | Available (needs phone verification) | Studio only, per video | Set by hand for top Shorts in interactive sessions |
| Ask Studio feedback on script, hook, and title | Later in 2026 | Studio only | Watch |

## Where to look each Sunday

- YouTube: the [official blog](https://blog.youtube/), [Creator Insider](https://www.youtube.com/@CreatorInsider),
  the [YouTube Help "What's new" page](https://support.google.com/youtube/answer/9057455), and the policy pages for
  [channel monetization](https://support.google.com/youtube/answer/1311392) and the Partner Program.
- APIs: [Data API revision history](https://developers.google.com/youtube/v3/revision_history) and
  [Analytics API revision history](https://developers.google.com/youtube/analytics/revision_history).
- Models: Hugging Face trending text-to-speech and image models; GitHub search for Shorts pipelines updated
  in the last month.

## Check log

- 2026-09-26: Made on YouTube (Sep 23) announcements reviewed; table above. The Analytics API has no
  "stayed to watch" metric, so `ytc stats` reports `engaged_share` (engaged views / views) instead.
- 2026-09-26: faster-whisper adopted for the speech check. On ep001–ep008, `small.en` (about 8 s a Short
  on the Mac) and `large-v3-turbo` (about 25 s) each raised 7–10 differences, almost all other spellings of
  rare names (Jessop / Jessup) or skipped short words, and neither found a real error. Kept `small.en`, at
  temperature 0 so a re-check gives the same answer. Turbo also misheard "Rats could skip court" as "Pigs…",
  so a flagged common word still needs `ytc phonemes` before anyone re-renders.
- 2026-09-26: Wikimedia now throttles automated downloads that don't use its standard thumbnail widths
  (20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840; <https://w.wiki/GHai>), hardest for originals
  fetched from cloud servers (429 with a 10-minute retry) and for User-Agents without contact details. The
  API rounds a requested thumbnail width up to the next standard one. `visuals.py` now asks for the largest
  standard width below the original, and render containers send the contact address.
- 2026-09-26: Modal's Starter plan includes $30 a month only with a payment method; this workspace has
  none and gets $1 a month as a hard limit (its usage page shows "$x / $1"). With a card, a spend limit of
  $0 keeps it free (<https://modal.com/docs/guide/budgets>). The studio reads the amount from the
  `YTC_MODAL_CREDIT` Actions variable.
- 2026-09-26: `astral-sh/setup-uv` publishes exact version tags only (`v10.2.0`); `@v10` fails to resolve.
- 2026-09-27: Deep study of GitHub Shorts pipelines: 105 searches found 6,460 repos, and 93 were cloned and
  read. The summary, ranked picture plan and verified repo table are in `github-shorts-study-2026-09-27.md`,
  with notes in `github-deep-2026-09-27/`. License traps found: rembg's default model, Depth Anything V2
  Base and Large, FramePack and HunyuanVideo (territory clause), MiniMax-H3, LTX-2's labelling rule, and
  PolyForm Noncommercial on video-talkcraft, anything2explainer, SeeCut and YumCut.
