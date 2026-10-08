# Atlas acceptance and learning

Atlas keeps its existing data-map niche and cloud-only producer/publisher split.

## Acceptance path

1. Fetch official values and definitions with bounded GET retries. Snapshot the source-response hash, source organization, values, entity years and definition. Mathematical share bounds and non-finite values are hard failures. A model's remembered outlier figures are advisory, never proof that official data is wrong.
2. Generate factual opening alternatives and choose a structurally valid one. Rotate topic families. Repair two-country rank shots into comparisons and missing named-country world callouts deterministically. Use accurate metric wording; aggregate totals include territories.
3. Check explicit entity/value associations, then review every title, hook, narration beat, description and card against the evidence and visual plans. Store complete surface verdicts and source-bound claims. Repair factual failures up to twice; drop only that episode after repeated failures. This remains probabilistic semantic review, not a guarantee of truth.
4. Render original geography with enclave masks, signed bar charts, fitted legends/source labels, reporting-year annotations, adaptive narration pace and readable camera arrival timing. Settled shots cache their geography for subtle camera pushes.
5. Fully decode the encoded MP4. Require portrait video and audio, 25–55-second absolute duration bounds and measured final loudness/peaks. Aim for 30–45 seconds; deviations are warnings. Independently recognize final encoded speech; material differences trigger at most one plain-wording script repair, followed by full factual review and a new render. Persistent material differences reject the episode; a small number of spelling/function-word recognition differences remain visible warnings. Decode/audio failures are not treated as script problems. Retain a contact sheet and exact media/script/data/claim hashes in qa.json.
6. ready.json binds the QA receipt. The publisher verifies the receipt and all artifact hashes before accepting the media. The publisher's receipt checker deliberately uses only the standard library.
7. Schedule through Buffer using stable episode identity, refresh delivery state and check the reported video using YouTube's official oEmbed endpoint. This confirms identity/title availability, not public-versus-unlisted visibility or processing state. Unconfirmed sent posts alert after four hours.

## Recovery

Waiting legacy episodes are re-rendered through the new gate, never silently grandfathered. A failed migration retires its ready marker and reopens the topic; future IDs do not reuse retired/failed identifiers. IDs continue beyond atlas999. Transient source failures retain resumable state for up to three attempts. One failed publisher candidate does not hide later valid candidates.

Legacy queued posts can receive an explicitly prepared, checked replacement under the same episode ID. The publisher verifies its new receipt and exact bytes, hosts a content-specific asset, checks the old post's title/media and future slot, edits the existing post, and confirms the new title/media/description/public setting at the same slot. It never edits a sent post or silently overrides an unexpected external change. An interrupted edit can recover the matching checked asset. The ledger retains the old title/media hash and the new QA binding.

## Learning

Public RSS measurements preserve previous history and record immutable 24h/72h/7d checkpoints only when a fresh observation falls within the following 12-hour collection window. These are observed checkpoints, not exact historical counts. RSS only exposes recent uploads; unavailable later checkpoints remain missing. Topic steering uses six or more comparable early checkpoints and their recorded ages, not raw lifetime totals. Retention, shares and subscriber conversion remain explicitly unavailable until the channel has authenticated Analytics API access. Public counts are not substitutes. RSS rating counts are stored separately and never labeled verified likes. At rollout the feed returned HTTP 200 with zero entries despite a visible upload; missing observations remain missing. The studio Google key returned Data API HTTP 401 (`required`), so authenticated channel access is still needed for reliable analytics.

## Validation

Use pipeline/tests/test_atlas_quality.py and test_atlas.py, producer isolation, speech and model-quota regression suites. Cloud atlas_quality_preview produces a private trial with the exact acceptance artifacts, contact sheet and MP4; it never schedules a post. Validate the returned artifacts using atlas.receipt.verify before rollout. Check the cloud producer's saved QA artifacts and a successful publisher run after rollout.

Visual bounding/fit logic and retained frames improve inspection; automatic OCR and universal visual correctness are not claimed. Model-provider outages and revoked publisher access can still stop service and are monitored. Neither quality acceptance nor unattended publishing guarantees monetization or growth.

Speech spelling tolerance excludes changed country names and direction/negation words. Older receipts with speech differences must be rechecked under this policy. Private atlas_outbox_verify reads parked media on the cloud volume host and returns only byte counts and matching hashes, supporting readback when a local storage-download hostname cannot be resolved.
