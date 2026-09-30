# G4a: motion and quality for archive stills

Study date: 2026-09-27. Scope: better motion and image quality for archive stills (old photographs,
engravings, paintings, documents). Everything must be free and headless on Modal: CPU today, GPUs allowed
within the $30/month credit, about $0.12 per Short today.

**Method**

- **Repo metadata:** `gh repo view` for stars, last push, and archived status. Licence type is from
  `licenseInfo`; for every "other" licence the LICENSE file itself was read.
- **Code:** read from shallow clones in `/tmp/ghdeep/g4a/`: DepthFlow, ShaderFlow, BrokenSource,
  parallax-maker, 3d-ken-burns, Wan2.2, ffmpeg-cheatsheet, and xfade-easing.
- **Model licences:** Hugging Face model cards and the HF API (`cardData.license`, gating).
- **Prices:** `curl -sL https://modal.com/pricing`.
- **No models were installed or run.** FFmpeg filtergraphs and a torch `grid_sample` micro-benchmark ran
  locally on an Apple Silicon Mac with 8 threads, using FFmpeg 7.1 (the pinned imageio-ffmpeg build our
  pipeline uses).
- **Local timings are lower bounds.** Modal x86 cores are likely slower per thread, so the cost estimates
  below assume up to 2× longer on Modal.
- **Scratch files:** test scripts and outputs are in `/tmp/ghdeep/g4a/` (`kb_test*.py`, `kb_detail.py`,
  `kb_final.py`, `warp_bench.py`, and renders in `kb/`).

## TL;DR: ranked recommendations

