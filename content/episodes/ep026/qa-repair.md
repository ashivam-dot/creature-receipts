# ep026 private draft QA — 2026-10-03

## Editorial and source check

The seven revised spoken beats map to the direct receipts in [research.md](research.md). Beats 3 and 4 use the Wisconsin State Climatology Office's wind and duration wording. The 110 mph wind, 2,000°F temperature, “freezing” river, 400-mile distance, and claim that Peshtigo was simply “forgotten” are gone. The public description generated from short.yaml includes the three cited source URLs and all four historical image credits.

## Private render

- Local, unhosted draft: [ep026-revised-private-draft.mp4](ep026-revised-private-draft.mp4). Git ignores MP4 files; the exact bytes were copied from the isolated worktree into this checkout for review. It has not been uploaded, scheduled, or published.
- SHA-256: c9c1237ee6f6215570d066f793d1cd8e3caa80c8de0881e6788aa9e4650331e7.
- Rendered from the revised short.yaml using the pipeline's current Kokoro am_fenrir voice at speed 1.15. Seven beats, 62 spoken words, 27.06 seconds.
- Video: H.264, 1080 × 1920, 30 fps, yuv420p. Audio: AAC, 48 kHz stereo. File size: 11.89 MB.
- Automated check: −14.4 LUFS integrated, −1.7 dBFS true peak, no duration, loudness, peak, or asset warnings.
- New work/manifest.json and work/speech.json correspond to this draft. The older review.json is from the rejected version and has not been used as approval.

## Visual check

I inspected the seven middle-of-beat frames at 540 × 960 phone scale in [beats 1–4](../../../reports/previews/ep026-repair-sheet-1.jpg) and [beats 5–7](../../../reports/previews/ep026-repair-sheet-5.jpg). All four archival selections loaded; the date and two fact cards rendered; captions and prominent card text were legible at that scale. The selected images match the described event and time:

1. September 1871 bird's-eye lithograph of Peshtigo, explicitly labeled “before the fire.”
2. October 8, 1871 dateline card.
3. Contemporary 1871 Peshtigo fire engraving, replacing the modern Umatilla fire photo.
4. “UNDER 2 HOURS” fact card, replacing the unsupported temperature card.
5. 1871 Peshtigo River refuge engraving, with no claim to identify Pernin within it.
6. “TWO BUILDINGS” fact card, replacing the unrelated cemetery painting.
7. 1871 Chicago fire newspaper engraving only during the Chicago line.

The opening and wind beats no longer repeat the same artwork. Rights, dates, and source limits are itemized in research.md. This is a still-frame inspection; full-motion visual approval remains for a human reviewer.

## Narration check and remaining gate

Automated speech recognition heard the complete script in order. It transcribed “Peshtigo” as “Pestigo” twice and “Pernin” as “Pernans” once; it also normalized spoken “October eighth” to “October 8.” These name differences require a human listening check. The tool available here cannot provide reliable ear review, so no claim of listening approval is made.

The per-episode editorial_hold.json remains. The channel scheduling lock also remains. A human should listen to the names, watch the full MP4, and decide whether the draft can replace the previously hosted rejected version. That earlier hosted file must not be rescheduled.
