# G3a: Engines for code-rendered "designed shots"

Scope: title and date cards, route maps, document and newspaper highlights, quote cards, kinetic type,
photo-on-paper frames and diagrams for beats with a weak or missing archive picture, plus richer motion on
archive photos. Everything must render unattended from a JSON scene spec on headless Linux (Modal CPU, or a
GitHub Actions ubuntu runner).

Method: `gh repo view` plus each LICENSE file, checked on 2026-09-27. Repos were shallow-cloned to
`/tmp/ghdeep/g3a/` and the code, cards and templates were read. For Remotion, only `LICENSE.md`, the license
FAQ and PR #3750 were read, through `gh api`. Nothing was installed or rendered, so every speed figure below
comes from the repos' own benchmarks and docs.

## Recommendation (short version)

**Use HyperFrames (Apache-2.0) as the one engine for designed shots.** Render each beat as its own
1080x1920 clip from about 8 vetted HTML templates that our Python fills from a small per-beat JSON spec. The
LLM chooses a recipe and fills its slots; it never writes HTML. Keep FFmpeg exactly where it is today:
concatenation, the ASS captions, SFX, loudnorm, and a per-beat fallback to the current zoompan clip.

Why HyperFrames:
- **No licence risk.** It is Apache-2.0 with no team-size cliff. Remotion's free licence stops at 3 people,
  and after that the cheapest automated plan has a $100/month minimum.
- **Frame-exact rendering on Linux.** It captures deterministically with Chrome's `beginFrame` and ships
  official Linux Dockerfiles.
- **Templates are plain HTML.** Python fills them with Jinja; there is no React build step.
- **Built-in checks and a large component library.** It has `lint`, `check` and `snapshot`, and 223 components
  that stretch to fit 9:16.
- **A ready-made visual grammar for history explainers.** The community `vox-explainer` skill supplies it.

Estimated cost is about $0.006–0.018 per Short to push the whole 45 s video through HyperFrames on an 8-core
Modal container, or about $0.003–0.008 if only the designed beats go through it. That is roughly $0.4–1.2 a
month at 60 Shorts.

## Verification (GitHub, 2026-09-27; licence read from the file)

| Repo | Stars | Forks | Created | Last push | Licence (from file) | Archived |
|---|---|---|---|---|---|---|
| heygen-com/hyperframes | 53,552 | 4,883 | 2026-03-10 | 2026-09-27 | Apache-2.0 ("Copyright 2026 HeyGen, Inc.") | no |
| heygen-com/hyperframes-community-skills | 153 | 11 | 2026-08-25 | 2026-09-24 | Apache-2.0 | no |
| nateherkai/hyperframes-student-kit | 1,045 | 327 | 2026-04-18 | 2026-09-25 | MIT ("Copyright (c) 2026 Nate Herk") plus a note excluding the AIS brand assets; GitHub shows "Other" | no |
| Vincentwei1021/video-shotcraft | 9,688 | 875 | 2026-07-19 | 2026-09-27 | Apache-2.0 | no |
| Vincentwei1021/video-talkcraft | 1,257 | 117 | 2026-08-22 | 2026-09-22 | PolyForm Noncommercial 1.0.0 | no |
| Vincentwei1021/anything2explainer | 2,108 | 296 | 2026-09-08 | 2026-09-18 | PolyForm Noncommercial 1.0.0 | no |
| nexu-io/html-video | 4,622 | 565 | 2026-05-27 | 2026-06-21 | Apache-2.0 | no |
| remotion-dev/remotion | 60,733 | 4,693 | 2020-06-23 | 2026-09-27 | Remotion License (source-available: Free or Company licence) | no |
| remotion-dev/template-tiktok | 282 | 69 | 2024-02-17 | 2026-09-05 | No LICENSE file; package.json says `"UNLICENSED"` | no |
| Remocn/remocn | 1,524 | 77 | 2026-04-07 | 2026-09-26 | MIT | no |

Runtime dependency worth knowing: **GSAP 3.15** (used by HyperFrames compositions and the Vox cards) is under
GreenSock's "Standard No-Charge" licence, now owned by Webflow (gsap.com/standard-license):
- It may be used free on "any website, web application, or digital interface", including commercially.
- The only prohibited use is inside no-code visual animation builders that compete with Webflow, plus
  removing its notices.
- Rendering our own videos is allowed. It is not an OSI licence, but it can be avoided, because HyperFrames
  also drives plain CSS animations, WAAPI and Anime.js (MIT).

---

## 1. heygen-com/hyperframes (the engine)

**What it is.** An HTML-first video framework. A composition is an HTML file:
- The root element carries `data-composition-id`, `data-width`, `data-height` and `data-duration`.
- Timed elements are `class="clip"` with `data-start`, `data-duration` and `data-track-index`.
- Animation is a paused GSAP timeline registered at `window.__timelines[id]`; CSS, WAAPI, Lottie and Three
  adapters also exist.

`npx hyperframes render` produces MP4, WebM or MOV (both with alpha), a PNG sequence, GIF or HLS. The
monorepo holds `core` (contract and lint), `engine` (browser and capture), `producer` (orchestration and
FFmpeg), `cli`, `player` and `studio`. It also has a registry of 165 blocks, 224 components and 8 examples.

### How rendering works

1. **Launch.** Puppeteer starts **chrome-headless-shell**: `packages/engine/src/services/browserManager.ts:141-145`
   lists the binary names, and line 180 resolves it "for deterministic BeginFrame rendering".
2. **Clock.** For frame *i*, the time is `floor(i)/fps`, never a wall clock. Every timeline and media element
   is seeked to that time.
3. **Capture on Linux.** It uses `HeadlessExperimental.beginFrame` with `--deterministic-mode
   --enable-begin-frame-control --run-all-compositor-stages-before-draw` (lines 222-229).
   - The launch probes that this works (lines 242-424) and otherwise falls back to screenshot capture
     (lines 696-743).
   - Graphics are software-rendered with SwiftShader: `--use-gl=angle --use-angle=swiftshader
     --enable-unsafe-swiftshader` (lines 1025-1038), with more SwiftShader workarounds at lines 924-965.
   - Chrome runs with `--no-sandbox --disable-dev-shm-usage` (lines 474-476).
4. **Encode.** On the Linux beginFrame path, frames stream straight into FFmpeg (libx264), and FFmpeg also
   mixes the audio. Other paths spill raw RGBA to disk, about 25 GB per minute at 1080p30 (render section of
   `docs/packages/cli.mdx`).
5. **Parallelism.** `--workers 1-24`, each a separate Chrome of about 256 MB (`packages/engine/src/config.ts:283`
   sets concurrency "auto"; the env var `PRODUCER_MAX_WORKERS` is at line 832). For fleets there are
   `plan()`, `renderChunk()` and `assemble()` primitives (`examples/k8s-jobs/README.md`).

### Runs headless on Linux in a container: yes

- **Official Dockerfile:** `packages/gcp-cloud-run/Dockerfile`.
  - Base image `node:22-bookworm-slim`, plus apt packages for FFmpeg, the Chromium shared libraries
    (libnss3, libgbm1, …) and Noto and Liberation fonts.
  - It installs `npx @puppeteer/browsers install chrome-headless-shell@148.0.7778.167 --path /opt/puppeteer`.
  - It sets `HYPERFRAMES_CHROME_PATH`, `PRODUCER_HEADLESS_SHELL_PATH`, `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true`
    and `CONTAINER=true`, and runs a beginFrame probe at build time.
