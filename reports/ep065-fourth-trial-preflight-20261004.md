# ep065 fourth private trial preflight — 2026-10-04

The third private trial was unfinished; its first render and rejection are archived in `reports/ep065-third-trial-evidence/` and `reports/ep065-third-trial-rejection-20261004.md`. The next dispatch is one explicitly authorized, bounded private trial. The episode remains on editorial hold for release.

The repaired script has 72 spoken words and passes `writer.problems()`. It preserves the Royal Commission's two separate findings: the commission did not believe action after August 27 could prevent the **fall**, while better judgment might have prevented the **loss of life**. Claims 8 and 15 in `research.json` quote the commission; claim 15's scan wording was checked in the original page, where OCR incorrectly reads “lose” for “loss.”

Seven beats use six approved local art files and a return to the opening image. The distinct third-beat crop and sixth-beat archival wreckage photograph address the previous review's visual concerns. All six file hashes match `topic.json` and `art/provenance.json`. `ShortSpec.load()` accepts the spec, its narration matches `script.json`, and an exact `cloud.context_bundle()` unpack retains the spec, research, script, hold, and six matching approved files.

The revised local preflight MP4 at `/tmp/ep065-fourth-local-preflight-b/ep065.mp4` has SHA-256 `e62cacab6905e45364fcabc022fb897baa5794cc4df2d01db927a7cae6f35402`. It runs 28.5 seconds, fully decodes, and has no `check.check()` warnings. Its final encoded track transcribes with zero differences under `small.en`; `speech_verified()` returns true for that exact hash and its manifest beats. The seven 360×640 review frames were inspected at `/tmp/ep065-fourth-local-contacts-b.jpg`. This is a local preflight file, not the cloud worker's release artifact. Direct listening was unavailable in this tool environment.

The full pipeline test suite passes: 238 tests. The private cloud trial and exact saved MP4 QA are still required.
