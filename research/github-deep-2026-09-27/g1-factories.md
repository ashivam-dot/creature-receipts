# G1: "topic in, finished Short out" factories (small-to-mid, recent)

Studied 2026-09-27. All ten repos were cloned shallowly to `/tmp/ghdeep/g1/<repo>` and read at code level
(prompts, planners, renderers, mixers). Nothing was installed or run. Stars, forks, dates and archive status come
from `gh repo view` today; the license column comes from the LICENSE file in each clone, not the GitHub badge.

| # | Repo | Stars (forks) | Created, last push | LICENSE file | Archived | Verdict |
|---|---|---|---|---|---|---|
| 1 | hassancs91/claude-faceless-shorts-creator | 269 (100) | 2026-07-15, 2026-08-18 | MIT | no | BORROW IDEA |
| 2 | tsensei/OpenReels | 199 (42) | 2026-03-28, 2026-04-10 | MIT | no | BORROW IDEA (port the verifier) |
| 3 | igennova/ZeroCost-Shorts | 74 (22) | 2026-04-15, 2026-08-03 | none (all rights reserved) | no | SKIP |
| 4 | Agent-Field/reels-af | 115 (37) | 2026-05-31, 2026-06-05 | Apache-2.0 | no | BORROW IDEA |
| 5 | gongnyang/reelforge | 82 (21) | 2026-07-06, 2026-07-30 | Apache-2.0 (+ NOTICE) | no | BORROW IDEA; WATCH HyperFrames |
| 6 | gyoridavid/short-video-maker | 1,379 (433) | 2025-04-14, 2025-06-21 | MIT | no | SKIP |
| 7 | IgorShadurin/app.yumcut.com | 885 (139) | 2026-02-13, 2026-09-03 | PolyForm Noncommercial 1.0.0 | no | SKIP |
| 8 | SaarD00/AI-Youtube-Shorts-Generator | 227 (62) | 2025-12-24, 2026-06-26 | MIT | no | SKIP (one idea) |
| 9 | feyzilim/clipfactory | 105 (13) | 2026-08-22, 2026-08-23 | Elastic License 2.0 | no | BORROW IDEA (shot planner) |
| 10 | Dark2C/Viral-Faceless-Shorts-Generator | 112 (32) | 2025-05-28, 2026-05-10 | none (all rights reserved) | no | SKIP |

Baseline we compare against (CONTEXT.md and our code): one still per beat, so a picture stays on screen for 5–8 s.
`pick.py` has a vision LLM rank 330 px thumbnails for all beats in one call, using Best/Good/Acceptable/Never tiers
(`PICK_PROMPT` at l.46; `THUMB_WIDTH=330` at l.16). Fallbacks are `_reuse_of` (the nearest earlier picture, l.300)
or a gradient (`visuals.py`). `render.py` does a `zoompan` up to 1.12x (l.39–48) and joins shots with hard cuts
via concat (l.77). SFX gains are fixed (l.29) and there is no music. `studio.py` renders up to 3 rounds. It rejects
the Short on the third failure, and any story fix re-picks every picture (l.310–340).

---

## 1. hassancs91/claude-faceless-shorts-creator: MIT, 269 stars, pushed 2026-08-18

**What it is.** A Claude Code agentic workflow: skills, a Remotion TSX kit, and Python mixing tools. It is not an
unattended pipeline. Claude hand-writes one TSX file per Short, and the skills stop at user audit gates. There are
three tracks:
- `make-short`: pure motion graphics.
- `make-ai-short`: fal video (paid).
- `make-vox`: Vox-style paper collage from AI images and cutouts.

Voice is ElevenLabs `/with-timestamps`, which is paid; its free tier is non-commercial.