- **Image size:** about 1.2 GB compressed and 3 GB unpacked; no published image (`examples/k8s-jobs/README.md`).
- **GPU:** `--browser-gpu` is off in Docker, so SwiftShader is used and no GPU is needed.
- **Memory:** `--low-memory-mode` switches on automatically at 8 GB RAM or less, but it reads the host's RAM,
  not the container limit. Set `PRODUCER_LOW_MEMORY_MODE` explicitly on Modal.
- **Health check:** `npx hyperframes doctor --json` (gate on `.ok`) checks Chrome, FFmpeg, `/dev/shm` and fonts.
- **Telemetry:** turn it off in the pipeline with `HYPERFRAMES_NO_TELEMETRY=1` or `DO_NOT_TRACK=1`
  (`docs/packages/cli.mdx:1225-1233`).

### Dependencies

- **System:** Node 22 or newer, FFmpeg, and chrome-headless-shell (Chrome for Testing, downloaded when the
  image is built).
- **npm:**
  - engine: `puppeteer ^25.8`, `puppeteer-core`, `hono`, `linkedom`
  - producer: fontsource fonts, `wawoff2`
  - cli: `@puppeteer/browsers`, `sharp`, `esbuild`, `fontkit`
  - `@hyperframes/producer@0.8.80` unpacks to 74 MB.
- **Scripts:** registry items load GSAP, d3 and topojson from jsdelivr at render time. We must bundle them
  locally.

### Render speed (from the repo's own measurements)

| Source | Setup | Result |
|---|---|---|
| `packages/producer/tests/perf/benchmark-results.json` (2026-03-11) | Linux x64, Node 22.17, **1080x1920**, 24 fps, 72 frames, 2 workers, quality high | 5.62 s total: capture 4.83 s (**67 ms per frame**, wall), encode 0.53 s |
| `packages/producer/tests/perf/README.md` | M-series Mac, 1 worker | 150 frames in 11.5 s; 600 frames in 34.5 s (capture 27.0 s, 45 ms per frame) |
| `docs/guides/performance.mdx` | 1920x1080, 300 frames, median of 3 runs | 25.0 s, dropping to **9.8 s** after removing one expensive CSS declaration (filters and blur cost the most) |
| `docs/deploy/aws-lambda.mdx:165-177` | 480 frames split over 5 Lambdas | $0.0214 |

**Estimate for our Short.** A 45 s video at 1080x1920 and 30 fps is 1,350 frames. On an 8-core, 8 GiB Modal
container with `--workers 4`, it should take about **45–150 s** (most likely around 90 s), plus 10–30 s cold
start while the ~3 GB image loads. Rendering only the designed beats (about 450–600 frames) should take about
20–60 s. `--experimental-fast-capture` claims roughly 2x more speed; `--quality draft` is for previews.

### Determinism

- The mechanism is the frame clock, seek, beginFrame capture, and pinned Chrome, fonts and FFmpeg
  (`docs/concepts/determinism.mdx`).
- The authoring rules (local skill `hyperframes-core/references/determinism-rules.md`): no `Date.now`, no
  unseeded `Math.random`, no network fetches at render time, and no infinite repeats.
- **The registry breaks its own rule:**
  - `registry/blocks/world-map/world-map.html:13-15` loads gsap, d3@7 and topojson-client from jsdelivr.
  - Line 281 fetches `world-atlas@2/countries-110m.json` from the CDN during the render.
  - Bundle every script and data file into the image.

### Techniques worth stealing

1. **Typed variables so the LLM never touches HTML.**
   - Slots are declared with `data-composition-variables` (types: string, number, color, boolean, enum) and
     bound with `data-var-text` / `data-var-src` or read as CSS `--{id}`.
   - Values come from `render --variables-file vars.json` or `--batch rows.json`, and `--strict-variables`
     turns unknown or missing variables into errors (`docs/packages/cli.mdx:874-877, 1026-1033`; local skill
     `hyperframes-core/references/variables-and-media.md`).
   - A sub-composition takes per-instance values:
     `<div class="clip" data-composition-src="./marker-highlight.html" data-variable-values='{"text":"…","emphasis_word":"Zero","style":"circle"}' data-start="0" data-duration="3.5">`.
2. **Components that stretch to fit, with cue times** (`registry/components/CATALOG.md`).
   - Each unit lists what it is, `use_when`, `avoid_when`, `pairs_with` and its variables.
   - A `cues` variable takes comma-separated seconds that lock reveals to the narration; extra duration
     simply becomes a hold.
   - Relevant for us: `marker-highlight` (style highlight, circle, underline or scribble; `draw_at`;
     `emphasis_word`), `per-word-rise`, `titlecard-lockup`, `typewriter`, `headline-slam`, `count-up`,
     `number-wheel`, `strikethrough-replace`, `svg-stroke-trace`, `hw-callout-circle`, `hw-underline`,
     `vox-annotate`, `ink-bleed-reveal`, `halftone-dissolve`, `before-after-wipe`, `iris-reveal`,
     `parallax-zoom`, `push-in`, `pull-back-reveal`, `grain-overlay`, `vignette`, `stop-motion-cadence`.
3. **Route maps.**
   - The route is an SVG path revealed by animating its stroke dash, and a plane icon rides the same path
     through CSS `offset-path` (`registry/blocks/nyc-paris-flight/nyc-paris-flight.html:80-101, 189`).
   - Real geography: `d3.geoNaturalEarth1()` with TopoJSON (`world-map.html:269`), or `d3.geoAlbersUsa()`
     (`us-map-flow.html:209`) with routes drawn as upward-bending quadratic arcs (`us-map-flow.html:226`).
4. **Built-in QA.** `lint`, `check` (layout and contrast), `snapshot --at t1,t2` (frames for our Gemini
   contact sheet) and `benchmark` (`docs/packages/cli.mdx:1056-1063`).
5. **Transparent output.** `--format mov` or `webm` gives a designed layer (callouts, labels, a highlight)
   that FFmpeg can overlay on an archive plate.

### Compared with our pipeline

**Better:**
- Real typography, SVG draw-on effects, masks and blend modes, geographic maps.
- Animation events timed to individual words.
- Byte-stable renders, and hundreds of reference components.

**Worse:**
- Adds a ~3 GB image and Node/Chrome moving parts.
- About 10x slower per frame than zoompan (still cheap).
- Very young: 240 releases in 6.5 months, now v0.8.80, which means API churn.
- Fixed-size blocks are mostly 16:9: 158 are 1920x1080, and only 13 are 1080x1920 (mostly social-media UI).
  The 223 stretchable components work at 1080x1920.

### How to adopt it

**As a tool, not copied code.**
- Pin `hyperframes@0.8.80` and `chrome-headless-shell@148.0.7778.167`.
- Bundle GSAP, fonts, d3 and a Natural Earth TopoJSON file (public domain) into the image.
- Keep our own templates in our repo; never pull from the registry at render time.

