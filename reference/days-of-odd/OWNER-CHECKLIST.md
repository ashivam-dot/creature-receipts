# Owner checklist

The agent signs in to every service with your Google account (<owner-email>, the owner's Chrome profile)
and does all the setup a login allows. This list keeps only what needs your phone, your face or ID, or
your card.

## Needed from you

Nothing is required: the channel runs in the cloud on free tiers without you or this Mac. Phone
verification is done (2026-09-26), and Studio shows standard, intermediate, and advanced features all
enabled, so the channel can apply for monetization once it qualifies.

### Your phone (set up 2026-09-27)

The agent set up your Android phone over USB:

- **ntfy** (from Google Play) is subscribed to the channel's private topic, shown as "Days of Odd". It
  rings when something needs attention: a run failed or couldn't save, Buffer can't post, a Short didn't
  go public, or stock is running low. Every morning, usually between 08:00 IST and noon, it also sends a
  summary: the day, Shorts live, views, subscribers, the next posts, stock, the last studio run, and the
  month's Modal and Cloudinary use, with a **YouTube Studio** button. **No summary by noon means the
  watchdog itself has stopped**; check <https://github.com/<owner>/days-of-odd/actions/workflows/watchdog.yml>.
- **YouTube Studio** is on Days of Odd: live views, subscribers, and comments.
- **Buffer** is signed in: the queue of scheduled Shorts (**Queue**) and what went out (**Sent**). It
  notifies you if a post fails.

For ntfy, the agent allowed notifications, set its battery use to **Allow background activity**, and
turned off **Manage unused apps**. Otherwise Android phone can close it, or Android can pause it after months
unopened, and alerts would stop. Anyone who knows the topic can read the alerts, so keep it to yourself.
USB debugging is still on; turn it off in Developer options if you like.

## Later: monetization (around Day 60–80)

When Studio's **Earn** tab says you're eligible, the agent will tell you. Then you:

1. Apply in **Studio, Earn**, and accept the terms including the **Shorts Monetization Module**.
2. Create or link an **AdSense** account (India address, your legal name).
3. Submit **tax info** in AdSense (W-8BEN, claiming the India–US treaty rate).

## Done by the agent (2026-09-26)

- **Channel:** Days of Odd (@DaysOfOdd) created under your Google account as a Brand Account, with picture,
  banner, description, keywords, country India, audience "not made for kids", and upload defaults
  (Education, English (United States), tags). Your other channels are untouched.
- **2-Step Verification:** already on for your account since July.
- **Buffer:** signed up with Google, email confirmed, Days of Odd connected, API key in `pipeline/.env`.
- **Cloudinary:** signed up with Google, API credentials in `pipeline/.env`.
- **Modal:** signed up with Google (workspace `<modal-workspace>`), API token in `pipeline/.env`. You added a card
  on 2026-09-27, and the agent set the **Spend limit** to **$0**: Modal stops anything that would be charged to
  the card, and runs only what the $30 monthly credit covers
  ([Modal: budgets](https://modal.com/docs/guide/budgets)). The studio uses about $1 of it a month for its
  own runs and about 12 cents a Short, so the credit covers about 230 Shorts a month against the plan's 90.
- **Cloud studio:** Modal runs it four times a day (`studio_run` in the `days-of-odd` app), making,
  reviewing, and scheduling Shorts on its own. Its state is in the private repository
  <https://github.com/<owner>/days-of-odd>, which it pushes to with a deploy key that reaches only that
  repository. GitHub's `studio` workflow is the backup, and works only when Modal's runs have stopped; its
  `watchdog` workflow sends the phone alerts. The laptop's hourly job is retired.
- **YouTube settings after your phone verification:** YouTube's automatic visual and audio "enhancement"
  off, comment spam filters on, and a notification when the channel becomes eligible to earn.
- **Series playlists:** the agent's tools sign in to YouTube's API as Days of Odd and add each live Short to
  its series playlist. Revoke any time at <https://myaccount.google.com/permissions>.

## Watching it

The watchdog on GitHub checks everything every 3 hours, sends new alerts to your phone, and sends the
morning summary (above). `/usr/bin/python3 monitor/monitor.py --digest` sends a summary now. On this
Mac, a monitor also runs every 15 minutes (launchd job `com.daysofodd.monitor`; it only reads). It shows a
macOS notification when something needs attention, and keeps a dashboard at `monitor/out/dashboard.html`
(`/usr/bin/python3 monitor/monitor.py --open` refreshes and opens it). Remove it with
`/usr/bin/python3 monitor/install.py --remove`. The Mac can be off: the channel doesn't depend on it.

## If a key changes

A key lives in three places: `pipeline/.env` on this Mac, the Modal secret `days-of-odd-studio` (which
Modal's runs use; `python3 pipeline/modal_secret.py modal` rebuilds it from `pipeline/.env` and `secrets/`),
and the repository's Actions secrets (<https://github.com/<owner>/days-of-odd/settings/secrets/actions>, for
GitHub's backup and the watchdog). Modal workers get the new value from the next run's deploy.

- **Cursor key:** (left out of this copy.)
- **Gemini, Buffer, or Cloudinary keys:** the same three places.
- **Mistral key** (`YTC_MISTRAL_API_KEY`, a backup model once Gemini's Flash quota is spent): the key "days-of-odd
  studio" on <owner-email>'s free Mistral account (<https://admin.mistral.ai>, API Keys), in the same three
  places. Without it the studio skips Mistral and uses its other backups.
- **OpenRouter key** (`YTC_OPENROUTER_API_KEY`, the Dots3 backup writer, 50 free requests a day): the key
  "days-of-odd studio" (no expiry, $1 limit, free models only) on <owner-email>'s OpenRouter account
  (<https://openrouter.ai/workspaces/default/keys>), in the same three places. Without it the studio skips OpenRouter.
- **YouTube sign-in** (the studio's playlists and stats fail with `invalid_grant`): on this Mac, run
  `uv run --no-sync ytc auth` in `pipeline/`, choose <owner-email> and then Days of Odd, run
  `python3 modal_secret.py modal`, and copy the new `secrets/token.json` into the `YTC_GOOGLE_TOKEN` secret:
  `gh secret set YTC_GOOGLE_TOKEN --repo <owner>/days-of-odd < ../secrets/token.json`.
- **Modal token** (the Mac and GitHub's backup use it; runs on Modal don't need one): `modal token new`, then copy it to
  the `MODAL_TOKEN_ID=` and `MODAL_TOKEN_SECRET=` lines of `pipeline/.env` and the Actions secrets of the same
  names.

## Optional extras

- **Instagram Reels cross-posting:** an Instagram professional account `@daysofodd` connected in Buffer would
  let the agent post each Short there too. (TikTok isn't available in India.)

## What you never need to do

Write, edit, upload, schedule, or title videos. The agent does all of that and writes a daily report
in `reports/`.
