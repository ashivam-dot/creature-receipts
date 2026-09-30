# calesthio/OpenMontage — deep dive (g2a)

Repo: https://github.com/calesthio/OpenMontage
Read from two clones: `/tmp/ghdeep/g2a/OpenMontage` (depth 1, HEAD `08e2151`, 2,115 files) and
`/tmp/ghdeep/g2a/OpenMontage-history.git` (blobless, full history). Nothing was installed or run.
The repo is AGPL-3.0, so everything below is paraphrased: ideas to reimplement, not code to copy.
The only verbatim text is the rubric wording, quoted because the brief asked for it.

## Verification (checked 2026-09-27)

| Item | Value | Source |
|---|---|---|
| Stars / forks / watchers | 61,505 / 7,832 / 338 | `gh repo view` |
| Created | 2026-03-29 | `gh repo view` |
| Last push | 2026-09-06. The last commit (2026-09-05) is docs-only; the last merged PRs were #506 and #507 on 2026-08-22 | `gh repo view`, `git log` |
| License | GNU AGPL v3. `LICENSE` is the standard 661-line text with no extra terms, and the README badge agrees | `LICENSE` file |
| Archived / fork / releases | no / no / none | `gh repo view` |

---

## 1. Legitimacy check

**Verdict: a real, substantive project. The marketing inflates some numbers, and several knowledge
files describe features the code doesn't have. No sign of star farming.**

Evidence of substance:
- 517 `.py` files (4.9 MB of Python), 121 `BaseTool` classes (so "100+ tools" holds), and 126 test files.
- CI (`.github/workflows/ci.yml`) runs lint and pytest contract tests on ubuntu-latest with FFmpeg. No render
  is tested in CI.
- History: 449 commits from 55 authors. The owner has about 311 (as `calesthio` and `Calesthio`); the next are
  0xDevNinja with 28 and Yiyabo with 13. There are 146 merge commits; 458 PRs (110 merged); 153 issues (97 open).
- Commits per month: March 29, April 76, May 2, June 83, July 141, August 117, September 1. So the project is
  active but slowing: nothing has merged since 2026-08-22.
- The first commit (2026-03-29, `a3e735cc`) added 1,147 files and 240k lines at once, so the code was
  developed privately and then published. Development was heavily AI-assisted (about 31
  "Co-Authored-By: Claude" trailers).
- The stars look organic: the fork/star ratio is 12.7%, there are many external PR authors, and growth is
  steady (findarepo: about +1.4k in 7 days, +134 per day).

The "700+ files" claim:
- `.agents/skills/` has 994 files (577 `.md`, about 110k lines, 90 packs). Most are vendored third-party docs:
  HyperFrames, Remotion, GSAP, three.js, manim, Tailwind, Vercel React, HeyGen, FLUX.
- `.claude/skills/` has 428 files; 403 of them are byte-identical copies of `.agents/skills`.
- OpenMontage's own knowledge is `skills/`: 157 `.md` files, 24.3k lines. **This is the valuable part.**
- The files are real content, not filler: across both trees there are 734 `.md` files with a median of 125
  lines, and only 19 are under 20 lines. But most of it is not OpenMontage's own work.

Claims that don't match the code (check before trusting a knowledge file):
1. `tools/analysis/visual_qa.py`: the docstring promises caption-occlusion and transition checks, and neither
   exists. The tool only samples frames (1 s, 25/50/75%, end − 1 s), runs ffprobe and runs volumedetect
   (`_review` :145, `_probe` :203, `_audio_levels` :289).
2. The "post-render self-review" (`tools/video/video_compose.py` `_run_final_review` :2285) uses ffprobe,
   treats a PNG under 2,000 bytes as a black frame, runs volumedetect, and compares the transcript to the
   script. **No vision model is called anywhere in the code**; visual judgement is left to the host
   coding agent looking at sampled frames.
3. The documentary compose director requires the LUTs `warm_film_100`, `cool_archive_60`, `neutral_doc_20`
   and `bleach_bypass_80` (`skills/pipelines/documentary-montage/compose-director.md:117-122`). None of them
   exists in code, and no `.cube` files ship. The `vintage_film` preset says it adds grain but adds no noise
   (`tools/enhancement/color_grade.py:56-62`).
4. `motion_score` is described as optical flow. In the code it is the mean absolute grey-level difference
   between the first and the middle thumbnail (`tools/video/corpus_builder.py:686-691`).
5. The Remotion "parallax" animation is a 30 px vertical drift at 1.1x scale, with no depth layers
   (`remotion-composer/src/Explainer.tsx:391-395`).
6. `d3-geo`, `topojson-client` and `world-atlas` are in `remotion-composer/package.json`, but no component
   imports them. The maps and timeline in the showcase documentary ("How Salt Made History") were written by
   hand for that one video ("atelier mode", `skills/meta/bespoke-composition.md`) and are not in the repo.
7. The NARA adapter says no API key is needed. An unauthenticated request to its endpoint
   (`catalog.archives.gov/api/v2/search`) returned the catalog's HTML app, not JSON.

Red flags and lock-in:
- **It cannot run headless as designed.** It is "agent-first": there is no Python orchestrator, and an AI
  coding assistant reads the YAML manifests and Markdown director skills, then calls the tools. Most stages
  default to `human_approval_default: true` and tell the agent to "END YOUR TURN" (for example
  `skills/pipelines/explainer/asset-director.md:284-290`).
- It nudges toward paid APIs. The sponsors are paid gateways (Atlas Cloud, Bloome) with referral links, and
  many tools are thin wrappers over paid APIs. Even so, a real zero-key path exists: Piper;
  Archive.org, NASA and Commons; Remotion, HyperFrames and FFmpeg.
- The reference-video features use yt-dlp and youtube-transcript-api (`video_downloader`,
  `transcript_fetcher`), which are **banned for us**.
- License traps the tools never mention:
  - `face_restore` defaults to CodeFormer, which is under the S-Lab License 1.0 (non-commercial; checked
    upstream).
  - `lip_sync` uses Wav2Lip, whose open-source version is non-commercial (checked in the upstream README).
  - The ESA adapter is CC BY-SA 3.0 IGO.
  - `freesound_music` labels every result "Creative Commons (check individual sound license)" and never
    uses Freesound's license filter.
  - `pixabay_music` scrapes the Pixabay website.