**Effort:** M for the Modal image, the render wrapper and 4 templates; L for about 10 templates plus the gates.
**Cost:** about $0.003–0.018 per Short (details in section 6).

**Risks and mitigations:**
- **Version churn:** pin exact versions.
- **Chrome crashes or timeouts:** time out each beat and fall back to the zoompan clip.
- **Hidden network fetches:** block the network while rendering.

**Verdict: ADOPT (as a tool).** It is an Apache-2.0, deterministic, headless-Linux renderer for HTML
templates that we fill from JSON, and the cheapest route to good designed shots.

---

## 1b. heygen-com/hyperframes-community-skills (the `vox-explainer` skill)

**What it is.** Eight independent skills. `vox-explainer` is the one relevant to us: it builds 60–90 s
"Vox-style history of X" collage explainers. The others (3D captions, p5 paint, posting-licence cards and so
on) are off-genre.

`p5-paint-animation` repaints a photo as brushstrokes, deterministically (p5 is LGPL-2.1, p5.brush is MIT). It
costs 5–20 s per frame, so at most it could make one painted still, which FFmpeg would then animate.

**Pipeline** (`skills/vox-explainer/SKILL.md`):
1. A topic or source router.
2. The script: a beat spine with fixed weights.
3. A design pass: a contact sheet from real assets, one tile per beat, **before** any animation is built.
4. Voiceover, with word timestamps as the clock.
5. The build: one clip group per beat.
6. Numeric QC gates.

### Techniques worth stealing

1. **A minimum mix of techniques, so a film can't be a slideshow** (`SKILL.md:156-205`). Every beat declares
   a layout recipe **and** a motion treatment in the plan. Each film needs at least:
   - one "zoom-isolation swap" (push into a photo, isolate the subject, cut through it);
   - one inverse zoom-through arrival on a payoff beat;
   - two drive-pasts;
   - one subject lifted off its background;
   - one newsprint-layering moment.
   Caps: "static-card / side-by-side layouts ≤ one third of beats; no two consecutive beats share the same
   layout recipe or the same treatment" (line 174).
2. **The zoom-in rule** (lines 180-205). "Pushing into a photograph promises the viewer the payoff is INSIDE
   the image." Only two follow-ups are allowed:
   - the subject lifts off its background and becomes the moving element; or
   - the image holds near full-frame while callouts draw on it.
   A push into a photo followed by a cut to something unrelated is banned. This directly fixes our "slow zoom
   that means nothing".
3. **Layout recipes** (`references/vox-collage-layout.md`):
   - **Evidence stack:** cards of one size piled with jitter at ±1.5–3° tilt, radius about 18 px, soft
     shadow, one card per phrase of narration, credit in the left margin.
   - **Zoom-isolation pair.**
   - **Two-panel compare.**
   - **Specimen grid:** the survivor stays bright while the other cells dim to 0.45.
   - **Lower-third** with a highlight chip that sweeps on.
   - **Newsprint layering:** a pale clipping strip *under* the words plus a low-opacity copy *on top*.
   - **Circle reveal:** the circle scales in steps along 0.30, 0.72, 0.943 and 1.0 over about 0.45 s.
4. **Asset honesty** (lines 48-62):
   - "Never recreate a photograph — an invented photo reads as slop where a recreated document reads as
     typesetting." A recreated document must be flagged on screen, for example "TYPESETTING RECREATED FROM
     THE 1839 TEXT".
   - When no PD or CC photo exists, the beat goes typographic, or shows a real successor artefact labelled as
     such.
   - **Library of Congress (LOC) newspaper recipe:** search, confirm the OCR page matches the image, then scale
     the ALTO word coordinates into the IIIF `info.json` pixel space before cropping; the two spaces differ by
     about 4x. This gives real highlights on the exact words of public-domain Chronicling America pages.
5. **Hard layout rules to check on the contact sheet** (lines 65-107):
   - no orphan elements, and the content covers most of the frame;
   - labels sit within one grid gap of their subject;
   - "annotations are measured": crop the rendered frame and verify the circle sits on the feature (line 85);
   - nothing overflows its container;
   - protect the caption rail.
6. **Motion** (`references/vox-collage-motion.md`):
   - Elements move in stepped 12 fps poses over smooth eases, while the camera moves smoothly. The helper is
     ``stepEase = (base,dur,fps=12) => p => e(Math.floor(p*n)/n)`` (lines 7-17).
   - Zoom-isolation push: `power4.in` over about 1.2 s to 4.5–7x.
   - Inverse zoom-through: `expo.out` over about 1.1 s from about 3.2x.
   - **Plate pushes: linear 3–4 % over the whole beat** (line 27). Our zoompan goes to 12 %.
   - Seams: the subject's centre stays within about 30 px and its size within about 10 % across the cut.
   - Show before tell: a visual may lead the narration by 1–1.5 s, and reactions start about 100 ms before
     their cause (line 45).
   - A deliberate 0.3–0.75 s hold before a reveal is good; more than 3 s is a planning bug (line 51).
7. **Gates** (`SKILL.md:144-150`; `vox-collage-motion.md:55-78`):
   - **Dead time:** difference every consecutive pair of rendered frames at **640x360 or larger, using two
     metrics**. A pair counts as still only if the mean absolute difference is below 0.25 **and** fewer than
     150 pixels changed by more than 12 levels. At 320x180 with the mean alone, small text reveals vanish and
     the check reports dead time that isn't there.
   - **Event density**, checked on the timeline because pixel differencing can't see slow creep: "no 3.0s
     window of any beat without a discrete authored event."
8. **On-screen text** (`references/vox-text-overlays.md`):
   - Every word on screen does exactly one job: guide the eye, carry the one promoted sentence of an act, or
     name something.
   - **Highlights always animate on** (lines 8-21): a colour bar sweeps behind the text by animating
     `backgroundSize` from 0 % to 100 % in about 0.4 s, and circles draw on by animating the stroke dash in
     about 0.4 s.
   - An anchor label is at most 3 words, paired with an arrow whose **tip touches the subject** (lines 26-29).
   - Credits always go in the same slot.
   - Suppress caption cues whose words are already promoted on screen.

**Better than ours:** an explicit visual grammar for history explainers, with numeric gates we can automate.

**Worse or irrelevant:**
- Tuned for 16:9 and 60–90 s.
- It stops for human approval of the design pass.
- The look is Vox's; we must not imply any affiliation.
- Its seam scripts start a preview server.

**How to adopt:** ideas, and the text can be adapted with attribution since it is Apache-2.0. Effort is S
for the gates and rules; M for zoom-isolation, which needs a cut-out model and a detail box.

**Verdict: BORROW IDEA.** This is the best written grammar I found for "history collage" motion, and it
directly addresses our slideshow look.

---

## 1c. nateherkai/hyperframes-student-kit

**What it is.** A course kit for making HyperFrames videos with Claude Code. Its style library
(`style-library/registry.json`) has **406 HTML cards**: vox-explainer 106 and kallaway 300, in three tiers.

Each card entry is `{id, style, tier, purpose, file, slots[], duration{min,max}, preview}`. History-friendly
Vox cards include section.map, section.stamp, section.classified, section.correction, section.tornstrip,
section.indexcard, stat.calendar, stat.engraving, stat.timeline-point, stat.isotype, stat.magnifier,
overview.timeline-3up, overview.dossier, overview.map-legend, label.pull-quote, label.circle and
label.magnify.

