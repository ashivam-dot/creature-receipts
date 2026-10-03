# ep045 private replacement review — 2026-10-03

**Status update, 22:27 IST:** The earlier public upload was made private after
the unqualified survival claim about the cancelled transport was checked
against the Winton family source. See [withdrawal.json](withdrawal.json).
The replacement remains an unhosted local draft under full editorial review.
The statements below describe the earlier private-render check.

This review applies to the local `ep045-replacement-private.mp4`, SHA-256 `f89475bf5bea7dc7000b5c664be40892c6bac17cb1768d0f8dcd80d0918b597f`. The MP4 is ignored by Git and remains in the isolated worktree. At the time of this render check, the then-public video `v4rp0oWvgSI`, its visibility, `publish.json`, and `public_clarification.json` were not changed. No replacement was uploaded or scheduled.

## Editorial and provenance

- The opening immediately states the planned 250-child train never left. Winton's face is unobscured, with “TRAIN NEVER LEFT” over his coat in the first frame. The 250 figure appears in speech and captions within the opening seconds.
- Direct USHMM and Winton family sources support the team credit, official 669 count, planned 250-child transport on 1 September 1939, cancellation when Germany invaded Poland, and the scrapbook's role in making the story public around 1988. The narration does not claim the children had boarded, assert an exact death count, or describe a fifty-year secret from Winton's wife.
- The Stockholm children and Polish tank images are absent. The station image is visibly labeled “PRAGUE · 1931 PHOTO” and serves as a location view. The 2015 photo shows the complete Winton memorial statue and is described in narration as a memorial; its ŠJů credit and CC BY 4.0 license are recorded. The 1938 Winton portrait is cropped to avoid implying an unidentified child was on the cancelled train. Source URLs and licenses are recorded in `research.md`, `visuals.json`, and `short.yaml`.

## Final media checks

| Check | Result |
|---|---|
| Duration | 29.49 seconds, within the pipeline's 17–35-second range |
| Script | 73 words across 6 beats |
| Integrated loudness | -14.3 LUFS |
| True peak | -1.8 dBFS |
| Pipeline warnings | None |
| Speech recognition | Full narration transcribed; zero word differences, recorded in `work/speech.json` |
| Visual review | Opening at 0–3 seconds, seven per-shot review frames, and one frame each second across the 29-second video examined. Winton's face is unobscured at 0 seconds and in the refreshed tracked `sheet.jpg`; the station date label, fact/date cards, and complete memorial statue remain readable. No blank or generated placeholder appears. Contact sheets are in ignored `work/replacement-contact-sheet.jpg` and `work/sweep-sheet-1.jpg` / `work/sweep-sheet-2.jpg`. |
| Focused tests | `test_editorial_hold.py`, `test_history_cards.py`, `test_short_reviews.py`: 11 passed |

This is a machine speech check plus a sampled visual sweep, not native playback or a human listening check. The draft is ready for that final review before a publication decision. The old public upload remains unchanged.
