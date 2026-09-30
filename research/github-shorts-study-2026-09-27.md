# GitHub deep study: how the best free Shorts pipelines work (2026-09-27)

The Sep 25 sweep (`github-sweep-2026-09-25.json`) listed the top search hits per category and checked their
licenses; it never read how any of them builds a Short. This study did, aimed at our main failure: 14 of our 15
rejected Shorts failed on visuals (mean visual score 2.9, against 4.6 for accepted ones).

## Method

- 105 GitHub searches (74 English and Chinese keyword searches, 21 topics, and 10 searches limited to repos
  created in 2026) found 6,460 repos. Filtering for relevance and activity left 423 with 150+ stars, plus 94
  with 40 to 149 stars pushed since December 2025.
- 93 repos were cloned and read (code, prompts, templates, knowledge files), in eight focused studies:
  faceless-Shorts factories, OpenMontage, the big frameworks, motion-graphics engines, explainer styles, photo
  motion and restoration models, picture sourcing (with live API tests on 7 of our topics), and craft, growth
  and quality checks.
- Licenses were read from each LICENSE file or model card, and stars, pushes and archived status re-checked on
  GitHub today (table at the end). Star farming was checked through watchers against stars and commit history.
- The detailed notes, with file paths and line numbers in each repo, are in
  `research/github-deep-2026-09-27/` (`g1` to `g5`, the brief each study got, and the sourcing test scripts in
  `g4b-scripts/`); this page is the summary and the plan.

## What we learned

1. **We're ahead where most repos are weakest, and behind exactly where our Shorts fail.** Most repos never
   check licenses, never look at the rendered video, and depend on paid generators. Our claims tables, license
   filter, vision picker, reviewer, and cloud operations are ahead of nearly all of them. We're behind on three
   things: how pictures are found (keyword search), how shots are designed (one still per beat, held 5 to 7
   seconds, cover-cropped, slow zoom), and the finish (no grade, no on-screen text besides captions).
2. **Pictures fail at the search, not at the picker.** In a live test on 38 beats from 5 of our episodes, our keyword
   route found 137 usable files and left 9 beats with none. An entity route found 948 and left 3; it goes from
   the beat's Wikipedia article to its Wikidata item, then to that item's image, its Commons category, and
   files tagged as depicting it. On the 23 beats judged by eye, beats with no acceptable candidate fell from 13
   to 2. Keyword search also returns homonyms: a line about the Lewis gun got Lewis Powell, one of Lincoln's
   assassination conspirators, and "Koepcke" got a 2023 US official (`g4b-sourcing.md` section 2).
3. **Pacing: a new picture every 2 to 3 seconds.** OpenMontage's Shorts guide and four other repos
   (content-skills, claude-youtube, claude-video-kit, super-video-maker-skill) agree on this, and
   claude-video-kit also requires a change within the first 2 seconds. We hold one still for 5 to 7 seconds.
4. **Our look is a monetization risk, not just a retention one.** YouTube's channel monetization policy
   (checked today) says "channels where content feels interchangeable from video to video are not allowed to
   monetize". Its examples include "Image slideshows, templated storylines, or scrolling text with minimal or
   no narrative, commentary, or educational value". Our narration and sources give us narrative and
   educational value, but 100 days of the same slideshow look is the pattern reviewers are told to find.
   Visual variety is a requirement for the goal.
5. **In 2026 the field moved to code-rendered designed shots, picked from recipe libraries by an agent.**
   Examples: HyperFrames (HeyGen, Apache-2.0, 53.6k stars, created March 2026), Remotion (free for
   individuals), OpenMontage (AGPL, 61.5k stars), reelforge and OpenReels. What's worth taking is their visual
   grammar: archive cards, detail punch-ins, maps, datelines, document highlights, counters, stamps, all timed
   to words. Not their workflows: OpenMontage, for one, stops for a human approval after every stage.
6. **Image-to-video isn't worth it yet.** The only open model with clean terms, Wan 2.2 I2V with Apache-2.0
   4-step distills, would cost an estimated $0.06 to $0.13 per clip on a GPU. It invents motion in historical
   photos and needs YouTube's synthetic-media label, which Buffer may not be able to set. Camera-only 2.5D
   (parallax) invents nothing and runs on CPU.

## Where we stand, stage by stage

