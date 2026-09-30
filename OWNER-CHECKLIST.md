# Owner checklist

The channel runs in the cloud on free tiers, without you or this Mac. This list keeps only what needs you:
your phone, your card, or a sign-in. Owner: aksha.shivam18@gmail.com (Chrome Profile 5). Setup started
2026-09-30; Day 0 is 2026-10-03.

## Needed from you

Nothing is required: every account was created by the agent on 2026-09-30 and the channel runs in the cloud.
Two optional steps help, in order of value:

1. **Phone verification** (<https://www.youtube.com/verify>, signed in as aksha.shivam18@gmail.com): needed
   before applying for monetization, not before.
2. **ntfy on your phone:** subscribe to the topic on the `YTC_NTFY_TOPIC` line of `pipeline/.env` (the agent
   tells you it once) for alerts and a morning summary. It's a different topic from Universe Receipts'.

## Done by the agent (2026-09-30)

- **Channel:** Creature Receipts (@CreatureReceipts), the YouTube channel of aksha.shivam18@gmail.com, with
  picture, banner, watermark, description, keywords, country India, and "not made for kids". Your work
  account was never used.
- **Google Cloud:** project `shorts-studio-two`, YouTube Data and Analytics APIs, OAuth app "Creature Receipts
  tools" in production (home page and privacy policy on GitHub Pages), signed in as the channel for stats and
  playlists.
- **Gemini, Buffer, Cloudinary:** accounts on your Google address (Buffer by email: use **Forgot password** at
  <https://login.buffer.com> if you ever want to sign in yourself). Keys in `pipeline/.env`, the Modal secret,
  and the GitHub repository's secrets.
- **Modal:** shares Universe Receipts' workspace (akshshivam5), its card, its $0 spend limit, and its $30 a
  month of credit. Nothing new to pay or watch.
- **Cloud studio:** private repository <https://github.com/ashivam-dot/creature-receipts>; Modal runs it four
  times a day, GitHub's `studio` workflow is the backup, and `watchdog` checks every 3 hours.

## Optional extras that add reach

- **Instagram Reels and Facebook Reels:** a professional Instagram account `@creaturereceipts` (and its
  Facebook page) connected in this Buffer account lets the studio post each Short there natively too. Buffer's
  free plan allows 3 channels. TikTok isn't available in India.
- **Your own voice:** recording narration yourself is the strongest defence against YouTube's
  inauthentic-content review when applying for monetization.

## Your phone

- **ntfy** is subscribed to the channel's private topic. It rings when something needs attention: a run
  failed or couldn't save, Buffer can't post, a Short didn't go public, or stock is running low. Every
  morning, usually between 08:00 and noon IST, it also sends a summary: the day, Shorts live, views,
  subscribers, the next posts, stock, the last studio run, and the month's Modal and Cloudinary use.
  **No summary by noon means the watchdog itself has stopped;** check
  <https://github.com/ashivam-dot/creature-receipts/actions/workflows/watchdog.yml>. Anyone who knows the topic can
  read the alerts, so keep it to yourself.
- **YouTube Studio**, on the channel: live views, subscribers, and comments.
- **Buffer**: the queue of scheduled Shorts (**Queue**) and what went out (**Sent**).

## Once a year: the Buffer key

The Buffer API key expires on 2027-09-30 (it's made for a year at most). Before then, make a new one at
<https://publish.buffer.com/settings/api> and give it to the agent (START-HERE, rule 2), which puts it in
the three places below. If it lapses, Buffer rejects the studio's posts and ntfy says so.

## Later: monetization

When Studio's **Earn** tab says you're eligible (1,000 subscribers and 10 million Shorts views in 90 days;
20 million for applications from 2027-02-01):

1. Apply in **Studio**, **Earn**, and accept the terms, including the **Shorts Monetization Module**.
2. Create or link an **AdSense** account with your legal name and address.
3. Submit your tax information in AdSense (W-8BEN if you're not in the US, claiming your country's treaty
   rate if it has one).

## If a key changes

A key lives in three places: `pipeline/.env` on this Mac, the Modal secret `creature-receipts-studio` (which
Modal's runs use), and the repository's Actions secrets (GitHub's backup runs and the watchdog). To change
one: `python3 kit/setkey.py NAME`, then `python3 pipeline/modal_secret.py modal`, then
`python3 kit/push_secrets.py`.

- **YouTube sign-in** (the studio's playlists and stats fail with `invalid_grant`): in `pipeline/`, run
  `uv run --no-sync ytc auth`, choose aksha.shivam18@gmail.com, and update the other two places as above.
- **Modal token** (this Mac and GitHub's backup use it; runs on Modal don't need one): it's Universe
  Receipts' workspace token. After `uv run --no-sync modal token new` in `pipeline/`, run
  `python3 kit/setkey.py --modal` and `python3 kit/push_secrets.py` in both studios.

## Pausing or stopping

- **Pause everything:** `uv run --no-sync modal app stop creature-receipts` in `pipeline/`, then disable the
  `studio` and `watchdog` workflows in the repository's **Actions** tab. Start again by enabling the
  workflows and running `gh workflow run studio`; that redeploys the Modal app. Universe Receipts keeps
  running.
- **Stop publishing only:** pause the queue in Buffer.

## What you never need to do

Write, edit, upload, schedule, or title videos. The studio does all of that and writes a daily report in
`reports/`.