### Techniques worth stealing

- **Design tokens** (`style-library/01-vox-explainer/DESIGN.md`):
  - Palette: paper #efe9dc, ink #17130e, blue #37BDF8, red #e23b2e, orange #f26a1b.
  - Type: Fraunces (300 and 900 italic), Archivo 700 uppercase with 0.16 em tracking, Caveat for hand notes.
  - Motion: `back.out(2.2)`, `steps(6)` stop-motion easing, stepped grain, slow push, rack focus.
  - Cut-out image slots get a halftone fill and a sticker outline.
  - Don'ts: no pure white or black, no smooth eases.
- **Engraving treatment** (`cards/tier1/t1-stat-engraving.html`): a CSS halftone with an orange multiply blend,
  a mask gradient, a line texture, a scrim and grain. It makes mismatched archive scans look like one family.
- **Plan schema** (`.claude/skills/short-form-edit/references/plan-schema.md`):
  `{duration,fps,scenes:[{id,start,end,layout,kind,anchor,anchorTime}],events:[{time,type,visual,anchor}],captions:[…]}`.
  Every scene and event is anchored to a spoken word. It also keeps a footage ledger (sha256; each scene used
  once per reel).
- **Quality gates** (`quality-gates.md:16`): "Cadence — >2.2 s gap without a deliberate story hold" fails,
  and Ken Burns stills do not count as B-roll. We run 5–7 s beats on one still, so we fail this by design.

**Better than ours:** a coherent paper-documentary style, and event-level anchoring.

**Worse or irrelevant:**
- The cards are 1920x1080 and need re-laying-out for 9:16.
- They load GSAP from a CDN.
- `docs/SHORT-FORM.md` relies on paid ElevenLabs and Kie.ai.
- The workflow expects an interactive agent.

**Licence:** MIT, plus `licenses/PIPELINE-USE-PERMISSION.txt` ("personal or commercial videos" allowed).
The AIS brand assets are excluded. Vox, Kallaway and Infinite are aesthetic references only, so no Vox
naming or logos. GSAP's own licence applies (`THIRD_PARTY_NOTICES.md`).

**How to adopt:** copy 3–5 MIT card layouts as starting points for our 9:16 templates and borrow the tokens.
Effort S–M.

**Verdict: BORROW IDEA.** The best ready-made "paper documentary" look, and it is MIT, but it needs vertical
re-layout.

---

## 1d. Local skills (`~/.cursor/skills/hyperframes*`, `media-use`)

These are symlinks to `~/.claude/skills/`.

- **`hyperframes-core`:** the composition contract, determinism rules, variables and minimal composition. Read
  in full; the facts above come from it.
- **`hyperframes-cli`:** the development loop (`init`, `lint`, `check`, `snapshot`, `render`, `doctor`).
- **`hyperframes-animation`:** 15 "blueprints" reverse-engineered from 50 product-launch clips. Useful
  shapes for us: `kinetic-type-beats`, `typewriter-reveal`, `spatial-pan-stations` (a milestone timeline
  panned by one camera), `titlecard-reveal` (a calm breather beat) and `dataviz-countup`.
- **`hyperframes-creative`:** 8 visual styles named after designers (Swiss Pulse, Velvet Standard, Shadow Cut
  and others) plus a mood-to-style guide.
- **`media-use`: SKIP for our pipeline.**
  - It needs `heygen auth login --oauth` for its free catalog, TTS and image search, which can't run
    unattended.
  - The licence of HeyGen's asset catalog for a monetized YouTube channel isn't stated.
  - Ideas to keep: a content-addressed media cache with a ledger, and sidechain ducking recipes.
- **Background removal:** HyperFrames' `remove-background` uses rembg's `u2net_human_seg` through
  onnxruntime-node (`packages/cli/src/background-removal/manager.ts:8`). It only segments people. Cut-outs of
  animals or objects (emus, spaghetti trees) need a general matting model, which is out of scope here.

---

## 2. Vincentwei1021 repos (shotcraft, talkcraft, anything2explainer)

### 2.1 How the recipe cards are structured

- **shotcraft** (`references/shots/<category>/*.md`, 157 cards):
  - Frontmatter: `name`, one-liner (一句话), use-when (适用), duration (时长), energy (能量), tags (标签).
  - Body: intent (意图); a phase table with frame ranges; **a parameter table** (typical value plus how
    changing it feels); an SFX pairing; known pitfalls; and the path of a reference implementation
    (Remotion TSX under `demos/`).
  - `gallery/api/library.json` is the machine index: `name, summary, use, duration, energy, intention,
    source, styles, category, tags`.
  - Categories: camera 10, data 13, effects 17, interaction 15, opening 11, outro 7, rhythm 11,
    transition 19, typography 26, ui-entrance 28.
- **talkcraft** (`references/cards/*.md`, 108 cards):
  - Frontmatter: input type (输入: V video, 图 image, 截图 screenshot, 文 text), semantic role (语义: hook,
    time/place, quote, data, contrast, twist, emphasis, …), props, and the code path (代码).
  - `references/taxonomy.md` indexes cards by input type.
- Demos hard-code their text; `PaperTitleCard.tsx` has a `WORDS` constant. So the cards are recipes to
  re-implement, not parameterized templates.

### 2.2 How an agent picks a recipe for a line

- **shotcraft** (`references/pipeline.md:115-160`):
  - **Stage 2** scans every card's frontmatter and picks a **primary and a backup** card for each item.
  - **Stage 3** arranges an energy curve (a low open, beats alternating with breathers, a high close) and
    budgets hold frames.
  - Film-level rules:
    - R1: a breath after every key piece of information (`aesthetic-rules.md:23`).
    - R4: at most 3 full-frame impacts per film (line 38).
    - Any single "hero" technique is used at most once per film.
    - Q11: readable text is at least 5 % of frame height for captions and 3 % for secondary text (line 103).
- **talkcraft:** first filter by **input type** (what media the line actually has), then by semantic role,
  then fill props.
- **anything2explainer:** at least one visible change per sentence. Each element appears between 6 frames
  before and 3 frames after the start of its subtitle block, and each shot settles 30–45 frames before it
  exits.

### 2.3 How word-level voiceover timing drives animation

This is talkcraft's `SKILL.md`, read for ideas only because of its licence.

- **Timestamps:** `timestamps.json` = `{sr,total,sentences:[{i,text,start,end,match,ok,words:[{text,start,end}]}]}`,
  from FireRedASR2-CTC or faster-whisper, with a median offset of 20–40 ms.
- **Character map:** `timing.json` maps every character of the text, for `atChar()`, `tSay` and `msSay`
  lookups.
- **Beats:** `beats.json` entries are `{t, anchor, sentence, what}`, where **`t` is always looked up from the
  anchor word, never typed**.
- **Rules:**
  - `beat_lint.py` enforces |Δ| ≤ 0.1 s (line 169).
  - Nothing is visible before its anchor word (line 170).
  - No empty open longer than 1.5 s before the first anchor (line 172).
  - Tail guard: an anchor within 0.7 s of the shot's out-point moves earlier or into the next shot; the hard
    floor is 0.5 s (lines 174-175).
  - SFX cues are `{t,name,vol≤0.35,rate?,clip?}`, about 12 dB under the voice, at most one per frame.