**Stages and key files**
1. **Script.** Beat grammar in `.claude/skills/make-short/SKILL.md` l.38–51: HOOK (0–3.4 s, "frame 0 FULLY composed —
   the payoff already visible"), SETUP, QUIZ, REVEAL "in 2–4 steps, each synced to a VO word", TWIST, and LOOP
   ("last frame == frame 0"). There is no CTA outro, and the pace is about 2.7 words per second.
2. **Voice and timing.** Every visual cue is retimed to real word starts. Example from
   `remotion/src/shots/vox-1/Vox1Coffee.tsx` l.41–47: `ethChip: 165 // "Ethiopian" 5.49s` and
   `stamp: 626 // "banned" 20.88s`.
3. **(a) Visuals.** Scenes are designed rather than searched:
   - Gemini image presets with sidecar JSON (`tools/gen_image.py`).
   - rembg cutouts (`tools/cutout.py`: u2net or white-key, erode 1 px, feather, trim).
   - Maps from public-domain Natural Earth data (`shorts/short-11-map/script.md`).

   Many layer events happen per beat. The Vox coffee Short has 11 camera keyframes over one board, about one camera
   move every 3–4 s.
4. **(b) Motion** (`remotion/src/lib/collage.tsx`). Most of the valuable craft is here:
   - **Camera and parallax.** Camera keyframes `{f,x,y,z}` eased with `EASE_INOUT = bezier(0.42,0,0.24,1)` (l.24,
     45–47), rendered as `scale(zoom) translate(W/2/zoom − camX, H/2/zoom − camY)`. Each layer adds parallax with
     `translate(−offX·depth, −offY·depth)`.
   - **Idle drift** (l.91–92): "every layer breathes, nothing ever fully freezes".
     `dx = sin(f·0.021+seed)·2.2·drift`, `dy = cos(f·0.017+seed·1.7)·2.6·drift`,
     `dr = sin(f·0.012+seed·0.6)·0.45·drift`.
   - **Entrances.**
     - pop: scale 0.55→1.
     - place: scale 1.28→1 with rotation ±7°→0, eased with `EASE_PLACE bezier(0.22,1.2,0.36,1)`, a soft overshoot (l.25).
     - Also slide-l/r, rise (90 px), wipe (clip-path) and fade.
   - **Archival photo** (l.201): filter `grayscale(1) sepia(0.42) contrast(1.06) brightness(0.97)`, with a cream
     border, tape, a caption and a −2° tilt.
   - **Grain** (l.262): SVG `feTurbulence` fractalNoise at 0.9, re-seeded every 2 frames, multiplied at 5% opacity.
   - **Text and marks.**
     - `SerifStatement` (l.323–351): staggered words with a highlight sweep, plus cream backing strips, which are
       "REQUIRED over busy layers".
     - `RubberStamp`: scale slams from 2.1 to 1.
     - `SketchArrow`: the path draws itself on.
     - `LabelChip`: a kicker plus text.
5. **(c) Captions** (`remotion/src/lib/shorts.tsx` l.11–13, 72). Chunks of 4 words or fewer, active word in
   `#f5d76e`, default y 1280. `SAFE = { top: 150, bottom: 500, right: 160, left: 60 }`, with the comment that
   captions "must sit ABOVE ~y1420". Also includes a ProgressBar, Kicker and BigTitle.
6. **(d) Sound**
   - **Gain calibration** (`brand.md` §7, `.claude/skills/suggest-sfx/SKILL.md` l.95–98): the SFX library is
     normalised to about −20 LUFS with a −1.5 dBFS ceiling. Their verdict: "a conservative gain table runs 4–8 dB too
     quiet — start at transitions/whooshes **−3**, story pops/impacts **0..+3**, stamps/snaps **0..+7**, layered-hero
     risers **0..+2**."
   - **Audibility check** (l.69–87): "RMS-diff the mixed audio vs the voice-only preview at each cue window: a
     story-critical cue should add **≥ +4 dB**, texture +1–3 dB." Percussive clips need about 3–5 dB more gain.
     Measure with tight windows of about 0.3 s, and measure a riser in its final third.
   - **Music bed** (`tools/mix_music.py` l.86–95): `highpass=f=90, volume≈−7 dB, afade 1.5 s`, then
     `sidechaincompress threshold=0.03 ratio≈3 attack=15 release=450`, then `alimiter`.
   - **SFX ducking** (`tools/mix_sfx.py` l.157): `threshold=0.15 ratio=2 attack=5 release=200`, then `alimiter 0.97`.
7. **(e) QA.** Stills are rendered at beat boundaries and hero frames at 0.5 scale
   (`node scripts/frames.mjs … --scale=0.5`, make-short SKILL.md l.72–73). Claude reads every PNG, then the user
   approves. There is no automated scoring.
8. **(f) Prompts.** `make-vox/SKILL.md`:
   - l.43: "A scene is 2–6 layers; if you can't name the layers, the scene isn't designed yet."
   - l.51: "Maps/archival: prompt 'NO text, no labels' — AI text is gibberish; chips annotate instead."
   - l.67: annotation positions are fractions of the layer (`mapPt(0.24, 0.52)`), so regenerating the art doesn't
     break them.

**Better than ours:**
- Designed scenes (collage, documents, maps) exist for lines that have no photo.
- Nothing is ever static.
- SFX audibility is measured.
- Frame 0 is the hook.

**Worse:**
- It needs a human and a coding agent per Short.
- Voice, images and video are all paid.
- It uses Remotion, which is free only for individuals and companies of 3 or fewer. Remotion also brings a
  Node + Chrome render stack.

**Adopt (ideas, ported to FFmpeg/Pillow or HyperFrames):**
- (1) Archive treatment for black-and-white stills: sepia curve, grain (`noise=alls=…:allf=t`), a small idle drift.
  Effort S, $0. Risk: sepia on colour paintings looks wrong, so apply it only to black-and-white photos.
- (2) SFX audibility check in `check.py`. Effort S, $0.
- (3) Label chips, stamps and highlight sweeps as overlays. Effort M in Pillow/FFmpeg. Cap them at 2 per Short;
  overuse looks cheap.

**Verdict: BORROW IDEA.** It has the best designed-shot vocabulary and the only measured SFX loop. The code itself
is Remotion TSX with paid APIs and human gates.

---

## 2. tsensei/OpenReels: MIT, 199 stars, pushed 2026-04-10

**What it is.** A tested TypeScript pipeline with a CLI and web UI:
1. research (Tavily);
2. a creative director writes the DirectorScore JSON;
3. a critic grades it;
4. TTS plus whisper alignment;
5. visuals and music run in parallel;
6. Remotion renders.

**Stages and key files**
- **(a) Visual type.** The creative director picks a `visual_type` per scene from ai_image, ai_video, stock_image,
  stock_video and text_card (`prompts/creative-director.md` l.14, 29). There is one visual per scene; scenes run
  3–12 s. Pacing tiers (l.44–46) are fast (8–12 scenes), moderate (7–10) and cinematic (5–8).
- **(a) Verification** (`src/providers/stock/stock-verifier.ts` l.25–35, 106):
  - The prompt: "Be strict: A toy rocket does NOT match 'rocket launch'; A generic sunset does NOT match 'Mars
    surface'; A cartoon illustration does NOT match a request for real footage; A loosely related image is NOT a
    match … Judge the SEMANTIC match … Ignore aesthetic quality."
  - Confidence bands: 0–0.3 clearly wrong, 0.3–0.6 loosely related, 0.6–0.8 reasonable, 0.8–1 strong.
  - Output is `{relevant, confidence, reason}`. A candidate passes when `relevant && confidence ≥ threshold`.
    Videos are judged on the frame at 1 s.
- **(a) Resolver** (`src/providers/stock/adaptive-resolver.ts` l.55, 107–153, 211, 243–245):
  1. Try the original query on each provider. Verify the top 3 image candidates (1 for video), downloading each only
     when it is about to be verified, and keep the highest confidence.
  2. If all are rejected, reformulate the query and retry (`query-reformer.ts`: 2–3 queries of 3–5 words, most
     specific first; it strips proper nouns).
  3. Then fall back to an AI image built with negative examples: *"Stock footage search failed. Rejected
     results:\n"<query>" returned: <reason> (confidence: x) … Generate an image that matches the original request,
     avoiding what the stock results showed."*

  Every attempt is logged.
- **(a) Variety.** `src/schema/director-score.ts` l.49–62 has a zod refinement: "Golden rule: no more than 2
  consecutive scenes of the same visual_type".
- **(b) Retention.** `prompts/playbook.md` l.86–88: "At the 5s, 15s, and 30s marks, a new scene must begin OR a
  surprising fact/visual contrast must be introduced." "Never exceed 12 seconds on a single visual."
- **(b) Motion.**
  - `AIImageBeat.tsx` scales 1→1+0.15·intensity, or pans ±50 px at 1.15.
  - `TextCardBeat.tsx` is a spring scale-in.
  - `TransitionSeries` handles transitions. Their meaning is fixed in `creative-director.md` l.19–23: crossfade for
    "reflective moments", slide_left for "forward progression", slide_right for "contrast, flashback, 'but
    actually'", wipe for a "new chapter", and flip "sparingly for dramatic reveals only".
- **(c) Captions and ending.** There are 7 caption styles. A final CTA scene is required (l.55), which is the
  opposite of our loop ending.
- **(d) Music.** `assets/music-manifest.json` lists 25 tracks, all under the "Pixabay License". That is outside our
  media rule and carries a Content ID risk. `MusicTrack.tsx` plays at a flat 0.15 with no ducking, and there is no
  SFX layer.
- **(e) QA.**
  - The critic grades only the plan JSON, with weights Hook 20, Arc 20, Pacing 15, Variety 15, Sync 10, Style 10,
    CTA 10, and a pass mark of 7. Nothing checks rendered frames.
  - `src/pipeline/orchestrator.ts` l.490–521 sets `MAX_REVISION_ROUNDS = 2` and "Tracks the highest-scoring revision
    (LLM refinement can degrade in later rounds)".
- **(f) Prompts.**
  - `prompts/image-prompter.md` rule 9 (l.27): *"Depict dark themes through atmosphere, not graphic content … Instead
    of 'a terrified patient with a bowl collecting blood', write 'a physician in a dim candlelit chamber, medical
    instruments on a wooden table, patient resting on a cot, heavy shadows'. Show the setting and tension, not the
    act."*
  - There are 14 style bibles in `src/config/archetypes/*.json`, with fields artStyle, lighting, compositionRules,
    culturalMarkers, mood, antiArtifactGuidance and visualColorPalette, plus transition and caption presets.
    Relevant ones: `cinematic-documentary.json` and `vintage-snapshot.json`.

**Better than ours:**
- Strict per-candidate verification with reasons.
- Rejections feed the next attempt.
- The variety rule is enforced in code.
- It keeps the best revision, not the last.

**Worse:**
- Its imagery is generic stock plus AI.
- The query reformer strips proper nouns, the opposite of what archive search needs.
- Pixabay music.
- No check of the rendered output.
- A CTA ending.

**Adopt:**
- Port the verifier and resolver loop to Python in `pick.py`. This is code-level (MIT), about 150 lines of TS.
  Effort M. Cost is about 1 free-tier Gemini Flash call per beat and $0 on Modal. Details are in insight 1 below.
- Port best-round keeping into `studio.py`. Effort S.
- Add the variety rule to our spec validator. Effort S.

**Verdict: BORROW IDEA.** The verifier and resolver are exactly the missing piece in our picker.

---

## 3. igennova/ZeroCost-Shorts: no LICENSE file, 74 stars, pushed 2026-08-03

**Pipeline**
1. Groq llama-3.3-70b writes one narration plus 5–6 image prompts (`pipeline/groq_script.py`).
2. The DeAPI `Flux_2_Klein_4B` model generates 768×768 images (`pipeline/images.py`). The README says HuggingFace,
   which doesn't match the code.
3. Edge TTS provides sentence timings.
4. SRT captions use proportional timing, not word alignment (`captions.py`).
5. `render_short.py` letterboxes the square images with scale+pad, alternates a 0.08 zoompan, and joins with a 0.5 s
   fadeblack xfade.

**Observations**
- Each picture stays up for about 8–10 s.
- No music or SFX.
- No QA.
- One reusable idea: `story_history.py` injects the last 50 titles as an anti-repeat block.
- The facts preset asks for "photorealistic documentary photography … National Geographic style" with no AI
  disclosure. That would be a credibility problem for us.

**Verdict: SKIP.** It is worse than ours at every stage and has no license.

---

## 4. Agent-Field/reels-af: Apache-2.0, 115 stars, pushed 2026-06-05

**What it is.** A showcase for the AgentField framework. The pipeline:
1. extract the article;
2. angle hunters propose angles, and a critic picks;
3. the narrator writes 2–3 scripts;
4. a pairwise judge chooses one;
5. a visual agent prompts one image per beat (Gemini 2.5 Flash Image, optional Veo);
6. an accent agent adds overlays;
7. a card planner builds subtitles;
8. FFmpeg stitches, with a 1.06 Ken Burns fallback.

The stack is paid: OpenRouter, Gemini image and Veo.

**Stages and key files** (`src/reel_af/`)
- **(f) Angles.** `agents/hunters.py` runs four hunters (specific_figure, reversal, temporal, cross_domain) at
  temperature 1.1 with an anti-cliché block. Evidence must name a person and a year. `agents/critic.py` scores
  novelty, specificity, hookability and narratability, then picks a diverse top 3.
- **(f) Script** (`agents/narrator.py`):
  - l.23–27: "THE ONE BIG RULE: THE HOOK DOES NOT REVEAL THE ANSWER … The answer comes 8-15 seconds in."
  - l.118: "The payoff's last few words should echo a distinctive word from the tease", which creates the rewatch loop.
  - l.161–162: "Each comma adds ~200ms of silence; each em-dash ~300ms; each period ~400ms. Audit your narration: if
    it has more than ~6 commas across 50 [words] …"
- **Judge.** `agents/judge.py` l.4: "LLM judges are much better at 'A or B?' than at 'is this a 7 or an 8?'" Its
  priorities, in order: hook, specificity, loop-back, trope avoidance, flow, stakes.
- **(a) Visuals** (`agents/visual.py`). One visual per beat; Veo clips come in 4, 6 or 8 s buckets
  (`planning/beats.py`). Rules by beat role:
  - HOOK: the most arresting image, with "one unexpected element" (l.16, 68).
  - PAYOFF: "Visually CALLBACK the hook" (l.21).
  - MECHANISM: "Illustrate concretely WHAT THIS NARRATIVE LINE SAYS. Not mood."
  - Evidence: "visual_anchor MUST be one of the evidence items … copied verbatim" (l.75).
  - Layout: "negative space upper-center" for subtitles (l.118).
- **(b/c) Accent overlays** (`agents/accent.py` l.22–74):
  - "THE DEFAULT IS emit_overlay=false. Most beats will not emit."
  - Six allowed patterns: number, named_entity, jargon_translation, hook_title_card (hook beat only), reaction and
    list_marker.
  - Text is 2–6 words, and the renderer uppercases it.
  - The overlay has to add information the viewer needs that the voice does not state outright (paraphrased).
- **(c) Captions.**
  - `planning/cards.py` l.5–26: a card holds at most 5 words and at most 1.9 lines of measured width. It breaks at
    gaps over 0.20 s, or at clause punctuation once it has 2 or more words. A trailing single-word card is folded
    into the previous one.
  - `planning/safe_zone.py` l.17–47: margins are 480 px at the bottom, 140 px on the right and 200 px at the top.
    Subtitles sit at 35% of the height (about 672 px). Accents sit at 62% (lower) or 22% (hook card) at 110 px,
    1.4× the subtitle size.
- **(d) and (e).** No music, no SFX, and no post-render QA.

**Better than ours:**
- The hook discipline.
- The pairwise judge.
- Overlays that default to none.
- Visuals anchored to evidence copied verbatim.

**Worse:**
- Paid, generated visuals.
- No archive sources.
- No QA.

**Adopt:**
- Pairwise choice between our 3 hooks or 2 drafts in `writer.py`. Effort S; +1 LLM call.
- Add "echo a distinctive hook word in the payoff" to SCRIPT-RULES. Effort S.
- Accent overlays as a second ASS style. Effort S–M.
- Put the claim's named entity and year verbatim into the per-beat visual queries. Effort S.
- Risk: the delayed-reveal hook conflicts with our "state the oddity in 12 words or fewer" rule. A/B test it on
  one series rather than switching.

**Verdict: BORROW IDEA.**

---

## 5. gongnyang/reelforge: Apache-2.0 + NOTICE, 82 stars, pushed 2026-07-30

**What it is.** A Korean-first, agent-driven motion-graphics factory built on HyperFrames 0.7.26 (Apache-2.0, HTML
plus GSAP to video). GSAP is vendored under GreenSock's "no charge" standard license.

The stack is free:
- edge-tts, an unofficial service, with a MeloTTS fallback.
- Images through an external "codex-imagegen runner": the pipeline writes `prompts.jsonl` and waits. In practice
  that depends on a Codex subscription.

The pipeline runs `tts → images → compile → render → gate`, with input hashes, resume state and locks.

**Stages and key files**
- **(f) Direction first.** `skills/reelforge/SKILL.md`: "never a slide deck … If a frame reads as a presentation
  slide, the scene fails." The D1 concept names "one named visual event per scene" and is written before any copy.
  A pilot gate runs on scene 1. Scene workers adapt gallery fragments ("No blank-canvas authoring").
- **Routing grammar** (`references/gallery/ROUTING.md`, in Korean). §0 has arc presets for scene intensity from 0 to
  100; for example ramp runs hook 15–30, build 35–55, peak 75–95, resolve 35–50. §A maps an intent verb (declare,
  enumerate, contrast, data, hard transition, linger, CTA) and an intensity band to technique IDs.
  - **§C budgets:**
    - peak-band effects appear only 1–2 times per video;
    - whip-pans and speed ramps must be outnumbered by calmer transitions;
    - light-flash is used only at chapter boundaries;
    - a scene emphasises one target;
    - "converge a sequence on 2–3 transition types".
  - **§D combination rules:**
    - one camera move per scene;
    - no ambient drift during an active camera move;
    - motion-vector inheritance (exit left, enter from left);
    - overshoot easing never on opacity.
- **(b) Pacing** (`references/design-direction.md` §4 l.74–97):
  - **Scene count.** 30 s means 7–10 scenes, averaging 3–4 s, with **12 cuts at most**. Alternate 2–2.5 s scenes
    with 4–5 s number or quote scenes, and never use the same layout 3 times in a row.
  - **Open and close.** The strongest visual appears **within 1.8 s**, and the last 3 s pay off the promise.
  - **Transitions.** Default to a cut. Use slide or wipe (0.2–0.25 s) only at chapter boundaries, and at most 1–2
    crossfades per 30 s, each 0.5 s or shorter.
  - **Reading time** = 0.5 s + characters/12, plus 0.4 s per extra unit. On-screen text stays between 20 CPS maximum
    and 0.83 s minimum.
  - **Motion budget.** Motion budget = scene length − reading time; below 0.8 s, use a fade-in only. "If copy is
    long, give up the motion."
- **13 amateur tells** (`references/strip-qc.md` l.16–23):
  - freezing after the entrance (every scene needs a "Develop" stage that refreshes every 2–4 s);
  - uniform easing;
  - no stagger;
  - ease-in entrances;
  - bounce beyond `back.out(1.7)`;
  - more than 12 cuts per 30 s;
  - reading-speed violations;
  - filter tweens;
  - more than one accent colour family;
  - crossfades over 0.5 s;
  - drop shadows on a dark canvas;
  - more than 1 primary motion plus 1 drift at once;
  - no hook within 1.8 s.
- **(e) Automated frame QC** (`scripts/craft-contact-sheet.mjs` l.58–63, 392–456). It samples frames at 0.6, 2.0 and
  3.6 s into each scene and applies four tests:
  - **Blank:** luma standard deviation must exceed 15, with luma = `(54R+183G+19B)>>8`.
  - **Empty centre:** the central 60% needs at least 400 edge pixels.
  - **Low contrast:** local contrast `(hi+0.05)/(lo+0.05)` at the 84th percentile must be at least 3.0.
  - **Frozen:** comparing t=2.0 with t=3.6 at 160×90, the mean absolute difference must be at least 0.35 and the
    changed-pixel ratio at least 0.003.

  Supporting pieces:
  - `src/gates/p5-common.mjs` l.240–265 samples a frame every 2 s plus one seeded-random frame per scene, keeping
    clear of the scene edges by 12% (clamped to 12–45 frames).
  - EasyOCR checks that subtitle boxes stay inside the safe zone.
  - `src/compiler/render-lint.mjs` has RF-* lint rules with fix hints.
  - The strip pass (SKILL.md l.96–101) runs `ffmpeg -i draft.mp4 -vf "fps=1,scale=480:-1" strip/f%02d.png`.
    "Blank frames, low contrast, and frozen motion after entrance fail automatically", and failing scenes are
    re-dispatched with the reason, at most 2 rounds per scene.
- **Blocks and fragments.**
  - Blocks: bar, compare, line, list, numbered, pie, quote, statistic.
  - Camera fragments: parallax-3plane, multiplane-push, eye-shift, orbit.
  - Transition fragments: whip-pan, match-cut, zoom-portal, light-flash.
  - Data fragments: count-up-punch, line-chart-trace.
  - Atmosphere: grain-flip.

  Each fragment has a meta file (`parallax-3plane.meta.json`: intensity band, arc fit, 3–5 s duration, text slots
  with maxChars, and mutate/keep lists). The fragment I read is authored at 1920×1080 and has an abstract tech look,
  not a photo look.
- **(d) License audit** (`THIRD_PARTY_LICENSES.md` l.31–42):
  - Background music may only be "verified FreePD CC0 tracks or Incompetech CC-BY 4.0 tracks with required credit
    text".
  - Forbidden: short-video-maker's 31 bundled tracks ("YouTube Audio Library terms prohibit standalone
    distribution"), the hyperframes SFX (Pixabay), MusicGen (CC-BY-NC weights), Coqui XTTS-v2, and Fish-Speech and
    F5-TTS (CC-BY-NC).

  `assets/bgm/PROVENANCE.md`:
  - FreePD closed in late 2025. I confirmed today that freepd.com shows "Site Closed … 2008-2025".
  - Tracks are fetched one at a time from Wayback `id_` URLs, for example
    `https://web.archive.org/web/20240211063716id_/https://freepd.com/music/Inspiration.mp3` (Rafael Krux, CC0).
  - Each track is recorded with CDX digests and hashes, then trimmed and given a 2 s fade.

**Better than ours:**
- The only repo that checks rendered frames automatically, not just with an LLM.
- Explicit cut, motion and transition budgets.
- License hygiene.

**Worse:**
- Abstract motion graphics, Korean-first.
- Every video needs a coding agent to author its scenes.
- Relies on a Codex image runner.

**Adopt:**
- (1) Port the four frame metrics to numpy in `check.py`. Effort S, $0.
- (2) Turn the pacing and transition budgets into validator rules. Effort S.
- (3) A FreePD-via-Wayback CC0 music set with per-track provenance. Effort S–M.
- (4) Try HyperFrames as a separate renderer for designed cards (quote, statistic, date, map). It adds headless Chrome
  to the Modal image (roughly 300 MB) and about 20–40 s of CPU per Short, around $0.01. The user already has
  HyperFrames skills installed. Risk: GSAP's license is GreenSock's own; it is free for commercial use but not an
  OSI license.

**Verdict: BORROW IDEA** for the QC metrics, budgets and license audit. **WATCH** HyperFrames for designed cards.

---

## 6. gyoridavid/short-video-maker: MIT, 1,379 stars, pushed 2025-06-21 (stale)

**What it is.** An MCP/REST render service. The caller (n8n or an LLM) supplies scenes as `{text, searchTerms}`.
For each scene it runs Kokoro TTS, whisper.cpp captions (token-level timestamps) and a Pexels video search, then
renders with Remotion and a random music track.

**Stages**
- **(a) Visuals.** `src/short-creator/libraries/Pexels.ts` filters for portrait HD files of exactly 1080×1920 that
  are at least 3 s longer than the audio, then **picks at random** (l.79–118). When searches fail it falls back to
  `jokerTerms = ["nature","globe","space","ocean"]` (l.6, 137–140). That is off-topic footage by design. There is no
  verification, one clip per scene, and no transitions.
- **(c) Captions** (`src/components/videos/PortraitVideo.tsx` l.64–70, 110–147):
  - one-line pages of up to 20 characters, split when words are more than 1 s apart;
  - Barlow Condensed at 6em, uppercase, white with a 2 px black stroke;
  - the active word gets a coloured background box;
  - centred by default.
- **(d) Music.** `src/short-creator/music.ts` holds 31 mood-tagged tracks and picks at random at a flat volume.
  `static/music/README.md` says they come "from the YouTube audio library". They are not CC0 or CC BY and must not be
  redistributed.
- **(e) and (f).** No QA and no prompts; the caller writes the script.

**Red flags:** stale for 15 months. Its popularity comes from the author's YouTube channel ("AI Agents A-Z").

**Verdict: SKIP.** A generic stock-footage render service with a random, off-topic fallback.

---

## 7. IgorShadurin/app.yumcut.com: PolyForm Noncommercial 1.0.0, 885 stars, pushed 2026-09-03

**What it is.** A Next.js SaaS with credits, billing, marketing email campaigns and "Image Prank" features.

A daemon runs the phases: script, audio, transcription, captions, images, video parts and metadata
(`scripts/daemon/helpers/executor/*`). The real media work is handed off with `npm run` to an external
"yumcut-shorts-tools v2" (`image:blocks-to-qwen`, `video:basic-effects`, `video:merge-layers`, `transcript:json`;
`scripts/helpers/project-guide.ts` l.93–359). That toolkit is not in this repo, and `gh search` finds no public copy.

Details that are visible:
- `scripts/daemon/helpers/video/parts-timeline.ts` gives one image per transcript block.
- Style prompts live in `content/prompts/*.txt`. The neo-noir one reads: "pure black-and-white … bold brush inking
  … cross-hatching … diagonal compositions … maintain continuity in character design and lighting direction across
  panels."

**License:** non-commercial, so no code for a channel that will be monetized.

**Red flags:** 885 stars on a SaaS repo whose core renderer is missing.

**Verdict: SKIP.**

---

## 8. SaarD00/AI-Youtube-Shorts-Generator: MIT, 227 stars, pushed 2026-06-26

**What it is.** About 500 lines of Python:
1. Gemini picks a "viral" topic, with no research.
2. Gemini writes 8–9 scenes, each with 2 Pexels queries.
3. Edge TTS voices each scene (`en-US-AvaNeural`, +10%).
4. FFmpeg splits each scene 50/50 between clip A and clip B.
5. Scenes are joined with a random 0.5 s xfade (fade, diagbr or diagtl).

There are **no captions** and no music. Cuts come roughly every 2.5 s.

**Technique worth taking.** `modules/brain.py` l.36–50: *"every sentence has a 'Visual Switch' … TWO different stock
videos for every single scene. visual_1: Matches the *start* of the sentence. visual_2: Matches the *end* of the
sentence or provides a reaction/context. Strictly Literal: If the text is 'The economy crashed,' do NOT search 'sad
man'. Search 'Stock market red chart'."* The split itself is crude: 50/50 by duration, not at a word
(`modules/composer.py` l.59–82).

**Red flags:**
- `composer.py` l.44–49 crops 150 px off the bottom of an AI avatar clip to remove a logo ("LOGO REMOVAL CROP"). That
  is watermark removal.
- Random clip choice.
- No fact check.

**Verdict: SKIP.** The only idea worth keeping is two visuals per line, one for its start and one for its end.

---

## 9. feyzilim/clipfactory: Elastic License 2.0, 105 stars, pushed 2026-08-23

**What it is.** A FastAPI plus frontend factory for creators who film their own B-roll:
1. A persona and template produce a script (OpenAI GPT-4.1 by default).
2. TTS produces word timings.
3. An LLM plans scenes over word indices.
4. A deterministic normaliser fixes the plan.
5. An asset ranker picks clips from a library tagged by a vision model.
6. FFmpeg renders with ASS captions, overlays and a ducked music bed.

Extras: trends (a yt-dlp download of TikTok/YouTube videos, forbidden for us), photo-mode slideshows, Telegram
delivery, and paid AI B-roll (OpenAI images, Google video, fal).

**Stages and key files** (`backend/app/`)
- **(a) Shot planning over words** (`llm/prompts.py` l.96–110, `PLAN_SYSTEM`):
  - *"Cut the video into scenes by choosing inclusive word-index ranges … Scene boundaries must fall on sentence or
    clause changes, or when the visual concept changes — never arbitrary … cover every word exactly once … Aim for
    shots of 1.5-4 seconds … The hook is its own short scene."*
  - `intent` describes "what the viewer should SEE … Not the words."
  - `overlay_text` (4 words or fewer) is allowed "for only 1-3 scenes per video — the hook and the key payoff".
- **(a) Deterministic normaliser** (`content/scene_planner.py`):
  - The header (l.1–4) sets the principle: "Voice timings are the master clock … Scenes never use fixed 5 s blocks."
  - Ranges are clamped and made contiguous.
  - `split_long` (l.139–170) splits any shot longer than max × 1.15 at the word nearest its midpoint, with a 0.3 s
    bonus for punctuation.
  - `merge_short` (l.172–197) merges a shot below the minimum into whichever neighbour stays shorter.
  - Split and merge repeat for up to 3 rounds.
  - **Each cut lands at the midpoint of the gap between two words** (l.212).
  - Overlays are capped while keeping the first (hook) and the last (payoff) (l.227–240).
  - A heuristic fallback (l.42–71) splits at clause breaks into shots of about 2.5–3.5 s.
- **(a) Ranking** (`llm/prompts.py` l.136–147, `RANK_SYSTEM`): *"Judge by the clip DESCRIPTION against the scene intent
  — the numeric score is only a weak prior … Never use the same asset_id for two scenes … Prefer visual match to the
  scene intent, then variety between consecutive scenes (alternate locations/shot sizes) … Avoid two consecutive
  scenes with the same action … recently_used=True … avoid them unless they are clearly the only good match, so
  videos do not all look alike."*
- **Freshness** (`assets/selector.py` l.15–20, 69–79, 156–159): score = relevance × quality × freshness.
  Freshness is 0.20 if the clip was used within a day, 0.45 at 1–3 days, 0.70 at 3–7 days, and 0.90 after that.
- **Library tagging** (`llm/prompts.py` l.181–187, `ANALYZE_SYSTEM`): the vision model sees evenly sampled frames and
  must "Describe literally what is visible … Do not invent things you cannot see". Tags include framing
  (close/medium/wide).
- **(b) Motion** (`renderer/filters.py`). Each shot gets a look:
  - zoom of 2.5–5% over the shot;
  - direction drawn from in / in / out / static, so consecutive shots differ;
  - oversampled 1.00–1.06 with a random crop offset;
  - zoom done with `scale=…:eval=frame` plus a centre crop, not zoompan.
- **(c) Captions** (`captions/generator.py` l.55–88, 217–231):
  - chunks of 2–5 words, broken at clause punctuation or a pause over 0.35 s; a sentence end always breaks;
  - each chunk is extended to the next one's start when the gap is under 0.5 s, so captions don't flicker;
  - an emphasis colour goes on the longest non-stopword;
  - chunks pop in from 80% to 100% scale;
  - overlays use a separate top-anchored ASS style with fades.
- **(d) Audio** (`renderer/audio.py`): voice at `loudnorm I=-16:TP=-1.5`; music at −20 dB with
  `sidechaincompress threshold=0.03 ratio=6 attack=40 release=400` and a 1.2 s fade-out.
- **(e) QA.** Unit tests only; no check of rendered frames.

**License.** ELv2 allows internal use and modification. It forbids offering the software as a hosted service and
removing its notices. We should reimplement rather than copy; the algorithm is about 150 lines.

**Red flags:** created 2026-08-22 and last pushed the next day, with 2 commits and 105 stars within a month. That
looks like a promoted launch with no track record. It also defaults to a paid LLM and uses yt-dlp.

**Better than ours:** the shot planner is exactly our missing "multiple shots per beat, cut on the voice" step.
Freshness across videos is another plus.

**Worse:** it is built for a personal B-roll library, not archives.

**Adopt:** reimplement the shot planner after TTS alignment (details in insight 3). Effort M; Modal render time is
roughly unchanged, since total frames stay the same.

**Verdict: BORROW IDEA.**

---

## 10. Dark2C/Viral-Faceless-Shorts-Generator: no LICENSE file, 112 stars, pushed 2026-05-10

**What it is.** A Docker Compose stack: an nginx UI, a Node "trendscraper", Piper TTS and speechalign.
- **Topics:** Google Trends is scraped with Puppeteer (`trendscraper/src/modules/google_trends_scraper_module.js`
  l.5, 29).
- **Script:** the LLM writes 250–300 words and must "finish with a call to action" (`LLM_module.js` l.1–13).
- **Footage:** YouTube videos are downloaded with yt-dlp for the background (`youtube_import_module.js` l.99–103).
- **Render:** one looping background video plus ASS subtitles whose style is patched with `sed`
  (`video_render_module.js` l.186–206, Montserrat ExtraBold).

Shell commands are built by string interpolation, which is an injection risk.

**Verdict: SKIP.** No license, and it relies on YouTube downloading and Trends scraping, both forbidden for us.

---

## Search for a better repo of this kind

**Queries.** I ran these through `gh search repos`, sorted by stars, and also with `--updated ">2026-03-01"`:
"faceless shorts wikimedia", "history shorts generator", "documentary shorts pipeline", "shorts generator ken burns",
"automated youtube shorts remotion", "wikimedia commons video generator", "ai shorts factory", "faceless video
generator", "youtube shorts automation", "kokoro shorts", "shorts pipeline gemini", "history youtube automation",
"short video factory". Code searches for Commons plus zoompan returned nothing.

**Result.** Nothing clearly better turned up in scope. None of these were cloned; their details come from search
results only:

| Repo | Stars | License (per GitHub) | Why not |
|---|---|---|---|
| SamurAIGPT/AI-Faceless-Video-Generator | 508 | MIT | Talking-face avatars |
| YILS-LIN/short-video-factory | 5,497 | AGPL-3.0 | Chinese product-marketing desktop editor |
| sanyo4ever/ai-shorts-factory | 11 | AGPL-3.0 | Too small |
| Hazy019/youtube-shorts-automation | 27 | MIT | Too small |

## Cross-cutting observations

- **No repo checks historical accuracy** (right period, right person) of a picture. The best verifier (OpenReels) is
  semantic only, so period and identity checks are ours to add.
- **None makes a second shot from the same still**, such as a detail crop. The repos with several shots per line
  simply use more stock clips. For an archive channel, the detail crop is the free equivalent.
- **Only reelforge checks rendered frames automatically.** claude-faceless has an agent read stills; everyone else
  trusts the plan.
- **Music is almost never done legally for our rules.** Repos either have none or use Pixabay or YouTube Audio
  Library tracks. The exception is reelforge: FreePD CC0 through Wayback, or Incompetech CC BY with credit.
- **Star counts don't track quality here.** The two most-starred repos (short-video-maker and YumCut) are the least
  useful: one is stale and random, the other non-commercial with its renderer missing.

---

## Top insights for Days of Odd (ranked)

### 1. Verify each chosen picture on its own, strictly, at a readable size, and feed rejections back

- **Source:** OpenReels `src/providers/stock/stock-verifier.ts` l.25–35, 106; `adaptive-resolver.ts` l.107–153,
  243–245.
- **Where:** after the joint pick in `pick.py`, before rendering.
- **How:** for each beat, send the chosen file at about 800 px (Commons `iiurlwidth=800`, not the 330 px thumbnail)
  to Gemini Flash, together with the beat line, its claim, and the year and place. Use a strict history prompt:

  > Be strict: a 1920s photo does NOT match an 1880s event; a modern replica, reenactment or museum reconstruction
  > does NOT match the original; a different person with the same name does NOT match; a generic ship does NOT match
  > a named ship; a map of the wrong region does NOT match. Ignore aesthetic quality.

  The model returns `{relevant, period_ok, confidence, reason}`, and a picture passes at 0.6 or above.
- **On failure:**
  1. verify the next alternate, downloading it only then;
  2. run `second_round` with the rejection reasons as "avoid" text;
  3. use a designed card (insight 2), never a gradient or a reuse.
- **Effort and cost:** M. About 9–18 extra Gemini calls per Short, within the free tier but watch the daily quota;
  batch 2–3 beats per call if needed. $0 on Modal.
- **Why first:** it attacks "the picture didn't show what the line says" and "wrong period", which together make up
  most of the 14 visual rejects.

### 2. Replace the gradient and reuse fallbacks with designed cards

- **Sources:**
  - claude-faceless `remotion/src/lib/collage.tsx` (l.91–92, 201, 262, 323–351) and `make-vox/SKILL.md` l.43–67;
  - reelforge `blocks/quote`, `blocks/statistic`;
  - OpenReels `text_card`.
- **History kit:**
  - **Date card:** a big year plus a place chip.
  - **Quote card:** a verbatim line from a claims-table source, with attribution.
  - **Document card:** a Commons scan of a newspaper or letter, with a highlight sweep on the key phrase.
  - **Map card:** a public-domain Natural Earth basemap with a pin and label chips; no text inside any AI art.
  - **Number card:** a count-up.
- **Styling:** each card gets sepia and grain, an idle drift, and one entrance.
- **Build:** Pillow plus FFmpeg overlays (S–M), or HyperFrames HTML (M; Apache-2.0; Chrome on Modal, about $0.01 per
  Short).
- **Why:** topics with few archive pictures stop failing on "no picture", which is the third rejection cause.

### 3. Two or three shots per beat, cut on word boundaries

- **Sources:**
  - clipfactory `backend/app/content/scene_planner.py` l.95–241 and `llm/prompts.py` l.96–110;
  - SaarD00 `modules/brain.py` l.36–50;
  - reelforge `references/design-direction.md` l.74–75;
  - OpenReels `prompts/playbook.md` l.86–88.
- **Cuts:** after alignment, split any beat longer than about 3.5 s at the clause break nearest its midpoint, and put
  the cut in the gap between two words.
- **Budget:** shots of 2–4 s (the hook shot 2 s or less), with no more than 12 cuts per 30 s.
- **The second shot is one of:**
  - a **detail crop** of the same picture: the picker returns a `detail` box (face, headline, object), used only
    when the crop keeps about 600 px or more of source width;
  - a verified `visual_2` for the end of the line;
  - an overlay event, such as a date chip landing.
- **Cost:** about $0.
- **Why:** it fixes the "static slideshow" look, and it makes insight 5 easier because each shot gets its own frame.

### 4. Keep the best round, and don't throw away good pictures on a rewrite

- **Source:** OpenReels `src/pipeline/orchestrator.ts` l.490–521 ("LLM refinement can degrade in later rounds").
- **The problem in ours:**
  - In `studio.py` l.310–332, a third failed render rejects the Short even when round 1 or 2 would pass the lenient
    `_passes(final=True)` rule (2 or fewer frame problems, 1 or fewer speech problems).
  - Any story fix re-runs `pick.pick` for every beat (l.336–340).
- **Change:**
  - Save each round's script and visuals.
  - At the end, publish the best-scoring round that passes the final rule, re-rendering it if needed.
  - After a rewrite, keep the pictures for beats whose text and claims didn't change.
- **Effort:** S. It may recover some of the 15 rejects immediately.

### 5. Deterministic frame checks per shot before Gemini, and one review frame per shot

- **Source:** reelforge `scripts/craft-contact-sheet.mjs` l.58–63, 392–456; `src/gates/p5-common.mjs` l.240–265.
- **Checks:** run numpy on 3 frames per shot (0.6 s in, the midpoint, and 0.3 s before the end), using reelforge's
  thresholds:
  - luma standard deviation of 15 or less means blank;
  - fewer than 400 edge pixels in the central 60% means empty;
  - local contrast below 3.0 means washed out;
  - a mean absolute difference below 0.35 between frames means frozen.

  Add black-border and caption-collision checks as well.
- **Review:** send Gemini one frame per shot, plus one seeded-random frame per beat that stays clear of the shot edges
  by 12%. Today it sees only one mid-beat frame per beat.
- **Effort and cost:** S, $0.

### 6. Variety and freshness rules

- **Sources:**
  - OpenReels `src/schema/director-score.ts` l.49–62;
  - reelforge `design-direction.md` l.74;
  - clipfactory `llm/prompts.py` l.136–147 and `assets/selector.py` l.15–20.
- **Tags:** give each shot a type (photo, painting/engraving, document, map, card) and a size (wide or detail).
- **Validator:** never 3 shots in a row of the same type or size, and alternate the motion direction.
- **Freshness:** penalise Commons files used in the last ~20 Shorts: ×0.2 if used within a day, ×0.45 at 1–3 days,
  ×0.7 at 3–7 days.
- **Effort:** S.

### 7. Accent overlays that default to off

- **Sources:** reels-af `src/reel_af/agents/accent.py` l.22–74 and `planning/safe_zone.py` l.17–47; clipfactory
  `llm/prompts.py` l.106–108.
- **Decision:** one LLM pass per script sets `emit_overlay` for each beat, false by default.
- **Content:** year/date, place, number, name, or a hook title. 2–5 words, at most 3 per Short, always considering
  the hook and the payoff.
- **Placement:** the upper third (y ≈ 0.22), opposite our captions at y = 0.60, with a fade in and out.
- **Implementation:** a second ASS style in `captions.py`.
- **Why:** it gives us on-screen hook text and anchors the "when and where" that archive pictures can't show.
- **Effort:** S–M.

### 8. Measure SFX audibility, and add an optional CC0 music bed with provenance

- **Sources:**
  - claude-faceless `.claude/skills/suggest-sfx/SKILL.md` l.69–98 and `tools/mix_music.py` l.86–95;
  - reelforge `THIRD_PARTY_LICENSES.md` l.31–42 and `assets/bgm/PROVENANCE.md`.
- **SFX check (in `check.py`):**
  1. Take the RMS over a 0.3 s window at each cue, or over the final third for risers.
  2. Compare the final mix with a voice-only render.
  3. A story cue must add at least +4 dB, and texture +1–3 dB.
  4. Otherwise, raise the gain. By their calibration, our −9, −10 and −13 dB may be 4–8 dB too quiet.
- **Music:**
  - 10–20 FreePD CC0 tracks from Wayback `id_` URLs, with hashes (FreePD itself is closed, which I confirmed).
  - Bed high-passed at 90 Hz and ducked hard with our existing sidechain settings.
  - A/B test music against no music.
- **Risk:** Content ID false claims on popular free tracks. Keep a claims log and prefer less-used tracks.
- **Effort:** S.

### 9. Pick hooks and scripts by pairwise comparison, and test a delayed reveal

- **Source:** reels-af `agents/judge.py` l.4 and `agents/narrator.py` l.23–27, 118, 161–162.
- **Changes:**
  - Choose among our 3 hooks with A-vs-B comparisons instead of one scored choice.
  - Add "echo a distinctive hook word in the payoff" to SCRIPT-RULES; it strengthens our loop.
  - Add a pause budget: no more than about 6 commas per 50 words.
  - Test "the hook does not reveal the answer; reveal it at 8–15 s" on one series only.
- **Effort:** S.

### 10. Motion and transition discipline

- **Sources:**
  - reelforge `references/strip-qc.md` l.16–23 and `references/gallery/ROUTING.md` §C–§D;
  - claude-faceless `make-short/SKILL.md` l.38–46;
  - OpenReels `prompts/creative-director.md` l.19–23.
- **Opening:** frame 0 fully composed, with no fade-in. The strongest picture and the hook text appear within 1.8 s.
- **Ending:** the last frame equals frame 0, for the loop.
- **Transitions:** hard cuts by default. At most 1–2 "peak" transitions per Short (a whip or a flash), placed at the
  twist.
- **Motion:** one camera move per shot, plus at most one subtle drift. The picture changes every 2–4 s, which happens
  automatically once insight 3 is in.
- **Effort:** S.
