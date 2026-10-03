# Winton rights-cleared private cut — 4 October 2026

**Status:** Private local candidate. The withdrawn public upload `v4rp0oWvgSI` remains private. No Buffer post, Cloudinary host, YouTube upload, publishing state, global hold, or earlier Modal backup was changed. This cut supersedes the AP-still candidates described in `narration-candidate-review.md` and `visual-upgrade-review.md`.

## Exact media and editorial content

| Check | Result |
|---|---|
| MP4 | `ep045-rights-clear-private.mp4` (ignored by Git), 11,768,073 bytes, SHA-256 `c1da9edb41de6b002d0b28b952bffd1d48e0020d29c10be2acb8140ebaf65549` |
| Spec and manifest | `short.yaml` SHA-256 `8c95c773459cd24aa642a35683e058192f31f3837ea819e54375f32490c40745`; `work/manifest.json` SHA-256 `8b8a07ee81bb6f29b4a4321f0055a8c289dc22e596c76a309517675604cee6c1`; manifest binds the MP4 hash |
| Decode and format | Full FFmpeg video and audio decode passed; H.264 1080 × 1920 at 30 fps, AAC audio, 29.453 seconds |
| Audio | 73 spoken words; −14.3 LUFS integrated, −1.7 dBFS true peak, automated warnings `[]`. The noise-based riser at the invasion transition was removed after an independent screen called it static-like. |
| Speech | `small.en` heard all words in the **finished MP4** with zero differences. Narration WAV ASR alone heard final “Prague” as “that proc”; the exact MP4 and [independent audio-only screen](narration-rights-clear-audio-screen.json) both heard “Prague station” and the full first line. The independent screen found no uncertain words, glitches, pronunciation concerns, or music masking. |
| Visuals | [Opening at 0.1, 1.5, 2.2 and 3.5 s](rights-clear-opening.jpg), [29-frame one-per-second sweep](rights-clear-sweep.jpg), and seven shot midpoints in [sheet](sheet.jpg) were inspected at phone size. Winton's face, date label, `TRAIN NEVER LEFT`, captions and 250 count are readable; no blank frame or text collision was seen. The native-pixel [crop comparison](rights-clear-crop-compare.jpg) preserves the tighter portrait framing and detail. |

The first beat states, “A train meant to rescue 250 children never left Prague.” The [Winton family](https://www.nicholaswinton.com/exhibition/kindertransport) and [BBC retrospective](https://news.bbc.co.uk/2/hi/uk_news/8227929.stm) support the planned transport, count and date. [USHMM](https://encyclopedia.ushmm.org/content/en/article/nicholas-winton-and-the-rescue-of-children-from-czechoslovakia-1938-1939) supports the 669 total and team role; the [family recognition account](https://www.nicholaswinton.com/exhibition/recognition-1988) supports the scrapbook's later publicity. The script does not claim boarding or a survival count for the cancelled transport.

## Image rights and context

The new first and fifth-beat portrait is [Hynek Moravec's photograph of Winton in Prague in October 2007](https://commons.wikimedia.org/wiki/File:Winton_Nicholas_4637.jpg). The Commons file wikitext identifies Moravec as photographer, says `self-photographed`, and carries his `{{self|GFDL|cc-by-3.0}}` grant. The API confirms CC BY 3.0 with [license terms](https://creativecommons.org/licenses/by/3.0/) permitting commercial reuse and adaptations with attribution. The tracked [derivative receipt](assets/winton-2007-portrait-cover.source.json) binds the source SHA-256, native 842 × 1600 pixel crop, and output SHA-256. The image is visibly labeled `WINTON • 2007 PHOTO`; it depicts neither the 1939 transport nor the scrapbook discovery. No Associated Press still is used in this MP4.

The 1931 Prague station photograph is labeled as a location view, and the 2015 memorial photograph is credited to ŠJů with sculptor Flor Kent. The generated 1,997-byte YouTube description lists all three image authors, source pages and licenses, plus direct links to the CC BY 3.0 and CC BY 4.0 license terms. The 2007 portrait crop is identified as a crop in its credit line. Designed cards carry the 669 count and 1 September 1939 dateline without presenting invented footage.

## Release status

The exact MP4 has been copied into held [episode `ep054`](../ep054/release-prep.md) as a prospective new upload, because old `ep045/publish.json` records the withdrawn sent post. The package has its own spec, manifest and media hashes; the old upload and backup are retained. Remaining human gates are native full-length listening, full-motion phone playback, and independent editorial signoff on this exact MP4 and title/description. A hosted-asset hash and Buffer/YouTube readback are still required during any coordinated release. The global and per-episode holds remain active.