- **For us:** Kokoro already gives exact word times, so anchors resolve with no speech recognition at all.

### 2.4 Vincentwei1021/video-shotcraft (Apache-2.0)

A Remotion product-promo skill: 157 cards and 214 previews (the README says 152). Its core rules:
- a seeded PRNG (mulberry32);
- a final review by a subagent with a clean context;
- hold rules: the brand mark holds at least 1 s, group motion ends with a 0.5 s pause, and the opening action
  gets at least 3 s.

**Tuned parameters worth stealing:**
- **paper-title-card** (`references/shots/typography/paper-title-card.md:22-26`):
  - Word *i* starts at frame `4+4i` and takes 9 frames, easing `bezier(0.2,0.75,0.3,1)`, scaling 1.28 to 1,
    with blur 7 px to 0 and opacity rising.
  - Exactly one italic accent word.
  - An underline grows over frames 16–34.
  - Serif at 116 px on paper `oklch(97.5% 0.008 82)` with a warm radial light; 8-frame fade out.
- **document-typewriter-reveal:** a mask wipe (width 100 % to 0, `bezier(.4,0,.6,1)`) with one caret riding
  its edge. The highlight grows 4 frames after the wipe ends, over 8 frames, at opacity 0.7.
- **timeline-travel** (`references/shots/data/timeline-travel.md`):
  - Speed curve maps `[0,.15,.88,1]` to `[0,.055,.9,1]`.
  - Each card springs up 6 frames before the camera arrives (damping about 11).
  - The final stop pushes 1 to 1.28 over 10 frames, then holds at least 30 frames.
- **depth-layer-moves** (`references/shots/camera/depth-layer-moves.md:3-17`):
  - Parallax layers move at 0.35, 0.7 and 1.4 of the camera speed.
  - Background layer: 2 px blur, 0.92 saturation, 0.85 opacity. Front layer: 3 px blur.
  - Pseudo dolly zoom: the background scales 1 to 2.25 and blurs 0 to 3.5 px; at most once per film.
- **Sound rules:**
  - S2: repeated SFX alternate between two samples, stepping the volume down.
  - S4: foley over decorative sounds, trimmed to the action.

**Better than ours:** tuned numbers for every move, and a machine-readable card index.

**Worse:**
- Built for SaaS promos.
- Runs on Remotion.
- `references/shots/ATTRIBUTION.md` says **48 cards were reverse-engineered from public promos and X or
  Douyin posts "not licensed for reproduction"** and then rewritten. The repo is Apache, but the provenance is
  murky.
- The SKILL tells the agent to ask users to tag the author on social media.

**How to adopt:** ideas and parameter values only, re-implemented in our HyperFrames templates. Effort S per
recipe.

**Verdict: BORROW IDEA.** The best-tuned parameter tables in the set, but don't copy the cards verbatim.

### 2.5 Vincentwei1021/video-talkcraft (PolyForm Noncommercial, so ideas only)

A Remotion skill for talking-head videos and vertical explainers: 108 cards (the README says 109).

- **Speed** (`README_EN.md:84`): a 201 s vertical video went from 13 to 9 minutes for the first full render.
  After changing one shot, a re-render takes **53 s**, because shots render as parallel segments that are
  then concatenated (`render_shots.mjs`). This supports rendering per beat.
- **QA scripts:**
  - `motion_check.py`;
  - `sfx_check.py` (peak at least −45 dBFS);
  - `contact_sheet.py` (3x4 sheets);
  - "burst triples" of frames at every state change.
- **Card `timeline-photo-strip`:**
  - The camera moves between stations in 0.9 s (`power2.inOut`) and holds 1.0 s at zoom 1.05.
  - The current station shows at brightness 1 and scale 1.03, the others at 0.7.
  - Finally it pulls back to 0.62 over 1.1 s and holds 1.2 s.
  - Camera formula: `camTo(z,px,py)={scale:z,x:480−z·px,y:270−z·py}`.
- **Card `map-route-pin`** (`template/cards/map-route-pin.tsx`): a stylized SVG coastline, not real
  geography. Worse than HyperFrames' d3 maps.

**Verdict: BORROW IDEA (ideas only, never code).** The rules for word-anchored beats and the tail guard are
exactly what we need.

### 2.6 Vincentwei1021/anything2explainer (PolyForm Noncommercial, so ideas only)

Turns anything into an explainer with Remotion and Kokoro (`am_liam` measures about 2.3 words per second).

- **Facts rule** (`SKILL.md:16`): "every number, English term, year, person's name on screen must be
  traceable to a source URL in the research doc." Unverified items appear neither on screen nor in the
  voiceover.
- **Render speed** (`SKILL.md:54`): 8,000 frames (about 4.5 minutes of video) in 3–4 minutes at concurrency 6.
- **`template/scripts/motion_check.py`:**
  - Samples every third frame and differences the grayscale content area at 320x180.
  - A mean below 0.35 counts as still; the longest still run must be at most 3.0 s.
  - The final hold (mean below 1.5) must last at least 30 frames.
  - Changed-pixel counts separate a true still (under 800 pixels) from small-area motion (800–2,500).
  - The Vox skill explains why 320x180 is too coarse; use its two metrics at 640x360 instead.

**Verdict: BORROW IDEA (ideas only).** The facts-on-screen gate and the stillness thresholds.

### 2.7 The most useful recipes for a strange-history Short

| Recipe | What it looks like | Typical line | Where it comes from (parameters above) |
|---|---|---|---|
| Letterpress date or title card | Words stamp in (scale 1.28 to 1, blur 7 px to 0), one accent word, an underline grows, warm paper | "November, 1932." / hook text | shotcraft paper-title-card; kit section.stamp and stat.calendar; HF `titlecard-lockup`, `per-word-rise` |
| Newspaper or document highlight | A real LOC page cropped to the exact words; a highlight sweeps on the spoken word; newsprint layering | "The papers called it…" | Vox LOC ALTO-to-IIIF recipe; shotcraft document-typewriter-reveal; HF `marker-highlight` |
| Zoom to a detail with a labelled callout | Push into the photo to a detail box, hold, then a circle draws on and an arrow labelled with at most 3 words appears | "Look at the hatpin." | Vox zoom-isolation and zoom-in rule; HF `hw-callout-circle`, `vox-annotate`; remocn scribble-circle and ink-arrow |
| Photo on paper or evidence stack | Archive photos as tilted cards with a shadow and a credit slot, one per phrase, with stop-motion jitter | "Then a second photo surfaced…" | Vox evidence stack; remocn polaroid, paper-sticker, stop-motion; kit halftone and sticker cut-outs |
| Route map with pins | d3 real-geography map; pins drop on place words; the route draws on | "…from Perth to Campion." | HF world-map, us-map-flow and nyc-paris-flight techniques; kit section.map and map-legend |
| Timeline stations | 3–5 dated stations; the camera docks at each on its year word, then pulls back | Escalating dates | shotcraft timeline-travel; talkcraft timeline-photo-strip; HF `spatial-pan-stations`; kit overview.timeline-3up |
| Quote card | A serif pull-quote, words rise in, one word highlighted, attribution chip | A real period quote | kit label.pull-quote; HF `per-word-rise` plus `marker-highlight` |
| Number card or icon grid | An odometer count-up, or a grid of repeated icons | "20,000 emus." | HF `count-up`, `number-wheel`; remocn rolling-number; kit stat.isotype |
| Myth versus fact | Strike through the myth, type the fact, a "HOAX" or "CORRECTION" stamp | Twists, hoaxes (Piltdown, spaghetti) | HF and remocn `strikethrough-replace`; kit section.correction and section.classified |
| Parallax on an archive photo | Subject cut out; layers move at 0.35, 0.7 and 1.4; grain and vignette | Any strong photo beat | shotcraft depth-layer-moves; HF `parallax-zoom` |