---

## 2. The 12 pipelines

The manifests are in `pipeline_defs/*.yaml`. A thirteenth, `framework-smoke.yaml`, is a test harness.

| Pipeline | Stability | What it makes | Relevance to us |
|---|---|---|---|
| animated-explainer | production | A fully AI-produced explainer from a topic: narration, visuals, music | **High**: narrated, with a library of scene types (designed shots) |
| documentary-montage | beta | A montage built by retrieving real footage (CLIP corpus); narration optional | **High**: archive sourcing, pacing, grading |
| hybrid | production | Source footage plus designed or generated support visuals | Medium: its rule that the source stays primary |
| animation | production | Motion graphics, diagram-led explainers, kinetic type | Medium: designed shots |
| cinematic | production | Mood-led trailers, brand films, montages, 3D fly-throughs | Low: grading and sound rules |
| screen-demo | production | Screen recordings and synthetic UI | Low |
| avatar-spokesperson | production | Presenter or avatar videos | None |
| talking-head | beta | Edits raw footage of a person speaking | None |
| character-animation | beta | Reusable rigged cartoon characters | None |
| clip-factory | beta | Cuts long-form video into many clips | None |
| podcast-repurpose | beta | Podcast audio into video | None |
| localization-dub | beta | Translated subtitles and dubbing | None |

### documentary-montage (closest for sourcing)

The manifest is `pipeline_defs/documentary-montage.yaml`: a $1 budget, 3 revisions per stage, 2
send-backs, 60 minutes. The executive-producer skill is
`skills/pipelines/documentary-montage/executive-producer.md`.

1. **idea** (`idea-director.md`, no tools). It writes a brief with:
   - a one-sentence thematic question;
   - one tone from a fixed list: elegiac, reverent, dreamlike, wry or urgent;
   - a duration and a shape;
   - a music plan and a one-line philosophical end tag (both mandatory);
   - optional narration.
2. **scene_plan** (`scene-director.md`, 358 lines, no tools). It fills slots, each with:
   - a concrete description and 2-3 queries;
   - preferred sources by era;
   - a hero flag.

   Hold times must sum to within 10% of the duration.
3. **assets** (`asset-director.md`, 526 lines). There are two paths:
   - The fast path uses `direct_clip_search`, and the agent inspects the thumbnails itself.
   - The standard path uses `corpus_builder` and `clip_search` for CLIP ranking.

   `music_gen` is optional. Every asset carries provenance, and rejected picks are logged with reasons.
4. **edit** (`edit-director.md`, 380 lines, no tools). It covers:
   - holds set by tone, and adjacency rules;
   - at most 4 transition types, and L-cuts;
   - a music and silence plan;
   - a one-line reason for every cut.
5. **compose** (`compose-director.md`, 383 lines).
   - `video_compose` renders with the Remotion `CinematicRenderer`, which is mandatory here.
   - `audio_mixer`, `color_grade`, `video_trimmer` and `video_stitch` are optional.
   - The end tag is a Remotion ProRes 4444 overlay with alpha, composited by FFmpeg `overlay` with
     `-itsoffset`.

Every stage goes through `skills/meta/reviewer.md` and then a human gate (except compose).

### animated-explainer (closest for narration and designed shots)

The manifest is `pipeline_defs/animated-explainer.yaml`: a $2 budget, 20 minutes. The skills are in
`skills/pipelines/explainer/`.

1. **research** (`research-director.md`): at least 3 existing pieces, 3 angles and 5 sources, using the agent's
   own web search.
2. **proposal** (`proposal-director.md`): at least 3 concepts and a cost estimate. It locks the runtime
   (Remotion, HyperFrames or FFmpeg) and the composition mode (templated or atelier).
3. **script** (`script-director.md`, 268 lines):
   - The arc is hook, setup, build, climax, landing.
   - The word budget must land within ±10%.
   - Delivery cues are required, plus an "enhancement cue" every 8-10 s.
4. **scene_plan** (`scene-director.md`, 263 lines):
   - 1-3 scenes per script section, each with a type: hero_title, stat_card, charts, comparison, callout,
     text_card, animation, diagram, generated or broll. Each type has a duration range.
   - At least 3 types are used, and never 3 or more consecutive scenes of the same type.
5. **assets** (`asset-director.md`, 290 lines):
   - Required tools: `tts_selector`, `image_selector`.
   - Optional tools: `video_selector`, `diagram_gen` (Mermaid), `code_snippet`, `math_animate` (manim),
     `music_gen`.
   - It generates one sample for approval before the batch, and self-reviews each prompt (CHAI).
6. **edit** (`edit-director.md`, 170 lines): an edit decision list with animation and transition per cut,
   word-level subtitles, audio layers with ducking, and the playbook's pacing rules.
7. **compose** (`compose-director.md`): `video_compose` and `audio_mixer` (plus `hyperframes_compose` and
   `video_stitch`). Duration must land within ±5%, followed by the final review.
8. **publish** (`publish-director.md`): `export_bundle`.

---

## 3. Visual sourcing

### Sources

There are 17 adapters in `tools/video/stock_sources/` (4,034 lines). This is the license text each one
records:

| Adapter | License recorded | Usable for us? |
|---|---|---|
| wikimedia (images and video) | The file's `LicenseShortName` or `UsageTerms`, else "verify per-file" | Only through our whitelist (Commons includes CC BY-SA) |
| archive_org (prelinger, opensource_movies, home_movies) | `licenseurl`, else a guess from the collection ("Public Domain / CC — verify per item") | Prelinger is likely PD; check the rest item by item |
| nara, noaa | Hard-coded "Public domain (U.S. federal government work)" | Mostly yes; the NARA API seems to need a key now (section 1, item 7) |
| loc | PD if the rights text contains "public domain" or "no known", otherwise "verify per item" | Yes, with that rule |
| nasa | "NASA Media Usage Guidelines (public domain with caveats)" | Yes (watch the caveats on logos and people) |
| dareful | CC BY 4.0 | Yes, with credit (nature footage only) |
| videvo | CC BY 3.0, or Videvo's own attribution license | Only the CC BY clips |
| pond5_pd | "Public domain (CC0 equivalent)", via an unofficial endpoint | Terms-of-service risk |
| esa | CC BY-SA 3.0 IGO | **No** (share-alike) |
| jaxa | "JAXA Digital Archives License (educational/informational use)" | **No** |
| pexels, pixabay_video, unsplash, coverr, mixkit | Each site's own "free" license | **No** under our PD/CC0/CC BY rule |