| Stage | Days of Odd today | Best seen | Where |
|---|---|---|---|
| Topic choice | LLM backlog, no picture check | Count usable pictures before accepting a topic; rank by Wikipedia pageviews | `g5` section 3; super-video-maker-skill; Pixelle |
| Script to pictures | Script first, pictures searched afterwards | Caption a picture inventory first, then write each line to a picture or a card ("could the viewer point at what I just named?") | Pixelle `asset_based.py`; super-video-maker-skill `VIDEO_COPY_PLAYBOOK.md` |
| Search | 3 to 4 keyword queries per beat on Commons; the Met and Art Institute of Chicago as fallbacks | Entity route (Wikipedia, Wikidata, category, "depicts"), period categories ("Philadelphia in the 1810s"), then Wellcome and Openverse | `g4b` sections 2 and 5 |
| Ranking | Gemini sees the first 5 search results per beat as 330 px thumbnails | SigLIP pre-rank on CPU (37 ms an image), Gemini sees the best 6 to 8; a strict check of each chosen picture at a readable size | OpenMontage `lib/corpus.py`; OpenReels `stock-verifier.ts` |
| No picture | Another beat's picture again, or a plain gradient | A designed shot built from facts: date, map, document, quote, number, timeline | reelforge, OpenReels, Pixelle, HyperFrames registry |
| Shots per beat | 1, for 5 to 7 s | 2 to 3, cut between words, 2 to 4 s each; a detail crop is the cheapest second shot | clipfactory `scene_planner.py`; vox-director; ViMax |
| Framing | Cover crop (a 4:3 photo keeps 42% of its width) | The whole picture as a card over a blurred copy of itself; small real photos allowed in the card | simon-skills; b-roll-finder; `g4a` section 3.3 |
| Motion | `zoompan` (integer steps, judder), linear | Eased sub-pixel camera; 2.5D push on a few wide scenes | `g4a` sections 3.1, 3.7 |
| Look | None | One grade for every source, light grain, vignette | lemo-opuscar `film.js`; OpenMontage `color_grade.py` |
| On-screen text | Captions only | Hook text on frame 0; at most 3 year or place chips | reels-af `accent.py`; content-skills |
| Sound | SFX; no music | SFX audibility check; optional CC0 bed ducked on word times | claude-faceless-shorts-creator `suggest-sfx`; youtube-shorts-pipeline `music.py` |
| Review | One frame per beat; scores 1 to 5 | Frames from every shot or the MP4 itself; cheap pixel checks first; decide on verified defects; keep the best round | reelforge gates; SeeCut; OpenReels orchestrator |
| Learning | Retention at the 10% point only (`auto.py:810`) | The whole curve mapped onto beats, and the non-subscriber curve | darkzOGx `scene-retention-engine.js` |

## The plan, ranked

### Phase 1: right pictures, designed stills (Python and FFmpeg only, about $0.01 more per Short)

1. **Entity-first sourcing** (`pick.py`, `writer.py`, `visuals.py`).
   - The writer names 1 to 3 exact Wikipedia titles per beat, a year or era, and whether the subject is
     timeless.
   - Per episode, batch-resolve them to Wikidata items, images and Commons categories, and probe period
     categories.
   - Per beat, search the entity's category, "depicts" (`haswbstatement:P180=Q…`), and the period category,
     keeping today's keyword queries as a complement.
   - Deduplicate across the Short by title and perceptual hash. Reject candidates linked to the line only by a
     shared name.
   - Store the chosen file title and a full license record, and render by title (this retires `pin()` and its
     losses). Exact API calls are in `g4b-sourcing.md` section 5.
2. **Screen topics and write to the pictures** (`auto.py`, `writer.py`). Before a topic is accepted, count its
   usable pictures. A picture-poor topic is kept only if designed shots can carry it. Caption 25 to 40
   candidates in one batched vision call, and give the writer that inventory, so every line names something
   we can show.
3. **Pre-rank, then verify strictly** (`pick.py`).
   - SigLIP ViT-B/16 (Apache-2.0 weights through open_clip, MIT) scores 30 to 60 candidates per beat on CPU,
     and Gemini picks from the best 6 to 8.
   - Then one batched Gemini call checks each chosen picture at 960 px (OpenReels uses about 800; 960 is the
     nearest standard Commons thumbnail width, see `tools-radar.md`) for identity, period, and "does it show
     what the line names". The rule is OpenReels': "a different person with the same name does NOT match".
   - A failure moves to the next alternate, then to another archive, then to a designed shot, never to a
     neighbour's picture.
   - Gemini's daily request quota is our binding limit, so every new vision check must ride in one request per
     Short.
