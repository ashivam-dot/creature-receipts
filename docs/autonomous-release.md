# Autonomous exact-media release (dormant)

The tracked `status/autonomous_release_policy.json` has `enabled: false` and
`require_instagram: false`. The existing `status/scheduling_hold.json` remains
in force. The reviewed destination is YouTube only. These changes do not
schedule anything.

The release path can run only after a later reviewed change sets `enabled` to `true`
and the automation environment sets `YTC_AUTONOMOUS_RELEASE=1`. Its episode floor
cannot be below ep063, and a draft's `topic.started_at` must be on or after the policy's
UTC cutoff. Existing ep050, ep051, and ep053 cannot enter this path.

New studio drafts record the SHA-256 of the exact MP4 in each review round and
then wait in `hold.json`. Production cannot write its own release certificate.
A reviewer outside production must check the complete hosted video and narration,
cited claims, visual identity and rights. An external trusted signer must then
provide `independent_review.json` for that exact candidate. The signed payload
binds the MP4 hash, hosted URL and public ID, topic start time, spec, manifest,
script, research, visual selections, review, and three explicit QA assertions.
The studio must not receive the private key.

On an active policy, a cloud run verifies the signature and hosted bytes before
minting a version-2 `release_certificate.json`. Each release checks the signature,
certificate and hosted bytes again; old producer-written certificates are rejected.
It lists cited claims with evidence from two source sites and records image licenses
and credit URLs. The gate rejects missing or changed evidence, ambiguous licenses,
or a missing hosted copy. It verifies all hosted video bytes again before each
platform schedules. These checks establish traceability and machine-checked rights
metadata. The independent reviewer supplies the factual, visual and listening
judgment that the producer's automated scores and contact sheet cannot establish.

The trusted Ed25519 public key is pinned in `kit/independent-review.pub`. Its
private half is held by the separate private
`ashivam-dot/history-last-hours-control` repository, whose manual signer remains
disabled. That control repository also has a dormant YouTube-only publisher and
no Buffer credential. Its owner-only private repository blocks the producer's
deploy key, but GitHub's current private-repository plan does not permit
required reviewer or branch protection rules. The existing producer runners
still hold the old Buffer credential, so actual publisher credential isolation
has not been achieved. The producer also holds the current Cloudinary write
credential; the control publisher must copy exact reviewed bytes to a distinct
control-owned media account so the producer cannot replace or delete the video
between review and Buffer fetch. Do not enable either release policy until the
old publisher credentials are removed and revoked from producer environments,
an independent approval boundary exists, and the control publisher is verified
end to end.
The external signer must serialize the review
without its `signature` using sorted keys, `(',', ':')` separators, UTF-8, and no ASCII
escaping, prefix those bytes with `history-last-hours-independent-review-v1` and
a zero byte, then base64-encode an Ed25519 signature of the result. The signed review
must have `version: 1`, the exact `subject` fields, `reviewer_key_sha256`, a UTC
`reviewed_at_utc`, `decision: approved`, and true `claim_sources`,
`visual_identity_rights`, and `full_video_audio` checks. A missing key, missing
review, failed check, changed file or media URL, or invalid signature keeps the
draft held. This path cannot publish unattended until the independent control
boundary and review handoff exist.

The intended independent release destination is YouTube only. The separate
control publisher has no Instagram operation. The legacy producer release code
still contains optional Instagram behavior, so it must remain dormant and must
not receive an Instagram destination setting for this channel. An episode-level
editorial hold still blocks release. New due times must be timezone-aware,
more than 30 minutes ahead, and no more than 30 days ahead.

The tracked policy chooses YouTube-only release because History has no connected
Instagram destination. The control repository pins the verified History Buffer
organization and YouTube channel IDs. Its publisher still requires a new
control-owned Buffer credential, a separate Cloudinary account and credential,
an enforced independent approval boundary, and a tested handoff back to the
producer before activation. Do not set
`YTC_AUTONOMOUS_RELEASE=1` in Modal or GitHub; the producer's own scheduling path
must stay dormant while the separate publisher boundary is built. Buffer's
create-post mutation has no idempotency key in this client, so the control
publisher serializes its workflow and reconciles complete post history before
any retry.