**No adapter enforces a license whitelist.** The license text is passed straight through into the clip
record (`tools/video/corpus_builder.py:554,613`, `tools/video/direct_clip_search.py:431,486`). Our
`_COMMONS_OK` regex is stricter.

Another caution: Pixabay's community library contains many unlabelled AI-generated clips. One OpenMontage
mode uses them on purpose for a children's fantasy style (`documentary-montage/asset-director.md:84-110`).
For a history channel, that makes our `_pixabay` fallback a disclosure risk.

### Search

- **Slot description first, queries second** (`documentary-montage/scene-director.md:100-133`).
  - Each slot gets a description built as subject, action or pose, environment, lighting, and an era or
    texture hint. It uses nouns and adjectives only, with no emotion words.
  - The test: if you can't picture a specific photograph from the description, the ranking model can't
    either (:118).
  - Then 2-3 short queries of 2-5 words: a literal one, a lateral one (a nearby concept) and, for hero
    slots, an association query.
  - **Ranking uses the description, not the queries**, which are only for recall
    (`asset-director.md:275-299`).
- **Period vocabulary and sources by era** (`scene-director.md:140-160`):
  - Vintage briefs use period words.
  - Each era maps to its best archive: NARA for WWII, the Cold War, Apollo and civil rights; LOC for
    public-domain newsreels before 1928; Prelinger for the 1940s-80s.
  - Vintage briefs require at least 60% of slots and picks to come from archive.org (`scene-director.md:291`,
    `asset-director.md:447`).
- **POV keyword** (`skills/creative/broll-planning.md:59-96`): add a camera-POV word to every stock query
  (drone, aerial, over-the-shoulder, macro, top-down, handheld, locked-off). A wrong POV is harder to fix than
  a wrong grade.
  - *Our adaptation:* on Commons, the equivalent is the medium word (photograph, engraving, poster,
    newspaper, map, portrait).
- **Commons query cascade** (`tools/video/stock_sources/wikimedia.py:134-187`). Commons search ANDs every term,
  so a long descriptive query returns nothing. The adapter tries three queries in turn:
  1. the full query;
  2. the two longest words that aren't years, after dropping stop words and words that name other archives
     ("prelinger", "archive", "footage");
  3. the single longest word.

  It stops at the first query that returns results. Archive.org uses a similar cascade.

### Ranking

- **Embedder** (`lib/clip_embedder.py`): CLIP ViT-B/32 (`openai/clip-vit-base-patch32`, MIT), 512-dimensional,
  L2-normalised, about 150-300 ms per image on CPU. Each clip embeds 5 evenly spaced thumbnails (skipping the
  first and last frame), which are mean-pooled and renormalised (`pool_frames` :138). Text is capped at 77
  tokens (:130).
- **Fused score** (`lib/corpus.py:234-245`): 0.7 × the image-embedding similarity + 0.3 × the similarity of an
  embedding of the source's own title, description and tags (capped at 500 characters).
  - The text weight is 0.5 when the source tags are good, and 0.15 for long prose tags such as Prelinger's.
- **Ranking parameters** (`documentary-montage/asset-director.md:275-299`):
  - k = 30 for hero slots, otherwise 12; `motion_min` 1.5.
  - Always pass `exclude_ids` (clips already used) so nothing is picked twice.
- **Thresholds** (:322-330):
  - 0.30 or more is strong.
  - 0.22-0.30 is plausible and needs judgement.
  - Under 0.22, the corpus doesn't have it: grow the corpus instead of taking the best of a bad set.
  - The code comment in `tools/video/clip_search.py:279-280` says 0.25, a small inconsistency.
  - At most 2 growth passes per slot. After that the slot is "unfilmable": drop it or ask for footage.
- **Diversity** (`lib/corpus.py`):
  - `find_similar_set` (:317) is MMR: score = (1 − λ) · similarity to the seed − λ · the maximum similarity to
    anything already picked.
  - `diversify` (:384) greedily removes near-duplicates next to each other, and the dropped slots are
    re-ranked.
- **Corpus sizing** (:238-242):
  - Fetch 8-12x the slot count, 4-8 results per source per query (20 or more adds noise).
  - Sanity checks: under 50 rows is too few; a skewed source mix is a problem; a mean motion score under 1.0
    means a slideshow is coming.
- **Judgement over score** (:305-320): choose on era, motion, how the clip sits next to its neighbours and the
  emotional register. A higher score never overrides the wrong tone. Each rejection is logged with a reason
  (for example: wrong era, a 2022 4K kitchen when the brief is vintage).

### Verification with vision models

**None happens automatically in code.** On the fast path the agent, or a sub-agent, looks at the thumbnails.
`video_understand` (CLIP, BLIP-2, LLaVA; GPU) can answer "Does this match: [scene]?"
(`skills/creative/video-understand-usage.md:92`), but no pipeline calls it automatically. **Our Gemini
ranker is already ahead here.**

### When nothing fits

- The slot is declared unfilmable after 2 growth passes (above).
- The b-roll fallback chain (`skills/creative/broll-planning.md:117-124`) is: new keywords, then another
  provider, then AI generation, then ask the user.
- The rule of thumb for real versus generated (:17-26): if it must look real (people, historical equipment),
  use real media; if it's abstract or specific to the concept, generate or design it.
- **Designed shots** come from the scene-type library (`remotion-composer/SCENE_TYPES.md`):
  - text_card, hero_title, stat_card, callout (a quote, tip or warning), comparison;
  - bar, line and pie charts, kpi_grid, progress_bar;
  - a Mermaid diagram, and an anime_scene (several stills with particles).

  The explainer scene director names reusable techniques (`explainer/scene-director.md:105-139`):
  - Diagram Reveal (build the picture as the narrator names each part);
  - Stat Card Punch (hold 4-5 s);
  - Before/After Split, Timeline Progression;
  - **Zoom and Focus** (start wide, then zoom into one component).
