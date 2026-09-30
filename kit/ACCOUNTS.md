# Accounts, one time

Do these in order, with the owner at the keyboard. Open each link in his own Chrome profile (START-HERE,
rule 5). He signs in and clicks; you explain what to click, set keys with `python3 kit/setkey.py`, and
check each step before moving on. Everything here is on a free plan.

Commands that start with `uv run` go in `pipeline/` and need `uv sync` to have finished.

| # | Account | Gives the studio | Owner's part |
|---|---|---|---|
| 1 | Google (personal) | the identity behind everything | two-step verification on |
| 2 | YouTube channel | the channel, as a Brand Account | phone verification |
| 3 | Google Cloud project | the YouTube Data and Analytics APIs and the OAuth client | consent |
| 4 | Google AI Studio | `YTC_GEMINI_API_KEY`, the main language model | none |
| 5 | Buffer | publishing to YouTube: `BUFFER_API_KEY`, `BUFFER_YOUTUBE_CHANNEL_ID` | connect the channel |
| 6 | Cloudinary | video hosting that Buffer fetches from: `CLOUDINARY_URL` | none |
| 7 | Modal | cloud runs and renders: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` | optional card |
| 8 | ntfy (phone app) | alerts and a morning summary | install the app |
| 9 | Mistral, OpenRouter (optional) | backup language models | Mistral asks for a phone number |

Also set the contact address now; it's sent to Wikimedia and the other archives in the User-Agent, as
their API rules ask: `python3 kit/setkey.py --set YTC_CONTACT=<owner's email>`.

## 1. Google account

Use the owner's personal Gmail account, and check that two-step verification is on:
<https://myaccount.google.com/signinoptions/two-step-verification>.

## 2. The YouTube channel

1. <https://www.youtube.com/account>, then **Add or manage your channel(s)**, then **Create a channel**.
   Enter the exact name from Phase 1. This creates a Brand Account, which keeps the channel separate from
   his personal one.
2. Set the handle: <https://studio.youtube.com>, **Customization**, **Basic info**, **Handle**.
3. Verify the phone number: <https://www.youtube.com/verify>. One number can verify only two channels a
   year. Verification unlocks intermediate features, and the Partner Program needs the advanced ones:
   Studio, **Settings**, **Channel**, **Feature eligibility**.
4. Channel settings to go through with him now (Studio, **Settings**):
   - **Channel**, **Basic info**: his country of residence (for tax and payments later), and keywords from
     `brand/CHANNEL-COPY.md` once you've written it.
   - **Channel**, **Advanced settings**: **No, set this channel as not made for kids.**
   - **Upload defaults**: category (Education, or Science & Technology if it fits better), language
     English (United States), and the default tags.
   - YouTube's automatic video and audio "enhancements": off. Comments: hold comments with links for
     review, and block spam words (crypto, WhatsApp, Telegram, giveaways, sub4sub).
   - **Permissions**: leave it alone. The studio doesn't need Studio access.
5. Later, in Phase 3, he uploads the channel picture, banner, and watermark from `brand/out/` and pastes
   the description (**Customization**, **Branding** and **Basic info**).

## 3. Google Cloud project, the YouTube APIs, and the OAuth client

The studio signs in to YouTube's APIs for analytics and playlists only. It never uploads through them:
uploads from an unaudited API project are locked to private, so publishing goes through Buffer.

1. <https://console.cloud.google.com/projectcreate>: create a project named after the channel's slug.
   **Don't enable billing on it.** Without billing, Gemini's free tier just stops at its quota; with
   billing, the same calls are charged.
2. **APIs & Services**, **Library**: enable **YouTube Data API v3** and **YouTube Analytics API**.
3. **Google Auth Platform** (the OAuth consent screen): **External** audience, app name "<channel name>
   tools", and his email as the support and developer contact.
4. **Audience**, then **Publish app**, to put it **In production**. In Testing mode, sign-ins expire every
   7 days, and Brand Account channels can't be added as test users. The app stays unverified, which is
   allowed for personal use with fewer than 100 users. When he signs in, Google warns that it hasn't
   verified the app; he continues, because it's his own app. If the screen insists on a home page and
   privacy policy, deploy `site/` (step 10) and use those links.
5. **Clients**, **Create client**, type **Desktop app**. Download the JSON, then:
   `python3 kit/setkey.py --google-client ~/Downloads/client_secret_<...>.json`.
6. After `uv sync`, tell the studio which Chrome profile is his (the directory from START-HERE, rule 5,
   such as `Default` or `Profile 2`): `python3 kit/setkey.py --set "YTC_CHROME_PROFILE=<directory>"`.
   Then, in `pipeline/`, run `uv run --no-sync ytc auth`. In the browser he picks his account, then **the new
   channel** (not his personal one), continues past the unverified-app warning, and allows every
   permission it asks for. That writes `secrets/token.json`. If the studio later reports `invalid_grant`,
   repeat this step and run `python3 pipeline/modal_secret.py modal` and `python3 kit/push_secrets.py`.
