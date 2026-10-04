# Checked accident source and art intake — 2026-10-04

The new daily intake reads at most two unused leads from the four-entry checked accident pool. It never writes the calendar or episode folders. A producer draft is **not** admitted by a technical pass, and the channel scheduling hold and independent control policy remain closed.

The 2026-10-04 local live check fetched both pinned pages for each lead, found the exact event phrases in readable text, read live Wikimedia Commons metadata, and downloaded four pinned JPEGs. Each downloaded byte sequence matched its SHA-256 in `strategy/ACCIDENT-INTAKE.json`. Commons currently reports each of these images as public domain, not copyrighted, with no attribution requirement. The image descriptions name the relevant disaster or location. I inspected the images themselves and restricted their possible use to the scenes in the manifest; this is a preflight scene note, **not** independent final-art approval.

| Lead | Source result | Exact art preflight | Selection result |
|---|---|---|---|
| Oppau, 1921 | The Norwegian Defence Research Establishment study and French ARIA page are live. The study is original *retrospective technical research*, not a contemporary inquiry into the 1921 accident. | A 1921 published view of the ruins and a 1921 postcard of damaged plant equipment; both may illustrate aftermath only. | Held as `original_report_missing`; full art plan and independent review absent. |
| Mann Gulch, 1949 | The 1949 U.S. Forest Service Board of Review OCR and Forest History Society page are live. Archive.org redirected its download to an `archive.org` mirror, which the intake bounds to that domain. | A postfire investigation party photograph and a labelled escape-fire route map; neither is live fire footage. | Technical preflight passed; only two images are checked, and the script, scene sequence, and exact media still need independent review. |

The source-pair claim overlap sheet has nine Oppau and ten Mann Gulch matched claims, but this intake checks a small set of exact page phrases for freshness. It does not rerun a claim-level script review. The two unused leads cannot sustain a 100-day series or establish recurring source and art replenishment.

The scheduled workflow preserves the JSON audit as a 14-day Actions artifact and maintains an owner issue even when both technical checks pass, because neither candidate is cleared for producer selection. A source outage, changed rights metadata, changed image bytes, or duplicate/used candidate is reported without admitting a draft. The private control supply issue remains the release-level hold.
