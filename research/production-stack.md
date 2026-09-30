**Bottom line:** everything except AI images and video runs on the 4-core CPU with commercially clean licenses: MoneyPrinterTurbo fed your own scripts, Kokoro narration, FFmpeg-burned word captions, stock or public-domain B-roll, and Apache-2.0 image models on borrowed GPU time. The biggest trap is `edge-tts`, the free voice in most of these pipelines. Stars and releases were pulled with `gh api` today; CPU speeds are extrapolated from other hardware.

### 1. End-to-end generators

| | Stars, latest release | License | Own script | TTS/caption swap | 4-core CPU |
|---|---|---|---|---|---|
| **[MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)** (top) | 125.8k, v1.3.7, 13 Sep 2026 | MIT | Yes | Easy: 11 TTS backends incl. Kokoro/Chatterbox; TTS-timed or faster-whisper subtitles | Yes (minimum 4 cores/4 GB) |
| **[Pixelle-Video](https://github.com/ATH-MaaS/Pixelle-Video)** (backup) | 28.4k, v0.1.15, 27 Jan 2026 | Apache-2.0 | Yes (fixed-script mode) | Via ComfyUI workflows | Visuals need a ComfyUI GPU |

[Verticals](https://github.com/rushindrasinha/youtube-shorts-pipeline) (MIT, 2.3k, v3.1.0 Jun 2026) takes your draft but needs Gemini for visuals; ShortGPT is stale (Feb 2025).

### 2. TTS

| | Stars, release | License (all commercial-OK) | 4-core CPU |
|---|---|---|---|
| **[Kokoro-82M](https://github.com/hexgrad/kokoro)** (top) | 9.0k, untagged, last push Aug 2025 | Apache-2.0 weights | 1.3–2× real time ([benchmark](https://heyneo.com/blog/kokoro-supertonic-inflect-nano-cpu-tts-benchmark)); emits word timestamps |
| **[Pocket TTS](https://github.com/kyutai-labs/pocket-tts)** (backup) | 9.7k, v3.3.0, 24 Sep 2026 | MIT code, CC-BY-4.0 weights (attribution; gated) | Vendor claims ~6× real time on 2 M4 cores |
| [Chatterbox](https://github.com/resemble-ai/chatterbox) | 26.6k, v0.1.2, Jun 2025 | MIT | Turbo slower than real time; Nano claims 3× on 8 cores |
| [KittenTTS](https://github.com/KittenML/KittenTTS) | 15.5k, 0.8.1, Feb 2026 | Apache-2.0 | 15–80M ONNX, CPU-first |

Piper moved to a [GPL-3.0 repo](https://github.com/OHF-Voice/piper1-gpl) with per-voice licenses; its popular `lessac` voice is [research-only](https://www.cstr.ed.ac.uk/projects/blizzard/2013/lessac_blizzard2013/license.html). StyleTTS2's pretrained models require telling listeners the speech is synthetic. Orpheus, Dia and Qwen3-TTS are Apache-2.0 but GPU-class. **Avoid:** F5-TTS weights (CC-BY-NC-4.0), XTTS-v2 (Coqui CPML), OpenAudio/Fish (CC-BY-NC-SA), VibeVoice (Microsoft says research only).

**`edge-tts` is not acceptable.** It impersonates the Edge browser using a hard-coded client token. The [Microsoft Services Agreement](https://www.microsoft.com/en-us/servicesagreement) bans circumventing access restrictions (§3(a)(vi)) and emulating "any software or other aspect of the Services" (§8(b)(ii)). A [Microsoft Q&A answer](https://learn.microsoft.com/en-au/answers/questions/5730260/inquiry-about-using-read-aloud) finds no permission to publish Read Aloud audio and points to Azure. The licensed route is [Azure Speech F0](https://azure.microsoft.com/en-us/pricing/details/speech/), with 0.5M free neural characters a month.

### 3. Captions

| | Stars, release | License | CPU |
|---|---|---|---|
| **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** (top) | 25.6k, v1.2.1, Oct 2025 | MIT | `small` int8 transcribed 13 min in 1m42s on 8 threads |
| **[WhisperX](https://github.com/m-bain/whisperX)** (backup) | 24.2k, 3.8.7rc1, Jun 2026 | BSD-2 | Adds wav2vec2 forced alignment |
| [stable-ts](https://github.com/jianfch/stable-ts) | 2.3k, archived | MIT | `align()` fits a known script; unmaintained |

With a known script, use Kokoro's timestamps or forced alignment, not transcription. Burn in per-word ASS events (`\k` karaoke, `\t` pops) with FFmpeg/libass, the fastest CPU path. Backup: [pycaps](https://github.com/francozanardi/pycaps) (MIT, 217 stars), CSS templates rendered in headless Chromium (slower).

### 4. Visuals

- **[Pexels](https://www.pexels.com/license/) (top):** commercial use, no attribution. Don't sell unaltered copies, show identifiable people in a bad light, or imply endorsement. The [API](https://www.pexels.com/api/documentation/) requires a prominent Pexels link and allows 200 requests/hour, 20k/month.
- **[Pixabay](https://pixabay.com/service/license-summary/) (backup):** same model; crops and filters still count as "standalone" copies. The [API](https://pixabay.com/api/docs/) covers images and video only, requires 24-hour caching, and bans "systematic mass downloads."
- **[NASA](https://www.nasa.gov/nasa-brand-center/images-and-media/):** generally uncopyrighted; don't imply endorsement, and clear logos and identifiable people.
- **[Commons](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia):** per-file licenses; watch attribution, share-alike, personality and trademark rights.
- **[Library of Congress](https://guides.loc.gov/p-and-p-rights-and-restrictions/risk-assessment):** grants no permissions, and "no known restrictions" is not a guarantee.

**AI images:** [FLUX.2-klein-4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B) (top) and FLUX.1-schnell (backup) are Apache-2.0, as are Z-Image-Turbo and Qwen-Image. SD 3.5 and SDXL-Turbo are free only under $1M annual revenue. FLUX.1-dev allows commercial outputs but limits the model itself to non-revenue use; avoid it. On CPU, klein-4B took ~235 s per 512² image on a 24-thread i7 ([sd-flux2.cpp](https://github.com/adithyab94/sd-flux2.cpp)); expect 10+ minutes here.

[ZeroGPU](https://huggingface.co/docs/hub/en/spaces-zerogpu) gives free accounts 5 GPU-minutes a day (pass your HF token to `gradio_client`); a forum post reports an extra 3-runs/day cap (unverified). [Lightning's pricing page](https://lightning.ai/pricing/) lists 5 credits at signup plus 25 after adding a card (~75 T4-hours); third parties claim 15 a month.

**Video:** [Wan 2.2](https://github.com/Wan-Video/Wan2.2) (17.6k, Apache-2.0) runs its 5B model on a 4090-class GPU. [LTX-2](https://github.com/Lightricks/LTX-2) (9.5k, v1.3.0 Aug 2026) needs a paid license only at $10M+ revenue. HunyuanVideo's license excludes the EU, UK and South Korea. CPU-only generation isn't feasible.

### 5. Music/SFX

- **[YouTube Audio Library](https://support.google.com/youtube/answer/3376882) (top):** monetizable and not Content ID-claimed; Creative Commons tracks need description credit. Studio-only, no API.
- **[Pixabay Music](https://pixabay.com/service/faq/) (backup):** some tracks are Content ID-registered, so keep the license certificate for disputes. No API.
- FreePD has permanently closed.
- **Programmatic:** [Openverse](https://api.openverse.org/v1/) (`license_type=commercial`; anonymous 200 requests/day) and [Freesound](https://freesound.org/docs/api/overview.html) (CC0 filter; originals need OAuth2).
- **AI music:** ACE-Step 1.5 is MIT but wants a GPU.

### 6. Thumbnails

Use [Pillow](https://github.com/python-pillow/Pillow) templates (13.8k, 12.3.0 Jul 2026, MIT-CMU). For cutouts, [rembg](https://github.com/danielgatis/rembg) (24.9k, v2.0.85 Sep 2026, MIT) with u2net/isnet (Apache-2.0) or BiRefNet (MIT) models. No open-source thumbnail generator was worth adopting.

### 7. Research

- YouTube autocomplete (`suggestqueries-clients6.youtube.com/complete/search?client=youtube&ds=yt&q=…`) answered anonymously today but is undocumented.
- Since 1 Jun 2026, the Data API's [`search.list`](https://developers.google.com/youtube/v3/docs/search/list) has its own bucket of 100 calls a day.
- The official [Google Trends API](https://developers.google.com/search/apis/trends) is still an application-only alpha, and pytrends is archived. [trendspyg](https://github.com/flack0x/trendspyg) (MIT, v1.8.0 Sep 2026) is maintained but drives Chrome for keyword data.
- [vidIQ Free](https://support.vidiq.com/en/articles/13928456-features-credits-by-plan) gives 150 AI credits a month; TubeBuddy Free limits keyword research.

### Recommended stack

| Component | Tool | License |
|---|---|---|
| Orchestration | MoneyPrinterTurbo, Edge TTS off | MIT |
| Narration | Kokoro-82M (backup Pocket TTS) | Apache-2.0 |
| Word timing | Kokoro timestamps, faster-whisper | Apache-2.0, MIT |
| Caption burn-in | FFmpeg/libass | LGPL/GPL, ISC (tools only) |
| B-roll | Pexels, Pixabay, NASA, LoC | Site licenses, PD |
| AI images | FLUX.2-klein-4B on ZeroGPU/Lightning | Apache-2.0 |
| AI video | Wan 2.2 5B, rented GPU | Apache-2.0 |
| Music/SFX | Audio Library; Freesound/Openverse CC0 | YouTube terms, CC0 |
| Thumbnails | Pillow, rembg (isnet/BiRefNet) | MIT-CMU, MIT, Apache-2.0 |
| Research | Autocomplete, Data API, trendspyg | Google terms, MIT |

### License traps

1. `edge-tts`, built into MoneyPrinterTurbo, Verticals, ShortGPT and Pixelle-Video.
2. Non-commercial weights: F5-TTS, XTTS-v2, OpenAudio, MusicGen, the FLUX dev family (even via someone else's Space), rembg's `bria-rmbg`.
3. NC voices: Pocket TTS's "cosette" and "jean" (NC datasets).
4. Non-commercial code: YumCut (PolyForm Noncommercial); Remotion needs a company license above 3 employees.
5. Revenue and territory caps: Stability ($1M), LTX-2 ($10M), Hunyuan (no EU/UK/KR).
6. Policy, not license: YouTube demonetizes [templated, mass-produced AI content](https://support.google.com/youtube/answer/1311392) and requires [disclosure of realistic AI](https://support.google.com/youtube/answer/14328491).
