# Set up a YouTube Shorts channel that runs itself

Paste this whole file into Cursor Agent (Opus 5.5), started in your home folder, on the Mac that will own
the channel. The agent does the setup. You, the owner, only do what needs your password, phone, card, or a
decision, and it asks for each of those when it gets there. Plan on about half a day, most of it waiting
on installs and the first renders. Afterwards the channel runs in the cloud and this Mac can be off.

---

You are setting up an automated YouTube Shorts studio for a **new channel in a new niche**, on this Mac,
for the person at the keyboard (the owner). The studio comes from a kit that runs a live channel today
(Days of Odd, strange-but-true history). When you're done, it runs on free cloud tiers four times a day:
it picks topics, researches them from real sources, writes, narrates, finds openly licensed pictures,
renders, reviews each Short against a quality gate, and schedules it on YouTube through Buffer. Nobody
needs to touch it, and the Mac can be switched off.

The kit is `~/Downloads/youtube-studio-kit.zip` (it came on Slack with this file). You'll work in
`~/youtube-studio`.

## Rules for the whole setup

1. **Some steps are the owner's alone:** passwords, SMS or two-step codes, phone verification, card
   details, clicking **Allow** on consent screens, and the final choice of niche and name. Ask for each
   one clearly, one at a time, with the exact link and what to click, then wait. Do everything else
   yourself.
2. **Keys never go in the chat.** The owner copies a key in the browser and tells you it's copied. You
   then run `python3 kit/setkey.py NAME`, which moves it from the clipboard into `pipeline/.env`, prints
   only its length, and clears the clipboard. Never print, `cat`, `grep`, or echo a value from
   `pipeline/.env` or `secrets/`, and never commit either one (`kit/verify.py` checks).
3. **Use the owner's personal Google account for every sign-up,** never a work account. Company
   accounts and seats (Google Workspace, a company Cursor seat) aren't meant for a personal, monetized
   channel. `research/free-image-generation-2026-09-28.md` covers this for Workspace Gemini.
4. **YouTube's rules come first** (the Hard rules in `CHANNEL.md`, and "Never" in `PLAYBOOK.md`). No
   bought views or subscribers, no bots, and no automating YouTube's website: publishing goes only through
   Buffer's official integration. Every claim must be sourced, and every picture public domain, CC0, or
   CC BY. Don't weaken these to make a step easier.
5. **Open web pages in the owner's own Chrome profile,** the one signed in to his personal Google account:
   `open -na "Google Chrome" --args --profile-directory="<dir>" "<url>"`. The profile directories and
   their accounts are listed in `~/Library/Application Support/Google/Chrome/Local State`
   (`profile.info_cache`). If there's more than one personal profile, ask which. The owner does the
   clicking. Don't use browser-automation tools on these sites.
6. **Long commands** (`uv sync`, renders, the first cloud runs) go in the background. Poll them rather
   than blocking.
7. If the "no approval prompts" setup sent earlier is installed, follow its tool rules
   (`~/.cursor/rules/no-approval-prompts.mdc`). The same table is in `PLAYBOOK.md`.
8. Keep a log in `reports/setup.md` as you go: each phase, what was decided and why, and anything left
   for the owner. Record decisions in `CHANNEL.md`'s decision log too.
9. Stop at each **Gate** and run its check. If it fails, fix the cause before moving on.

## Phase 0: Tools and the kit (15 minutes)

1. Check what's installed: `xcode-select -p`, `brew --version`, `uv --version`, `gh --version`,
   `git --version`, and `ffmpeg -hide_banner -filters | grep subtitles`. The last one confirms FFmpeg has
   libass, which the captions need. Install anything missing with `brew install uv gh ffmpeg`. If
   Homebrew itself is missing, the owner installs it from <https://brew.sh>; it asks for his Mac password.
2. Unpack the kit: `ditto -x -k ~/Downloads/youtube-studio-kit.zip ~/`, which makes `~/youtube-studio`.
   If that folder already exists, stop and ask. A second download may be named
   `youtube-studio-kit (1).zip`; use the newest. If the Slack message gave a SHA-256, compare it with
   `shasum -a 256` of the zip first, and stop if they differ.
3. GitHub: the owner needs a personal GitHub account. Run `gh auth login --hostname github.com --git-protocol https --web --scopes workflow`;
   he approves it in the browser.