7. Give the studio the channel's ID (the monitor reads the channel's public feed with it). In `pipeline/`:

   ```bash
   uv run --no-sync python -c "from googleapiclient.discovery import build; from ytc.youtube import _credentials; c = build('youtube', 'v3', credentials=_credentials()).channels().list(part='snippet', mine=True).execute()['items'][0]; print(c['id'], c['snippet']['title'])"
   ```

   If the title isn't the new channel's, the sign-in picked the wrong channel: repeat step 6. Otherwise, in
   `~/youtube-studio`: `python3 kit/configure.py --channel-id <the UC... id>`.

## 4. Gemini API key

<https://aistudio.google.com/apikey>, **Create API key**, in the project from step 3 (import the project
if AI Studio doesn't list it). Copy it, then run `python3 kit/setkey.py YTC_GEMINI_API_KEY`. The free tier's
daily quotas are what the studio is built around (`pipeline/src/ytc/llm.py`).

## 5. Buffer

1. <https://buffer.com>, **Get started for free**, and sign up with his Google account.
2. Connect a channel: **YouTube**, his Google account, then **the new channel**. Grant everything Buffer
   asks for; it requires all four YouTube permissions.
3. The API key: <https://publish.buffer.com/settings/api>, **Personal Access**, **+ New Key**. Name it
   "<slug> studio", keep the default permissions, and set the expiration to **1 year**. Put a reminder in
   his calendar about 11 months out to replace it; the studio alerts if Buffer rejects the key. Copy it,
   then run `python3 kit/setkey.py BUFFER_API_KEY`.
4. After `uv sync`: `uv run --no-sync ytc channels` lists the connected channels. Save the new channel's
   id: `python3 kit/setkey.py --set BUFFER_YOUTUBE_CHANNEL_ID=<id>`.

The free plan holds 10 scheduled posts per channel. The studio keeps finished Shorts waiting in
`content/episodes/` and refills Buffer as posts go out.

## 6. Cloudinary

<https://cloudinary.com/users/register_free>: sign up with Google. On the dashboard
(<https://console.cloudinary.com>), open **API Keys**, and copy the **API environment variable**
(`cloudinary://<key>:<secret>@<cloud name>`). Then run `python3 kit/setkey.py CLOUDINARY_URL`; a leading
`CLOUDINARY_URL=` is removed if it was copied too. The free plan rejects videos over 100 MB, so renders are
capped at 40 MB. Hosted copies are deleted two days after a Short goes live.

## 7. Modal

1. <https://modal.com/signup>: sign up with GitHub or Google.
2. After `uv sync`: `uv run --no-sync modal token new`, and he approves it in the browser. Then run
   `python3 kit/setkey.py --modal` to copy the token into `pipeline/.env`.
3. Credit. The Starter plan includes $1 of compute a month without a card, and $30 a month with one. A
   Short made on Modal costs about $0.12, and the four daily runs about $1 a month.
   - **With a card (recommended):** he adds one under **Settings**, **Usage & Billing**, and sets the
     **spend limit to $0**, so Modal stops rather than charging anything. Then run
     `python3 kit/setkey.py --set YTC_MODAL_CREDIT=30`.
   - **Without a card:** leave `YTC_MODAL_CREDIT=1`. Most Shorts are then made on GitHub's free runners:
     about 40 a month instead of 90 or more, within the free plan's 2,000 minutes.

## 8. ntfy on his phone

After `python3 pipeline/modal_secret.py` has made the topic (Phase 5): he installs **ntfy** (App Store or
Google Play), taps **+**, and enters the topic from the `YTC_NTFY_TOPIC` line of `pipeline/.env` on the
default server. On Android, also allow notifications and turn off battery optimization for ntfy. It
rings when something needs attention, and sends a summary every morning (after 08:00 IST).

## 9. Optional backup models

Once Gemini's daily quotas run out, the studio carries on with free backup models. None of these is
required; without them, it waits for the next day's quota.

- **Mistral:** <https://console.mistral.ai>. The free Experiment plan asks for a phone number. Create an
  API key, then run `python3 kit/setkey.py YTC_MISTRAL_API_KEY`.
- **OpenRouter:** <https://openrouter.ai/settings/keys>. Create a key with a $1 limit (the studio only
  uses free models), then run `python3 kit/setkey.py YTC_OPENROUTER_API_KEY`.
- **Cursor:** the last resort (`cursor_llm.py`). Use a key from his personal Cursor account only, never
  from a company seat. It's fine to leave this unset.

## 10. Optional: the app's home page and privacy policy

Only if Google's consent screen requires them. `site/` has both pages (edit them in Phase 3). Put them on
Cloudflare Pages for free: `npx wrangler login`, then
`npx wrangler pages deploy site --project-name=<slug without dashes> --branch=main`. That gives
`https://<project>.pages.dev/` and `.../privacy.html`.

## Where each key lives, once set up

1. `pipeline/.env` and `secrets/` on this Mac. Both are git-ignored.
2. The Modal secret `<slug>-studio`, which Modal's runs read. `python3 pipeline/modal_secret.py modal`
   rebuilds it.
3. The repository's Actions secrets, which GitHub's backup runs and the watchdog read.
   `python3 kit/push_secrets.py` sets them.

A changed key goes in all three: `kit/setkey.py`, then `pipeline/modal_secret.py modal`, then
`kit/push_secrets.py`.