4. **Two shots per beat** (`pick.py`, `render.py`, `spec.py`). The picker returns a detail box for the thing
   the line names and the word that reveals it. The renderer cuts or pushes into the box on that word, and
   splits long beats at the clause nearest the middle. Shots run 2 to 4 seconds, and the hook shot 2 seconds
   or less. A crop must keep at least about 600 px of real width.
5. **Archive card as the default framing** (`render.py`). The whole picture sits as a slightly tilted card
   (torn edge, outline, shadow, small source chip) over a blurred, darkened copy of itself. This stops cropping
   the subject out of wide pictures, makes old images look designed, and lets real 450 to 1,199 px photos in:
   the actual 1932 Emu War photos are all smaller than our 1,200 px minimum.
6. **Smooth camera and one look** (`render.py`). Replace `zoompan` with an eased sub-pixel camera, which in the
   motion study's test cut judder from 0.43 to 0.01 px a frame for about 1.4 s more render time per clip. Use
   one grade and vignette for every source and light grain in the final encode; heavy grain made files 4.7
   times larger, which would break Buffer's 40 MB limit.
7. **Hook text and chips** (`captions.py`). Show 3 to 7 words that sharpen the spoken hook on frame 0 for about
   3 seconds, plus at most 3 year or place chips per Short in the upper third. Narrow the captions to 74% of
   the width, because today's widest reach x = 972, under the Shorts buttons.
8. **Keep the best round** (`studio.py`). Today each fix round overwrites the last, and the Short is rejected
   if the final round fails (lines 326 to 332), even when an earlier round would have passed the final rule.
   Save every round's script, pictures and render, and publish the best one that passes. After a rewrite,
   keep the pictures of beats whose text didn't change.
9. **Cheap checks before Gemini, and a reviewer that sees every shot** (`check.py`, `studio.py`). Pixel checks
   catch blank, black, frozen, low-contrast or repeated frames. Audio checks catch silence inside speech,
   clipping, and SFX that don't lift the mix by 4 dB at their cue. The reviewer gets one frame from every shot
   plus a random frame per beat, or the 540p MP4 at 2 fps. It must name the defect and the fix.

### Phase 2: designed shots for beats with no true picture

