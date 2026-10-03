# ep025 private replacement review — 2026-10-03

This review applies to the locally rendered replacement `ep025-replacement-private.mp4`, SHA-256 `4c329bfc954293da18534a6471acbda1ca7d348fc0983ae129b4f51239801b29`. The MP4 is ignored by Git and remains only in this isolated worktree. The original YouTube upload remains private under `withdrawal.json`; this review does not authorize reupload or scheduling.

## Source and editorial review

- Direct Airship Heritage Trust and Trust-supplied survivor-list checks support six eventual survivors: four engineers in engine cars, Leech and Disley inside the hull. One additional man escaped the wreck but died days later. See `research.md` for links and the source-by-source receipts.
- Narration says a final 17-hour post-refit trial took place without a full-speed test, then describes the observed dives, impact and fire. It does not assign a settled cause to the first dive or a specific ignition source.
- Title and hook no longer promise a proved cause. The first image shows archival R101 wreckage at 0.20 seconds; no standalone date card delays the stakes.

## Final media checks

| Check | Result |
|---|---|
| Duration | 32.90 seconds, within the pipeline's 17–35-second range |
| Script | 81 words across 7 beats |
| Integrated loudness | -14.4 LUFS |
| True peak | -1.8 dBFS |
| Pipeline warnings | None |
| Speech recognition | Full narration transcribed; zero word differences against the script, recorded in `work/speech.json` |
| Visual review | Frames at 0.20, 1.00 and 3.00 seconds, plus one middle frame of each beat, checked for legibility, image/story fit and placeholders. The archival wreckage opening and the revised “4 + 2” card are readable; no blank or generated placeholder appeared. |
| Focused tests | `test_editorial_withdrawal.py`, `test_editorial_hold.py`, and `test_history_cards.py`: 6 passed |

Speech recognition is a machine check; no native listening check is claimed. The 1929 Cardington image represents R101 and is not footage of the last flight. The March 1931 inquiry PDF was downloaded and its official cover verified, but the scan is image-only and was not text-audited; the scripted points are supported by the directly read Airship Heritage Trust pages.