- **Never use an AI image for exact text.** Anything with verbatim text must be a code-rendered card
  (`explainer/asset-director.md:262`, `scene-director.md:254`).
- **The hybrid pipeline's rules**, which fit a history channel well (`pipeline_defs/hybrid.yaml:57-145`):
  - keep source-led and support-led beats separate;
  - support assets must fill real narrative gaps;
  - generated inserts must not eclipse the source's truth.
- For batch work, OpenMontage itself recommends templated scenes over hand-authored ones
  (`skills/meta/bespoke-composition.md:22-26`).

### Varying shots and pacing

- **Hold time by tone** (`documentary-montage/edit-director.md:66-70`; slot counts in `scene-director.md:46-50`).
  Base / min / max in seconds:

  | Tone | Base | Min | Max | Slots per 60 s |
  |---|---|---|---|---|
  | elegiac | 4.0 | 2.5 | 7.0 | ~15 |
  | reverent | 3.5 | 2.0 | 6.0 | ~17 |
  | dreamlike | 3.0 | 1.5 | 5.5 | ~20 |
  | wry | 2.0 | 1.0 | 4.0 | ~30 |
  | urgent | 1.2 | 0.5 | 2.5 | ~50 |

  Hero slots (the opening, the turn and the final image) get the maximum. **"Wry" matches our tone: about
  2 s per shot.**
- **Rules for adjacent shots** (`edit-director.md:204-212`):
  - same subject at the same scale: change the scale;
  - same palette: break it at least every 4 cuts;
  - same motion direction: flip one.
- Never hold the same shot length 3 times in a row (`skills/creative/cinematic.md:75`).
- Arrange by story beat, not by score, and log any reordering (:79-96).
- Trimming (:108-119): cut before the action ends, and leave 4-6 frames of handle. Slow short clips to
  0.5-0.75x; never freeze-frame.

---

## 4. Motion and editing

- **Shot vocabulary** (`schemas/artifacts/scene_plan.schema.json`): each scene has a `shot_language` with:
  - `shot_size`: extreme_wide, wide, medium_wide, medium, medium_close, close_up, extreme_close_up,
    over_shoulder, insert, establishing;
  - `camera_movement`: 18 values;
  - `lens_mm`, `lighting_key` (11 values), `depth_of_field`, `color_temperature`.

  Each scene also has `shot_intent`, `narrative_role` (establish_context, build_tension, deliver_payload,
  evidence, comparison, resolution, and others), `information_role`, `hero_moment` and `texture_keywords`.
  `lib/shot_prompt_builder.py` turns these into a five-layer prompt: camera, then movement, then subject,
  then lighting, then an adapted style hint rather than one fixed prefix on every scene.
- **Still-image motion in Remotion** (`remotion-composer/src/Explainer.tsx:345-413`). Scale and
  translation interpolate linearly over the shot:
  - zoom-in 1.0→1.18; zoom-out 1.18→1.0;
  - pan-left/right of ±40 px at 1.15x;
  - ken-burns 1.0→1.22 with a drift of −25 px x and −15 px y;
  - "parallax", which is only a vertical drift.

  Each still also gets a spring fade-in, a fade to 0.3 opacity over the last 8 frames (for crossfades), and a
  radial vignette.

  Real footage (`CinematicRenderer.tsx:40-114`) gets a very slow push (1.015→1.0), a CSS grade
  (contrast 1.06, saturation 0.88, brightness 0.92), a tone gradient multiplied over it, and a vignette.
- **Title cards** (`CinematicRenderer.tsx:162-386`): words appear with a 3-frame stagger. Each fades in over
  14 frames while its blur settles from 6 px to 0 and it rises 14 px. Accent lines grow from the centre,
  over a darkened, blurred background clip.
- **Transitions**:
  - The documentary pipeline allows at most 4: a hard cut (the default), a dissolve of 0.5-1.0 s, a fade to
    black of 0.5 s, and fade-in/out bookends. Wipes, push/slide, zoom blurs, RGB splits, light leaks and
    glitch are banned (`edit-director.md:153-180`).
  - L-cuts carry ambient sound 0.5-1.5 s across the 3-4 hardest cuts (:218-225).
  - FFmpeg `xfade` fade and fadeblack are in `tools/video/video_stitch.py:616-657`.
  - HyperFrames has a registry of 16 transition families.
- **Parallax / 2.5D**: not implemented. There is no depth estimation or layer separation anywhere.
- **Image-to-video**:
  - Paid APIs: Kling, Veo, Runway, Seedance, MiniMax.
  - Local GPU: `wan_video` drives Wan 2.2 TI2V-5B (Apache-2.0) with operations `image_to_video` and
    `first_last_frame`. It needs 12 GB of VRAM, or about 2 GB with sequential offload at about 4 s per step
    (`docs/PROVIDERS.md:1244-1348`).
  - `ltx_video_modal` calls an LTX-2 endpoint you deploy yourself on Modal.
- **Captions** (`remotion-composer/src/components/CaptionOverlay.tsx`): pages of 6 words at 42 px. The active
  word is highlighted with a glow, spoken words are full colour, and **upcoming words are dimmed to about
  60% opacity**.
- **Overlays**: section_title, stat_reveal (a corner badge), a hero_title overlay, and the end tag.
- **Color**: `color_grade` presets are FFmpeg `colorbalance` + `curves` + `eq` chains: cinematic_warm and
  cinematic_cool, moody_dark, bright_clean, vintage_film, high_contrast, neutral
  (`tools/enhancement/color_grade.py:25-75`). One grade per timeline, never per clip. **Low-resolution
  footage is letterboxed, never upscaled** (`documentary-montage/compose-director.md:41-85, 348-350`).
