# Mann Gulch source and scene-art input — 2026-10-04

**State:** private review input for the unused `mann-gulch-1949` lead. The producer's accident selection policy remains disabled, its approved ID list remains empty, and this input admits no draft or release. A technical preflight is not an editorial, rights, or final-video approval.

## Factual spine and source pins

The original [1949 U.S. Forest Service Board of Review report](https://archive.org/download/nfsl_2_43087/p17053coll2_43087.pdf) is the primary source (26-page scan, SHA-256 `a3595a83b33135beb5384da1ec2533a4ec6f7f2489fbb0dfa7ac4f084c4c81e0`). Its [searchable OCR](https://archive.org/download/nfsl_2_43087/p17053coll2_43087_djvu.txt) was fetched separately (42,009 bytes, SHA-256 `888726925bb43cedc49c22813dcf9db7a7fbe42742a52e6717d5074481d69f19`). The independent [Forest History Society account](https://foresthistory.org/research-explore/us-forest-service-history/policy-and-law/fire-u-s-forest-service/famous-fires/mann-gulch-fire-1949/) was fetched on 4 October 2026 (HTML SHA-256 `e2de1c1baaa93197bd5dc03d8a70b2523033bc3eb820a18953461e49b8049808`). These hashes identify the copies inspected; the daily audit refetches the live pages and checks event phrases rather than requiring unchanged HTML/OCR bytes.

| Bounded claim | Primary location | Limit for a script |
| --- | --- | --- |
| On 5 August 1949, 16 firefighters were entrapped; 13 died and three survived. | Board scan PDF p. 4, summary. | The Board distinguishes 11 deaths that day and two the next day. |
| The planned route to the river was cut off; the crew turned toward the ridge. | Board scan PDF p. 12, narrative. | This was an advancing fire, not a blocked bridge or an order to abandon the crew. |
| Dodge lit an escape fire in grass at about 5:55 p.m. and survived in the burned area. | Board scan PDF pp. 12–13, Dodge's account and sequence. | The 1993 diagrams below are reconstructions, not footage or photographs of this action. |
| How many crew members understood Dodge's directions could not be established. | Board scan PDF p. 16, finding 7. | Do not portray the men who died as ignoring a simple rescue instruction. The report records a relative's opposing view of whether the escape fire impeded some men; the Board rejected that view in its finding 9 on PDF p. 17. |

The Board's own contemporaneous diagram is visible on PDF p. 19 and explicitly says it is diagrammatic and not exact in scale or position. It is a reference for claim checking here; no rights conclusion is drawn for that separately credited or uncredited illustration.

## Exact art offered for independent scene review

All four files below were visually inspected. The exact remote bytes are pinned in `strategy/ACCIDENT-INTAKE.json`. Commons' live metadata currently says `Public domain`, `Copyrighted=false`, and `AttributionRequired=false` for each. The new smokejumper image's Commons file record also links an official Forest Service Pacific Northwest Flickr item carrying a Public Domain Mark and `PD-USGov-USDA-FS`; the new diagram credits Forest Service researcher Richard C. Rothermel and the 1993 agency report. These are rights leads for an independent reviewer, not a substitute for that review.

| Scene role | Image and exact SHA-256 | Accurate use and limit |
| --- | --- | --- |
| Period context | [1949 Forest Service smokejumper and spotter](https://commons.wikimedia.org/wiki/File:Smokejumper_and_Spotter_2-6-1949_(22736663516).jpg) — `e9048a2cfe424b5985dfb45a25fef4986d9b3fec5ef24529bfbc4acbdc27b67b` (new 1280 px Commons thumbnail) | The photo shows a jumper at an aircraft door. It is **not identified as the Mann Gulch crew, aircraft, or jump**. The file title supplies the 1949 date, but no original negative or subject-identification record was checked. Caption as period context only. |
| Event route and timing | [Rothermel Figure 1](https://commons.wikimedia.org/wiki/File:Fig._1_from_Rothermel,_General_Technical_Report_INT-299,_May_1993.jpg) — `d9fbef4a342807e14c031b2c4b1603bdcbc21fc52ab258fd3a5c70cb8e29db9c` (new original JPEG) | U.S. Forest Service **1993 reconstruction** of the 1949 fire, crew route, and escape fire. Use a legible selected crop with its date, never as a contemporaneous field map or live scene. |
| Escape-fire location | [Rothermel escape-fire route map](https://commons.wikimedia.org/wiki/File:Mann_Gulch_Fire,_1949._Dodge_%22escape_fire%22_map.jpg) — `6341aec7f1c9c7fc1efa66799f31f209653cc78da5398d4efbd1c9a436b8145a` (existing 1280 px Commons thumbnail) | Use a close crop showing the separate advancing fire and Dodge's escape fire; label as a retrospective diagram. The Commons description has a stray 2018 date in a secondary note, while the file date and source report are 1993. |
| Actual site after the fire | [1949 investigation party photograph](https://commons.wikimedia.org/wiki/File:MannGulchFire.jpg) — `f7d731393700011e80b16ead89a4980a54db04ceb99142d6906818a93e063734` (existing JPEG) | Shows investigators on the burned Mann Gulch slope. It cannot depict the fire, the escaping crew, or Dodge lighting grass. Commons lists an unknown photographer and a National Interagency Fire Center source; the original source link was not independently recovered. Hold its final use for a stronger rights/provenance check. |

The [four-phone-crop preview](previews/mann-gulch-scene-options-2026-10-04.jpg) is derived only from those pinned bytes (SHA-256 `949f5c196c0b82ae8001d1a4f90348e811efc763022b778ecea2a8d071a164ba`). It demonstrates usable subject crops, while the two maps still need deliberate split crops or editorial overlays for small-screen legibility. It is not a proposed final frame sequence.

The expanded bounded intake passed a local live check at `2026-10-04T13:56:45Z`: four source pages and six exact JPEGs fetched, Mann Gulch `technical_preflight_pass`, Oppau `original_report_missing`, `eligible_for_selection=0`, and `release_enabled=false`. The three focused intake tests passed. This is a freshness and byte-integrity result, not a source-claim or final-art verdict.

[Cloud preflight run 37207502857](https://github.com/ashivam-dot/creature-receipts/actions/runs/37207502857) passed on input commit `6a2b3d0` at `2026-10-04T13:58:07Z`. Its downloaded JSON artifact has SHA-256 `4b097404d63c482197b4df9d654dcdd63b0a10e79e7de84ac9c6813c4c728f00` and independently records four Mann Gulch image checks, two Oppau image checks, one technical pass, zero eligible candidates, and `release_enabled=false`. The workflow refreshed the existing producer supply issue; it did not render, schedule, or upload a video.

## Remaining review and release limits

The official [1993 Forest Service PDF](https://www.fs.usda.gov/rm/pubs_int/int_gtr299.pdf) returned HTTP 403 from this environment, and the `fireleadership.gov` copies timed out during TLS handshakes. The Commons file records and downloaded exact images were inspected, but those government-hosted copies were not. The 1949 primary report scan is hosted by Internet Archive; its PDF metadata names the U.S. Forest Service as author, but the original agency-hosted report was not located. The investigation photograph's creator is unknown. Resolve that photo's provenance or replace it before claiming the full art set is rights-cleared.

No claim-level final script, selected crops, exact render, independent phone-size review, audio QA, or recurring supply/cost proof exists for this lead. Issue [history control #14](https://github.com/ashivam-dot/history-last-hours-control/issues/14) therefore remains open, and `HISTORY_CONTROL_AUTOMATION=0` and all selection, intake, signing, and publishing holds remain in place.