---

## 3. nexu-io/html-video (Apache-2.0)

**What it is.** A multi-engine "HTML to video" wrapper with 15 templates.

`packages/adapter-hyperframes/src/render.ts` does **not** use HyperFrames' deterministic producer (lines 2-10,
75-81, 308-316, 335-362):
- It opens the page in Playwright with `recordVideo`, a real-time screencast.
- It waits with `waitForTimeout`.
- It then re-encodes with FFmpeg (libx264, crf 20).

Timing therefore depends on the wall clock, so frames drop under CPU load, exactly the failure mode we need to
avoid on shared Modal CPUs.

According to `templates/NOTICE.md`, 8 templates are direct forks of HyperFrames examples, 1 comes from the
student kit, and 6 are original. The last push was 2026-06-21, three months ago.

**Worth borrowing:** the template metadata shape in `templates/frame-light-leak-cinema/template.html-video.yaml`:
`id, engine, category, best_for ("Documentary cold open"), output {aspects incl. 9:16, fps, duration
min/max}, inputs.schema (JSON Schema with maxLength), examples, license`.

**Verdict: SKIP.** A thin real-time recorder with forked templates. Keep only the metadata shape.

---

## 4. Remotion, template-tiktok, Remocn

### 4.1 Remotion licence verdict for a single-owner monetized channel

From `LICENSE.md` on main (read via `gh api`):
- "Individuals and small companies are allowed to use Remotion to create videos for free (even commercial)".
- Free Licence eligibility: "an individual", a for-profit organisation with up to 3 employees, a non-profit,
  or anyone evaluating.
- Permitted: "use … non-commercially or commercially for the purpose of creating videos and images".
- Not permitted: copying or modifying Remotion's code in order to sell, rent, license, relicense or
  sublicense a derivative.

From the licence FAQ (`packages/docs/docs/license/faq.mdx`):
- "an individual, whether for personal or commercial use"
- "Can I make money under the Free License? Yes"
- "Can I run an automation under the Free License? Yes"
- Company Licence: **Creators** at $25 a month per seat; **Automators** at $0.01 per render with a **$100
  monthly minimum**.

