# ep054 first public release — Winton

**Status:** [Buffer post `6ac158d3fec5913394846da1`](publish.json) sent at **4 October 2026, 04:30 IST**. [Public Short `GeYxkROXScI`](https://www.youtube.com/shorts/GeYxkROXScI) was verified on the owned YouTube channel at 04:31 IST; the [readback receipt](public-readback.json) records the checks. `ep054.mp4` is ignored by Git and backed up in a [private Modal volume](private-modal-backup.json), with the stored bytes independently hashed. The exact file remains [hosted on Cloudinary](publish.json) and was downloaded and hash-checked. The channel-wide `status/scheduling_hold.json` remains active, with no approved post exception. The withdrawn `ep045` upload `v4rp0oWvgSI` remains private.

The new `ep054.mp4` preserves the [ep045 rights-clear narration](../ep045/rights-clear-review.md) while replacing the station view with a verified [2017 CC0 aerial](assets/prague-station-2017-crop.source.json). It is 14,809,197 bytes, SHA-256 `6b43913005bbb9fade2e1f82ef5396a512c35a572004c1345b59da3f282bade0`. The old cut remains private and is a different file. This package’s bindings are:

| Field | SHA-256 |
|---|---|
| `media_sha256` | `6b43913005bbb9fade2e1f82ef5396a512c35a572004c1345b59da3f282bade0` |
| `spec_sha256` (`short.yaml`) | `9fa74905e2ce409432414129569f8342031168b4b9e4ae9109f26396d7f221fa` |
| `manifest_sha256` (`work/manifest.json`) | `1aa5e5747175c772987ebf10eb32964efd4f9562edf4bc9ead77f02e9d2dd1fa` |

`short.yaml` and the manifest both identify `ep054`; the package contains the local Winton and station derivatives, provenance receipt, research, script, visuals, narration and review frames. Manifest asset paths are relative to this package. The generated 2,054-byte description includes all three image credits, direct CC BY license links, the memorial crop notice, and the CC0 image source page. `media_binding()` returns the three hashes above; the [publish record](publish.json) names those exact hashes and the byte-verified URL. No `withdrawal.json` or `remote.json` was inherited. The scheduling guard still rejects ordinary scheduling under the channel hold.

**Booked slot:** Sunday **4 October 2026, 04:30 IST** (Saturday 3 October, 19:00 US Eastern). The [machine-only owner decision](machine-release-decision.json) approved one controlled schedule after independent factual, rights, audio, frame and credit checks. No native human listening or full-motion phone review occurred; those limitations are recorded in the decision. The hosted hash, empty initial queue, and created post's media URL, channel, title, description, privacy and due time were checked, with results in the [readback receipt](buffer-readback.json). Keep the old Winton video private.

## Controlled release under the channel hold

The channel hold stays in place. The reviewed release used a short-lived, exact-hash allowlist only while scheduling this one post. It required a bound pre-hosted `hold.json`, downloaded the hosted video to check its SHA-256, checked the video/spec/manifest binding, and read the empty Buffer queue before creating the post. After the successful scheduling readback, the allowlist was removed and only `approved_buffer_post_id: 6ac158d3fec5913394846da1` remained in the channel hold until public verification. That post ID was removed after the public result passed; `block_existing_queue: true` remains set. Automatic scheduling, ordinary `ytc publish`, queued edits, crossposts, and resends remain blocked.

The initial Buffer readback returned `scheduled`, the correct YouTube channel, public privacy, exact title/text/media URL, and the intended due time. After the slot, Buffer returned `sent` with no error and an empty scheduled queue. The owned YouTube Data API returned the same title and description, channel `UC6e6OB3iw3yp8JnnBYxLItA`, public privacy, successful processing, 30-second duration, and an original file size of 14,809,197 bytes. An anonymous download of the public video fully decoded with H.264 video and AAC audio; frames sampled at 1 fps matched the approved source with SSIM 0.980113. See the [public readback](public-readback.json) for the media hashes and observed fields. The old ep045 upload remains private.

This package contains no `release_allowlist`; the channel hold no longer names an approved Buffer post ID. Hosting, public send, and YouTube readback are complete. The channel hold continues to block new releases.

## Independent inspection

From the candidate worktree root:

```sh
shasum -a 256 content/episodes/ep054/ep054.mp4 content/episodes/ep054/short.yaml content/episodes/ep054/work/manifest.json
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate -of json content/episodes/ep054/ep054.mp4
cat content/episodes/ep054/assets/winton-2007-portrait-cover.source.json
cat content/episodes/ep054/assets/prague-station-2017-crop.source.json
cat content/episodes/ep045/rights-clear-review.md
cat content/episodes/ep054/post-rerender-audio-screen.json
```

The current release decision used decoded-frame and machine-audio checks, with their limits recorded in `machine-release-decision.json`. A later native listener can play `content/episodes/ep054/ep054.mp4` from start to finish with sound and at phone size, then inspect `rights-clear-opening.jpg`, `rights-clear-sweep.jpg`, and `sheet.jpg` alongside the moving video. The prior ep045 video screen is historical evidence and does not bind this render.
