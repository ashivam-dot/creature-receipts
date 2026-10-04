# Autonomous exact-media release (dormant)

The tracked `status/autonomous_release_policy.json` has `enabled: false`. The existing
`status/scheduling_hold.json` remains in force. These changes do not schedule anything.

The release path can run only after a later reviewed change sets `enabled` to `true`
and the automation environment sets `YTC_AUTONOMOUS_RELEASE=1`. Its episode floor
cannot be below ep063, and a draft's `topic.started_at` must be on or after the policy's
UTC cutoff. Existing ep050, ep051, and ep053 cannot enter this path.

New studio drafts record the SHA-256 of the exact MP4 in each review round and
then wait in `hold.json`. Production cannot write its own release certificate.
A reviewer outside production must check the complete hosted video and narration,
cited claims, visual identity and rights. An external trusted signer must then
provide `independent_review.json` for that exact candidate. The signed payload
binds the MP4 hash, hosted URL and public ID, spec, manifest, script, research,
review, and three explicit QA assertions. The studio must not receive the private key.

On an active policy, a cloud run verifies the signature and hosted bytes before
minting a version-2 `release_certificate.json`. Each release checks the signature,
certificate and hosted bytes again; old producer-written certificates are rejected.
It lists cited claims with evidence from two source sites and records image licenses
and credit URLs. The gate rejects missing or changed evidence, ambiguous licenses,
or a missing hosted copy. It verifies all hosted video bytes again before each
platform schedules. These checks establish traceability and machine-checked rights
metadata. The independent reviewer supplies the factual, visual and listening
judgment that the producer's automated scores and contact sheet cannot establish.

The signing gate remains unconfigured: `kit/independent-review.pub` has no trusted
key and there is no independent signer. The producer's deploy key can push this
repository, so a signing workflow and secret in this repository would not create
an independent trust boundary. A separate control repository or service must own
the review code and private key, and the producer must not be able to change its
protected workflow, key, or approval policy. Before activation, pin the trusted
reviewer's base64 raw Ed25519 public key in a reviewed commit, define a separate
review and signing process, and isolate the publishing credentials or deployment
from producer-controlled changes. The external signer must serialize the review
without its `signature` using sorted keys, `(',', ':')` separators, UTF-8, and no ASCII
escaping, prefix those bytes with `history-last-hours-independent-review-v1` and
a zero byte, then base64-encode an Ed25519 signature of the result. The signed review
must have `version: 1`, the exact `subject` fields, `reviewer_key_sha256`, a UTC
`reviewed_at_utc`, `decision: approved`, and true `claim_sources`,
`visual_identity_rights`, and `full_video_audio` checks. A missing key, missing
review, failed check, changed file or media URL, or invalid signature keeps the
draft held. This path cannot publish unattended until the independent control
boundary and review handoff exist.

When active, the hold allows only this certificate-scoped path to create a YouTube
post. The policy must explicitly set `require_instagram` to `true` or `false`.
With `true`, both Buffer channels must be connected, unlocked, and unpaused before
YouTube scheduling; the run pairs a Reel for the same video and due time while the
slot is more than 30 minutes ahead. With `false`, certified YouTube scheduling can
proceed without Instagram. If a History Instagram channel is connected later, set
its exact `BUFFER_INSTAGRAM_CHANNEL_ID` and the run can add a Reel to a certified
scheduled or live YouTube post within the retry window. The configured Instagram
ID must resolve to an Instagram destination in the same Buffer organization as
the verified History YouTube channel. An unrelated channel, including Mool's
Instagram, is never selected automatically. A wrong optional Instagram ID is
reported without holding the YouTube release.

If the YouTube slot passes before Instagram accepts the Reel, the next run selects
a fresh Instagram slot within seven days of the YouTube slot. Existing matching
posts are searched across Buffer's complete history and reconciled only
when their text and hosted video URL match. A failed Instagram attempt remains
retryable, including after YouTube is live; the hosted media is retained while no
Instagram post is recorded. A matching Buffer error post stops for review. New due
times must be timezone-aware, more than 30 minutes ahead, and no more than 30 days
ahead. With optional Instagram, a newly connected account skips new Reels for
YouTube slots older than seven days, but still reconciles an already accepted Reel.
With required Instagram, a retry beyond seven days stops for review.
An episode-level editorial hold still blocks release.

The tracked policy still has `require_instagram: true`, so activation requires a
connected History Instagram channel and a `BUFFER_INSTAGRAM_CHANNEL_ID` in the
studio runner. Neither was present in the October 4 read-only audit. A later
reviewed policy change may set `require_instagram: false` for YouTube-only release.
For Modal, put `YTC_AUTONOMOUS_RELEASE=1` in the `creature-receipts-studio` secret
only after that review. Add the exact History Instagram ID there if the account is
connected. The GitHub backup workflow maps the ID from its
`BUFFER_INSTAGRAM_CHANNEL_ID` repository secret and the flag from its
`YTC_AUTONOMOUS_RELEASE` repository variable; both are currently unset. Enable the
flag on one studio executor at a time. Buffer's current
create-post mutation has no idempotency key in this client, so two simultaneous
executors could race between checking for an existing post and creating one.
