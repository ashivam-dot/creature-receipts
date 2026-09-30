# G3b: visual styles and automated scene design

Checked on 2026-09-27.
- Stars, watchers, forks and dates come from `gh api repos/<owner>/<repo>`.
- Licences were read from each clone's LICENSE file, or noted as absent.
- Code was read from shallow clones in `/tmp/ghdeep/g3b/<repo>` at the commit listed. Nothing was installed or run.
- Small `curl` checks covered the Remotion LICENSE, the Depth Anything model cards, the Natural Earth terms, and the Wikidata and Library of Congress APIs.

**Scope.** For each repo, four questions:
1. How does a script line become a scene?
2. What is the visual grammar?
3. How does the look stay consistent across a video?
4. Can it run headless, automated and free?

The aim is our main failure. 14 of 15 rejected Shorts failed on visuals: the picture was wrong, from the wrong period, or missing. And the look reads as a static slideshow (one still per beat, zoompan up to 1.12×, hard cuts).

## Summary

| Repo | Stars | Watchers | Forks | Licence (from the file) | Created | Last push | Archived | Commit | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Alisa0808/vox-director | 2,057 | 12 | 313 | MIT | 2026-07-10 | 2026-08-11 | no | 668ec39 | BORROW IDEA (strong) |
| cyberlesterr/paper-collage-video | 235 | 0 | 28 | MIT code; textures, style-catalog PNGs and demo media all rights reserved | 2026-07-17 | 2026-09-13 | no | bd53136 | BORROW IDEA |
| Anil-matcha/vox-ai-motion-graphics-generator | 223 | 2 | 44 | **none** (README badge says MIT) | 2023-11-07 | 2026-09-02 | no | c685644 | SKIP |
| trustfuture/simon-skills | 203 | 0 | 48 | MIT | 2026-09-20 | 2026-09-24 | no | 3ad0a25 | ADOPT (port the card recipe) |
| showlab/Code2Video | 2,076 | 13 | 289 | MIT | 2025-09-29 | 2026-08-24 | no | 1142d8e | BORROW IDEA |
| iart-ai/motion-skills (index) | 516 | 3 | 42 | MIT | 2026-06-22 | 2026-09-23 | no | 91834c6 | BORROW IDEA (strong, via packs) |
| iart-ai skill packs (map-animation 13, kinetic-typography 12, explainer-video 26, tiktok-video 11, youtube-video 3 stars) | 3–26 | 0 (first 4 checked) | 3–8 (first 4 checked) | MIT (each) | 2026-06-22 | 2026-06-22 | no | 390ca98 / fccc94b / 3e2d411 / 2a77533 | (see index) |
| lifeprompt-team/remotion-scenes | 49 | 0 | 5 | MIT | 2026-02-04 | 2026-02-05 | no | 02c7a84 | SKIP |
| av/remotion-bits | 481 | 4 | 27 | **no LICENSE file** (package.json says MIT) | 2026-01-23 | 2026-09-15 | no | de35fda | WATCH |
| lemomo-ai/lemo-opuscar | 323 | 0 | 38 | MIT code + CC BY 4.0 guides, STYLE.md files and films (GitHub reports NOASSERTION) | 2026-09-26 | 2026-09-27 | no | 108fa78 | ADOPT (port two shaders) + BORROW IDEA |
| athemeroy/awesome-opus-5-5-videos | 237 | 1 | 19 | CC BY 4.0 | 2026-09-25 | 2026-09-27 | no | f0728e6 | BORROW IDEA (small) |
| FelippeChemello/podcast-maker | 705 | 8 | 92 | MIT | 2021-03-16 | 2026-01-11 | not flagged; README says archived | 5975680 | SKIP |
| *Search finds* | | | | | | | | | |
| BrokenSource/DepthFlow | 1,547 | 11 | 122 | AGPL-3.0 | 2023-06-24 | 2026-08-25 | no | f526fb4 | WATCH (run only as a separate tool) |
| longweekendlabs/parallax-studio | 3 | 0 | 0 | MIT | 2026-05-06 | 2026-09-03 | no | 81828ca | ADOPT (port ~60 lines) |
| yanliudesign/mono-color-skill | 3,284 | 2 | 93 | MIT code; `examples/` all rights reserved | 2026-08-19 | 2026-09-02 | no | c8ff705 | BORROW IDEA |
| pyang5166/gbro-collage-broll | 1,311 | 5 | 112 | MIT | 2026-07-15 | 2026-07-15 | no | a1a4ee2 | BORROW IDEA (small) |
| Yiijoe/route-map-video | 0 | 0 | 0 | **none** | 2026-06-06 | 2026-06-06 | no | 8c25f99 | BORROW IDEA (tiny) |

Also checked, but not studied in depth:
- **mrlancelot/MapYoutubeVideos** (2★, no licence). Scripts only: history map Shorts on *our* topics.
- **niovideoshelp-jpg/documentary-remotion** (0★, no licence). One hand-directed documentary.
- **topmonroe9/travel-animation** (0★, MIT). Browser app on modern OpenFreeMap tiles.
- **vt-vl-lab/3d-photo-inpainting** (7,093★, last push 2024-08-30). The LICENSE file is MIT, although GitHub says "other". A 2020 research pipeline (MiDaS depth plus layered-depth mesh inpainting); I read only the file list, and its weight licences are unchecked.
- **sniklaus/3d-ken-burns** (1,572★). **CC BY-NC-SA 4.0, excluded.**
- **DepthAnything/Depth-Anything-V2** (8,873★). The code is Apache-2.0. Per README L178–180 and the Hugging Face model cards, only the **Small** weights are Apache-2.0; Base, Large and Giant are **CC BY-NC 4.0**.

**Star skepticism.** Watchers per 100 stars is the proxy, as in G2b.
- Most repos sit between 0.4 and 1.1.
- **mono-color-skill is the outlier at 0.06**: 3,284 stars in 5 weeks with 2 watchers.
- Three young repos have zero watchers: paper-collage-video (235★), simon-skills (203★ in one week) and lemo-opuscar (323★ in **one day**).
- vox-director reached 2k stars in a month and promotes Atlas Cloud (paid; default watermark "Made with Atlas Cloud"). Anil-matcha repackaged it under a 2023 repo without the MIT notice.

None of this says the code is bad. The lemo-opuscar shaders and simon's card recipe are real, readable code. It does mean stars say nothing about quality here.