- **Sound**:
  - `audio_mixer` ducks the music by 12 dB by default, with a 200 ms attack and 500 ms release, then runs
    loudnorm.
  - Music is required in the documentary pipeline, with one held silence of about 2 s at the emotional
    centre and a 3-5 s fade at the tail (`edit-director.md:129-134`).
  - Numbers are in section 6.
- **Render engines**:
  - **Remotion** (React, `npx remotion render`): source-available, not open source. It is free, including
    for commercial use, for individuals and companies of up to 3 people (checked in upstream `LICENSE.md`).
  - **HyperFrames** (HTML + GSAP, `npx hyperframes render`): Apache-2.0 (checked upstream). Requires
    Node ≥ 22 and FFmpeg.
  - **FFmpeg** directly.
  - No MoviePy (it isn't in `requirements.txt` or imported anywhere).
  - Both browser engines render through headless Chromium, so they run on Linux in a container. OpenMontage's
    CI doesn't exercise them, and its notes warn to render one at a time because each render starts its own
    Chromium (`skills/core/remotion.md:331`).

---

## 5. Quality control

### Plan-level gates (deterministic; they score the plan's fields, not pixels)

`video_compose._pre_compose_validation` (`tools/video/video_compose.py:1415`) blocks the render on a
delivery-promise violation or a slideshow-risk verdict of "fail".

- **`lib/slideshow_risk.py`** scores 6 dimensions from 0 to 5 (lower is better):
  - **Repetition:** +2 if one scene type exceeds 70%; +1.5 if fewer than 60% of descriptions are unique;
    +1.5 if one shot size exceeds 60%.
  - **Decorative:** 5 × the share of scenes with no information, narrative or shot intent.
  - **Weak motion:** 4 × the share of moving shots without a `shot_intent`.
  - **Weak intent:** 5 × (1 − the share of scenes with a `shot_intent`).
  - **Typography:** 4.0 if text cards exceed 60% of scenes, 2.5 above 40%, 1.0 above 20%.
  - **Cinematic claims:** 1.8 for each missing item (a hero moment, movement in 30% of scenes, lighting in
    30%).

  The verdict comes from the average: **under 2 "strong", under 3 "acceptable", under 4 "revise", 4 or more
  "fail".**
- **`lib/variation_checker.py`** applies to plans of 4 or more scenes. Each violation adds 0.6 (capped at 5):
  - one shot size in more than 50% of scenes;
  - 3 or more consecutive shots of the same size;
  - more than 60% static (it asks for movement in at least 40%);
  - one lighting setup or fewer;
  - no hero moment, or a hero with the same shot size as a neighbour;
  - generic phrases ("a beautiful", "stunning", "modern") in 30% of scenes;
  - texture keywords in under 30% of scenes, or a `shot_intent` in under 50%.
- **`lib/delivery_promise.py`** (`validate_cuts` :113): a minimum share of motion by promise type:
  motion-led 0.7, source-led 0.3, avatar 0.3, hybrid 0.2, explainers 0. Text cards, charts and other "slide
  grammar" don't count as motion.
- **`lib/verify_scene_pacing.py`**: every narration cue needs a visual landmark within ±1.0 s. It also flags
  overflow, and more than 5 s of frozen frame.
- **`tools/analysis/composition_validator.py`**: checks that cuts and assets exist, `out > in`, narration
  runs no more than 1 s past the video, and warns when the music is shorter than the video.

### Post-render checks (`video_compose.py:2178-2500`)

- **ffprobe:** flags a duration under 1 s, a duration drift over 25%, a resolution under 320x240, or no audio
  stream.
- **Frames** at 10/35/65/90% (:2405): a PNG under 2,000 bytes counts as a black frame (:2422).
- **volumedetect** (:2477-2489): a mean below −60 dB is silent; above −40 dB narration is present; above
  −50 dB music is present; a peak above −0.5 dB is clipping.
- **Transcript against script** (`_compare_transcript_to_script` :2178-2284): word accuracy by set overlap
  must be at least 0.9. Words such as "dot", "comma" or "hyphen" that are spoken but not in the script count
  as a **TTS punctuation leak**, which is critical.
- **Frame-quality thresholds** (`skills/creative/video-understand-usage.md:39-41, 79, 121`), stated in the
  skill file only; nothing automates them:
  - blur (Laplacian variance) under 100 fails; above 500 is sharp;
  - mean brightness must be between 50 and 200;
  - contrast (pixel standard deviation) under 30 fails.

### Reviewer loop (`skills/meta/reviewer.md`), quoted

The severities (:40-49) come from the CHAI paper (arXiv 2604.21718v2):
- **critical:** "Must fix before proceeding… every critical finding MUST carry a `proposed_fix` (concrete
  replacement text, exact field value, or specific corrective action). A critical finding without a proposed
  fix is downgraded to `investigation`."
- **suggestion:** "Should fix… Suggestions MUST carry a `proposed_change`."
- **nitpick:** "Could fix."
- **investigation:** "A real concern but you cannot pinpoint the fix… do not block on it."

The example of a good finding: "Section 3 narration is 180 words for a 10-second window — that's 1080 wpm,
impossible to speak. Cut to 25 words." The bad one: "Script might be too long."

The decision table (:83-87):
- "0 critical → **Pass**";
- "1+ critical → **Revise** … (max 2 rounds)";
- "After 2 revision rounds, still critical → **Pass with warnings** … Never block indefinitely."

The CHAI rules also ask for findings that are Accurate (they point to a field or frame), Complete (look for
the same class of error elsewhere) and Constructive (they carry a fix). The final self-review needs at least 4
sampled frames. In atelier mode, two scenes sharing a primary visual subject is a critical finding.

### Self-evaluation rubrics, quoted (score 1-5; "If any dimension scores below 3, revise")

- **Script** (`explainer/script-director.md:192-205`):
  - "Hook power — Would someone stop scrolling in the first 3 seconds?"
  - "Word count accuracy — Within ±10% of target for the duration?"
  - "Narrative flow — … 'Therefore/but' not 'and then'?"
  - "Enhancement density — At least one cue every 8-10 seconds?"
  - "Voice performance — Are pauses, emphasis, pace, and sample section explicit?"
  - "Jargon management"
  - "Climax payoff — Does the aha moment deliver on the hook's promise?"
  - "CTA relevance"
