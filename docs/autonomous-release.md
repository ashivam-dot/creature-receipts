# Autonomous exact-media release (dormant)

The tracked `status/autonomous_release_policy.json` has `enabled: false`. The existing
`status/scheduling_hold.json` remains in force. These changes do not schedule anything.

The release path can run only after a later reviewed change sets `enabled` to `true`
and the automation environment sets `YTC_AUTONOMOUS_RELEASE=1`. Its episode floor
cannot be below ep063, and a draft's `topic.started_at` must be on or after the policy's
UTC cutoff. Existing ep050, ep051, and ep053 cannot enter this path.

New studio drafts record the SHA-256 of the exact MP4 in each review round. After
hosting, the studio writes `release_certificate.json` only when the kept round has
clean full-decode, finished-MP4 transcription, and review results. The certificate
binds the MP4, spec, manifest, script, research, review, hosted URL and public ID.
It lists cited claims with evidence from two source sites and records image licenses
and credit URLs. The gate rejects missing or changed evidence, ambiguous licenses,
or a missing hosted copy. It verifies all hosted video bytes again before each
platform schedules. These checks establish traceability and machine-checked rights
metadata; they cannot prove the historical interpretation or legal status of a
source independently.

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
