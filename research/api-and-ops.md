**Bottom line:** Unverified API uploads are still forced to private, and browser-automating YouTube Studio breaks YouTube's Terms, so passing the API audit is the critical path. Lightning's free tier works, with caveats: phone verification, a possible 2–3-business-day wait for gmail.com signups, and a restart every 4 hours.

**1. Lightning AI**
- **Signup:** No card needed; a non-virtual phone number is required. Personal emails "may take 2-3 business days" to verify (work emails are faster). No waitlist, but not every country is supported. ([account](https://lightning.ai/docs/platform/overview/faq/create-account), [FAQ](https://lightning.ai/docs/platform/overview/faq))
- **Credits:** 5 at signup, 25 more with a card (1 credit = $1); Lightning can change grants anytime. ([pricing](https://lightning.ai/pricing), [billing](https://lightning.ai/docs/platform/overview/faq/billing))
- **Free Studio limits** ([students](https://lightning.ai/docs/platform/overview/setups/academia/students), [auto-sleep](https://lightning.ai/docs/platform/build/ai-studio/auto-sleep), [disk](https://lightning.ai/docs/platform/build/ai-studio/manage-disk-size)):
  - One 4-CPU Studio at a time with a 400 GB disk. The Drive gives 10 GB free, up to a 50 GB cap.
  - After 4 hours of runtime it "switch[es] to billed" until restarted. At zero credits, Lightning warns, then shuts workloads down.
  - It auto-sleeps after 10 idle minutes; running processes keep it awake. Disabling auto-sleep makes it paid.
- **Environment** ([environment](https://lightning.ai/docs/platform/build/ai-studio/modify-environment), [background](https://lightning.ai/docs/platform/build/ai-studio/background-execution), [on-start](https://lightning.ai/docs/platform/build/ai-studio/on-start-actions), [pipelines](https://lightning.ai/docs/platform/inference/pipelines/scheduling)):
  - Preinstalled: Python 3.10.10, conda, `uv`. `apt-get` installs persist.
  - Scripts keep running after you close the tab; notebooks don't.
  - `~/.lightning_studio/on_start.sh` runs on every start.
  - No in-Studio cron is documented. SDK Pipelines accept `Schedule("<cron>")` but run as billed Jobs.
  - No egress limit is documented; official examples scrape external sites.
- **SDK:** `lightning-sdk` 2026.9.18.post1 needs **Python 3.11+**; this Mac's `/usr/bin/python3` is 3.9.6. Export `LIGHTNING_USER_ID` and `LIGHTNING_API_KEY` (profile → Global Settings → Keys). Adapted from [the docs](https://lightning.ai/docs/platform/developers/sdk/studio); signatures checked against the source:

```python
from lightning_sdk import Studio
s = Studio(name="yt-render", teamspace="<teamspace>", user="<username>")  # creates if missing
s.start()                                         # CPU-4 (free) by default
s.upload_file("job.json", remote_path="jobs/job.json")
print(s.run("python render.py jobs/job.json"))    # blocks; raises on non-zero exit
s.download_file("out/final.mp4", "final.mp4")
s.stop()
```
Once it's running, the SDK pings it every 30 seconds until your process exits, blocking auto-sleep; always call `stop()`.
- **CLI:** `lightning login`, then `lightning studio start|stop|ssh --name N --teamspace owner/ts`. Files: `lightning cp <file> lit://owner/ts/studios/N/<path>`. ([CLI](https://lightning.ai/docs/platform/developers/cli/studio))
- **SSH (free):** In the Terminal plugin, "Connect via SSH" gives a one-liner that creates a key and a `Host ssh.lightning.ai` entry. Then run `ssh s_<studio-id>@ssh.lightning.ai`. Or add a public key in Global Settings → Keys. ([SSH](https://lightning.ai/docs/platform/build/ai-studio/ssh-access))
- **Terms:** §5(g)(iv) forbids anything that "involves commercial activities and/or sales without Lightning AI's prior written consent, such as … advertising", though the docs pitch it for a "side hustle". Ask support@lightning.ai for written consent before monetizing. ([ToS](https://lightning.ai/legal/terms-and-conditions))

**2. YouTube Data API**
- **Setup:** Use an External consent screen with yourself as a test user, plus a Desktop-app client (loopback redirect; the out-of-band flow is gone). `youtube.force-ssl` covers uploads, thumbnails, captions, and `channels.update`; add `yt-analytics.readonly`. Neither is restricted (only `dataportability.youtube.*` is); Google's own sensitive-scope example is deleting a YouTube video. ([desktop OAuth](https://developers.google.com/youtube/v3/guides/auth/installed-apps), [restricted](https://support.google.com/cloud/answer/13464325))
- **7-day tokens:** Confirmed for Testing mode. To avoid them, click **Publish app** and stay unverified under Google's personal-use exemption (under 100 users). You'll see an "unverified app" warning and a 100-new-user cap. Refresh tokens then last until revoked or 6 months unused. ([audience](https://support.google.com/cloud/answer/15549945), [exemption](https://support.google.com/cloud/answer/13464323), [expiry](https://developers.google.com/identity/protocols/oauth2))
- **Private lock:** Still in force; the [videos.insert page](https://developers.google.com/youtube/v3/docs/videos/insert) was updated Sep 14, 2026. Locked videos can't be appealed and must be re-uploaded ([help](https://support.google.com/youtube/answer/7300965)).
  - The [audit form](https://support.google.com/youtube/contact/yt_api_form) asks for a legal name ("self" for individuals), a public URL, privacy policy and ToS screenshots, a demo login, the Cloud project number, OAuth and upload screenshots, and your quota needs.
  - It also demands "significant independent value to the YT ecosystem", a risk for a personal tool.
  - No turnaround is published. A 2020 report took about a week; 2026 reports describe 4+ weeks of silence ([May](https://stackoverflow.com/questions/79936153), [July](https://discuss.google.dev/t/youtube-api-compliance-review-silent-for-4-weeks-after-remediation-4-unanswered-follow-ups-pii-removed-by-staff/388185/1)).
- **Quota** (resets at midnight Pacific; [calculator](https://developers.google.com/youtube/v3/determine_quota_cost), [history](https://developers.google.com/youtube/v3/revision_history)):
  - `videos.insert` and `search.list` each have their own bucket of 100 calls/day, 1 unit per call, since June 1, 2026.
  - Everything else shares 10,000 units/day: `thumbnails.set` 50, `captions.insert` 400, `playlistItems.insert` 50, `channels.update` 50, `channelBanners.insert` 50, `videos.list` 1.
- **Fields** ([videos](https://developers.google.com/youtube/v3/docs/videos)):
  - `publishAt` requires `privacyStatus=private` on a never-published video.
  - `containsSyntheticMedia` exists (since Oct 30, 2024).
  - `selfDeclaredMadeForKids`, `defaultLanguage`, `defaultAudioLanguage`, `categoryId`, and `tags` (500 characters total) all work.
  - `recordingDetails.location` is deprecated.
- **Not possible via the API:** channel name (title changes error), handle, profile picture, and feature unlocks. Custom thumbnails and uploads over 15 minutes both require phone verification. ([channels.update](https://developers.google.com/youtube/v3/docs/channels/update), [features](https://support.google.com/youtube/answer/9890437))

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]
creds = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES
        ).run_local_server(port=0, prompt="consent")   # refresh token by default
yt = build("youtube", "v3", credentials=creds)
yt.videos().insert(part="snippet,status", body={"snippet": {"title": "…", "categoryId": "27"},
    "status": {"privacyStatus": "private", "publishAt": "2026-10-01T15:00:00Z",
               "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}},
    media_body=MediaFileUpload("final.mp4", resumable=True)).execute()
```

**3. Analytics**
- **Metrics:** `reports.query` (`ids=channel==MINE`) supports views, engagedViews, estimatedMinutesWatched, averageViewDuration, averageViewPercentage, likes, shares, comments, and subscribersGained/Lost, broken down by day, video, and insightTrafficSourceType. ([metrics](https://developers.google.com/youtube/analytics/metrics), [dimensions](https://developers.google.com/youtube/analytics/dimensions))
- **Impressions and CTR:** Not in that API. Since Jan 15, 2026 the Reporting API has them: `channel_reach_basic_a1` gives `video_thumbnail_impressions` and `video_thumbnail_impressions_ctr` per date and video, and `channel_reach_combined_a1` adds traffic source and device. Reports are daily CSVs, generated only after you create a reporting job. ([reports](https://developers.google.com/youtube/reporting/v1/reports/channel_reports))
- **Latency:** 48–72 hours. Use `videos.list` for near-real-time counts. ([data model](https://developers.google.com/youtube/analytics/data_model))

**4. Fallback: YouTube Studio**
- **Studio:** Takes 15 files per upload batch, but each video is scheduled individually. The daily upload cap spans web, mobile, and the API. ([upload](https://support.google.com/youtube/answer/57407), [schedule](https://support.google.com/youtube/answer/1270709))
- **ToS:** You may not "access the Service using any automated means (such as robots, botnets or scrapers) except (a) in the case of public search engines, in accordance with YouTube's robots.txt file; or (b) with YouTube's prior written permission;". Identical in the US (Dec 15, 2023) and Indian (Jan 5, 2022) versions, so automating Studio needs YouTube's written permission. ([terms](https://www.youtube.com/t/terms))

**Unverified:** free-machine RAM (third parties say 16 GB); whether an SDK stop/start resets the 4-hour clock; whether ffmpeg is preinstalled (installable via `apt-get`); whether `nohup` jobs started with `run()` survive; free-tier access to Jobs; a "15 credits/month" grant (third-party sites only); the exact SSH one-liner.

Scratch files only in `/tmp/ytresearch/a/`; nothing installed.