4. Read these before going further: `kit/NICHE-ADAPTATION.md`, `kit/ACCOUNTS.md`, `PLAYBOOK.md`,
   `CHANNEL.md`, and the decision log in `reference/days-of-odd/CHANNEL.md`. That log explains why the
   pipeline works the way it does, including the mistakes that shaped it.

**Gate 0:** `python3 kit/verify.py --stage kit` passes.

## Phase 1: Niche and name (with the owner, 30 minutes)

1. Research which Shorts niches are growing right now, from current data: vidIQ, Tubefilter, YouTube's
   own trend reports, and channel trackers. `research/niche-selection.md` and
   `research/shorts-strategy.md` are a starting point from September 2026; refresh them.
2. Keep only niches this studio can make well:
   - **One true, surprising story or fact per Short,** 40 to 58 seconds long. Each one is researched from
     web pages, and every claim must appear on two different sites. Every topic needs an English
     Wikipedia article, because the studio finds, checks, and ranks topics through Wikipedia.
   - **Pictures it's allowed to use:** public domain, CC0, or CC BY only, found through Wikimedia Commons,
     Wikidata, Openverse, NASA, Wellcome Collection, the Met, and the Art Institute of Chicago. Niches
     whose pictures are mostly copyrighted (celebrities, sports, films, games, brands, current news) or
     ShareAlike/NonCommercial won't work.
   - **Advertiser-friendly and low policy risk:** no medical, legal, or financial advice, no gore, true
     crime, or politics, and nothing aimed at children.
   - **Pays well:** English with a US-first audience. The studio posts in US Eastern evening slots.
   - **Not strange-but-true history,** which is Days of Odd, the channel this kit comes from.
   - Good fits for the studio include space and astronomy (NASA, ESA, and ESO imagery), the deep ocean
     (NOAA), strange animals and nature, science and inventions, geography and strange places, art
     mysteries (public-domain paintings), mythology told through art, and medicine's past (Wellcome).
3. Give the owner a shortlist of 3 to 5 with evidence for each: example channels and how fast they grew,
   the pay category, the picture supply you actually checked on Commons with the license filters, the
   policy risk, and whether you could list 100 topics. Recommend one. **The owner chooses.**
4. Series: 4 to 7 named series for the niche, each a promise viewers can recognize. See the Series
   section of `reference/days-of-odd/strategy/STRATEGY.md`.