- **Scene plan** (`explainer/scene-director.md:226-237`):
  - "Visual storytelling — Does each scene advance understanding, not just decorate?"
  - "Script alignment — Does every scene match what the narrator is saying at that moment?"
  - "Technique variety"
  - "Playbook fidelity"
  - "Asset feasibility — Can every required_asset actually be generated with available tools?"
  - "Pacing — … High-info scenes balanced with breathing room?"
- **Assets** (`explainer/asset-director.md:228-237`): Completeness, Audio quality, Visual consistency ("Do all
  images look like they belong to the same video?"), Budget adherence, Playbook fidelity.
- **Documentary-montage review focus** (`pipeline_defs/documentary-montage.yaml:53-178`), quoted:
  - "Slot descriptions use concrete noun-and-adjective language"
  - "Every slot has 2-3 short search queries"
  - "At least 2 slots are marked hero"
  - "No clip_id is picked for two slots"
  - "Provenance (provider, original_url, license) present on every asset"
  - "Standard path: corpus size >= 8x slot count, scores >= 0.22, diversify ran clean"
  - "Hero slots hold longest; mid-sequence cutaways shortest"
  - "No two adjacent cuts share subject AND scale"
  - "Transition vocabulary is at most 4 distinct values"
  - "Every cut has a reason"
  - "Uniform LUT applied across the timeline"
  - "Overlay mode: extract a frame from the overlay region and verify text is visible over footage, not over
    black."

---

## 6. Production knowledge worth keeping (paraphrased)

The statistics are cited from TikTok, YouTube, Shortimize and OpusClip; treat the exact percentages as
directional.

**Shorts pacing and retention** (`skills/creative/short-form.md`):
- A visual change every 1-3 s; 20-40 cuts per minute; **no static hold over 3 s** (:16, :101-104). Pattern
  interrupts every 2-4 s are credited with 58% average retention against 41% without (:108).
- Completion falls with length: 0-15 s 92%, 16-30 s 84%, 31-60 s 68% (:47-49). Shorts cluster around 13 s or
  the full 60 s (:55). Total watch time is what matters, so a 45 s video with 70% completion beats a 15 s video
  with 40% (:57).
- Viewers decide within about 1.7-3 s (:61). Retention at 3 s maps to reach: 60-70% about 1.6x, 70-85% about
  2.2x, 85% or more about 2.8x (:68-70). Checkpoints: 70% at 3 s, 60% at 15 s, 50% at 30 s (:76).
- **Hook:** text on screen within 0.5 s (people read before they listen), voice from 0 s, motion in frame 1
  (:93).
- **YouTube Shorts safe area is 984x1500**, with dead zones of 120 px at the top, 300 px at the bottom and
  96 px on the right. The cross-platform safe area is 900x1400 (:27;
  `skills/creative/typography.md:80-88`).
- **Captions:** 42 px or larger, bold sans-serif, word-by-word highlight, at most 2 lines
  (`short-form.md:128`; `typography.md:134-146`: 32-42 characters per line, a semi-opaque box or a 2-4 px
  stroke, 4.5:1 contrast).
- **On-screen text:** 3-5 words in the upper part of the safe area, a 0.2-0.3 s pop entrance, on screen for at
  least 1 s per 13 characters (`typography.md:92-98`). Ease out with a cubic curve; never animate text
  linearly (:111-120).
- **Audio for Shorts:** music at −22 to −26 dB, 90-110 BPM for explainers, instrumental only; voice at
  180-200 words per minute (`short-form.md:149, 156, 161`).
- End on a loop back to the start (the 60 s template).

**Story and narration** (`skills/creative/storytelling.md`):
- Describe the **visual cause, not the emotion**. For example, instead of "a powerful swell", write when the
  music drops out, for how long, and what comes back (:62-69).
- Hook types: contrarian, outcome, mystery (a date plus "something impossible happened"), stakes (:92).
- Link beats with "but" and "therefore", never "and then"; present the misconception first, then refute it
  (Muller 2008) (:107-124).
- A new visual element every 3-5 s at long-form pace; 1-3 s of silence after the key insight; one line of
  camera intent per beat (:136, :145, :161-165).
- Mayer's principles (temporal contiguity; seductive details) argue against decorative pictures that don't
  show the line.

**Shot selection and documentary style**:
- Tone sets the hold table (section 3). Hero shots go at the opening, the turn and the ending.
- One grade per video, letterbox instead of upscaling, at most 4 transition types, and a reason for every cut
  (the documentary directors).
- Documentary average shot length is 6-12 s long-form against 1-3 s in montage; never 3 identical lengths in
  a row; the word "cinematic" is banned in favour of concrete choices; take the music out for 3-5 s at the
  key reveal (`skills/creative/cinematic.md:32, 63, 75, 142`).
- Pixabay's free API caps images at 1,280 px, and its download URLs expire
  (`skills/creative/stock-sourcing-usage.md:80-83`). That rules it out for our 1,200 px+ crops anyway.

**Sound** (`skills/creative/sound-design.md`):
- Levels: music bed 18-20 dB below the dialogue; effects at least 6 dB below it; true peak no higher than
  −1.5 dBTP (:10-16, :82-83).
- **Start a whoosh 10-20 ms before the visual change**; it lasts 400-500 ms (:12, :65-73). A pop runs under
  200 ms; an impact sits at −12 to −6 dB; a riser lasts 1-3 s.
- Duck music by 6-12 dB under voice, and cut 2-4 kHz in the music so speech is clear (:32-33).
- Voice chain: high-pass at 80 Hz, cut 500 Hz, boost 2-5 kHz, cut 6-8 kHz; compress 3:1 with a 1-5 ms attack
  and 10-20 ms release (:15-16).

**Visual prompting** (`explainer/asset-director.md:192-208`): draft the prompt, critique it against five
aspects (subject, subject motion, scene, spatial framing, camera), then rewrite it, replacing subjective
adjectives with their visual causes. Log all three versions.

---

## 7. Tools: free versus paid

There are 121 tools. Sources for the classification: `docs/PROVIDERS.md` (pricing), the `BaseTool` metadata,
and my AST scan.

- **Free (local or open source):**
  - analysis: `clip_search`, `scene_detect`, `frame_sampler`, `transcriber` (faster-whisper), `visual_qa`,
    `composition_validator`, `audio_probe`, `audio_energy`, `face_tracker`, `video_analyzer`, and
    `video_understand` (GPU);
  - audio and post: `audio_mixer`, `audio_enhance`, `color_grade`, `subtitle_gen`, `auto_reframe`,
    `silence_cutter`, `video_compose`, `video_stitch`, `video_trimmer`, `remotion_caption_burn`,
    `hyperframes_compose`;
  - graphics: `diagram_gen` (Mermaid), `code_snippet`, `math_animate` (manim), `threejs_world`,
    `blender_world`;
  - enhancement: `bg_remove` (rembg), `upscale` (Real-ESRGAN);
  - voice and music: `piper_tts`, `music_library`, `export_bundle`.
- **Free with local or Modal GPU:**
  - `wan_video` (Wan 2.1/2.2, Apache-2.0);
  - `comfyui_*`, `local_diffusion`;
  - `ltx_video_local`, `ltx_video_modal`, `hunyuan_video`, `cogvideo_video` (custom weight licenses: check
    each);
  - `face_restore` and `lip_sync` (**non-commercial weights**, see section 1).
- **Free with a key or a free tier:**
  - stock: `pexels_*`, `pixabay_*`, `corpus_builder`, `direct_clip_search` (Commons, Archive.org and NASA
    need no key);
  - `freesound_music` (mixed licenses);
  - `google_tts` (1M characters per month free for each voice tier);
  - `azure_tts` and `azure_stt` (F0 tier);
  - `elevenlabs_tts` and `music_gen` (10k characters per month; attribution on the free tier).
- **Paid only:**
  - FAL-based tools (`flux_image`, `recraft`, `seedream`, `kling_video`, `seedance_video`, `minimax_fal`,
    `fal_elevenlabs_*`);
  - Atlas; Kling official; OpenAI and Sora; `google_imagen` / `google_music` / `veo` / `gemini_omni_video`
    (`docs/PROVIDERS.md:799-831` lists no free tier for them, only Google Cloud's $300 new-account credit);
  - Runway, HeyGen, Higgsfield, Suno (its free tier is non-commercial), Grok, DashScope, Doubao, MiniMax,
    Hunyuan cloud, Jimeng, Fish Audio.
- **Banned for us:** `video_downloader` and `transcript_fetcher` (they touch YouTube), and `pixabay_music`
  (scraping).

---

## Better or worse than ours

**Where it is better:**
- **A planning vocabulary with checks.** Every shot carries a size, movement, intent, narrative role and hero
  flag, and deterministic rules turn "slideshow" into measurable violations. We plan one visual per beat and
  check nothing about variety.
- **A retrieval funnel.** It fetches 8-12x candidates, pre-ranks cheaply with fused image and caption scores,
  sets thresholds for grow-or-give-up, dedupes with MMR, and logs rejections with reasons. We send at most 5
  candidates per beat to Gemini.
- **Real archival motion sources**: Archive.org/Prelinger, NARA, LOC, NASA and Commons video. We only fetch
  stills from our archive sources.
- **Designed shots and an edit grammar:** stat, quote, comparison and timeline cards, word-stagger titles,
  crossfades and fades to black, L-cuts, music and silence planning, one uniform grade.
- **Knowledge files with concrete numbers** for pacing, typography, safe areas and sound.
- **Post-render technical checks:** transcript against script, audio levels, black frames.

**Where it is worse or irrelevant:**
- No automated visual judgement in code, where we have a Gemini pick and a contact-sheet review. For an
  unattended pipeline we're ahead.
- License handling is record-only, where ours is a strict whitelist. Music sourcing is unsafe (scraping,
  unfiltered Freesound).
- It is not headless (an interactive agent plus human gates), is non-deterministic, is AGPL, and is heavy
  (Node + Chromium + Python, with GPU optional).
- Several documented features are unimplemented (section 1). Much of the tool count is paid-API wrappers.

---

## Adoption (ideas only; the AGPL means we write our own code)

| Change | Code or idea | Effort | Modal cost | Risks |
|---|---|---|---|---|
| 2-3 shots per beat: full frame, a detail crop from the focus point, and a second image or card; no still held over about 3 s | Idea | M | CPU only, about +$0.01 per Short | Needs 2-3x more images; mitigate with detail crops from the same image |
| Rich per-beat visual spec (subject, action, setting, era/date, medium, the noun that must be visible) and typed queries (literal, lateral, association, with period words) | Idea (a `writer.py` schema change) | S | 0 | Longer prompts |
| CLIP (or SigLIP) pre-rank over 8-12x candidates with a fused title/description score, then Gemini picks from the top 5-8 | Idea (our own about 150 lines) | M | About 1 min of CPU per Short, under $0.01; roughly 0.6 GB of weights in the image or a Volume | Thresholds are tuned for video thumbnails, so recalibrate on our accepted and rejected beats; CLIP is weak on era |
| Commons query cascade (full, then the 2 longest non-year words, then 1) plus LOC's rights-text rule | Idea | S | 0 | Dropping years raises wrong-era risk, so the era check must stay in the pick prompt |
| Mark a beat "unfilmable" early and route it to templated designed shots (date/place card, map pin, document or newspaper crop, quote card, number card, timeline) instead of reusing a neighbour's picture or a gradient | Idea; render with PIL/FFmpeg or HyperFrames (Apache-2.0) | M | PIL: about 0. HyperFrames: Node 22 + Chromium in the image, about 1-2 min of CPU per Short | Templates can make every Short look alike; rotate 2-3 styles |
| Deterministic variety checks: no 3 shots of one size in a row, a hero shot at hook and twist, alternating pan direction, no adjacent same subject and scale, at most 4 transition types | Idea (Gemini tags shot size, medium and subject during the pick; a Python checker enforces) | S | 0 | Tagging noise |
| Reviewer findings must carry a concrete fix (a query, a crop, a pool swap or a card type), and one error prompts a check of every beat for the same class | Idea (a `studio.py` prompt change) | S | 0 | None; our gate stays stricter (no "pass with warnings") |
| Hook frame: 3-5 words of hook text on screen from frame 1 inside the 984x1500 safe area; motion in frame 1 | Idea (libass) | S | 0 | Must not duplicate the caption; OpenMontage's reviewer treats that as critical |
| One global grade, light grain and vignette over mixed-era stills; for low-resolution or wide images, a blurred fill (our variant of OpenMontage's letterbox) instead of an upscale | Idea (FFmpeg `curves`/`eq`/`colorbalance`, `noise`, `vignette`) | S | Negligible | Over-grading colour photos |
| Music bed of CC0/CC BY instrumentals at −22 to −26 dB, ducked 6-12 dB; about 1.5-2 s of silence before the twist; whoosh 10-20 ms before the cut | Idea (we already have the sidechain code) | S-M | 0 | Sourcing music: only a strict license filter (for example Freesound `license:"Creative Commons 0"`) |
| Post-render checks: per-frame blur, brightness and contrast; black frames; volumedetect for silence and clipping; faster-whisper transcript against script (≥ 0.9, plus punctuation leaks) | Idea (faster-whisper is MIT) | S | About 10-20 s of CPU per Short | False positives on dark archive photos; tune the brightness floor |
| Short real archival motion clips (Prelinger, LOC, NARA, Commons video) cut into beats | Idea | M | CPU for downloads and transcodes | Per-item license checks; few clips outside the 1900s-1980s |
| Image-to-video (Wan 2.2 TI2V-5B, Apache-2.0) for 1-2 non-person hero shots, labelled as AI | Tool (run separately) | L | Modal GPU minutes per 5 s clip; measure first | Credibility; never animate real people; disclosure |

---

## Verdict: BORROW IDEA

It is the most concrete free knowledge base and plan-check design I've seen for narrated documentary videos.
But the code is AGPL, orchestrated by an interactive agent with human gates, never judges visuals
automatically, and doesn't enforce licenses. So reimplement the ideas in our Python pipeline; don't run or
vendor it.

---

## Top insights for Days of Odd (ranked)

1. **Break the slideshow: 2-3 shots per beat, and never hold a still over about 3 s.** The Shorts guidance is
   a change every 1-3 s (`skills/creative/short-form.md:16, 101-104`); the "wry" tone table puts the base hold
   at about 2 s (`skills/pipelines/documentary-montage/edit-director.md:66-70`). Build each beat from a wide
   frame, a detail crop driven by Gemini's focus point ("Zoom and Focus",
   `explainer/scene-director.md:136-139`), and a second image or a designed card. Alternate the motion
   direction.
2. **Write a picture brief per beat, not just queries.** Use subject, action, setting, era/date and medium,
   plus the noun that must be visible, with no emotion words. The test is whether you could name a specific
   photograph (`documentary-montage/scene-director.md:100-133`; `skills/creative/storytelling.md:62-69`).
   Queries: literal, lateral, association, with period vocabulary. Rank on the brief, not the query
   (`documentary-montage/asset-director.md:275-299`). This targets "the picture doesn't show the line" and
   "wrong period".
3. **Widen the funnel and pre-rank cheaply.** Fetch 8-12x candidates from Commons, LOC, NARA, the Met, AIC and
   NASA, with the Commons query cascade (`tools/video/stock_sources/wikimedia.py:134-187`). Score them with
   CLIP: 0.7 image + 0.3 title/description (`lib/corpus.py:234-245`). Dedupe with MMR (`lib/corpus.py:317`).
   Grow the pool at most twice if the best score is below the floor (`asset-director.md:322-330`), and send
   the top 5-8 to Gemini. Log rejections with reasons.
4. **Stop reusing a neighbour's picture for empty beats.** Declare the beat unfilmable, then render a
   templated designed shot: a date/place card, map pin, document crop, quote card, number card or timeline
   (`remotion-composer/SCENE_TYPES.md`; the technique list in `explainer/scene-director.md:105-139`). Follow
   the hybrid pipeline's rule that archival source stays primary and support visuals only fill real gaps
   (`pipeline_defs/hybrid.yaml:142-145`). Never use an AI image for text
   (`explainer/asset-director.md:262`).
5. **Make "not a slideshow" a measurable gate before render.** Have Gemini tag shot size, medium and subject
   during the pick; then reject 3 same-size shots in a row, any repeat of subject and scale, or a missing hero
   shot at hook or twist (`lib/variation_checker.py`, `lib/slideshow_risk.py` thresholds; adjacency rules in
   `edit-director.md:204-212`).
6. **Require a concrete fix for every reviewer finding.** A critical finding without a proposed fix gets
   downgraded, and one error means checking all beats for the same class (`skills/meta/reviewer.md:40-49`).
   Wire the fix type (query, crop, pool swap, card) straight into `pick.replace`.
7. **Package the hook frame.** Show 3-5 words of hook text within 0.5 s inside the Shorts safe area (984x1500,
   with 120/300/96 px dead zones), with motion in frame 1 and voice at 0 s (`short-form.md:27, 93`;
   `typography.md:80-88`).
8. **Give mixed-era stills one look.** Apply one global grade with grain and a vignette; use a blurred fill
   for wide or low-resolution images instead of upscaling (`documentary-montage/compose-director.md:41-85,
   348-350`; recipes in `remotion-composer/src/CinematicRenderer.tsx:63-111` and
   `tools/enhancement/color_grade.py:25-75`).
9. **Add music and a silence.** Use an instrumental CC0/CC BY bed at −22 to −26 dB, ducked 6-12 dB, with about
   1.5-2 s of silence before the twist; start the whoosh 10-20 ms before the cut (`short-form.md:149, 156`;
   `skills/creative/sound-design.md:10-16, 32-33, 65-73`; `edit-director.md:129-134`). Don't copy their music
   sourcing.
10. **Check the rendered file itself.** Check frames for blur, brightness, contrast and black; check audio
    with volumedetect; run faster-whisper against the script (≥ 0.9 word accuracy, plus punctuation leaks)
    (`tools/video/video_compose.py:2178-2290, 2405-2489`; `skills/creative/video-understand-usage.md:39-41`).
