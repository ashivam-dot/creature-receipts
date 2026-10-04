# Autonomous exact-media release (dormant)

The tracked `status/autonomous_release_policy.json` is disabled. The existing
`status/scheduling_hold.json` remains in force. This branch does not schedule anything.

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
post, then an Instagram Reel for the same video and due time. Both Buffer channels
must be connected, unlocked, and unpaused before YouTube scheduling. Existing
matching posts are reconciled to avoid duplicates after an interrupted run. A failed
Instagram attempt remains retryable; a matching Buffer error post stops for review.
An episode-level editorial hold still blocks release.

Activation also requires a connected Instagram channel and a
`BUFFER_INSTAGRAM_CHANNEL_ID` available to the studio runner. Neither was present
in the October 4 read-only audit. Set these only after connecting the channel and
reviewing a newly certified episode and the actual Buffer destinations.
Enable `YTC_AUTONOMOUS_RELEASE=1` on one studio executor at a time. Buffer's current
create-post mutation has no idempotency key in this client, so two simultaneous
executors could race between checking for an existing post and creating one.
