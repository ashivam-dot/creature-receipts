# ep038 event-motion review

Status: private comparison only. The editorial hold remains in force. Nothing was uploaded, hosted, scheduled, or published.

The comparison MP4 shows the sourced repair on the left and the event-motion upgrade on the right. The baseline and
upgrade use the same corrected narration and labeled representative imagery, so the review isolates the visual change.

## Artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `private-review/ep038-baseline-sourced.mp4` | 12,915,340 | `f908a23bd5c943d51b45314ef3f79d8f7a71edbac65f3c932167fa4c3d99c86d` |
| `private-review/ep038-event-motion.mp4` | 11,874,773 | `6099b43792d618f52bbdb2e74188331a04b29e9a3b899bfe1019a50caa150487` |
| `private-review/ep038-motion-comparison.mp4` | 16,343,845 | `3a7701db404ac5ab7996939b30625b897cd60ec5e308696d23cf6c7a0edcedd8` |
| `visual-upgrade-contact-sheet.jpg` | 487,685 | `afc1aa5edc3a53d204b5c515c00b10a2ef23af688f98d627174c18c5854b6c87` |
| `short.yaml` | 6,605 | `c2e514f556481b77192c76973cdd8f3074b13015432e605de34ba4131652d4ab` |

The MP4s are ignored by Git and remain local in this isolated worktree. The comparison is 2160×1920 at 30 fps and
24.298 seconds; its left and right halves are the baseline and upgrade respectively.

## Visual gains

- Beat 1 now fills the phone frame with the actual July 28, 1945 exterior aftermath photograph instead of presenting
  a lower-resolution landscape photograph as a small print.
- A second actual July 28 press photograph adds interior wreckage at impact, avoiding three consecutive uses of the
  exterior image. Both new selections are public domain Commons files with their page, author, date, and license recorded.
- Seven beats have authored camera paths: climb into smoke, sweep with the representative B-25, push into the impact,
  descend with the engine and elevator, move laterally through the rescue, and ease out on the survival reveal.
- The final shot reverses to the opening camera coordinates (`1.10` zoom, `x=.50`, `y=.75`) to retain the loop.
- The representative B-25 remains labeled `B-25 TYPE • 1942 PHOTO`; the rescue photograph remains labeled
  `UNIDENTIFIED CRASH CASUALTY`. Interior and building wreckage are also labeled without claiming an elevator image.

## QA

- Upgrade: 1080×1920 H.264, 30 fps, 24.30 seconds, 81 words, -14.1 LUFS, -1.7 dBFS true peak.
- Speech recognizer coverage: 100% on all eight beats, with no differences.
- Automated video warnings: none.
- Renderer and episode regression suite: 80 passed.
- Contact sheet and beat frames inspected at phone-frame resolution. The full-frame opening, labels, captions, and
  source changes are legible and internally consistent.

## Remaining review risks

- Beats 4 and 6 use clearly labeled event wreckage because no verified elevator-shaft or elevator-car photograph is
  available; the downward motion carries the action but the image is contextual.
- These are animated archival stills. The authored motion improves direction and pacing but does not create documentary
  footage of the crash or fall.
- Automated speech alignment passed, but no native listening approval or final release approval is claimed.
