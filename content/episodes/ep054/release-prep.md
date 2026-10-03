# ep054 held first-release package — Winton

**Status:** Local and private. `ep054.mp4` is ignored by Git; no Cloudinary URL, Buffer post or YouTube upload exists for this package. `editorial_hold.json` and the channel-wide `status/scheduling_hold.json` both block scheduling. The withdrawn `ep045` upload `v4rp0oWvgSI` and its historical records remain private and intact.

The [source cut and QA](../ep045/rights-clear-review.md) are bound to the exact same MP4 bytes. The copied `ep054.mp4` is 11,768,073 bytes, SHA-256 `c1da9edb41de6b002d0b28b952bffd1d48e0020d29c10be2acb8140ebaf65549`. Its package bindings are:

| Field | SHA-256 |
|---|---|
| `media_sha256` | `c1da9edb41de6b002d0b28b952bffd1d48e0020d29c10be2acb8140ebaf65549` |
| `spec_sha256` (`short.yaml`) | `b22e80cd740771c666ea0c6431ea14169f5bb9607d242782f89b1f4713014e12` |
| `manifest_sha256` (`work/manifest.json`) | `0a4e76658a043c62fcd8e863181406a9f2c560ae01dc7292102f26c20fdf8bef` |

`short.yaml` and the manifest both identify `ep054`; the package contains the local Winton and station derivatives, provenance receipt, research, script, visuals, narration and review frames. Manifest asset paths are relative to this package. The generated 1,997-byte description includes all three image credits and direct CC license/source links. `media_binding()` returns the three hashes above; the package has no inherited `publish.json`, `hold.json`, `withdrawal.json`, or `remote.json`. The scheduling guard was directly checked and rejected this package under the current hold.

**Earliest configured evening slot:** Sunday **4 October 2026, 04:30 IST** (Saturday 3 October, 19:00 US Eastern). The next is 07:00 IST (21:30 Eastern). Use the first only if exact-media native listening, phone playback, independent editorial signoff, hosted hash, queue inspection and controlled scheduling can finish by 04:00 IST. Otherwise use the next available reviewed slot; neither time is booked. Recheck the remote `main` tree for an `ep054` collision before integration, and read back the Buffer post's media URL, channel, title, description and due time before any public send. Keep the old Winton video private.

## Controlled release under the channel hold

The channel hold stays in place. After native listening, full-motion phone review, independent source/rights/editorial signoff, and a fresh remote-ID and Buffer queue check, host the exact reviewed video into a bound `hold.json`. Download that public URL and verify its SHA-256 against the media hash above. Then remove this package's `editorial_hold.json` only if all three local bindings still match. Add a **single** `release_allowlist` object to `status/scheduling_hold.json` with `episode_id: ep054`, the three exact hashes above, and an `expires_at_utc` timestamp with a UTC offset and a short review window. The guard compares the local video, spec, and manifest files, plus the spec and manifest episode IDs, before allowing the explicit reviewed-release command to reach Buffer. It checks again after any manifest media stamp. An expired, malformed, or mismatched entry fails closed. Keep `block_existing_queue: true`. The automatic scheduler and ordinary `ytc publish` still stop on the channel hold; queued edits, crossposts, and resends remain blocked.

Call `ytc publish content/episodes/ep054/short.yaml --at <offset-aware-slot> --reviewed-release` for the chosen slot. This entrypoint requires the active channel hold, a bound pre-hosted `hold.json`, and a fresh full download whose SHA-256 matches the reviewed media before any Buffer read or mutation. It cannot host in-line. Read back the created Buffer post's ID, channel, title, full text, due time and media URL. Once those match, put that exact ID in the hold as `approved_buffer_post_id`; the watchdog then exempts only that one queued post. Any other queued post still triggers the strict empty-queue alert. An approved ID is a watchdog exception only; it does not authorize another schedule. Keep the hold and old Winton upload private through the release. If any check fails, remove or pause the new Buffer post before its due time and restore the episode hold. Remove the two exception fields after the approved post has been sent and read back from YouTube.

This package contains **no** `release_allowlist` or `approved_buffer_post_id` now. Those values belong in the channel hold only at the reviewed release step; the current hold file is unchanged. Hosting, scheduling, and public send remain pending.

## Independent inspection

From the candidate worktree root:

```sh
shasum -a 256 content/episodes/ep054/ep054.mp4 content/episodes/ep054/short.yaml content/episodes/ep054/work/manifest.json
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate -of json content/episodes/ep054/ep054.mp4
cat content/episodes/ep045/assets/winton-2007-portrait-cover.source.json
cat content/episodes/ep045/rights-clear-review.md
cat content/episodes/ep045/narration-rights-clear-audio-screen.json
```

Play `content/episodes/ep054/ep054.mp4` from start to finish with sound and at phone size. Inspect `content/episodes/ep054/rights-clear-opening.jpg`, `rights-clear-sweep.jpg`, and `sheet.jpg` alongside the moving video. The audio-only model screen is a receipt, not a substitute for independent human listening.