10. **HyperFrames as the engine for designed shots**, as a separate, pinned Modal image (reasons below). A card
    never replaces a real picture of the named thing when one exists (b-roll-finder's rule). Our own templates
    take typed variables that the LLM fills per beat. Each beat renders as its own clip, and a
    failed render falls back to the archive card. The first templates:
    - dateline
    - locator or route map (Natural Earth, which is public domain; coordinates from Wikidata)
    - newspaper or document highlight
    - quote card
    - counter
    - timeline
    - verdict stamp ("HOAX", "ACQUITTED")

    Every fact on a card must come from the claims table. Start with a spike that renders 3 templates on Modal
    and measures time and cost against the estimate of $0.003 to $0.02 per Short.
11. **Illustrations in one fixed engraving style** for moments that were never photographed. Use FLUX.1-schnell
    on Workers AI (already in `visuals.py`), label it "ILLUSTRATION" on screen, use at most 2 per Short, and
    never show a realistic face of a real person.
12. **2.5D on wide scenes, at most 2 per Short.** For a clear subject, a two-plane push-in cut out with
    BiRefNet_lite (MIT, ONNX). For deep scenes, a depth push with Depth Anything V2 Small (Apache-2.0; the
    Base and Large weights are non-commercial).
13. **Variety and transition rules in code.** Each Short has at least 4 shot kinds, never 3 same-kind shots in
    a row, and neighbouring shots use different camera moves. Hard cuts are the default, with a slide or page
    turn for time passing and one impact at the twist.

### Phase 3: close the loops (once there are enough views)

14. **Per-beat retention.** Map the full retention curve (and the non-subscriber curve) onto each Short's beat
    times, recording each beat's shot kind. Flag drops of 8 points or more, judge only Shorts with 20+ views and
    at least 72 hours online, and feed the results into `strategy/LEARNINGS.md`.
15. **Script rules we lack:**
    - a re-hook at 5 to 8 seconds
    - "but" and "therefore" links between beats
    - the payoff by about 80% of the runtime
    - a hook word echoed in the payoff (it strengthens the loop)
    - no two beats opening with the same word
    - hooks chosen by pairwise comparison
16. **Music as an experiment**, CC0 or public domain only, with a license log, ducked on Kokoro's word times.
    FreePD is closed. The tracks bundled with MoneyPrinterTurbo and short-video-maker came from YouTube, and
    Pixelle's default track has no stated license, so none of them can be reused.
17. **Calibrate the reviewer.** Gate on verified defects, compare fix rounds pairwise in both orders, and keep
    a small copy of each rejected Short as a test case; `reject()` deletes them today.

Costs: Phase 1 adds well under a cent per Short (SigLIP on CPU, a little more encode time). Phase 2 adds an
estimated $0.003 to $0.02 per Short for HyperFrames and $0.005 to $0.03 for depth. That's against about $0.12
per Short today, within Modal's $30 credit. None of it needs a paid API.

## Why HyperFrames for designed shots

- **Headless and deterministic.** It renders frame by frame in headless Chrome, with software graphics (no
  GPU) and a clock that seeks to each frame. It ships an official Dockerfile. Its own Linux benchmark rendered
  1080x1920 at about 67 ms a frame.
- **Plain HTML templates** with declared variables (`--variables-file`, `--strict-variables`), so Python fills
  them without a React build. The registry has the pieces we need: route and world maps on real geography
  (d3-geo), marker highlights, typewriter, count-up, stamps, and grain.
- **License.** Apache-2.0; GSAP, which it uses, is free. Remotion is free for us today but needs a company
  license once 4 or more people work on the channel (contractors count in 5.0), and needs React.
- **Why not all Python.** Pillow, NumPy and FFmpeg could do about 70 to 80% of these shots, which is why
  Phase 1 uses them. Maps, drawn callouts and typography would each become custom pixel code, and look worse.
- **Risks.**
  - It has had 240 releases in 6.5 months, so pin exact versions (`hyperframes@0.8.80`,
    `chrome-headless-shell@148.0.7778.167`).
  - Registry items load scripts and map data from a CDN while rendering, so bundle them and block the network.
  - The image is about 3 GB.
  - Set `HYPERFRAMES_NO_TELEMETRY=1`.

## License traps (never use)

| What | Why |
|---|---|
| Depth Anything V2 Base/Large, DA3 Large/Giant, Apple Depth Pro weights | Non-commercial or research-only |
| sniklaus/3d-ken-burns | CC BY-NC-SA |
| CodeFormer; GFPGAN's NVIDIA and DFDNet parts | Non-commercial (and they repaint faces) |
| rembg's default model (RMBG-2.0) | Non-commercial; use BiRefNet_lite instead |
| FramePack, HunyuanVideo | Tencent license excludes the EU, UK, and South Korea |
| MiniMax-H3 (and its "Apache" Turbo distill) | Needs an application for US use |
| LTX-2 | Free under $10M revenue, but every output must be labelled machine-generated |
| video-talkcraft, anything2explainer, SeeCut, YumCut | PolyForm Noncommercial |
| clipfactory | Elastic License 2.0 (source-available) |
| OpenAI's CLIP weights | Model card rules out deployed use; use SigLIP |
| Colorization (DDColor, DeOldify) | Allowed, but it invents colors of real uniforms and faces; not for a history channel |
| Anything built on yt-dlp or YouTube scraping (last30days, hypit, clipfactory's trends feature, Dark2C, b-roll-finder's YouTube route) | Our hard rules |

## Repos worth knowing (verified 2026-09-27)

Stars, last push and license are from GitHub and the LICENSE file today. Verdicts: adopt means use the tool or
port permissive code; borrow means reimplement the idea.

| Repo | Stars | Last push | License | What we take | Verdict |
|---|---:|---|---|---|---|
| heygen-com/hyperframes | 53,571 | 2026-09-27 | Apache-2.0 | Engine for designed shots | Adopt (Phase 2) |
| calesthio/OpenMontage | 61,516 | 2026-09-06 | AGPL-3.0 | Picture briefs, CLIP pre-rank, variety checks, Shorts rules | Borrow |
| tsensei/OpenReels | 199 | 2026-04-10 | MIT | Strict picture verifier, keep best round, no 3 same shots in a row | Borrow |
| gongnyang/reelforge | 82 | 2026-07-30 | Apache-2.0 | Frame checks, pacing budgets, quote and statistic blocks | Borrow |
| hassancs91/claude-faceless-shorts-creator | 269 | 2026-08-18 | MIT | Archive collage kit, SFX audibility check | Borrow |
| Agent-Field/reels-af | 115 | 2026-06-05 | Apache-2.0 | Overlays off by default, pairwise hook choice | Borrow |
| feyzilim/clipfactory | 105 | 2026-08-23 | Elastic-2.0 | Splitting beats into shots, freshness penalty | Borrow (idea only) |
| ATH-MaaS/Pixelle-Video | 28,452 | 2026-06-14 | Apache-2.0 | Asset-first writing, HTML frame templates | Borrow |
| HKUDS/ViMax | 12,509 | 2026-09-20 | MIT | First-frame/last-frame shot decomposition | Borrow |
| darkzOGx/youtube-automation-agent | 3,871 | 2026-09-25 | MIT | Retention curve mapped onto scenes, with drop-off thresholds | Borrow |
| rushindrasinha/youtube-shorts-pipeline | 2,302 | 2026-06-09 | MIT | Music ducking on word times, hook templates | Borrow |
| harry0703/MoneyPrinterTurbo | 126,270 | 2026-09-27 | MIT | Spring caption pop; little else for us | Borrow (small) |
| Alisa0808/vox-director | 2,057 | 2026-08-11 | MIT | Two shots per beat, style library, Pillow motion engine | Borrow |
| trustfuture/simon-skills | 203 | 2026-09-24 | MIT | Archive card recipe | Adopt (port) |
| lemomo-ai/lemo-opuscar | 324 | 2026-09-27 | MIT code, CC BY 4.0 docs | Print pass and redraw shaders | Adopt (port) |
| showlab/Code2Video | 2,076 | 2026-08-24 | MIT | Grid-referenced visual review | Borrow |
| cyberlesterr/paper-collage-video | 235 | 2026-09-13 | MIT code | Motion directing rules (its textures are all rights reserved) | Borrow |
| iart-ai/motion-skills | 516 | 2026-09-23 | MIT | Map and kinetic-type recipes, safe zones | Borrow |
| heygen-com/hyperframes-community-skills | 153 | 2026-09-24 | Apache-2.0 | `vox-explainer` skill and its gates | Borrow |
| nateherkai/hyperframes-student-kit | 1,046 | 2026-09-25 | MIT | Vox collage style spec | Borrow |
| Vincentwei1021/video-shotcraft | 9,690 | 2026-09-27 | Apache-2.0 | Shot-card format (48 of its cards were reverse-engineered from promos not licensed for reproduction) | Borrow (format only) |
| mlfoundations/open_clip | 14,170 | 2026-09-25 | MIT | SigLIP pre-rank | Adopt |
| xinntao/Real-ESRGAN | 36,918 | 2024-08-06 | BSD-3-Clause | `realesr-general-x4v3`, only past 1.3x magnification, never on faces or text. Idle since 2024, so vendor its 69-line network and weights rather than depend on the package | Adopt (vendor) |
| BrokenSource/DepthFlow | 1,547 | 2026-08-25 | AGPL-3.0 | Only as a separate tool, if a Modal GPU exposes OpenGL | Watch |
| Wan-Video/Wan2.2 (+ ModelTC/LightX2V) | 17,650 | 2026-09-21 | Apache-2.0 | Masked sky or water motion on paintings, disclosed | Watch |
| louisedesadeleer/b-roll-finder | 119 | 2026-06-11 | MIT | Blurred fill, sub-pixel zoom | Borrow |
| joeseesun/qiaomu-cut-skill | 338 | 2026-07-19 | MIT | License record per asset | Borrow |
| runesleo/claude-video-kit | 120 | 2026-09-27 | MIT | Pacing gate (average shot of 3 s or less) | Borrow |
| kurbaitaev/ghost-editor | 61 | 2026-09-24 | MIT | Audio and safe-zone checks | Borrow |
| vyralcontent/content-skills | 119 | 2026-06-22 | MIT | Three-layer hook, hook text | Borrow |
| WordPress/openverse | 379 | 2026-09-25 | MIT | Secondary image source (`license=cc0,pdm,by`) | Adopt (API) |
| remotion-dev/remotion | 60,734 | 2026-09-27 | Remotion License | Free for individuals; not our engine | Watch |
| gyoridavid/short-video-maker | 1,379 | 2025-06-21 | MIT | Falls back to random stock clips | Skip |
| RayVentura/ShortGPT | 7,982 | 2025-02-10 | MIT | Scrapes Bing Images | Skip |
| hypit-ai/hypit | 16,628 | 2026-09-26 | Modified Apache | Built on yt-dlp and cloning viral videos | Skip |
| mvanhorn/last30days-skill | 63,008 | 2026-09-23 | MIT | Built on yt-dlp and browser cookies | Skip |
| eat-pray-ai/yutu | 693 | 2026-09-25 | Apache-2.0 | Data API only, no analytics | Skip |
| IgorShadurin/app.yumcut.com | 885 | 2026-09-03 | PolyForm Noncommercial | Rendering code not public | Skip |
