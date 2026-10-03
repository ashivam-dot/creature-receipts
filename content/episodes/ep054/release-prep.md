# ep054 held first-release package — Winton

**Status:** Held, pre-hosted, and not queued. `ep054.mp4` is ignored by Git and backed up in a [private Modal volume](private-modal-backup.json), with the stored bytes independently hashed. The exact file is also [hosted on Cloudinary](hold.json) and was downloaded and hash-checked; no Buffer post or YouTube upload exists for this package. `editorial_hold.json` and the channel-wide `status/scheduling_hold.json` both block scheduling. The withdrawn `ep045` upload `v4rp0oWvgSI` and its historical records remain private and intact.

The new `ep054.mp4` preserves the [ep045 rights-clear narration](../ep045/rights-clear-review.md) while replacing the station view with a verified [2017 CC0 aerial](assets/prague-station-2017-crop.source.json). It is 14,809,197 bytes, SHA-256 `6b43913005bbb9fade2e1f82ef5396a512c35a572004c1345b59da3f282bade0`. The old cut remains private and is a different file. This package’s bindings are:

| Field | SHA-256 |
|---|---|
| `media_sha256` | `6b43913005bbb9fade2e1f82ef5396a512c35a572004c1345b59da3f282bade0` |
| `spec_sha256` (`short.yaml`) | `9fa74905e2ce409432414129569f8342031168b4b9e4ae9109f26396d7f221fa` |
| `manifest_sha256` (`work/manifest.json`) | `1aa5e5747175c772987ebf10eb32964efd4f9562edf4bc9ead77f02e9d2dd1fa` |

`short.yaml` and the manifest both identify `ep054`; the package contains the local Winton and station derivatives, provenance receipt, research, script, visuals, narration and review frames. Manifest asset paths are relative to this package. The generated 2,054-byte description includes all three image credits, direct CC BY license links, the memorial crop notice, and the CC0 image source page. `media_binding()` returns the three hashes above; the bound `hold.json` names those exact hashes and the byte-verified URL. No `publish.json`, `withdrawal.json`, or `remote.json` was inherited. The scheduling guard still rejects ordinary scheduling under the current hold.

**Earliest configured evening slot:** Sunday **4 October 2026, 04:30 IST** (Saturday 3 October, 19:00 US Eastern). The next is 07:00 IST (21:30 Eastern). The [machine-only owner decision](machine-release-decision.json) approves one controlled schedule for the first slot after independent factual, rights, audio, frame and credit checks. No native human listening or full-motion phone review occurred, and those limitations are recorded in the decision. The hosted hash and empty Buffer queue have been checked; read back the created post's media URL, channel, title, description and due time before public send. Keep the old Winton video private.

## Controlled release under the channel hold

The channel hold stays in place. The exact reviewed video is already hosted in a bound `hold.json`, and its downloaded bytes match the media hash above. The one-time [machine-only decision](machine-release-decision.json) records the independent source/rights/editorial checks and the unavailable human listening and phone review; it does not claim those checks happened. After a fresh remote-ID and Buffer queue check, remove this package's `editorial_hold.json` only if all three local bindings still match. Add a **single** `release_allowlist` object to `status/scheduling_hold.json` with `episode_id: ep054`, the three exact hashes above, and an `expires_at_utc` timestamp with a UTC offset and a short review window. The guard compares the local video, spec, and manifest files, plus the spec and manifest episode IDs, before allowing the explicit reviewed-release command to reach Buffer. It checks again after any manifest media stamp. An expired, malformed, or mismatched entry fails closed. Keep `block_existing_queue: true`. The automatic scheduler and ordinary `ytc publish` still stop on the channel hold; queued edits, crossposts, and resends remain blocked.

Call `ytc publish content/episodes/ep054/short.yaml --at <offset-aware-slot> --reviewed-release` for the chosen slot. This entrypoint requires the active channel hold, a bound pre-hosted `hold.json`, and a fresh full download whose SHA-256 matches the reviewed media before any Buffer read or mutation. It cannot host in-line. Read back the created Buffer post's ID, channel, title, full text, due time and media URL. Once those match, put that exact ID in the hold as `approved_buffer_post_id`; the watchdog then exempts only that one queued post. Any other queued post still triggers the strict empty-queue alert. An approved ID is a watchdog exception only; it does not authorize another schedule. Keep the hold and old Winton upload private through the release. If any check fails, remove or pause the new Buffer post before its due time and restore the episode hold. Remove the two exception fields after the approved post has been sent and read back from YouTube.

This package contains **no** `release_allowlist` or `approved_buffer_post_id` now. Those values belong in the channel hold only at the reviewed release step; the current hold file is unchanged. Hosting is complete; scheduling and public send remain pending.

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