**The big picture.**
- **The shared fix for the slideshow look.** Every serious repo uses more than one shot per beat, cutting every 2.5–6 s. Every picture becomes a *composed layer stack* (background, card, subject, text, texture), never a bare full-frame crop.
- **Three ways to keep a video consistent:**
  - one style block reused verbatim in every image prompt (vox);
  - one palette-and-surface profile (paper-collage);
  - **one post pass that every source goes through** (lemo's Redraw and FilmPost). Only this one unifies *mixed archive sources* without a human.
- **The best shots for our failure need no found picture.** Maps, datelines, counters, quotes and timelines are drawn from data. No repo here ties them to a checked fact source. For us, Wikidata (CC0) plus Natural Earth (public domain) can do that; both were verified below.
- **Everything useful runs headless and free.** It is FFmpeg, Pillow/NumPy/OpenCV, or a deterministic HTML page captured by headless Chromium. The paid parts are optional: Atlas/MuAPI image-to-video and Gemini Omni.
- **No repo automates layout.** vox's element engine is placed by hand: "the per-video layout is manual (until an LLM auto-layout layer exists)" (`references/local-engine.md`). Code2Video's grid anchors plus our vision picker fill that gap.

---

## 1. Alisa0808/vox-director — BORROW IDEA (strong)

A Claude skill that turns a topic into a 30–60 s "Vox-style" paper-collage explainer.

- **Line → scene.** `beats.json` (SKILL.md) picks an `arc`, for example `timeline` for history or `myth_buster`. Beat count follows duration: 30 s → 6–8 beats, 60 s → 10–12. **Each beat splits into 2 shots**, a WIDE shot carrying the headline and then a DETAIL cut-in. The shot schema (SKILL.md ~L251):

  ```json
  {"id":"a","dur":5,"title":true,"shot_size":"WIDE","camera_move":"push_in","scene":"...","element_motion":"..."}
  ```

  Each shot becomes one image prompt through `compose_collage_prompt(scene, title_cn, title_en, bg, aspect, with_title, style, palette, type_style, finish)` in `scripts/styles.py`, which returns `f"{block} SCENE (as layered paper cut-outs): {scene}.{title} Aspect ratio {aspect}."`.
- **Grammar.** Layered hand-cut paper on one flat background colour per beat. The headline is baked into the keyframe. Clips come from image-to-video models.
- **Consistency.** The style block is reused verbatim on every beat (`references/prompt-guide.md`: "color can change, texture shouldn't"), and `THEME_PRESETS` fixes idiom, palette, type, finish, mood and motion.
- **Headless/free.** Partly.
  - Paid: keyframes from nano-banana-2 (~$0.08 each), clips from gemini-omni-flash (~$0.13) through `scripts/atlas_cloud.py` / `provider.py`, with Kling for real people. `models-and-gotchas.md` puts a 30 s film at about $0.8–1.0.
  - Free: `kenburns.py` (FFmpeg only), `motion.py` (Pillow keyframe engine) and `mg_scrapbook.py` (FFmpeg card scrapbook) all run headless. `extract_elements.py` cuts collage pieces out with a paid remove-background API (`youchuan/v8.1/remove-background`).

**Techniques worth stealing**
- **Two shots per beat, cut every ~4–6 s** (SKILL.md L61–62, L132–139): "A beat's narration is ~8–10s, so give each beat 2 shots (a *wide* establishing shot ... then a close detail cut-in)"; "never let a single shot exceed ~7s".
- **Anti-monotony** (`references/beat-layer.md` L111–120):
  - No two adjacent beats use the same camera move.
  - Alternate the families scale ↔ translate ↔ static, and reserve static for the payoff.
  - The `hook_payoff` rhythm is "push_in → pan → parallax → static → push_in → tilt → pull_out → static".
  - The `timeline` rhythm: "pan the same direction beat-to-beat ... → push_in on the turning point → pull_out on the takeaway".
  - L56: "Change something visually every 3–5s; never hold a static poster >8s".
- **Style library** (`scripts/styles.py`):
  - L64–71 `COLLAGE_MECHANICS`: "layered hand-cut paper cut-outs with visible torn and scissor-cut edges, tape corners and soft real paper drop shadows ... Halftone print dots, newspaper-clipping scraps ... Figures are PRINTED / illustrated cut-outs, NOT CGI".
  - L73–112 `STYLE_LIBRARY`. `photo-collage` is "real black-and-white archival photographs cut out and layered with soft drop shadows, one restrained accent color ... museum-like". There is also `newsprint-editorial`.
  - L119–149 `THEME_PRESETS`.
- **Blurred-cover background plus a sharp fitted card, in pure FFmpeg** (`scripts/kenburns.py` L50–63). The zoompan that follows is `z='min(zoom+0.0009,1.18)'`, alternating in and out.

  ```
  [0:v]scale=W:H:force_original_aspect_ratio=increase,crop=W:H,boxblur=26:2,eq=brightness=-0.05[bg];
  [0:v]scale=W:H:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2
  ```

- **Scrapbook cards** (`scripts/mg_scrapbook.py`):
  - Constants: `CREAM="0xE9E1D0"`, card width 0.84·W, `TILT=[-2.5,2.0,-2.0,2.5,-1.5,2.2]`, `TRANS=["slideright","slideleft","slideup",...]`, `WHIP=0.3`.
  - Cards rotate with `rotate={rad}:c=none:ow=rotw():oh=roth()`.
  - The xfade chain recomputes its offsets.
  - Screen-blended confetti needs gbrp inputs.
- **Pillow keyframe engine** (`scripts/motion.py`):
  - Layers are `Layer(img, keys=[dict(t,x,y,s,r,a,e)])`. The `back` easing uses s=1.70158. Helpers: `slap` (1.5 → 1 in 0.25 s) and `pop_settle` (1.35 → 1.0).
  - The camera zooms `1+0.06*(t/T)` with an impact shake `22*exp(-8d)*sin(d*60)`.
  - The shadow comes from the alpha channel (alpha 130, blur 9, offset 10,16).
  - Frames are piped as rawvideo into ffmpeg. This is the pattern we'd use.
- **Per-beat accent colour from the image** (`scripts/text_overlay.py` `accent_color()`): quantize to 24 colours and score `sat*val*count**0.3`.
- **Video-prompt rules** (`prompt-guide.md`): one move per shot; "Never write snap/punch-in/slam/quick zoom"; "for critical text, overlay in post".

**Better than ours:** cadence and camera rhythm are designed, not derived from aspect ratio; every frame is a layered composition. **Worse:** the core path is paid; headlines baked into AI images garble, and realistic AI posters of real events would need disclosure; free-engine layouts are placed by hand; nothing checks facts or period.

**Adopt:**
- Idea plus a little MIT code: the kenburns card graph (S), the anti-monotony rules in place of `pick._motion` (S), and the two-shot beat across spec, pick and render (M).
- Modal cost: none beyond FFmpeg time. Risk: none if the MIT notice is kept on copied code.

**Verdict:** BORROW IDEA (strong). The two-shot beat and the move rhythm are the cheapest big win. Skip its paid generation path.

## 2. cyberlesterr/paper-collage-video — BORROW IDEA

A Codex/Claude plugin that compiles a brief into a Remotion paper-collage video through contract files, with human approval gates: intake → 3 scenario cards → style/voice approval → preview approval. Chinese-first.

- **Line → scene.** Scenario cards become scene contracts listing graphic roles, annotations and a transition *intent*, which compile to Remotion props.
- **Grammar.** Paper layers with depth parallax, editorial annotations, and transitions chosen by intent.
- **Consistency.** One style profile from `public/style-catalog/catalog.json` covers theme colours, surface, motion and a review focus.
- **Headless/free.** Remotion renders headless, but the flow waits on humans at each gate, and the bundled textures are not reusable.

**Techniques worth stealing**
- **Transition by narrative intent** (`skills/make-paper-collage-video/references/motion-directing.md` L286–303):

  | Intent | Transition | Duration | Use |
  |---|---|---|---|
  | `continuity` | slide, paper edge | 0.45 s | same action or thought continues |
  | `location-change` | wipe | 0.5 s | viewer moves to a new place |
  | `time-passage` | page-turn (clean set: dip 0.5 s) | 0.7 s | a later moment begins |
  | `focus-reveal` | iris | 0.55 s | attention narrows onto a subject |
  | `chapter-reset` | shutters | 0.65 s | a chapter closes |
  | `impact` | cut | 0 s | a deliberate shock or reveal |

  Rules: "never alpha-crossfade semantic scenes"; rhythmic cuts land in the outgoing last 20% or the incoming first 20%.
- **`visual-sfx` typography** (L263–267): 1–8 characters, `stamp|shake|drop-impact`, bound to a sound cue, rare.
- **The `archival-collage` profile** (`catalog.json`). Directives:
  - "Use aged paper, restrained sepia color, halftone print texture, and archival cutout framing." / "Treat photographs and documents as tactile evidence layers with legible hierarchy."
  - Negative: "Glossy modern gradients, neon color".
  - Composition: "one dominant archival focal point"; "Preserve readable margins, captions, and document edges".
  - Colours: canvas `#342d27`, sceneBackground `#756552`, accent `#a84d3f`, ink `#26211d`, subtitle `#f3e8d0` on `rgba(38,33,29,.82)`.
  - Surface: texture opacity 0.14 in multiply; subject edge is a 2 px paper outline `#d9ccb0`; drop shadow offset (2,6), blur 4, `rgba(24,20,17,.38)`.
  - Motion: pacing "measured"; at most one visual-sfx per scene, lasting 0.25–0.6 s.
  - reviewFocus: "Evidence hierarchy stays sober and legible without decorative nostalgia overpowering facts."
- **Depth parallax for layered cut-outs** (`src/parallax.mjs` L4–19): `amount=(depth-focalDepth)*strength; x=cameraX*amount; y=cameraY*amount; scale=1+(cameraZoom-1)*amount`. It only works with at least 2 distinct depths.
- **Transition overlays** (`src/SceneTransitionOverlay.tsx`): an 18 px paper-edge bar, a torn-wipe polyline, a 14 px iris ring, a page-turn fold (`rotateY` up to 68°), and shutters.
- **Editorial nodes** (`src/EditorialNodes.tsx` L337–384). `timeline()` spaces events on a line (focused dot r=5, others 3.5) with labels alternating above and below. Annotation kinds: arrow, leader-line, label, badge, callout, bracket, numeric-counter, percentage-counter.
- "Choose the smallest truthful mechanism."

**Better than ours:** the most complete written grammar for transitions and archival surfaces, with an explicit "evidence hierarchy" review focus. **Worse:** human gates and a heavy contract compiler. `ASSET_LICENSES.md` reserves all rights to `public/textures/**`, `public/style-catalog/*.png` and the demo media, so none of those can be copied.

**Adopt:** ideas only. A transition-intent enum (S), the archival palette and surface constants (S), and the timeline node spec (S). No cost.

**Verdict:** BORROW IDEA. The intent → transition table and the archival profile become our house rules.

## 3. Anil-matcha/vox-ai-motion-graphics-generator — SKIP

This is vox-director rebranded as "muapi-director" on the paid api.muapi.ai.
- `styles.py` is the same code with comments stripped; the video models are swapped for veo3.1, runway and kling.
- There is **no LICENSE file**, and vox-director's MIT notice is not kept.
- The repo was created in 2023 and repurposed.

**Verdict:** SKIP. It's an unlicensed copy of repo 1; use the original.

## 4. trustfuture/simon-skills — ADOPT (port the card recipe)

Skills for a Chinese investigation-video channel. Two matter here: `investigation-video` (Remotion evidence collage) and `whiteboard-video`.

- **Line → scene.**
  - Whiteboard: a `scenes.js` DSL where beats are split by `|` → Excalidraw JSON via rough.js → Playwright headless Chromium `seek(t)` with 4 workers → ffmpeg. Frame identity is checked with `ffmpeg -f framemd5`.
  - Investigation: the LLM writes Remotion scenes on top of a fixed template and rules.
- **Grammar.** Real material, a sharp foreground over a blurred background, and one unified collage treatment (`references/visual-collage-v2.md`).
- **Consistency.** One template with one texture stack.
- **Headless/free.** Yes: Playwright and Remotion. The stickers come from a local imagegen CLI, which is not free.

**Techniques worth stealing**
- **The evidence-card recipe** (`skills/investigation-video/template/remotion/index.jsx` L7–15, minified):
  - Easing: `e=(f,s=0,d=22)=>interpolate(f,[s,s+d],[0,1],{easing:Easing.bezier(.18,.8,.22,1)})`.
  - Torn edge: `polygon(1% 1%,18% 0,31% 1%,49% 0,68% 1%,89% 0,99% 2%,100% 32%,99.5% 70%,100% 98%,84% 99%,62% 98%,47% 100%,26% 99%,1% 100%,0 70%,.5% 42%)`.
  - Background: the same media with `blur(23px) saturate(.45) brightness(.38)` (`.95` on light scenes), a slow `scale(1+f*.00008)`, and a faint 96 px grid with `perspective(1000px) rotateX(8deg)`.
  - Texture: SVG `feTurbulence type=fractalNoise baseFrequency=.8 numOctaves=3` at opacity .05, jittered ±1 px every 4–6 frames; 20 drifting dust specks at .14; a vignette `inset 0 0 190px #00000035`.
  - Sticker: four 4 px `#f5f3e9` drop-shadows (a white outline) plus `drop-shadow(14px 24px 22px #0006)`, bobbing `sin(f/60)*5`.
  - Cards: `rotate([-4,3,-2][i])`, sliding in with `translateX((1-q)*180)` from staggered starts [16,37,58] over 13 frames.
  - Tape: a 210×55 strip `#b5c5adbb` at `rotate(4deg)`.
  - Draw-on underline: `pathLength="1" strokeDasharray="1" strokeDashoffset={1-e(f,20,22)}`.
  - A `<Note>` shows "source · date".
- **Honesty rule** (`visual-collage-v2.md`): an AI-made object is labelled in frame "AI concept illustration, not the real item", and evidence is never faked with AI.
- **Reading-time rules** (`skills/investigation-video/SKILL.md`):
  - L65: short on-screen text holds at least 2.5–3 s.
  - L66: evidence stays 8–9 s, with about 5 s of reading after its entrance.
  - L68: footage cuts every ~3–7 s.
  - L35: "static image + zoom ... doesn't automatically solve the PPT feel".
- **Whiteboard pen timing** (`whiteboard-video` `config.json` `render.pen`): 1000 px/s, minimum 0.35 s per stroke, 0.12 s gaps, 0.06–0.2 s per character.

**Better than ours:** a complete, parameterized archive card. One treatment fixes the aspect-ratio crop problem, makes old images look designed, and shows the credit on screen. **Worse:** React/Remotion; one week old; Chinese-focused.

**Adopt:**
- Port the recipe (MIT) to Pillow/OpenCV (M). Build the torn mask, outline, shadow and tape once per image, then apply only affine moves and alpha blends per frame.
- Modal: CPU seconds.
- Risk: taste. Keep tilts small and tape rare.

**Verdict:** ADOPT (port the recipe). It becomes the default shot for every archive image.

## 5. showlab/Code2Video — BORROW IDEA

Research code (ICML 2026) for educational Manim videos.

- **Line → scene.** `prompts/stage2.py` writes a storyboard, `{"sections":[{"id","title","lecture_lines" (≤10 words),"animations"}]}`. Then `src/external_assets.py` fetches ≤4 icons (IconFinder `premium=0` or Iconify), `stage3.py` writes Manim code, the code is rendered and debugged, `stage4.py` gets multimodal feedback, and the result is refined.
- **Grammar.** Manim objects placed on a named 6×6 grid.
- **Consistency.** A base class plus a scoring rubric (`prompts/stage5_eva.py`: 5 × 20 points for layout, attractiveness, logic, accuracy and visual consistency).
- **Headless/free.** Manim renders headless; the LLM calls cost money.

**Techniques worth stealing**
- **Grid anchors for LLM layout** (`prompts/stage3.py` L16–32): "Use 6x6 grid system (A1-F6) for precise positioning ... self.place_at_grid(obj, 'B2', scale_factor=0.8) ... NEVER use .to_edge(), .move_to(), or manual positioning!". `prompts/base_class.py` maps each cell to x = 0.5+j, y = 2.2−i.
- **A critic that sees the grid** (`src/agent.py` L402–449 `get_mllm_feedback`; `GRID.png` at L102). It sends Gemini the rendered video, a grid reference image and a position table. The stage-4 output is `{"layout":{"has_issues":true,"improvements":[{"problem","solution","line_number","object_affected"}]}}`: "List up to 3 layout problems", with `feedback_rounds=2`.

**Better than ours:** the only repo that lets an LLM place things by named cells and then checks the placement visually. Our contact-sheet review has no spatial vocabulary. **Worse:** Manim and classroom visuals; icon licences vary per icon.

**Adopt:**
- Ask the picker to return `detail: "C2:D4"` on a 6×6 grid over each chosen image (S).
- Overlay the grid on review contact sheets and ask for ≤3 problems given by cell (S).
- Cost: a few extra Gemini tokens.

**Verdict:** BORROW IDEA. Grid cells let the picker say "punch in on the tank" and the reviewer say "the caption covers the face".

## 6. iart-ai/motion-skills and its packs — BORROW IDEA (strong)

The index repo holds only a README, a showcase and `tools/verify`. The real content is in docs-only packs, each made in a single day (2026-06-22), with UTM links back to iart.ai.

- **Line → scene.** The explainer pack's storyboard template has the columns VO / VISUAL / KEY MOTION / TRANSITION (on the exact word) / CAPTION / ASSET. Maps are driven by a data array of beats `{lng,lat,label,hold,zoom,route}`.
- **Consistency.** A style-spec sheet: "color = meaning; never reassign".
- **Headless/free.** The examples are Remotion (see the licence note in repo 7), but the recipes work in any renderer.

**Techniques worth stealing**
- **Vector maps** (`map-animation-skills/skills/map-animation/references/vector-maps.md`):
  - Framing: `geoMercator().fitSize([W,H],geojson)` (L13), preferred over a hand-tuned scale (L19). Equal Earth or Natural Earth projections for world views; orthographic for a globe.
  - Pins drop on `spring({damping: 12, stiffness: 120})`, staggered `i*STEP*4` (L79–84).
  - Routes draw on with `pathLength={1} strokeDasharray={1} strokeDashoffset={1-draw}` (L104). Great-circle arcs come from `geoInterpolate` (L64), with a travelling dot.
  - Labels are counter-scaled by `1/scale` so the map zooms but not the type (L59).
  - **12 fps stutter on overlays only**: `STEP=Math.round(fps/12); f=Math.floor(frame/STEP)*STEP`, with the camera on raw frames (L39–43).
  - Gotchas: `[lng,lat]` order and the antimeridian.
- **Kinetic type** (`kinetic-typography-skills/skills/kinetic-typography/SKILL.md`): mask reveal `translateY(110%)→0` with `cubic-bezier(0.16,1,0.3,1)`, 400–600 ms per fragment. Stagger 60–100 ms for lines, 40–70 ms for words, 20–40 ms for characters; about 800 ms total at most. A `?t=N` freeze harness.
- **Explainer timing** (`explainer-video-skills/skills/explainer-video/references/script-to-screen-workflow.md`): 2.3 words/s; `scene_seconds = words/pace + 0.4`.
- **Retention pacing** (`tiktok-video-skills/skills/short-form-video/references/retention-pacing.md`):
  - Hook text on screen by frame 1 (L18); the hook component is "text present from frame 0, micro-overshoot, no fade-up" (L46).
  - Uneven cuts every 2–4 s.
  - On the cut, a punch-in spring (damping 13, stiffness 220) scales 1 → 1.1 (L41).
  - Safe box 900×1400 at (90,260) in 1080×1920 (L134–135). Keep clear ~120 px at the top, ~300 px at the bottom and ~60 px on the right.

**Better than ours:** concrete numeric recipes for maps and type, which are exactly the shots we lack. **Worse:** documentation only, 3–26 stars per pack, part marketing.

**Adopt:** the ideas, in our own renderer. Maps are M effort using Natural Earth plus Wikidata coordinates. Cost: CPU seconds.

**Verdict:** BORROW IDEA (strong). The map recipe is the blueprint for our locator and route shots.

## 7. lifeprompt-team/remotion-scenes and av/remotion-bits — SKIP / WATCH

- **remotion-scenes** is a gallery of hard-coded scenes.
  - `src/scenes/CinematicAnimations/CinematicVintage.tsx`: flicker 0.9–1.0 every 2 frames, random scratches when random > 0.7, and `feTurbulence baseFrequency 0.9 numOctaves 4` re-seeded every 2 frames at opacity .15.
  - `CinematicDocumentary.tsx` is only a hard-coded title.
  - It has two days of commits. There's no line → scene logic.
- **remotion-bits** is a component library: AnimatedCounter, AnimatedText, TypeWriter (3 frames per character by default, plus an `errorRate`), ScrollingImages, ParticleSystem, Scene3D, GradientTransition, MatrixRain. It has **no LICENSE file**; `package.json` and the README badge both claim MIT.
- **Remotion's licence** (`LICENSE.md`, fetched 2026-09-27):
  - Free, *including commercial use*, for "an individual", "a for-profit organization with up to 3 employees", non-profits, and evaluation. Larger companies need a Company License.
  - "In Remotion 5.0, the license will slightly change."
  - It is source-available, not OSI open source. A one-person channel qualifies today. A plain Playwright `render(t)` page (lemo, simon) avoids the question entirely.

**Verdict:** remotion-scenes SKIP (generic, hard-coded). remotion-bits WATCH: the counter and typewriter timings are useful references, but copying waits for a real LICENSE file.

## 8a. lemomo-ai/lemo-opuscar — ADOPT (port two shaders) + BORROW IDEA

A library of 39 code-drawn film styles. Each has a `STYLE.md` and demo source, alongside `DIRECTOR.md` (directing method) and `TECHNIQUE.md` (build method).

- **Line → scene.** The director (an LLM) writes `TREATMENT.md` with a shot list (framing, angle, camera move, duration and *why*), a second-by-second beat sheet and a cue map. One `timeline.js` drives picture, sound and captions.
- **Grammar and consistency.** Per style: palette tokens, type, motion and camera tables. Some styles also run a whole-frame post pass.
- **Headless/free.** Yes. Each film is a page exposing `window.DUR`, `window.render(t)` and `window.READY`, captured by Playwright; audio is synthesized or taken from CC0/CC BY libraries. The voice is Kokoro af_heart (the same as ours) with a faster-whisper check. WebGL2 needs a GPU or SwiftShader in headless Chromium.
- **History-relevant styles:** silent-film, halftone-dossier, woodcut, dataviz, watercolor (ends on a painted map), risograph, blueprint, spy-titles, and ukiyoe (the camera travels over a print like a handscroll).

**Techniques worth stealing**
- **Redraw: photo → ink drawing in one shader** (`styles/silent-film/demo/engine/redraw.js`, shader L46–85, class L87–134):
  - Luminance, with contrast 1.08.
  - Gaussian blurs at σ=1.1 and 1.6σ.
  - XDoG ink lines, `ink = smoothstep(eps, eps+1/phi, -(g1-g2)*p)` (L63–66).
  - A soft posterize into 5 wash steps (L68–74).
  - Hatching in the dark areas: 45°, then crossed, then a third angle, with hand wobble and broken strokes. It is re-drawn every two frames (`bk = floor(frame/2)`, L75–76).
  - Photo mode uses `bilateral: 3, p: 34, eps: .24`.
  - `STYLE.md` §3: "Real video frames go through the same pass ... so footage and drawing share one hand."
- **FilmPost: one print look over any canvas** (`engine/film.js`, shader L15–95):
  - Gate weave (L28), optical softness, and halation on highlights (L35).
  - Per-frame flicker and uneven density; an S-curve (L41); print black .055 and white .93 (L44).
  - Four vertical scratches, each living a few frames (L46).
  - Brown edge burn (L60), vignette (L65), and two-octave silver grain that is coarser in the mids (L68). Silver → sepia toning (L74).
  - **"The one colour"** (L80): a mask keeps one element's hue while it still gets grain and exposure.
  - `weaveAt` adds an occasional perforation jump (L114). `damage()` adds dust, a hair in the gate for ~10 frames, and a rare blotch (L152–180).
- **Halftone dossier** (`styles/halftone-dossier/STYLE.md`):
  - Paper `#F4ECDD`, built procedurally: a 96×54 random tile upscaled, per-pixel noise ±13 with a −4 blue bias, vignette `rgba(120,100,80,.35)`, and a fold line.
  - Halftone: a rotated dot grid with dot radius = density × step × maxK (step 20–26 px, maxK .6–.72), a different screen angle per layer, multiplied together.
  - Headlines carry a misregistration shadow offset 8/8.
  - **Stamp slam**: 0.09 s from 2.6× to 1×, a 5% bounce, camera shake, and a flash capped at 0.5.
  - Dot-wipe transition: an 80 px grid of dots growing to r=62 over 0.44 s.
  - A case-number HUD with a chapter chip.
  - The "case file" frame: "any topic becomes 'the case against X'", counts 01/02/03, then a verdict stamp. It fits *Hoaxes That Fooled Everyone* and *Trials You Won't Believe* as is.
- **Woodcut** (`styles/woodcut/STYLE.md` §3, §10): a lit grey image goes through `woodcutFilter` so the cuts follow isophotes. One colour plate, `#C8502A`, "only for the thing that burns".
- **Capture rules** (`TECHNIQUE.md` L46–57):
  - Animate on twos only where the style wants it; the camera stays smooth.
  - Use one world → screen function.
  - **JPEG screenshots are about 8× faster than PNG**; run one browser per worker.
  - **Add grain in ffmpeg, not in the page.** `core/render/mux.sh` L9 uses `noise=c0s=$GR:allf=t` with a default of 2, after a two-pass loudnorm to −14 LUFS / TP −1.2 (L6–8).
- **Directing rules** (`DIRECTOR.md` §7–10):
  - Subtitles hold at least 1.8 s and at least the spoken line + 0.6 s. Text holds (letters ÷ 15 + 1.5) s after it finishes animating in. Title cards hold at least 4 s.
  - Use at least four different camera moves. At key moments the subject fills at least ⅓ of the frame height.
  - The most common failures: the subject is too small; colour is laid on the same colour; subtitles cover the subject; transitions show blank frames.

**Better than ours:** the only code in this study that automatically unifies mismatched sources into one hand. That is our exact problem: a Commons photo, a Met painting and a FLUX image in one Short. **Worse:** the shaders are WebGL2; each style film is directed by hand; the repo is one day old. The guides are CC BY 4.0, so credit LemoLab if we copy text.

**Adopt:**
- Port Redraw and FilmPost to NumPy/OpenCV (MIT; keep the notice). Effort M, about 200 lines; everything vectorizes.
  - Redraw runs once per still.
  - FilmPost's per-frame work is only grain, flicker and weave.
- Modal: cents per Short.
- Risk: heavy damage looks like a TikTok filter. Keep strength around 0.3, and never damage text.

**Verdict:** ADOPT (port two shaders), plus BORROW IDEA for the directing and pacing rules and the dossier grammar.

## 8b. athemeroy/awesome-opus-5-5-videos — BORROW IDEA (small)

A curated corpus of X posts with videos made using Claude Opus 5.5: 1,511 candidate posts, 1,401 distinct MP4s and 168 reviewed cases. It includes a classifier-labelled domain × style table (`data/domain-style.csv`), production paths (`data/cases.csv`) and a production guide (`docs/visual-effects-fit.md`).

**What recurs.** My tally from `domain-style.csv`, counting only "yes" and "likely" labels:
- **49 history/culture videos.** Primary styles: motion graphics/UI 11, 3D render 9, flat vector cartoon 8, painterly ink/sand 8, hand-drawn sketch 5, paper cut-out collage 4, pixel art 3.
- **Timelines dominate the topics**: "5000 years of Indian history", "Timeline of Western civilization", "History of human flight".
- Across the 168 reviewed cases, production paths are procedural 2D 52, transformed existing sources 32, educational explainer 27, and 3D/real-time 19.
- The guide's acceptance stages:
  1. Brief and keyframes.
  2. The hardest 2–4 s rendered, checking 12–24 neighbouring frames and re-seeking in different orders.
  3. The full pass.
- Caveats: the labels are classifier judgments, not verified authorship, and engagement isn't a quality score.

**Verdict:** BORROW IDEA (small). It confirms that code-drawn 2D and timelines are the common history look. Nothing to run.

## 9. FelippeChemello/podcast-maker — SKIP

A 2021 CLI that turned a newsletter JSON into a "podcast" YouTube video.
- **Line → scene:** a fixed Remotion template (`video/src/Podcast/*`: Title, AudioWaveform, and an Arc transition with a spring at damping 10).
- Azure TTS; a Gemini 2.0 image for the thumbnail only.
- Rendered by GitHub Actions whenever content is pushed (`.github/workflows/build-video.yml`).
- The README says it is archived, and the last commit is "Disable cron schedule and add archive notice". The successor, FelippeChemello/ai-video-engine, has 28★ and no licence reported.

**Verdict:** SKIP. It is archived, and its visual grammar is a podcast player.

---

## GitHub search: what exists

Several long queries returned **nothing**: "documentary style video generator", "archival footage video", "history explainer video", "map animation route", "animated route map video", "newspaper headline animation". Shorter queries found the following.

- **Depth parallax.**
  - **BrokenSource/DepthFlow** (AGPL-3.0): a GPU ray-marched 2.5D parallax. Its default estimator is `DepthAnythingV2` with `model = Small` (`depthflow/estimators/anything.py` L22, L82, loading `depth-anything/Depth-Anything-V2-small-hf`). Headless needs `backend="headless"` with EGL (`website/docs/exporting.md` L31, L58); CPU-only rendering through llvmpipe is slow (`website/get/docker.md`). AGPL is fine to *run* as a separate CLI, never to copy.
  - **longweekendlabs/parallax-studio** (MIT) is the copyable version:
    - `app/core/animator.py` L182–226: `influence=(depth-focus)*2; map = coord - influence*d - (coord-centre)*zoom*influence`, then `cv2.remap(..., BORDER_REPLICATE)`.
    - Amplitude: `max(60, long_edge*0.06) * gain`, with `gain = clamp(0.18/std(depth), 0.35, 1.0)` (L126–140).
    - A gradient-weighted feather on steep depth edges stops outlines tearing (`depth_model.py` L320–396).
    - The model is Depth-Anything-V2-Small fp16 ONNX from `onnx-community/depth-anything-v2-small` (`depth_model.py` L67), and the code itself tags Base as "CC-BY-NC-4.0" (L90). It runs on CPU through onnxruntime.
- **Print design systems.**
  - **yanliudesign/mono-color-skill** (MIT code; examples reserved) is a *prompt* system for one- or two-ink editorial prints. It renders nothing; `scripts/` only build boards and validate. Its rules are good:
    - At most two inks, each with a set *plate role*: the dominant ink carries 70–85%, the accent 15–30%.
    - 25–55% empty paper, and **one focal event** plus a quieter release zone.
    - "Type collides with the object"; a 5–12× type scale jump; one manual gesture family.
    - A deterministic seed from a hash of the recipe.
    - Bounded imperfections (`design-system/imperfections.json`): ink density 6–12%, dry edge 1–4%, halftone drift 5–10%, registration drift 1–3 mm, broken-gesture gaps 4–12%. "Never alter supplied wording or factual information."
  - **pyang5166/gbro-collage-broll** (MIT) makes 5 s halftone paper-collage B-roll with a paid video model (Gemini Omni Flash) and three human gates. The reusable idea is **assemble from empty**: the first frame is a blank colour field, and pieces arrive in the order "structure → subject or cards → action → result". Style signature: "black-and-white halftone photographic cut-outs mixed with selective colored cardstock ... crisp cut edges, cream keylines, soft paper shadows".
- **Maps.**
  - **Yiijoe/route-map-video** (no licence): a Remotion skill whose `SKILL.md` places points by *screen percentage*, not real geography. The one good idea is that each point's badge **lights up when the narrator says its name**, using Whisper word timestamps.
  - **topmonroe9/travel-animation** (MIT) uses MapLibre with OpenFreeMap street tiles (OSM data, so attribution is needed) and exports from a visible browser tab. That is modern-looking and not headless.
  - **mrlancelot/MapYoutubeVideos** has no rendering code (only TTS scripts): about 55 scripted history map Shorts with "Time / Narration / Visual / Meme" tables at 2–4 s per row. Many of its topics are ours (Emu War, Molasses Flood, Dancing Plague, Beer Flood, Pig War, Tulip Mania, Year Without a Summer). It relies on copyrighted memes. **It shows a direct competitor format.**
  - **niovideoshelp-jpg/documentary-remotion** (no licence): `STORYBOARD.md` shows the same documentary grammar. "Path builds through interception points as voice mentions each task"; "Neutral map → traced boundaries → restrained halo → organic red fill → names"; photos labelled "historical archive illustrations"; "No numerical performance claims invented."
- **Newspapers.** Only toys: raj-tagore/newspaper-clipping-generator (0★), KumariShambhavi/Fake-Newspaper-Generator (1★, Tkinter). No strong clipping generator exists, so we'd build a small one.
  - **Library of Congress / Chronicling America:** `loc.gov/collections/chronicling-america/?fo=json` and the legacy `chroniclingamerica.loc.gov` JSON endpoint both returned **HTTP 403 with a Cloudflare "Just a moment..." challenge** to curl from this machine. Test from Modal before relying on it. hugovk/chroniclingamerica.py (9★) is a client. Commons already holds many front-page scans.
- **Fact sources for drawn shots (verified).**
  - **Wikidata works:** `wbsearchentities` "Great Molasses Flood" → Q1129089, with P625 (42.3685, −71.0558) and P585 1919-01-15. The data is CC0.
  - **Natural Earth terms:** "All versions of Natural Earth raster + vector map data found on this website are in the public domain."
- **Fonts** (verified from google/fonts, where the folder name is the licence):
  - OFL: Old Standard TT, IM Fell English, IM Fell DW Pica, Courier Prime, Playfair Display (+SC), UnifrakturMaguntia, Bebas Neue, Oswald, Abril Fatface, Libre Baskerville, EB Garamond, Rye, Source Serif 4, Caveat, IBM Plex Mono, Space Grotesk, Anton.
  - Apache-2.0: Special Elite, Roboto Slab.
- **XDoG references:** heitorrapela/xdog (66★, MIT) and Kazuhito00/XDoG-OpenCV-Sample (15★, MIT). The algorithm is about 15 lines; lemo's version is better tuned.

---

## Proposal: the Days of Odd visual grammar

### Principles
1. **Two shots per beat:** a wide shot, then a detail or a data card. Cut every 2.5–4 s, so 12–18 shots per Short instead of 6–9 stills.
2. **No bare full-frame crops.** Every picture is a layer stack: background, card or cut-out, marks, text, texture.
3. **One print pass over everything,** so photos, paintings, engravings and illustrations read as one film.
4. **When no true picture exists, draw the fact** (place, date, number, quote, sequence). Don't search harder, and don't fake it.
5. **Every fact on screen carries a research source.** Every made image says so on screen.
6. **Rhythm and transitions are rules in code,** not choices left to the LLM.

### The 12 shot types

| # | Shot `kind` | Use it when | The LLM / research must supply | Headless render | Ideas from |
|---|---|---|---|---|---|
| 1 | `card` (archive card) | Default for any real photo, engraving, painting or document; required when the aspect ratio is far from 9:16 | Nothing new: picker output (file, focus), `credit` from metadata, optional `caption` ≤5 words | Precompute background (cover, blur ~23 px, sat .45, bright .38 or paper) and card (fit 84–90% width, house grade, seeded torn mask, 3–4 px cream outline, shadow, tape on ≤1 in 3). Per frame: slide in over 13–23 frames on bezier(.18,.8,.22,1), push 1.00→1.04, background drifting at a different rate. Source chip in mono type | simon `index.jsx` L7–15; vox `kenburns.py` L50–63, `mg_scrapbook.py`; paper-collage archival profile |
| 2 | `detail` (punch-in) | Second shot of a card beat: the face, sign, date or object the line names | `detail` cells on the chosen image ("C2:D3", 6×6 A1–F6); `mark` circle / underline / arrow / box / none; `label` ≤3 words; `on_word` | Crop to the cells; fall back to a card if the crop's short side is under ~540 source px. Cut in with a spring punch 1.0→1.08 (13/220). Red-pencil mark drawn on over 0.4 s at the word's timestamp (noisy polyline, slight overshoot) | vox 2 shots/beat; Code2Video grid; simon underline; iart punch-in; mono-color "one gesture family" |
| 3 | `depth` (2.5D push) | Wide scenes with clear depth: street, crowd, ship, building. Never portraits, documents, maps or flat paintings. At most 2 per Short | `depth: true` (the renderer rejects it if depth std < ~0.08); direction | Depth-Anything-V2-**Small** ONNX on CPU, once per image. Feather steep edges, then per-frame `cv2.remap` with displacement ≈1.5–2.5% of the long edge plus a slight zoom; then grade | parallax-studio `animator.py` L182–226, `depth_model.py`; DepthFlow (tool only); paper-collage `parallax.mjs` |
| 4 | `cutout` (figure) | Introducing a person or key object when a portrait or object photo exists; strong hook frames | `subject` noun; `bg` palette token | Matting model (**licence not yet verified**; candidates to check: rembg/u2net, BiRefNet, SAM 2) → 4 px cream outline + soft shadow over a flat ink or paper field with a radial halftone halo. `pop_settle` 1.35→1.0 in 0.3 s, then a 5 px idle bob. Low confidence → card | simon sticker; vox `motion.py`; gbro cut-outs; lemo halftone halo |
| 5 | `dateline` | First mention of place and time ("Boston, January 15, 1919") and time jumps ("Forty years later") | `place`, `date` from research or Wikidata (P585/P580), never from the LLM's memory; optional `stamp` | Procedural paper. The date in a display serif at 180–260 px with a mask reveal (translateY 110%→0, cubic-bezier(.16,1,.3,1), 500 ms, 60 ms word stagger); the place in letter-spaced caps; optional faint map silhouette; hold ≥ letters/15 + 1.5 s | iart kinetic type; lemo DIRECTOR §7; paper-collage visual-sfx |
| 6 | `map` (modes `locator` / `route` / `spread`) | The place matters and there's no local image; journeys, voyages, spreads, "how far" | `places: [{name, qid}]` with coordinates from Wikidata P625; `mode`; `zoom` world / country / region / city; `on_word` per place | Natural Earth drawn as an old atlas: paper land, 2–3 px ink coast, toned or hatched sea. Projection fitted to the safe box (Mercator for city and region, Equal Earth for world). Camera eases in. Pin spring (12/120) on its word. Great-circle route (n=40) drawn with dash-offset in the accent colour, with a travelling dot. Labels counter-scaled. Overlays at 12 fps, camera smooth. Before 1900, skip modern borders or label them "present-day borders" | iart `vector-maps.md` L13–104; route-map-video; documentary-remotion; lemo watercolor map |
| 7 | `newspaper` (`scan` / `recreation`) | The press covered it (Hoaxes, Wait That Happened?, Trials): the headline is both proof and hook | `scan`: file (PD) plus `headline_box` cells. `recreation`: verbatim `headline`, `paper`, `date`, `source_url`; never invented | Scan: card treatment, push to the headline cells, then a yellow highlighter wipe (multiply, 0.35 s) or red circle; hold ≥5 s after entrance. Recreation: procedural newsprint, UnifrakturMaguntia masthead, condensed caps headline, halftone photo plate, greyed column texture, 1–2 px misregistration, a "RECREATION" tag | vox newsprint-editorial; lemo `halftone()`; mono-color plate roles; simon evidence timing |
| 8 | `quote` | Research holds a verbatim quote from a judge, hoaxer or reporter. At most 1 per Short | `quote` (≤20 words, verbatim), `speaker`, `year`, `source_url` | Paper card in typewriter or serif italic, with words revealed on Kokoro word timestamps. Large accent-colour quote marks; speaker in small caps with an optional mini cut-out. **Burned-in captions are hidden while the card reads** (the card *is* the caption) | remotion-bits TypeWriter; lemo intertitles and "cards are the subtitles"; iart stagger |
| 9 | `counter` | A number is the point ("2.3 million gallons", "38 minutes", "$14,000") | `value`, `unit`, `from` (default 0), optional sourced `compare`, `on_word` | A 300–500 px numeral, flat fill overprinted with a halftone clipped to the glyph, counting up with an ease-out over 0.8–1.2 s so it lands on the word; unit in small caps; optional row of repeated icons; digits stepped at 12 fps | remotion-bits AnimatedCounter; paper-collage numeric-counter; lemo halftone numerals |
| 10 | `timeline` | Durations, sequences, before and after ("the 335-year war") | `events: [{year, label ≤3 words}]` from research; `focus` index | A rule across paper with ticks and dots (focused dot larger), labels alternating above and below. Camera pans left → right, always the same direction. The focus event pops; only the focus gets the accent | paper-collage `EditorialNodes.tsx` L337–384; vox timeline rhythm; awesome-opus history corpus |
| 11 | `illustration` (reconstruction) | The moment itself was never photographed (the tank bursting, a courtroom outburst). At most 2 per Short; never realistic faces of real people | `scene`: one moment, one subject, one action, period details. **The style block is fixed in code, not written by the LLM** | FLUX.1-schnell on Workers AI (already in `visuals.py` `_ai`, L353–361) with one fixed engraving block ("19th-century wood engraving, black ink cross-hatching on cream paper, no text, no colour"), then Redraw (XDoG + 5-step wash + hatch), then treated as a card. In-frame label "ILLUSTRATION" | vox style block verbatim; lemo `redraw.js` L46–85; simon AI label |
| 12 | `stamp` (verdict overlay) | The payoff word: HOAX, GUILTY, ACQUITTED, BANNED, BACKFIRED, MYTH, TRUE. One per Short, on the static payoff shot | `word` (1–2 words), `on_word` | A double-bordered vermilion rubber stamp with a noise-thresholded ink mask, tilted −10° to +12°. Slams in 0.09 s from 2.6× to 1×, then a 5% damped bounce, a 16 px shake decaying over 0.3 s, a flash ≤0.5, and the stamp SFX | lemo halftone-dossier `stampEl`/`stampAnim`; paper-collage visual-sfx |

**Loop rule (not a shot type).**
- The last shot returns to frame 0's composition: same image, same card placement. This matches vox `loop_close` and iart's loop sentence.
- Frame 0 is the most striking shot, with hook text already on screen. No fade-in.

### Scene schema (extends `short.yaml`)

```yaml
beats:
  - text: "In 1919, a wave of molasses swept through Boston."
    shots:
      - kind: card
        source: commons
        query: "Great Molasses Flood 1919"
        focus_x: 0.45
        focus_y: 0.40
      - kind: detail
        detail: "B3:C4"          # 6x6 grid cells on the chosen image, from the vision picker
        mark: circle
        on_word: "molasses"
    transition: cut              # cut | slide | page_turn | dip | iris | impact
  - text: "Boston, January 15th, just after noon."
    shots:
      - kind: dateline
        place: "Boston, Massachusetts"
        date: "1919-01-15"
        source: "https://www.wikidata.org/wiki/Q1129089"
      - kind: map
        mode: locator
        zoom: city
        places: [{name: "North End, Boston", qid: "Q1129089"}]
    transition: slide
```

**Choosing shots.** These rules go in `SCRIPT-RULES.md` and are checked by a validator.
- **Beat 1:** a `card`, `cutout` or `newspaper`, with the hook text visible at frame 0.
- **First mention of a place or time** → `dateline` or `map`. **Movement or spread** → a `map` route.
- **A number that is the point** → `counter`. **A verbatim quote in research** → `quote` (at most 1). **Press coverage in research** → `newspaper`.
- **The moment with no photo** → `illustration` (at most 2). **The payoff word** → `stamp`.
- **Otherwise** → `card` followed by `detail`.
- **Constraints:**
  - At least 4 distinct kinds per Short.
  - No more than 2 consecutive picture shots without a detail or data shot.
  - At most 2 `depth` shots.
  - Every fact field (date, coordinates, number, quote, headline) must match a source in the research notes, or the shot falls back to a card.
  - Shots last 2.0–4.5 s.
  - Any on-screen text holds at least max(1.8 s, letters/15 + 1.5 s) after its reveal.
- **Camera moves.** The renderer assigns them, not the LLM:
  - Rotate through the families scale (push/pull), translate (pan/tilt/drift) and static, so adjacent shots never share a family.
  - `stamp` and payoff shots are static.
  - Timeline beats pan the same direction.
  - This replaces the aspect-ratio rule in `pick._motion` (`pick.py` L196).

### The house look: "The Odd Archive"

- **Palette tokens.** Taken from paper-collage's archival profile and lemo:
  - ink `#26211D`, dark ground `#342D27`, mid `#756552`;
  - paper `#F3E8D0`, generated procedurally, never copied textures;
  - **one accent, vermilion `#C8502A`**, with one role only: marks, routes, stamps and the caption keyword;
  - highlighter `#FFC628`, only for newspaper highlights and the caption highlight.

  No cyan, no neon, no gradients.
- **Grade (every image, every source).** A FilmPost-style print:
  - old photos go fully monochrome; colour sources keep 10–20% of their hue;
  - sepia 0.15–0.25, black .055, white .93, and a gentle S-curve.
  - Optionally, the one-colour mask keeps the key subject's hue.
- **Texture.**
  - Procedural paper (lemo's `buildPaper` recipe) multiplied at about 0.14 on grounds and cards.
  - **Grain once, in the final FFmpeg encode** (`noise=c0s=2:allf=t`; try 3–4 for archive-heavy Shorts), not in the frame renderer.
  - Flicker ±2% and weave ±1 px on photo layers only; sparse dust; a vignette.
  - Never damage or "boil" text.
- **Typography.**

  | Use | Font | Licence |
  |---|---|---|
  | Dates, headlines | Old Standard TT | OFL |
  | Newspaper heads, counters (condensed caps) | Oswald, Anton | OFL |
  | Documents, quotes | Special Elite | Apache-2.0 |
  | Source chips, labels | IBM Plex Mono | OFL |
  | Mastheads | UnifrakturMaguntia | OFL |

  - Captions stay Montserrat Black for legibility.
  - Change the caption accent from cyan `#00E5FF` to vermilion and the highlight from `#FFD400` to `#FFC628` (`spec.py` `CaptionStyle`, L54–65).
- **Transitions by intent** (paper-collage):
  - default: a hard cut on the beat;
  - `slide` with a paper edge (0.45 s) for continuity;
  - `page_turn` (0.7 s) or a `dip` to paper (0.5 s) for time passing;
  - `iris` (0.55 s) into a detail;
  - `impact`: a cut plus a stamp or shake.
  - **No crossfades.** The whoosh in `SFX_PLACEMENT` (`render.py` L29) attaches to slides and page turns; the stamp gets its own SFX.
- **Motion.**
  - Cameras and cards move smoothly at 30 fps. Overlays (pins, marks, digits, stamps) may step at 12 fps.
  - Entrances use bezier(.18,.8,.22,1); punch-ins use spring(13, 220); pops use a back overshoot.
  - Pieces arrive in the order structure → subject → mark (gbro's "assemble from empty").
- **Safe zones.**
  - Key content stays inside the 900×1400 box at (90,260).
  - The caption band (y ≈ 0.60·H ± 150 px) stays clear of labels and pins.
  - No information in the top 120 px or bottom 300 px.
- **Honesty labels.**
  - "ILLUSTRATION" on generated images and "RECREATION" on typeset clippings.
  - A source chip on archive cards, which is also the on-screen credit for CC BY.
  - "present-day borders" on modern maps.
  - Stylized engravings are not realistic, so `synthetic_media` stays false, but the label keeps trust.
- **Series accents (later, same house look).**
  - Hoaxes and Trials get the dossier HUD: case number, "EXHIBIT A" chips and the verdict stamp.
  - History Got It Wrong gets MYTH/FACT stamps.

### Rendering on Modal
- **One Python frame engine**, say `shots.py`.
  - Each kind is a function `(shot, assets, t) → RGBA frame` over layers precomputed once.
  - Frames are piped as rawvideo to ffmpeg for each shot (the vox `motion.py` pattern), then joined by the existing `_concat` (`render.py` L77).
  - Transitions are short rendered overlap segments.
  - Dependencies: Pillow, NumPy, OpenCV and onnxruntime. **Their licences should be re-checked before adding; I didn't verify them in this pass.**
- **Estimated cost.**
  - 45 s × 30 fps is 1,350 frames. With precomputed layers, each frame is a few affine warps and alpha blends, roughly 10–30 ms on one core at 1080×1920. That's about 0.5–1 CPU-minute per Short.
  - Add Redraw and the grade once per image, and depth once per depth shot (~1–3 s each).
  - Roughly a cent per Short at Modal's CPU list price. **This is an estimate, not a measurement.**
- **Optional Chromium path** for richer type and maps, as lemo and simon do it: a `render(t)` page, Playwright, JPEG capture, one browser per worker, and a `framemd5` determinism check. It sidesteps the Remotion licence question.
- **Review.** Overlay the 6×6 grid on the Gemini contact sheet. Ask for ≤3 layout problems by cell, plus "does each shot kind fit its line?" (Code2Video).

---

## Top insights for Days of Odd

1. **Two shots per beat, with a vision-picked detail.** Effort S–M.
   - The picker returns grid cells for the detail the line names, and the renderer punches in on it with a mark.
   - It cuts every 2.5–4 s, and the detail shot reuses the image already picked, so no extra searches.
   - This is the biggest single lever against "static slideshow" and "picture doesn't match the line".
   - Sources: vox `SKILL.md` L61–62, L132–139; Code2Video `prompts/stage3.py` L16–32; iart `retention-pacing.md` L41.
2. **The archive card is the default for every real image.** Effort M.
   - Blurred self-background, tilted torn card, outline, shadow and a source chip.
   - It fixes the wide-photo crops that lose the subject, makes old images look designed, and puts the CC BY credit on screen.
   - Sources: simon `index.jsx` L7–15; vox `kenburns.py` L50–63; paper-collage `catalog.json`.
3. **One house print pass over every source.** Effort M.
   - Grade, procedural paper, grain in FFmpeg, and flicker only on photos.
   - Commons photos, Met paintings and FLUX illustrations then read as one film.
   - Sources: lemo `engine/film.js` L15–95 and `core/render/mux.sh` L9.
4. **Draw the fact when there's no true picture.** Effort M–L.
   - Datelines, maps, counters, timelines and quotes, filled from research, Wikidata (CC0) and Natural Earth (public domain), both verified.
   - These shots can't be "the wrong period", which is the root of 14 of 15 visual rejections.
   - Sources: iart `vector-maps.md`; kinetic-typography `SKILL.md`; paper-collage `EditorialNodes.tsx`.
5. **Illustrations only in one fixed engraving style.** Effort M.
   - Run them through Redraw and label them. This finally puts the existing FLUX path (`visuals.py` L353–361) to work for beats with no archive image, without realistic fakes.
   - Sources: vox `styles.py` and `prompt-guide.md`; lemo `redraw.js` L46–85; simon's AI label rule.
6. **Rhythm and transitions as code.** Effort S.
   - Adjacent shots never share a camera-move family; the payoff is static; transitions follow intent (cut, slide, page turn, iris, impact); no crossfades.
   - This replaces `pick._motion` (`pick.py` L196) and `_image_motion` (`render.py` L39–48).
   - Sources: vox `beat-layer.md` L111–120; paper-collage `motion-directing.md` L286–303.
7. **Reveal on the word.** Effort S once the shots exist.
   - Pins, marks, counters and stamps fire on the Kokoro word timestamps of the thing named.
   - Sources: route-map-video `SKILL.md`; documentary-remotion `STORYBOARD.md`; lemo's "one timeline drives picture, sound and captions".
8. **Readability and safe-zone validators.** Effort S.
   - Text holds at least max(1.8 s, letters/15 + 1.5 s), and evidence at least 5 s after its entrance.
   - The 900×1400 safe box; the hook on frame 0; captions hidden under quote cards; the caption accent changed from cyan to vermilion.
   - Sources: lemo `DIRECTOR.md` §7; simon `SKILL.md` L65–68; iart `retention-pacing.md` L18–54, L134–135.
9. **Grid-referenced visual QA.** Effort S.
   - Overlay A1–F6 on the Gemini contact sheet and ask for ≤3 problems by cell, plus a "shot fits the line" check.
   - Source: Code2Video `src/agent.py` L402–449.
10. **A 2.5D depth push for at most 2 wide scenes per Short.** Effort S–M.
    - Depth-Anything-V2-**Small** ONNX (Apache-2.0) plus `cv2.remap` with feathered edges, ported from parallax-studio (MIT, `app/core/animator.py` L182–226).
    - Licence trap: the Base, Large and Giant weights are CC BY-NC 4.0, so never use them.
    - DepthFlow (AGPL) is only an option as a separate GPU tool.