Pending changes for Remotion 5.0 ([PR #3750](https://github.com/remotion-dev/remotion/pull/3750), open since
2024-04-22, not merged; the LICENSE.md header already says "In Remotion 5.0, the license will slightly
change"):
- Eligibility becomes "an organization or team of individuals with up to 3 people", and contractors count.
- A new rule forbids running a rendering service where users upload their own Remotion code.
- Users must accept the Terms and Conditions.

**Verdict: YES, free for Days of Odd today.** One individual owning a monetized channel with fully automated
renders is explicitly allowed under both the current wording and the proposed 5.0 wording. The caveats:
1. If the channel becomes a company or team of 4 or more (under 5.0, including contractors), a Company Licence
   is required. The Automators plan's $100 monthly minimum would break our "everything free" rule.
2. It is source-available, not open source. The terms can change between major versions, so pin v4.
3. Everything built on Remotion (remocn, the shotcraft demos) carries this requirement too.

HyperFrames' own comparison page (`docs/guides/hyperframes-vs-remotion.mdx`) agrees: "free for individuals and
companies up to three people".

**Verdict on Remotion as our engine: WATCH.** It is mature (6 years old) and the licence is fine today. It
loses to HyperFrames for us because of the team-size licence cliff, the React/TSX build step in a Python
pipeline, and the fact that an LLM writing TSX is riskier than our code filling HTML templates.

### 4.2 remotion-dev/template-tiktok (no licence; `"UNLICENSED"`)

- `sub.mjs` runs Whisper.cpp with `medium.en` (1.5 GB) to produce captions.
- `src/CaptionedVideo/index.tsx:53,100-101` calls `createTikTokStyleCaptions` with
  `combineTokensWithinMilliseconds: 1200`, so each caption page covers about 1.2 s.
- `Page.tsx` fits the text to 90 % of the width (at most 120 px, uppercase), draws a 20 px black stroke with
  `paintOrder: stroke`, and colours the active word #39E508. Each page enters with a 5-frame spring
  (scale 0.8 to 1, translateY 50 to 0).

Our libass captions already do the same: word highlight, chunking, a scale-in. We don't need Whisper because
Kokoro gives the timestamps.

**Verdict: SKIP.** Nothing new, and there is no licence to copy under.

### 4.3 Remocn/remocn (MIT)

**What it is.** shadcn-style copy-paste Remotion components: 158 components plus 3 libraries, 48 UI pieces
and 7 templates. They take proper props; for example `PolaroidProps` has `caption`, `captionAt`, `width` and
`frameColor` (`registry/remocn/polaroid/index.tsx:37-45`).

On-genre pieces: polaroid, paper-sticker, page-turn, crumple-toss, halftone-print, stop-motion, ink-arrow,
ink-underline, scribble-circle, marker-highlight, typewriter, handwrite, rolling-number, number-wheel,
lens-zoom, focus-pull, pixelate-region, vhs-filter, grain-dissolve, ember-burn, whip-pan, zoom-blur and
strikethrough-replace. The shader components depend on `@paper-design/shaders-react` (Apache-2.0).

**Technique worth stealing: the stop-motion clock** (`registry/remocn/stop-motion/index.ts:1-40`):
- `qf(frame, step=3) = floor(frame/step)*step` holds each pose for 3 frames (10 poses per second at 30 fps).
- `hash01(seed)` is an FNV-1a hash.
- `paperJitter` offsets each pose by up to ±1.4 px and ±0.35°, seeded by `"<id>:x:<pose>"`.
- `steppedSpring` is a spring evaluated on the stepped frame.

It is about 30 lines, works in any engine, and is deterministic. It gives "hand-placed paper" motion.

**Verdict: BORROW IDEA.** Take the stop-motion clock and use the component list as a design reference. Adopt
the code only if we ever choose Remotion.

---

## 5. FFmpeg, Pillow and libass only: what they can and can't do

libass animation tags: `\t` (animate a change of `\fscx`, `\fscy`, `\blur`, `\alpha` or colour), `\move`,
`\fad`, `\frz`/`\org` (rotation), `\k` (karaoke timing), `\p` (vector drawings) and `\clip`.

**Rectangular `\clip` can be animated with `\t`, which is the trick behind wipe reveals and highlight
sweeps.** FFmpeg's filters take expressions of `t`: `overlay` x and y, `rotate`, `crop` x and y, `zoompan`,
and `perspective` with `eval=frame`. `xfade` offers about 50 transitions. Pillow can draw anything per frame
in Python and pipe it into FFmpeg.

| Designed shot | Pure FFmpeg + Pillow + libass? | Browser engine really needed? |
|---|---|---|
| Title or date card (stamp-in words, blur-in, growing underline) | **Yes.** One ASS event per word with `\t(\fscx\fscy\blur\alpha)`; the underline is a drawing with an animated `\clip`; a paper background from Pillow | No (the browser gives nicer kerning and fitting) |
| Typewriter date or place | **Yes.** Per-character `\alpha` timing or `\k`, plus a drawn caret | No |
| Split-flap board | Hard: pre-render the flap frames in Pillow | Much easier (HF `split-flap-board`) |
| Quote card with a highlight sweep | **Yes.** A Pillow card plus an ASS rectangle drawing with an animated `\clip` | No |
| Document or newspaper crop, zoom to region, highlight | **Yes.** Pillow crop (from ALTO boxes), a time-expression zoom, an ASS or overlay highlight | No |
| Photo on paper (tilt, shadow, tape, stop-motion jitter) | **Yes.** Pillow composite, then `overlay` x and y with `floor(t*12)/12` steps and `rotate` | No |
| Callouts: circle draw-on, curved arrows, labels | Partly. ASS clips are rectangles only, so a circle or arrow drawing on needs per-frame Pillow arcs | Much easier (SVG stroke-dash animation) |
| Map with real geography, route draw-on and pins | Doable: Natural Earth plus shapely/pyproj plus a per-frame Pillow polyline. M–L effort per style | Much easier and prettier (d3-geo, SVG) |
| Timeline stations with a camera pan | **Yes.** One tall Pillow canvas plus a time-expression `crop` | No |
| Count-up number | **Yes.** One ASS event per value, or Pillow frames | No |
| Rich kinetic type (staircase layout, mixed fonts, masks, blend modes) | Partly. Per-letter ASS events work; masks and blends are limited | Yes, for the premium look |
| Multiplane parallax | **Yes**, after segmentation and inpainting: overlay layers at different zoom and pan speeds | No |
| Zoom-isolation with the subject lifting out | Partly: needs a cut-out model, and the seam alignment is manual maths | Easier to choreograph in the browser |
| Grain, vignette, sepia grade, light leaks | **Yes.** `noise=alls=..:allf=t`, `vignette`, `curves`/`lut3d`, `blend=screen` with CC0 leak clips | No |
| Transitions (wipe, slide, circle, pixelize, whip) | **Yes.** `xfade` covers about 50 | Only for shader or velocity-matched transitions |
| 3D tilt of a page | **Yes.** `perspective` with `eval=frame` | Easier with CSS 3D |
| Diagrams and flowcharts | Hard | Yes |

**Bottom line:** FFmpeg, Pillow and libass can make roughly 70–80 % of these shots at near-zero render cost.
But every recipe becomes bespoke pixel maths in Python, typography and callouts look cheaper, and there is no
template library to start from. A browser engine wins on typography, SVG draw-on, maps, masks and blend modes,
on existing templates, and on the LLM's fluency in HTML and CSS. At our volume the cost difference
(about $0.01 per Short) doesn't matter.

---

## 6. The one engine: HyperFrames, and how it fits our pipeline

```
beats + Kokoro word timestamps (already produced)
  → LLM writes one shot JSON per beat: recipe + slots + cue words   (section 7)
  → pydantic validation: recipe from a closed list, slot length limits, every cue word appears in the beat
    text, the technique-floor rules, every on-screen number/name/year exists in the claims table
  → resolve cue times from word timestamps; resolve media with the existing visuals.py (plus LOC scans)
  → Jinja fills a template from our repo → one composition per beat (1080x1920, 30 fps, exact beat length)
  → `hyperframes check` (0 errors) → `hyperframes render --workers 4 --quality standard` per beat
  → on error or timeout (for example 120 s per beat): fall back to today's zoompan clip for that beat
  → existing FFmpeg concat + ASS captions + SFX + loudnorm
  → frames for the contact sheet → Gemini review, plus a stillness gate and an event-density gate
```

**Modal image.** Extend the current `debian_slim` image. Copy the apt list from HyperFrames'
`packages/gcp-cloud-run/Dockerfile` (FFmpeg, libnss3, libgbm1, libasound2 and the other Chromium libraries,
plus Noto fonts), then:
- install Node 22 from NodeSource;
- `npm i -g hyperframes@0.8.80`;
- `npx @puppeteer/browsers install chrome-headless-shell@148.0.7778.167 --path /opt/chs`;
- set `HYPERFRAMES_CHROME_PATH=/opt/chs/...`, `HYPERFRAMES_NO_TELEMETRY=1` and
  `PRODUCER_LOW_MEMORY_MODE=false`.

Bundle GSAP, d3, topojson-client, a Natural Earth TopoJSON file and our OFL fonts into `/opt/hf-assets`, and
block the network during renders.

**Captions.** Designed templates must keep the caption band clear: our captions sit around y≈1152 of 1920, so
reserve roughly y 1040–1300. When a quote or title card already shows the spoken words, suppress the duplicate
caption cue (the Vox rule).

**Cost per Short.** Modal list price is $0.0000131 per physical-core-second plus $0.00000222 per GiB-second.
Our current render function (`cloud.py:93`: `cpu=8.0, memory=8192`) therefore costs $0.000123 per second.

| Scenario | Frames | Wall time (estimated) | Cost |
|---|---|---|---|
| Only the designed beats through HyperFrames (about 3 of 8 beats) | 450–600 | 20–60 s | **$0.003–0.008** |
| The whole 45 s Short through HyperFrames | 1,350 | 45–150 s | **$0.006–0.018** |
| Cold start of the ~3 GB image, per container | – | 10–30 s | +$0.001–0.004 |

That is about $0.4–1.2 a month at 60 Shorts, well inside the $30 credit, even if real templates run 3x
slower. Avoid blur and backdrop filters, which cost 2.5x in HyperFrames' own guide.

On the GitHub Actions backup (a 4-vCPU ubuntu runner), expect about 2–4 minutes per Short at no cost.

**Why not the others:**
- **Remotion:** the team-size licence cliff, React bundling and TSX (section 4.1).
- **FFmpeg only:** bespoke code for every recipe and weaker typography and maps (section 5). FFmpeg stays as
  the assembler and the fallback.

---

## 7. A minimal JSON scene spec (what the LLM writes per beat)

The LLM writes only `recipe`, `slots`, `cues` and optionally `camera`, `claims` and `backup`. Our code
supplies durations (from Kokoro), cue times (from the cue words), media files (from our picker), fonts,
colours and SFX.

```json
{
  "beat": 2,
  "shot": {
    "recipe": "map_route",
    "backup": "date_card",
    "slots": {
      "points": [
        {"label": "Perth", "lat": -31.95, "lon": 115.86},
        {"label": "Campion", "lat": -31.03, "lon": 118.43}
      ],
      "route": "arc",
      "kicker": "WESTERN AUSTRALIA, 1932"
    },
    "cues": [
      {"word": "Campion", "do": "pin", "target": 1},
      {"word": "machine", "do": "route"}
    ],
    "camera": "push_slow",
    "claims": ["c3"]
  }
}
```

Other recipes use the same shape:

```json
{"recipe": "archive_photo", "slots": {"frame": "paper", "label": "THE HATPIN", "detail": "auto"},
 "cues": [{"word": "hatpin", "do": "detail"}, {"word": "hatpin", "do": "circle"}]}
{"recipe": "document", "slots": {"source": "loc", "query": "emu war machine guns 1932", "highlight": "machine guns"},
 "cues": [{"word": "guns", "do": "highlight"}]}
{"recipe": "quote_card", "slots": {"quote": "…", "who": "Maj. G.P.W. Meredith", "year": "1932", "accent": "tanks"},
 "cues": [{"word": "tanks", "do": "highlight"}]}
{"recipe": "stat_card", "slots": {"value": 20000, "suffix": "", "label": "EMUS"}, "cues": [{"word": "twenty", "do": "count"}]}
{"recipe": "myth_fact", "slots": {"myth": "Spaghetti grows on trees", "fact": "An April Fools' hoax, 1957"},
 "cues": [{"word": "hoax", "do": "strike"}]}
```

**Recipe index entry.** The LLM chooses from a JSON index shaped like the shotcraft, talkcraft and html-video
indexes:

```json
{"id": "map_route", "use_when": "the line moves between named real places, or where it happened matters",
 "avoid_when": "places unknown, or more than 5 places", "input": "none", "semantic": ["place", "journey"],
 "duration_s": [3, 8], "energy": "mid",
 "slots": {"points": "2-5 x {label<=18 chars, lat, lon}", "route": "arc|line|none", "kicker": "<=26 chars"},
 "cues": ["pin:<i>", "route"], "sfx": {"pin": "pop", "route": "whoosh_soft"}}
```

**The shelf** (a closed enum): `archive_photo` (motion: push, pull, pan, detail; frame: full or paper),
`evidence_stack`, `date_card`, `title_card`, `map_route`, `document`, `quote_card`, `stat_card`, `timeline`,
`myth_fact`.

**Choosing a recipe for a beat:**
1. **Input filter:** if the picker's best photo scores below 4 out of 5, only recipes that need no photo are
   allowed.
2. **Match the line's meaning:**
   - a date or place → `date_card`
   - a journey → `map_route`
   - a number → `stat_card`
   - a quote → `quote_card`
   - a hoax or contradiction → `myth_fact`
   - several dates → `timeline`
   - the thing itself → `archive_photo` with `detail`
3. **Variety:** never repeat the previous beat's recipe.

**Validator rules** (from the sources above):
- Every cue word must appear in the beat text.
- The first event lands within 1.5 s of the beat start.
- There is an event at least every 3.0 s; we aim for 2.2–2.5 s.
- No cue within 0.5 s of the beat end.
- Static text cards make up at most half the beats. The Vox cap is a third, but we have more
  picture-starved topics.
- At least one `archive_photo` with `detail` per Short when photos exist.
- Every on-screen number, year or name must be in the claims table.

---

## 8. Red flags

- **Star velocity:**
  - HyperFrames: 53.5k stars in 6.5 months, HeyGen-marketed. The code is still substantial and real:
    Dockerfiles, beginFrame capture, tests and benchmarks.
  - shotcraft: 9.7k in about 10 weeks.
  - anything2explainer: 2.1k in 3 weeks; no push since 2026-09-18.
  - html-video: 4.6k stars for a real-time screen recorder with mostly forked templates; stale since June.
- **Card counts don't match the files:** shotcraft claims 152 against 157 cards; talkcraft claims 109 against
  108.
- **shotcraft:** 48 cards come from promos that were "not licensed for reproduction", and the SKILL tells the
  agent to ask users to tag the author.
- **HyperFrames:** pre-1.0 with about one release a day, so pin exact versions. Its own registry fetches from
  a CDN during render.
- **Student kit and `media-use`:** the kit's Shorts path needs paid ElevenLabs and Kie.ai; `media-use` needs a
  HeyGen login.
- **Licences:**
  - talkcraft and anything2explainer are PolyForm Noncommercial: ideas only.
  - template-tiktok has no licence.
  - Remotion's terms change in v5.

---

## Top insights for Days of Odd (ranked)

1. **Add a designed-shot layer using HyperFrames.** Render each beat from our own ~8 HTML templates, which the
   LLM selects and fills with JSON. When a beat's best photo scores below 4 out of 5, it must switch to a
   recipe that needs no photo: a date card, map, document, quote, number card or myth-versus-fact card.
   - **Why:** this targets the visual failures that caused 14 of our 15 rejections (a wrong picture or no
     picture).
   - **Cost:** effort M–L; about $0.003–0.018 per Short. Fall back to zoompan for any beat that fails.
2. **Anchor every on-screen event to a spoken word.** Cue word → Kokoro time, then lint:
   - |Δ| ≤ 0.1 s;
   - nothing visible before its word;
   - no cue within 0.5–0.7 s of a cut.
   - **Why:** Kokoro already gives us word timestamps. Effort S. (Ideas from talkcraft and the kit.)
3. **Enforce event density.** Require a new visual event at least every 2.2–3 s, checked on the timeline.
   Also add a render-side stillness check with two metrics at 640x360 (mean below 0.25 and fewer than 150
   changed pixels means still).
   - **Why:** today each still sits unchanged for 5–7 s. Effort S.
4. **Replace plain Ken Burns on archive photos:**
   - the photo on a paper card;
   - a push to a detail box supplied by the vision LLM, landing on the cue word;
   - a circle that draws on, plus an arrow labelled with at most 3 words;
   - the zoom-in rule: push in only when the payoff is inside the image;
   - plate pushes of 3–4 %, not 12 %.
   - Effort M.
5. **Newspaper highlights from real Chronicling America pages** (public domain before 1930). Use ALTO word
   boxes to crop through IIIF, then sweep a highlight on the spoken word. Never fake a photo; a recreated
   document is allowed only with an on-screen flag. Effort M.
6. **Validate the variety of each plan:** no two consecutive beats with the same recipe, a cap on static text
   cards, at least one detail zoom per Short, highlights always animated on. Effort S.
7. **One house style: "paper documentary."**
   - Palette: paper, ink and one accent.
   - Type: Fraunces or another serif, plus Archivo uppercase.
   - Motion: elements in stepped 12 fps poses with jitter (the remocn clock) while the camera moves smoothly.
   - Texture: grain and vignette, with a halftone "engraving" treatment for mismatched scans.
   - Effort S–M; this is taste encoded as tokens.
8. **Facts-on-screen gate:** every number, year or name on screen must match the claims table before render.
   Effort S. (Idea from anything2explainer.)
9. **Per-recipe SFX pairings:**
   - stamp → thud
   - highlight → marker
   - pin → pop
   - typewriter → keys
   - route → soft whoosh
   Keep SFX about 12 dB under the voice, at most one cue per frame, and alternate samples when a sound
   repeats. Effort S (needs CC0 samples).
10. **Contact sheets from `hyperframes snapshot`**, taken at each beat's key cue, not its midpoint, so Gemini
    reviews the shot's payoff frame. Effort S.