5. Name and handle: 5 short, brandable candidates. Check each handle with
   `curl -s -o /dev/null -w '%{http_code}' https://www.youtube.com/@<handle>` (404 means it's free), and
   search YouTube for channels already using the name. **The owner chooses.**
6. Apply it:

   ```bash
   cd ~/youtube-studio
   python3 kit/configure.py --name "<Name>" --handle <Handle> --github <github-user>/<repo> \
       --email <owner's personal email> --day-zero <launch date, YYYY-MM-DD> --hashtag <first hashtag> \
       --series "<Series 1>" "<Series 2>" "<Series 3>" "<Series 4>"
   ```

   It changes the identity everywhere (code, workflows, docs, Modal app names) and can be run again.
   Record the niche, name, and reasons in `CHANNEL.md`'s decision log.

**Gate 1:** `python3 kit/verify.py --stage configured` passes.

## Phase 2: Accounts (the owner at the keyboard, 45 to 60 minutes)

Work through `kit/ACCOUNTS.md` in order: the YouTube channel (a Brand Account, with phone verification),
a Google Cloud project with the YouTube APIs and an OAuth client, a Gemini API key, Buffer (connected to
the new channel), Cloudinary, and Modal. Mistral and OpenRouter are optional backup models. Start
`cd pipeline && uv sync` in the background at the beginning of this phase: it downloads about 2 GB, and
Buffer, Modal, and YouTube's sign-in need it.

**Gate 2:** `python3 kit/setkey.py --list` shows every required key set, and `uv run --no-sync ytc channels`
(run in `pipeline/`) lists the new channel. After `uv run --no-sync ytc auth` (the owner picks his
account, then **the new channel**), `secrets/token.json` exists, and `kit/configure.py --channel-id` has
the new channel's ID (`kit/ACCOUNTS.md`, step 3).

## Phase 3: Make it the new niche's studio (you, 1 to 2 hours)

Follow `kit/NICHE-ADAPTATION.md`: rewrite every `NICHE:` spot for the new niche, write
`strategy/STRATEGY.md` and `strategy/PLAN-100.md`, seed `strategy/CALENDAR.md` (at least 40 topics across
the series, plus the next 8 weeks of anniversaries), fill in `CHANNEL.md`, and make the brand (avatar,
banner, watermark, channel description, keywords). The owner uploads the channel art in YouTube Studio,
under Customization; open `brand/out/` for him.

**Gate 3:** `python3 kit/verify.py --stage adapted` passes.

## Phase 4: The first Short, made on this Mac (30 to 60 minutes, mostly waiting)

1. In `pipeline/`:
   `YTC_RENDER_HERE=1 YTC_RANK_HERE=1 uv run --no-sync ytc produce --topic "<a strong topic from the calendar>" --series "<its series>"`.
   It makes one Short end to end on this Mac and hosts it on Cloudinary, ready for Buffer. The first run
   also downloads the voice, speech, and picture-ranking models.
2. Read what it made in `content/episodes/ep001/`: `research.json`, `short.yaml`, and `review.json` (the
   quality gate's scores and notes). Then open `ep001.mp4` for the owner.
3. If the scores are under 4 or the owner doesn't like it, improve the prompts and rules (not the checks),
   delete the episode folder, and make it again. **The owner approves the first Short.** Anything left in
   `content/episodes/` gets scheduled by the first cloud run.

**Gate 4:** the first Short passes the gate (every score 4 or more, and no `ytc check` warnings), and the
owner has approved it.

## Phase 5: Into the cloud (30 to 45 minutes)

1. In `~/youtube-studio`: `git init -b main`, `git add -A`, then run `python3 kit/verify.py --stage predeploy`
   and fix anything it reports. After that, `git commit -m "Studio setup"` and
   `gh repo create <github-user>/<repo> --private --source . --push`.
2. `python3 pipeline/modal_secret.py` adds a deploy key to the repository (the only thing Modal's runs
   can push to), makes the ntfy alert topic, and builds the Modal secret. Then run
   `python3 kit/push_secrets.py` for GitHub's Actions secrets and variables.
3. The owner installs **ntfy** on his phone and subscribes to the topic on the `YTC_NTFY_TOPIC` line of
   `pipeline/.env`. Tell him the topic name once, on screen. Anyone who knows it can read the alerts.
4. First cloud run: `gh workflow run studio --repo <github-user>/<repo> -f produce=3 -f daily=no`. It
   deploys the Modal app (with its schedule: four runs a day), starts three Shorts on Modal, and schedules
   ep001 into Buffer. Follow it with `gh run watch`, then `git pull` and read `status/status.json`.
5. About an hour later, run it again (`-f produce=0`) or wait for the next scheduled run. It collects the
   finished Shorts and schedules them. Check the queue in Buffer and in `status/status.json`.
6. `gh workflow run watchdog --repo <github-user>/<repo>` sends the day's summary to the owner's phone.
7. With the owner, finish the YouTube Studio settings from `kit/ACCOUNTS.md` (under "Channel settings").

**Gate 5:** `status/status.json` shows a run on Modal with no errors. The Modal app `<slug>` has
`studio_run` on its schedule, Buffer shows the next posts queued, and the owner received the ntfy summary.

## Phase 6: Hand-off

1. Fill in `OWNER-CHECKLIST.md`: what the owner may ever need to do, where each key lives, and how to
   renew the Buffer key before it expires.
2. Commit and push. Then give the owner a short summary:
   - **Where it runs:** Modal runs it four times a day, GitHub's `studio` workflow is the backup, and the
     `watchdog` checks every 3 hours.
   - **What it costs:** nothing on the free tiers. With a card on Modal, the spend limit is $0.
   - **How to watch it:** the ntfy morning summary, the YouTube Studio app, and the Buffer app.
   - **How to pause everything:** `modal app stop <slug>`, then disable the `studio` and `watchdog`
     workflows in the repository's Actions tab.
   - **What comes later:** applying for monetization when YouTube Studio shows he's eligible (1,000
     subscribers and 10 million Shorts views in 90 days). YouTube can still turn down channels that look
     mass-produced, and his own recorded voice is the strongest protection against that.
3. The Mac isn't needed from here on. Say so.