| # | Change | Effort | Added Modal cost per Short | Licence |
|---|---|---|---|---|
| 1 | Replace `zoompan` with a sub-pixel `perspective` camera and smoothstep easing | S | ≈ $0.002–0.004 | FFmpeg only |
| 2 | Wide images: fit the whole picture over a blurred backdrop instead of the 9:16 cover crop | S | ≈ $0 (same filter cost as #1) | FFmpeg only |
| 3 | Detail zoom or punch-in cut to a box from the vision LLM, timed to the emphasis word | S–M | ≈ $0 | FFmpeg plus a prompt field |
| 4 | One grade and vignette for the whole Short; no heavy grain | S | < $0.007 | FFmpeg only |
| 5 | Two-plane push-in parallax for stills with a clear subject | M | ≈ $0.005 | BiRefNet_lite ONNX (MIT) |
| 6 | Depth-displacement parallax for deep scenes (landscapes, streets, paintings) | M | ≈ $0.005–0.03 | Depth Anything V2 Small (Apache-2.0) plus our own torch code |
| 7 | Real-ESRGAN `realesr-general-x4v3`, only when magnification exceeds 1.3× | S–M | ≤ $0.004 | BSD-3-Clause |
| 8 | Designed shots: split-screen comparison and picture-in-picture inset (graphs tested) | S each | ≈ $0 | FFmpeg only |
| 9 | Later and optional: masked image-to-video, paintings and landscapes only | L | ≈ $0.06–0.13 per clip (estimate) | Wan2.2 + lightx2v distill (Apache-2.0); disclosure needed |

**Skip:**

- 3d-ken-burns: CC BY-NC-SA and CUDA-only.
- CodeFormer: S-Lab non-commercial.
- GFPGAN: its NVIDIA and DFDNet parts are non-commercial, and it changes faces.
- Depth Pro weights: research-only.
- DA V2 Base/Large and DA3 Large/Giant: CC BY-NC.
- rembg's default model, RMBG-2.0: CC BY-NC.
- FramePack and HunyuanVideo: territory clause excludes the EU, UK, and South Korea.
- MiniMax-H3: needs an application for US use.
- Colourisation: invents facts.

## 1. Our baseline, measured

In `pipeline/src/ytc/render.py`:

- `_cover()` (L32–36) scales an image to cover the frame and crops at the focus point.
- Stills are rendered at L58 as `_cover(2*W, 2*H)`, then `_image_motion()` (L39–51), then `TO_BT709`.
- `_image_motion()` is `zoompan` with linear `on/n` progress, a maximum of 1.12×, and the zoom always
  centred (`iw/2-(iw/zoom/2)`).

Problems:

1. **Integer jitter.** `zoompan` rounds x and y to whole pixels (FFmpeg trac #4298, also noted in
   rendi-api/ffmpeg-cheatsheet). Even on the 2× canvas, a pan moves in 0 or 1 px steps. Measured with phase
   correlation on a 5 s `pan_right`, the frame-to-frame displacement has a **standard deviation of
   0.433 px**. That shows as stepping, and it is worst on slow moves, which is every move we make.
2. **Linear motion.** There is no easing, so every clip starts and stops abruptly at the hard cut.
3. **The cover crop throws away most of a wide image.**
   - A 4:3 image keeps **42%** of its width; a 3:2 image keeps **37.5%**.
   - In a test with a 4:3 lightning photo and focus point (0.62, 0.52), the crop removed both lightning
     bolts, which are the subject.
   - A 1200×800 source (our Commons minimum is 1,200 px) must be upsampled **2.7×** to fill 1080×1920, so
     it looks soft.
   - This is a plausible cause of some "the picture didn't show what the line says" rejections.
4. **Zooms go to the centre**, not to the focus point or to the detail the line mentions.

## 2. Local benchmarks

### Camera smoothness

Test: a 5 s move at 1080×1920 (150 frames), with judder measured by phase correlation. Render times are
local, with an x264 `veryfast` or `ultrafast` intermediate.

| Variant | Judder std (px per frame) | Render time per 5 s clip |
|---|---|---|
| Ours: `zoompan` on a 2× cover canvas | **0.433** | 1.2 s |
| `zoompan` on a 4× canvas (the cheatsheet's "scale up first" tip) | about half of ours | not recorded |
| `perspective`, cubic, with `-loop 1` input | ≈ 0.01 | ≈ 8 s (the image is decoded and rescaled every frame) |
| `perspective`, cubic, with a `loop` filter after the cover and `-framerate 30` input | **0.008** (max jump 0.04) | **2.6 s** |
| The same plus smoothstep easing | no steps | 2.6 s |
| Detail zoom from full frame to a 1.6× box, eased | smooth | 2.2 s |
| Fit over a blurred backdrop, with a 1.00→1.08 push | smooth | 2.2 s |
| Two-plane parallax (two `perspective` layers plus `overlay`) | smooth | 8.0 s, including an x264 `medium` encode |

The eased variant reported a maximum jump of 0.27 px. That is a phase-correlation artefact where the speed
crosses a whole pixel, not a real step.

**Gotcha:** without `-framerate 30` before `-i`, the image2 demuxer runs at 25 fps, and `loop` or `setpts`
conversions drop or duplicate a frame. In testing that showed up as a false 0.36 px std. Put `-framerate 30`
on the input and don't use `setpts`.

### Look and grain bitrate

Test: our final CRF 19, preset `medium`, on a 5 s eased pan (`kb_final.py`).

| Look | Size | Compared with ungraded |
|---|---|---|
| Ungraded | 1.09 MB | — |
| Grade + vignette | 1.26 MB | +16% |
| Grade + light temporal grain (`noise=c0s=3:c0f=t+u`) | 1.54 MB | +41% |
| Grade + light static grain (`noise=c0s=3:c0f=u`) | 1.52 MB | +39% |
| Grade + heavy temporal grain (`noise=c0s=7:c0f=t+u`) | 5.14 MB | **+372% (4.7× larger)** |

An earlier run on a different clip measured the grade at −17%. Treat the grade as roughly bitrate-neutral
and dependent on content.

Heavy grain would push a 50 s Short past our 40 MB cap. The `maxrate` limit would then force blockier
video, and YouTube's re-encode smears grain anyway. Light grain is affordable if wanted; heavy grain is not.

### Depth-displacement warp cost

Test: torch `grid_sample` on CPU with 8 threads, output 1080×1920 (`warp_bench.py`, synthetic depth, no
model).

| Inverse-warp iterations | Final sampling | Per frame | Per 5 s clip (150 frames) |
|---|---|---|---|
| 0 (plain affine) | bilinear | 12 ms | 1.8 s |
| 3 | bilinear | 35 ms | 5.2 s |
| 3 | bicubic | 67 ms | 10.0 s |

## 3. Tested filtergraphs, ready to copy

All of these were run with our FFmpeg 7.1 binary. `W` and `H` inside `perspective` are the input
frame's size. `on` is the output frame index.

### 3.1 Sub-pixel eased Ken Burns (replaces `zoompan`)

Command-line form, tested: an eased `pan_right` on a 1.12× overscanned cover canvas (1210×2150).

```bash
E="((on/149)*(on/149)*(3-2*(on/149)))"
ffmpeg -framerate 30 -i IMG -vf "scale=1210:2150:force_original_aspect_ratio=increase,crop=1210:2150,setsar=1,\
loop=loop=149:size=1:start=0,\
perspective=x0='(W-W/1.12)*$E':y0='(H-H/1.12)/2':x1='(W-W/1.12)*$E+W/1.12':y1='(H-H/1.12)/2'\
:x2='(W-W/1.12)*$E':y2='(H+H/1.12)/2':x3='(W-W/1.12)*$E+W/1.12':y3='(H+H/1.12)/2'\
:interpolation=cubic:eval=frame,scale=1080:1920:flags=lanczos,format=yuv420p" -frames:v 150 out.mp4
```

A drop-in sketch for `render.py` (not applied; it keeps our motion names and the 1.12× maximum):

```python
OVERSCAN = 1.12
SW, SH = 2 * round(W * OVERSCAN / 2), 2 * round(H * OVERSCAN / 2)  # 1210x2150


def _camera(frames: int, z0: float, z1: float, x0: float, x1: float, y0: float, y1: float) -> str:
    """Crop box eased from zoom z0 at (x0, y0) to z1 at (x1, y1); positions are 0..1 across the free margin."""
    p = f"(on/{max(frames - 1, 1)})"
    e = f"({p}*{p}*(3-2*{p}))"
    z = f"({z0}+({z1}-{z0})*{e})"
    bw, bh = f"(W/{z})", f"(H/{z})"
    left = f"((W-{bw})*({x0}+({x1}-{x0})*{e}))"
    top = f"((H-{bh})*({y0}+({y1}-{y0})*{e}))"
    right, bottom = f"({left}+{bw})", f"({top}+{bh})"
    return (f"perspective=x0='{left}':y0='{top}':x1='{right}':y1='{top}'"
            f":x2='{left}':y2='{bottom}':x3='{right}':y3='{bottom}':interpolation=cubic:eval=frame")


MOVES = {  # z0, z1, x0, x1, y0, y1
    "zoom_in": (1, OVERSCAN, .5, .5, .5, .5), "zoom_out": (OVERSCAN, 1, .5, .5, .5, .5),
    "pan_left": (OVERSCAN, OVERSCAN, 1, 0, .5, .5), "pan_right": (OVERSCAN, OVERSCAN, 0, 1, .5, .5),
    "pan_up": (OVERSCAN, OVERSCAN, .5, .5, 1, 0), "pan_down": (OVERSCAN, OVERSCAN, .5, .5, 0, 1),
}

# Still-image branch of _render_clip:
vf = (f"{_cover(SW, SH, visual.focus_x, visual.focus_y)},loop=loop={frames - 1}:size=1:start=0,"
      f"{_camera(frames, *MOVES[motion])},scale={W}:{H}:flags=lanczos,{TO_BT709}")
ff.run("-framerate", str(FPS), "-i", asset.path, "-vf", vf, "-frames:v", str(frames), *INTERMEDIATE, "-an", out)
```

- **Zoom toward the focus point, not the centre.** Set `x1` and `y1` to the focus point's position inside
  the cover canvas. That takes the source size and about five lines of Python.
- **Keep the `loop` filter after the scale** rather than `-loop 1` on the input. The filter caches the
  scaled frame once: 2.6 s against about 8 s per clip.

### 3.2 Detail zoom to coordinates (tested: `kb_detail.py`, 2.2 s per 5 s clip)

```python
def detail_zoom(cx: float, cy: float, zoom: float, frames: int) -> str:
    """Ease from the full frame into a zoom-x box centred on (cx, cy) in 0..1, clamped inside the frame."""
    n = max(frames - 1, 1); p = f"(on/{n})"; e = f"({p}*{p}*(3-2*{p}))"
    bw, bh = f"(W/{zoom})", f"(H/{zoom})"
    bx = f"min(max({cx}*W-{bw}/2,0),W-{bw})"; by = f"min(max({cy}*H-{bh}/2,0),H-{bh})"
    x0, y0 = f"({bx})*{e}", f"({by})*{e}"
    x1, y1 = f"(W+(({bx})+{bw}-W)*{e})", f"(H+(({by})+{bh}-H)*{e})"
    return (f"perspective=x0='{x0}':y0='{y0}':x1='{x1}':y1='{y0}':x2='{x0}':y2='{y1}':x3='{x1}':y3='{y1}'"
            f":interpolation=cubic:eval=frame")
# vf = f"{cover},loop=loop={N-1}:size=1:start=0,{detail_zoom(0.62, 0.52, 1.6, N)},scale=1080:1920:flags=lanczos,format=yuv420p"
```

- **Limit the zoom.** Keep the final zoom at or below about 1.3× on 1,200 px sources unless the image has
  been upscaled (§6 Real-ESRGAN). The 1.6× test end frame is visibly soft.
- **Punch-in cut variant.** Split the beat at the emphasis word's timestamp: a wide shot with a 1.00→1.04
  drift, then a hard cut to the box with its own gentle drift. That gives two shots per beat from one
  still, and ties the picture to the word the caption highlights. We already have word timestamps and
  emphasis words.
- **Reveal variant.** Run it in reverse, starting on the detail and pulling out to the whole picture. It
  suits hook beats.

### 3.3 Fit over a blurred backdrop for wide images (tested, 2.2 s)

```bash
E="((on/149)*(on/149)*(3-2*(on/149)))"; Z=1.08
ffmpeg -framerate 30 -i IMG -filter_complex "[0:v]split=2[a][b];\
[a]scale=1210:2150:force_original_aspect_ratio=increase,crop=1210:2150,gblur=sigma=40,eq=brightness=-0.12:saturation=0.7[bg];\
[b]scale=1210:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-80,setsar=1,loop=loop=149:size=1:start=0,\
perspective=x0='(W-W/$Z)/2*$E':y0='(H-H/$Z)/2*$E':x1='W-(W-W/$Z)/2*$E':y1='(H-H/$Z)/2*$E'\
:x2='(W-W/$Z)/2*$E':y2='H-(H-H/$Z)/2*$E':x3='W-(W-W/$Z)/2*$E':y3='H-(H-H/$Z)/2*$E'\
:interpolation=cubic:eval=frame,scale=1080:1920:flags=lanczos,format=yuv420p" -frames:v 150 out.mp4
```

- **When:** images with an aspect ratio of about 1.0 or wider.
- **Why:** it shows 100% of the picture instead of 37–42%, and samples a 1,200 px source at about 1:1
  instead of upsampling it 2.7×.
- **Captions:** the `-80` lifts the photo to leave caption room below; tune it to our ASS position.
- **Detail zooms from fit mode:** go no deeper than about 1.25×, or cut to a cover-mode detail crop.

### 3.4 Grade and vignette for the whole Short (tested)

```text
eq=contrast=1.06:saturation=0.85:gamma=0.97,colorbalance=rs=0.03:bs=-0.03:rh=0.02:bh=-0.02,vignette=angle=PI/5
```

- **Where:** apply it once in the final encode, **before** `ass=`, so the captions aren't vignetted.
- **Grain:** optionally append `noise=c0s=3:c0f=t+u` (about +22% size). Never use `c0s` ≥ 6.
- **What it does:** mixed sources (black-and-white photos, colour paintings, Met CC0 objects) get one warm,
  slightly desaturated look without colourising anything. YouTube lists colour and lighting filters and
  "vintage effects" as needing no disclosure.

### 3.5 Light leak (tested; not recommended yet)

```text
-f lavfi -i "gradients=s=540x960:r=30:d=5:c0=0xff8a2a:c1=0x000000:c2=0xffd27a:n=3:speed=0.04:seed=7"
[1:v]gblur=sigma=40,scale=1080:1920,format=gbrp,fade=t=in:st=2.2:d=0.25,fade=t=out:st=2.55:d=0.5[leak];
[0:v]format=gbrp[base];[base][leak]blend=all_mode=screen:all_opacity=0.35
```

It reads as a flat warm wash rather than a leak. If we use it, use it once per Short on the twist cut.

### 3.6 Motion blur on pans (tested; not needed)

Render at 4× the frame rate (`loop=loop=599`, 120 fps) with the same `perspective`, then
`tmix=frames=4,fps=30`. That costs 4× the render time and only helps fast "whip" moves. Our moves are about
0.7 px per frame.

### 3.7 Two-plane parallax (tested with a feathered ellipse as a stand-in mask; 8.0 s per clip)

```bash
ffmpeg -framerate 30 -i layer_bg.png -framerate 30 -i layer_fg.png -filter_complex "\
[0:v]loop=loop=149:size=1:start=0,<box z 1.00→1.04 about subject centre>[b];\
[1:v]format=yuva444p,loop=loop=149:size=1:start=0,<box z 1.00→1.10 about subject centre>[f];\
[b][f]overlay=format=auto,scale=1080:1920:flags=lanczos,format=yuv420p" -frames:v 150 out.mp4
```

`<box …>` is the `box()` helper in `kb_final.py`: the same eased and clamped `perspective` as §3.2, with a
start and end zoom. `perspective` handles `yuva444p` alpha correctly.

**No inpainting is needed when the move is a push-in centred on the subject.** The foreground grows, so it
covers its own silhouette in the background plate. Small ghost edges can appear only at concave parts of
the outline, and at a 6% scale difference they are minor.

### 3.8 Split-screen and picture-in-picture (tested; 0.9 s and 3.4 s)

```bash
# Split-screen: two 1080x955 halves; the lower half slides in with ease-out over 0.35 s
color=c=white:s=1080x1920:r=30:d=5[canvas];
[0:v]scale=1080:955:force_original_aspect_ratio=increase,crop=1080:955,setsar=1,loop=loop=149:size=1:start=0[top];
[1:v]scale=1080:955:force_original_aspect_ratio=increase,crop=1080:955,setsar=1,loop=loop=149:size=1:start=0[bot];
[canvas][top]overlay=0:0[t1];[t1][bot]overlay=x='W*pow(1-min(t/0.35,1),2)':y=965,format=yuv420p

# Picture-in-picture: white-bordered inset fades in at 0.5 s over a slowly pushing, slightly blurred background
[0:v]<cover + loop + eased box 1.00→1.06>,scale=1080:1920:flags=lanczos,gblur=sigma=2[bg];
[1:v]scale=460:-2,pad=iw+12:ih+12:6:6:color=white,format=yuva420p,loop=loop=149:size=1:start=0,fade=t=in:st=0.5:d=0.3:alpha=1[p];
[bg][p]overlay=x=W-w-60:y=300,format=yuv420p
```

- Each 1080×955 half is close to landscape shape, so a 4:3 photo keeps about 85% of its width.
- Uses: "then and now", "the claim and the proof", "the man and the letter".

## 4. Modal prices (from `curl modal.com/pricing`, 2026-09-27)

| Resource | Price per second | Notes |
|---|---|---|
| CPU | $0.0000131 per physical core (2 vCPU) | Our render container is `cpu=8`, `memory=8192`, so $0.0001226/s (about $0.44/h) |
| Memory | $0.00000222 per GiB | |
| T4 | $0.000164 | |
| L4 | $0.000222 | |
| A10 | $0.000306 | |
| L40S | $0.000542 | |
| A100 40 GB | $0.000583 | |
| A100 80 GB | $0.000694 | |
| RTX PRO 6000 | $0.000842 | |
| H100 | $0.001097 | |
| H200 | $0.001261 | |
| B200 | $0.001736 | |
| B300 | $0.001972 | |
| Volumes | $0.09 per GiB per month | 1 TiB per month free |

All prices are at the default (no region pinned). Cost estimates assume one Short is about 50 s, which is
about ten 5-second clips (6–9 beats).

| Technique | Time per 5 s clip | Cost per Short |
|---|---|---|
| `perspective` camera (§3.1–3.3) | +1.4 s over `zoompan`, local | +$0.002–0.004 |
| Grade in the final encode | +1–3 s, local (noisy) | < $0.007 |
| Two-plane parallax on 3 beats | +4 s per clip, plus BiRefNet_lite about 2–4 s per image (estimate) | ≈ $0.005 |
| Depth warp: DA-V2-Small plus torch | depth about 1–2 s per image (estimate) plus a 5–10 s warp, local | 3 beats ≈ $0.005–0.01; all beats ≈ $0.012–0.03 |
| DepthFlow on CPU (Mesa llvmpipe) | ≈ 75–115 s (author reports about 2 fps at 1080p on a 12-core 5900X) | all beats ≈ $0.09–0.14 (doubles cost per Short); 3 beats ≈ $0.03–0.04 |
| DepthFlow on T4 via EGL, *if Modal exposes GL* | ≈ 3–5 s, plus a 20–40 s cold start | ≈ $0.015–0.02 |
| Real-ESRGAN general-x4v3 on a 1 MP input | ≈ 3–8 s per image on CPU (estimate: 2.4 MFLOP per input pixel) | ≤ $0.004 for 4 images |
| Image-to-video: Wan2.2-I2V-A14B + lightx2v 4-step, 480p, H100 | ≈ 30–45 s compute, plus a 30–90 s cold start (about 28 GB fp8 experts and the T5 encoder) | **≈ $0.06–0.13 per clip** when 2–3 clips share one cold start |
| Image-to-video: Wan2.2-TI2V-5B undistilled, 720p, L40S | ≈ 525 s (Wan's 4090 figure) | ≈ $0.30 per clip |

## 5. Honesty and disclosure (YouTube policy, checked 2026-09-27)

Sources: the YouTube Help article "Disclosing use of GenAI content" (support.google.com/youtube/answer/14328491)
and the YouTube Data API `videos` resource.

- **No disclosure needed:** "color adjustment or lighting filters", "special effects filters, like adding
  background blur or vintage effects", and "video sharpening, upscaling or repair". Camera moves, crops,
  detail zooms, split-screen and PiP, and small 2.5D parallax invent no events.
- **Disclosure required:** "alter footage of a real event or place" and "generate a realistic-looking scene
  that did not actually occur". Animating a historical photo with image-to-video falls here.
- **How to disclose:** the API field is `status.containsSyntheticMedia` on `videos.insert` and
  `videos.update`, available since the 2024-10-30 API revision.
- **Our gap:** we publish through Buffer, and it is **unverified** whether Buffer can set this flag. Doing it
  ourselves would need a write-scope OAuth token; the pipeline is read-only today.
- **Where our techniques fall:**
  - **Safe:** camera-only motion, 2.5D parallax at small amplitudes, and a mild upscale.
  - **Avoid:** face restoration, which changes faces, and colourisation, which invents colours.
  - **Label and restrict:** image-to-video.

## 6. Per-repo notes

### A. 2.5D and parallax renderers

#### BrokenSource/DepthFlow

**Verified:** 1,547 stars, last push 2026-08-25, AGPL-3.0, not archived. Code read at version 1.0.1.

**Pipeline:**

1. Load the image.
2. Estimate depth, or accept a supplied depth map.
3. Upload the image and depth as textures.
4. A GLSL fragment shader ray-marches the depth as a height field, per pixel, per frame (parallax occlusion
   mapping).
5. Optional post effects: lens distortion, depth of field, vignette, inpaint, and colour (including sepia).
6. Read the frames back and pipe them to FFmpeg.

**Key files:**

- **Depth estimator:** `depthflow/estimators/anything.py`.
  - The default is `DepthAnythingV2` with `model = Small` (L22). It loads
    `depth-anything/Depth-Anything-V2-{Small|Base|Large}-hf` through transformers (L74–98, L82).
  - Post-processing, `_post` (L95–98): `gaussian_filter(sigma=0.6)` then `maximum_filter(size=5)`. The
    max filter dilates near regions, so edge stretching lands on the background, not the subject. V1 uses
    sigma 0.3 (L66–69).
- **Camera state:** `depthflow/state.py` L108–146.
  - `height=0.20` ("Peak surface height, the parallax intensity").
  - `steady=0.05` ("Focal depth for offsets, the pivot point of the effect").
  - Also `focus`, `zoom`, `isometric=0.30`, `dolly`, and `offset=(x, y)`.
  - Sub-states for vignette, inpaint, and colours at L149–157.
- **Shader:** `depthflow/resources/depthflow.glsl` L52–108 is a two-stage ray march: forward probe steps
  of `1/mix(50,120,quality)`, then backward refinement at `1/mix(200,2000,quality)`, looping up to 1,000
  iterations per pixel. Normals come from depth derivatives (L100–102). Lens effect L162–169; blur
  L177–178; sepia L212.
- **Preset motions:** `examples/presets.py`.
  - `Vertical` and `Horizontal`: `offset = 0.8*sin(cycle)`, `isometric 0.6`, `steady 0.3`.
  - `Dolly`: `height 0.30, steady 0.35, focus 0.35, zoom 0.95, isometric 0.5*(1-cos(cycle))`.
  - Also `Circle` and `Orbital`.
- **Batch rendering:** `examples/batch.py` L19–60 subclasses `DepthScene`, uses
  `MyAnimation(backend="headless")`, and calls `scene.main(output=..., time=5, ssaa=1.5)`.
  - Version 1.0 dropped the old CLI presets and batch mode in favour of Python scripts. The 0.9.x legacy
    line still has them but is capped at Python 3.13 with a pinned imgui.
- **Input guidance** (`website/docs/inputs.md`): "Wires, fences, posts, hair threads, and small details
  *will* cause artifacts", and "use images with a clear central object". The scene size matches the input;
  "matching aspect ratios isn't required". Crop to 9:16 first.

**Headless on Linux:** see ShaderFlow below. On a GPU it uses the NVIDIA glvnd EGL ICD; without one, it
falls back to Mesa llvmpipe (docs call it "slow").

**Speed at 1080×1920:**

- GPU: the author reports about 580 fps raw at 1080p on an RTX 3060, so about 3–5 s per 5 s clip once
  x264 encoding is included.
- CPU: the author reports about 2 fps with a 5900X at 100%, so about 75–115 s per clip.

**Better than ours:** real occlusion-aware 2.5D, a focus-plane pivot, and ready-made moves.
**Worse:** needs OpenGL, which Modal GPUs may not expose (see BrokenSource). CPU rendering costs about 10×
our DIY warp. Archive photos with wires, poles, or hair will artefact.

**Adoption:**

- **Tool:** run it unmodified as a separate process or container; AGPL is fine to run. AGPL §13 only binds
  a *modified* program offered to network users, and output videos are not covered works. Never copy its
  code into our repo.
- **Idea:** re-implement focus-plane displacement in our own torch code (§6 in the TL;DR; M effort).
- **Risks:** Modal GPU OpenGL status in 2026 is unverified. Test with a one-minute T4 function that prints
  `ctx.info["GL_RENDERER"]`; "llvmpipe" means no GPU GL.

**Verdict: BORROW IDEA** (focus-plane parallax, the `_post` depth clean-up, and the preset curves). Adopt it
as a tool only if the T4 EGL test passes; on CPU it doubles our cost per Short.

#### BrokenSource/ShaderFlow (DepthFlow's engine)

**Verified:** 148 stars, last push 2026-08-15, AGPL-3.0, not archived.

**Key code:** `shaderflow/scene.py`.

- L41–57: `WindowBackend.infer` picks the headless backend.
- L139–157: on Linux it creates the context through moderngl-window's headless window with an EGL
  backend, via glcontext.
- On a CPU-only container, Mesa's EGL gives llvmpipe (packages `libegl1`, `libegl-mesa0`,
  `libgl1-mesa-dri`).

**Verdict: SKIP** as a direct dependency; only relevant through DepthFlow.

#### BrokenSource/BrokenSource (monorepo)

**Verified:** 48 stars, last push 2026-02-28, AGPL-3.0 at repo level. `docker/cloud/modal_com.py` carries
its own header: "(c) 2024, Tremeschin, MIT License".

**What `modal_com.py` shows:**

- L10–12: "The T4 GPU seems to be the only one with OpenGL acceleration enabled on Modal by default". For
  other GPUs you "ask the support team to enable `graphics, video`".
- Base image `nvidia/opengl:1.2-glvnd-runtime-ubuntu22.04` (L27).
- `@app.function(gpu="t4", cpu=4, memory=4096)` (L39).

**What `docker/include/opengl.dockerfile` shows (L2–22):** `NVIDIA_DRIVER_CAPABILITIES=all` and a glvnd EGL
vendor JSON pointing at `libEGL_nvidia.so.0`.

**Verdict: BORROW** the Modal and EGL recipe if we test DepthFlow on a T4.

#### provos/parallax-maker

**Verified:** 105 stars, last push 2026-09-26, AGPL-3.0, not archived.

**What it does:** an interactive tool (web UI) that exports glTF for Blender or Unreal. Key code in
`parallax_maker/segmentation.py`:

- `analyze_depth_histogram` (L46–68) splits depth into N equal-population slices.
- `create_slice_from_mask` makes feathered RGBA "cards".
- `render_view` (L150–219) warps each card with its own homography, using sub-pixel `cv2.warpPerspective`
  corners because rounding causes visible shifting, and composites back to front.
- `render_image_sequence` (L273–327) renders a dolly camera.

For a dolly-in, a nearer card scales by `d_card/(d_card - push)`.

**Better than ours:** it handles bigger moves than a single displacement warp.
**Worse:** a full UI with Blender or Unreal export, and AGPL.

**Verdict: BORROW IDEA.** Depth-quantised cards with per-card sub-pixel warps are the multi-plane
generalisation of §3.7. Do not use the tool itself.

#### sniklaus/3d-ken-burns

**Verified:** 1,572 stars, last push 2026-06-01, not archived. LICENSE file: **CC BY-NC-SA 4.0**
(non-commercial).

**Code:** `common.py`, `autozoom.py`, and `depthestim.py` import `cupy`, and the README says "Several
functions are implemented in CUDA using CuPy". It is CUDA-only.

**Verdict: SKIP.** Non-commercial licence and GPU-only.

#### vt-vl-lab/3d-photo-inpainting

**Verified:** 7,093 stars, last push 2024-08-30, **MIT** (LICENSE file), not archived.

It builds a layered depth image with learned inpainting and renders with vispy (OpenGL). It dates from
2020 and takes minutes per image.

**Verdict: SKIP.** Overkill for camera moves of 5% or less, and it brings the same headless OpenGL problems.

### B. Depth models (licences from HF model cards and the HF API)

| Model | Licence (verified) | CPU-feasible for one still? | Verdict |
|---|---|---|---|
| **Depth Anything V2 Small** (`depth-anything/Depth-Anything-V2-Small-hf`, 24.8M params) | **Apache-2.0** | Yes: about 1–2 s at 518 px (estimate). Runs in our transformers 5.17 with no new dependencies. | **ADOPT** |
| DA V2 Base and Large (`-Base-hf`, `-Large-hf`) | **CC BY-NC 4.0** | — | SKIP (non-commercial) |
| DA V1 Small, Base, Large (`LiheYoung/Depth-Anything`: 8,220 stars, pushed 2024-07-17) | Apache-2.0 in the repo LICENSE and HF cards. DepthFlow's docs say non-Small V1 is non-commercial: a conflict. | Yes | SKIP (superseded by V2) |
| DA3 Small and Base (`ByteDance-Seed/Depth-Anything-3`: 6,397 stars, pushed 2026-07-27, repo Apache-2.0) | Apache-2.0 | Yes | WATCH |
| DA3 Large and Giant | **CC BY-NC 4.0** | — | SKIP |
| **DA3MONO-LARGE** and DA3METRIC-LARGE | **Apache-2.0** | Slow (a Large ViT, about 5–15 s estimated) | WATCH. Its package needs numpy<2, xformers, and open3d; we have numpy 2.5, so it would need a separate Modal image. |
| Video Depth Anything Small (`DepthAnything/Video-Depth-Anything`: 2,203 stars, pushed 2025-10-07) | Apache-2.0 | — | SKIP (built for video) |
| Depth Pro (`apple-aiml-research/ml-depth-pro`: 5,730 stars, pushed 2026-09-11) | Code: Apple sample-code licence. Weights (`apple/DepthPro-hf`): **apple-amlr, research only**. | — | SKIP |
| Marigold (`prs-eth/Marigold`: 3,233 stars, pushed 2026-09-06, code Apache-2.0) | depth v1-1: OpenRAIL++. depth v1-0 and lcm-v1-0: Apache-2.0. | No (a Stable Diffusion 2 based diffusion model) | SKIP |
| MiDaS (`isl-org/MiDaS`: 5,418 stars) | MIT, **archived** (last push 2024-08-23) | Yes | SKIP (superseded) |
| MoGe-2 (`microsoft/MoGe`: 2,981 stars, pushed 2026-09-09) | MIT (LICENSE file, plus DINOv2 notices). `Ruicheng/moge-2-vitl-normal`: MIT. | ViT-S yes | WATCH (outputs geometry and point maps; extra dependencies) |
| Distill-Any-Depth (`Westlake-AGI-Lab/Distill-Any-Depth`: 693 stars, pushed 2025-04-21, MIT) | `xingyang1/Distill-Any-Depth-Small-hf`: MIT | Yes | WATCH. It is unverified whether the Large variants started from DA V2 Large's non-commercial weights, so use only Small if at all. |

### C. Segmentation, matting, and inpainting (for two-plane parallax)

#### ZhengPeng7/BiRefNet

**Verified:** 4,231 stars, last push 2026-09-02, MIT, not archived. Weights: `ZhengPeng7/BiRefNet_lite`
(MIT) and `onnx-community/BiRefNet_lite-ONNX` (MIT).

**Use:** runs on the onnxruntime 1.30 we already have, at 1024×1024 input with ImageNet normalisation and a
sigmoid mask output. Use it only when the mask covers about 5–60% of the frame in one connected component,
meaning a clear subject (portrait, statue, object). Documents and crowds get the flat camera.

**Verdict: ADOPT.**

#### danielgatis/rembg

**Verified:** 24,899 stars, last push 2026-09-20, MIT code.

**Licence trap:** its **default model is now BRIA RMBG-2.0**. `remove()` calls `new_session("bria-rmbg")`
(`rembg/bg.py` L324), and the README marks bria-rmbg as "**The default.**" (L507). `briaai/RMBG-2.0` is
tagged `bria-rmbg-2.0`, links to CC BY-NC 4.0, and is gated. Its permissive options are `birefnet-general`,
`birefnet-general-lite` (README L501), `isnet-general-use`, and `u2net`.

**Verdict: SKIP the package.** Call BiRefNet ONNX directly instead. If rembg is ever used, always pass
`-m birefnet-general-lite`.

#### facebookresearch/sam2 (SAM 2.1)

**Verified:** 19,928 stars, last push 2026-05-30, Apache-2.0. `facebook/sam2.1-hiera-small` is Apache-2.0.

**Idea:** box-prompted masks. The vision LLM supplies the box of "the thing the line names", and SAM makes
the mask. That beats salient-object matting when the subject isn't the most prominent object in the frame.

**Verdict: WATCH** (use it if BiRefNet picks the wrong subject too often).

#### facebookresearch/sam3

**Verified:** 11,805 stars, last push 2026-09-18. Custom "SAM License". `facebook/sam3` is gated with
manual approval.

It segments from a text prompt (for example, "the emu"), which is attractive.

**Verdict: WATCH.** The custom licence and manual gating are obstacles.

#### advimman/lama and Carve/LaMa-ONNX

**Verified:** 10,280 stars, last push 2025-02-05, Apache-2.0. `Carve/LaMa-ONNX` is Apache-2.0, with a fixed
512×512 input, and runs on onnxruntime.

**Verdict: BORROW** only for lateral parallax moves that expose holes. A push-in doesn't need it.

### D. Image-to-video (for paintings and landscapes only)

#### Wan-Video/Wan2.2

**Verified:** 17,650 stars, last push 2026-09-21, Apache-2.0, not archived. Weights
`Wan-AI/Wan2.2-TI2V-5B` and `Wan-AI/Wan2.2-I2V-A14B` are Apache-2.0.

**Timing table** (`assets/comp_effic.png` in the clone):

- TI2V-5B at 720p: about 525 s on one RTX 4090, 22.8 GB peak.
- I2V-A14B: 328 s at 480p and over 1,000 s at 720p on one H100.

**Version check:** the Wan-AI HF organisation has no open Wan 2.5, 2.6, or 2.7 weights. Blog claims of an
"open Apache-2.0 Wan 2.7" are false.

**Distilled checkpoints:**

- **lightx2v** (repo `ModelTC/LightX2V`: 2,860 stars, pushed 2026-09-26, Apache-2.0), all Apache-2.0 on HF:
  - `lightx2v/Wan2.2-Lightning` includes `Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1`.
  - `lightx2v/Wan2.2-Distill-Loras` has 4-step I2V-A14B LoRAs.
  - `lightx2v/Wan2.2-Distill-Models` has 4-step I2V-A14B checkpoints in fp8 and int8, plus a 720p build
    dated 2026-04-12.
  - Four steps with no classifier-free guidance, against the default 40 steps with guidance, is about
    1/20 of the transformer compute.
- **FastWan2.2-TI2V-5B** (`hao-ai-lab/FastVideo`: 4,508 stars, pushed 2026-09-27; model Apache-2.0):
  3-step DMD at 121×704×1280. But its `pipeline_tag` is text-to-video, and it was distilled data-free on
  **text-to-video**, so image conditioning is undocumented. Test it before relying on it.

**Honest use, if ever:**

- **Paintings and landscapes only**, never photos of real people.
- **Composite as a cinemagraph:** keep the original still everywhere except a mask over sky, water, or smoke
  (far depth from DA-V2-Small, minus BiRefNet subjects). Use FFmpeg `maskedmerge` so faces and people can
  never change.
- **Disclose:** set `status.containsSyntheticMedia` and show an on-screen "animated" label.
- **Resolution:** 480p output is upscaled 2.3× to fill the frame. That is acceptable for painted skies
  inside the mask.

**Cost:** ≈ $0.06–0.13 per clip (see §4). Effort L: a new GPU Modal function, about 30 GB of weights in a
Volume, prompt design, and masking.

**Verdict: WATCH.** It is the only licence-clean image-to-video path, but it is not a first priority, and
the Buffer disclosure gap has to be solved first.

#### lllyasviel/FramePack

**Verified:** 17,259 stars, last push 2025-10-16, Apache-2.0 code.

Its weights, `lllyasviel/FramePackI2V_HY` (no licence tag on HF), are derived from HunyuanVideo and so fall
under the **Tencent Hunyuan Community License**. That licence's territory **excludes the EU, UK, and South
Korea**. Publicly displaying outputs on YouTube is a breach risk. Speed is about 1.5–2.5 s per frame on a
4090, roughly $0.12–0.20 per clip.

**Verdict: SKIP.**

#### Tencent-Hunyuan/HunyuanVideo-1.5

**Verified:** 4,560 stars, last push 2026-04-10. `tencent/HunyuanVideo-1.5` uses the
`tencent-hunyuan-community` licence, not Apache-2.0 as some blogs claim. It has the same territory clause.

**Verdict: SKIP.**

#### Lightricks/LTX-Video and Lightricks/LTX-2

**Verified:**

- LTX-Video: 10,991 stars, last push 2026-01-05. Code Apache-2.0. Weights under the "LTX-Video Open Weights
  License 0.X": royalty-free, but use restriction (e) forbids placing content "without expressly and
  intelligibly disclaiming that the … content is machine generated".
- LTX-2: 9,533 stars, last push 2026-08-26. The LTX-2 Community License (also for LTX-2.3 fp8; not
  "Apache 2.0" as blogs claim) is free below $10M annual revenue and has the same disclaimer duty.

Monetised individual use is therefore free, but every output must be labelled as machine-generated.

**Verdict: WATCH.**

#### MiniMaxAI/MiniMax-H3 (Hugging Face, August 2026)

A 33B image+text-to-video model with audio. Its `minimax-h3-community-license-agreement` requires an
application for use in the **USA**, EU, UK, and South Korea.

`lightx2v/Minimax-h3-Turbo` is tagged Apache-2.0, but it is a distill of H3, so the base licence still
governs. It is also heavy: H100 or H200 class.

**Verdict: SKIP.**

### E. Upscaling, restoration, and colourisation

#### xinntao/Real-ESRGAN

**Verified:** 36,918 stars, last push 2024-08-06, BSD-3-Clause (code and release weights), not archived.

**The model to use:** `realesr-general-x4v3` is `SRVGGNetCompact(num_feat=64, num_conv=32, upscale=4,
act_type='prelu')`, set up at `inference_realesrgan.py` L79–84.

- **Denoise control:** blend it with `realesr-general-wdn-x4v3` using DNI weights
  `[denoise_strength, 1 - denoise_strength]` (L99–104). Use about 0.5 to keep some grain.
- **Vendor the architecture:** `realesrgan/archs/srvgg_arch.py` is a 69-line file that needs only torch
  once the basicsr registry decorator is dropped.
- **Avoid `basicsr`:** its last PyPI release, 1.4.2 (2022-08-30), imports
  `torchvision.transforms.functional_tensor` in `basicsr/data/degradations.py` L8, which newer torchvision
  removed. Our venv has no torchvision at all.

**When to use it:** only when the source-to-output magnification exceeds 1.3×. Typical cases are portrait
cover crops, detail zooms, and small Met/AIC/NASA files. Use ×2 output. Don't apply it to faces or document
text crops: a GAN invents texture there.

**Verdict: ADOPT** (small model, CPU, BSD-3).

#### chaiNNer-org/spandrel

**Verified:** 315 stars, last push 2026-04-12, MIT.

A generic loader for many super-resolution architectures. Its dependencies weren't checked.

**Verdict: WATCH** (vendoring the 69-line class is lighter).

#### SwinIR, Swin2SR, and HAT

**Verified:**

- `JingyunLiang/SwinIR`: 5,598 stars, last push 2024-05-14, Apache-2.0.
- `mv-lab/swin2sr`: 695 stars, last push 2024-08-19, Apache-2.0. `caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr`
  is Apache-2.0 and runs in transformers.
- `XPixelGroup/HAT`: 1,596 stars, last push 2024-06-02, Apache-2.0.

These transformer super-resolution models are one to two orders of magnitude slower on CPU than
SRVGGNetCompact, for little visible gain at our 1080p output.

**Verdict: SKIP for now.**

#### TencentARC/GFPGAN

**Verified:** 37,682 stars, last push 2024-07-26. Licence "other": Apache-2.0 plus NVIDIA StyleGAN2
(non-commercial) and DFDNet (CC BY-NC-SA) components. It regenerates faces.

**Verdict: SKIP.**

#### sczhou/CodeFormer

**Verified:** 18,166 stars, last push 2025-11-18. **S-Lab License 1.0 (non-commercial).**

**Verdict: SKIP.**

#### microsoft/Bringing-Old-Photos-Back-to-Life

**Verified:** 15,722 stars, last push 2023-10-26, MIT.

Stale, with a heavy dependency stack, and its face-enhancement stage alters faces.

**Verdict: SKIP.**

#### piddnad/DDColor and jantic/DeOldify

**Verified:**

- `piddnad/DDColor`: 1,503 stars, last push 2026-01-17, Apache-2.0 (code and weights).
- `jantic/DeOldify`: 18,479 stars, **archived** 2024-10-19, MIT.

**Colourisation is not advisable** for a history channel. It invents the colours of real uniforms, skin,
and flags, and historians object to it. If it is ever used, label it "colourised". The grade in §3.4 gives
visual unity without inventing anything.

**Verdict: SKIP.**

### F. FFmpeg references

#### rendi-api/ffmpeg-cheatsheet

**Verified:** 1,744 stars, last push 2026-04-29, **no licence** (all rights reserved), so take ideas only.

**Useful parts:**

- Its Ken Burns tip is to upscale before `zoompan` to reduce jitter (trac #4298). Our measurement: a 4×
  canvas only halves the judder, and `perspective` removes it.
- `skills/ffmpeg/references/command-patterns.md` L110–114: an `xfade` slideshow.
- `skills/ffmpeg/SKILL.md` L83–88: a timed overlay with `enable='gte(t,1)*lte(t,7)'`.

Everything else is generic.

**Verdict: BORROW IDEA** (minor).

#### scriptituk/xfade-easing

**Verified:** 124 stars, last push 2026-09-09, MIT.

It provides eased custom `xfade` expressions, for example cubic in-out wipedown (README L75–88):
`st(0,if(lt(P,0.5),4*P^3,1-4*(1-P)^3));if(gt(Y,H*(1-ld(0))),A,B)`.

It needs `-filter_complex_threads 1`, because the `st()`/`ld()` state is shared between slice threads.
Per-pixel evaluation is slow, but that's fine for a 0.3 s transition. FFmpeg 7.1's built-in `xfade`
transitions (fades, wipes, slides, zooms) need no expressions.

**Verdict: BORROW IDEA**, for one or two accent transitions per Short (for example, on the twist). Keep
hard cuts as the default.

#### mifi/editly

**Verified:** 5,510 stars, last push 2025-05-12, MIT.

It is a Node, headless-gl, and fabric stack. Its README Ken Burns is `zoomDirection` plus `zoomAmount`
(linear).

**Verdict: SKIP.** After change #1 it offers nothing we lack.

## Top insights for Days of Odd

1. **Swap `zoompan` for the eased sub-pixel `perspective` camera.**
   - Effort S. About +1.4 s per clip, or ≈ $0.002–0.004 per Short.
   - Judder drops from 0.433 to 0.008 px per frame, and every clip gains ease-in and ease-out.
   - Code sketch in §3.1. Remember `-framerate 30` on the input and the `loop` filter after the scale.
2. **Stop cover-cropping wide pictures.**
   - For aspect ratios of about 1.0 or wider, fit the whole image over a blurred, darkened copy with a
     1.00→1.08 push (§3.3). Effort S, cost ≈ $0.
   - It shows 100% of the picture instead of 37–42%, and avoids upsampling 1,200 px sources 2.7×.
   - This goes straight at "the picture didn't show what the line says" when the subject was cropped out.
3. **Make the picture point at the words.**
   - Extend the vision-LLM ranking output from a focus point to a box, `(x0, y0, x1, y1)`, around the thing
     the line names, plus a treatment: `cover` / `fit` / `detail` / `parallax_subject` / `parallax_depth` /
     `document`.
   - Render a detail zoom, or a punch-in cut on the caption's emphasis word, into that box (§3.2).
   - That gives two shots per beat from one still at ≈ $0 extra. Cap zoom at about 1.3× unless the image
     is upscaled.
   - Add each beat's *end* frame to the Gemini contact sheet so the reviewer judges the crop viewers
     actually land on.
4. **Use one grade and vignette for the whole Short, before the captions, with no heavy grain** (§3.4).
   - Effort S, bitrate roughly neutral.
   - Heavy grain made files 4.7× larger and would break the 40 MB cap; light grain (`c0s=3`) costs about
     +22%.
   - No colourisation.
5. **Two-plane push-in parallax for clear-subject stills** (§3.7).
   - Mask from `onnx-community/BiRefNet_lite-ONNX` (MIT) on the onnxruntime we already have.
   - Foreground 1.00→1.10, background 1.00→1.04, centred on the subject, so no inpainting is needed.
   - Effort M. About 8 s per clip locally, ≈ $0.005 per Short on 3 beats.
   - Gate on the mask covering 5–60% of the frame in one component.
6. **Depth-displacement parallax for deep scenes.**
   - `depth-anything/Depth-Anything-V2-Small-hf` (Apache-2.0) through our transformers install. Clean the
     depth like DepthFlow: gaussian sigma 0.6, then a size-5 maximum filter.
   - Then 3 fixed-point iterations of torch `grid_sample`: `src = grid + offset*(depth(src) - focus)`, with
     the focus at the subject's depth, an offset of about 0.02–0.05 in grid units, and a 1.00→1.06 zoom.
   - Effort M. 5–10 s per clip, ≈ $0.005–0.03 per Short.
   - Run DepthFlow itself (AGPL, as a separate container) only if a T4 `GL_RENDERER` check shows NVIDIA and
     not llvmpipe. On CPU it would roughly double our cost per Short.
7. **Real-ESRGAN `realesr-general-x4v3` (BSD-3), only when magnification exceeds 1.3×.**
   - Vendor the 69-line `SRVGGNetCompact`, blend with the wdn model at denoise 0.5, and output ×2.
   - Never on faces or document text crops. Never GFPGAN or CodeFormer.
   - ≤ $0.004 per Short.
8. **Add two designed-shot templates the planner can request** (§3.8): a split-screen comparison with a
   slide-in second half, and a PiP inset over a document or map. Both graphs are tested, run in 1–3 s, and
   cost ≈ $0.
9. **Image-to-video: not now.** If it is ever tried:
   - Wan2.2-I2V-A14B plus the lightx2v 4-step distill (all Apache-2.0), paintings and landscapes only.
   - Mask-composite onto the original still, set `containsSyntheticMedia`, and show an on-screen label.
   - ≈ $0.06–0.13 per clip (estimate). Solve Buffer's missing disclosure flag first.
10. **Licence traps to hard-code as "never":**
    - rembg's default model (RMBG-2.0), DA V2 Base/Large, DA3 Large/Giant, Depth Pro weights,
      3d-ken-burns, CodeFormer, and GFPGAN.
    - FramePack and HunyuanVideo (territory clause) and MiniMax-H3, including its "Apache" Turbo distill.
    - LTX-2 only with a machine-generated disclaimer.
