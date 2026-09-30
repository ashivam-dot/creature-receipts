# Creature Receipts: source of truth

- **Channel:** Creature Receipts (@CreatureReceipts), <https://www.youtube.com/@CreatureReceipts>, the YouTube
  channel of the Google account aksha.shivam18@gmail.com (not a Brand Account; the name shows only on YouTube).
  Channel ID `UC6e6OB3iw3yp8JnnBYxLItA`. Buffer channel ID `6abcba6dea19ca0bde30177e`. Created 2026-09-30.
- **Niche:** true stories of strange animals, extreme biology, and deep-sea life, every claim backed by sources
  ("receipts") listed in the description. English, for a US audience (then the UK, Canada, Australia). Space
  belongs to the sister channel Universe Receipts.
- **Series:** Built Different, Deep Sea Files, Back From Extinction, Evolution Got Weird, Nature's Record
  Breakers, Animal Myths, Busted. First hashtag `#animals`.
- **Owner account:** aksha.shivam18@gmail.com (a personal Google account); the owner lives in India, so the
  channel country is India. Chrome profile: Profile 5. Never use the owner's work account or its Chrome
  profile for anything on this channel.
- **Accounts (on aksha.shivam18@gmail.com unless noted, created 2026-09-30):** Google Cloud project
  `shorts-studio-two` (YouTube Data and Analytics APIs, OAuth app "Creature Receipts tools" in production,
  unverified, Desktop client); a Gemini key from the AI Studio project `creature-receipts` on akshshivam5@gmail.com (see the decisions log); Buffer (free, email sign-up); Cloudinary (free,
  cloud `uj4a07e7`); Modal: Universe Receipts' workspace `akshshivam5`, shared; GitHub `ashivam-dot`. Public repository <https://github.com/ashivam-dot/creature-receipts> (secrets only in Modal and Actions secrets). App home page and privacy policy on GitHub
  Pages: <https://ashivam-dot.github.io/creature-receipts-site/>. Modal app: `creature-receipts`.
- **Dates:** Day 0 is 2026-10-01; Day 100 is 2027-01-09.
- **Target:** YouTube Partner Program monetization on Shorts before the 2027-02-01 threshold change, and as
  much growth toward the owner's 100,000-subscriber goal as original, accurate Shorts can earn. The honest
  cases are in `strategy/PLAN-100.md`.
- **Format:** YouTube Shorts only, 40–58 seconds, at US Eastern evening slots: 2 a day, then 3 from Day 15, 4
  from Day 30, and 5 from Day 50, each step only while engaged views per Short hold (`auto.slots_per_day`),
  monetized through the Shorts path of the YouTube Partner Program.
- **Built from:** the studio of Universe Receipts, itself built from the Days of Odd kit.
  `reference/days-of-odd/` has that channel's documents; its decision log explains why the pipeline works
  the way it does.

Start here: `PLAYBOOK.md` (the daily routine), `strategy/STRATEGY.md`, `strategy/PLAN-100.md`,
`strategy/CALENDAR.md`, `strategy/SCRIPT-RULES.md`, `OWNER-CHECKLIST.md`. This channel's research is in
`research/channel/`.

## Standing instructions from the owner

- The agent manages the channel end to end: niche, audience, format, settings, branding, scripts, voice,
  editing, captions, titles, hashtags, scheduling, promotion, and analytics. It writes a daily report in
  `reports/`.
- Use the best available open-source repo, library, framework, or tool for each job. Re-check GitHub
  (stars, recent pushes, archived status, commercial-use license) before adopting or replacing a tool, and
  record the check in `research/`.
- Production never stops and never needs the Mac: it runs in the cloud on free tiers (see "How it runs").
  The Mac only monitors.
- Open anything on the channel's Google account in the owner's own Chrome profile, never with bare `open`.
- The owner signs in to every service himself. The agent never stores or types passwords, SMS codes, or
  card details, and keys go into `pipeline/.env` with `kit/setkey.py`, never through the chat.

## Hard rules

- No bought subscribers or views, bots, sub-for-sub, engagement pods, spam comments, fake accounts,
  reuploads of other creators' content, or misleading titles. These violate YouTube policy and end monetization.
- No automated use of YouTube's website for anything recurring: uploads, comments, likes, subscriptions,
  views, or scraping. YouTube's terms forbid automated access. Publishing goes through Buffer's official API
  integration; analytics through the official APIs. One-time account setup (creating the channel, branding, settings) is done by the owner, in his own
  browser.
- The YouTube API sign-in can edit the channel, but the pipeline only reads analytics, adds Shorts to
  playlists, and (when built) moderates held comments. Never edit, delete, or upload videos through it.
- Every Short has an original, sourced script with a claims table, so it passes YouTube's inauthentic-content review.
  Disclose realistic synthetic media when YouTube requires it.
- Use only assets whose licenses allow commercial use: public domain, CC0, or CC BY with credit.

## How it runs

| Job | Tool | Cost |
|---|---|---|
| Running the channel | The cloud studio on Modal: `studio_run` in the Modal app `creature-receipts` runs `ytc auto` four times a day (11:05, 17:05, 23:05, 05:05 IST) on a fresh clone of the repository <https://github.com/ashivam-dot/creature-receipts>, and pushes what changed with a deploy key that reaches only that repository. Each run deploys that clone's code as the app first (so `slot_watch` runs the latest code), syncs Buffer, files live Shorts into playlists, collects finished Shorts, does the daily routine in the first run after 14:00 IST (stats, learnings, new topics, report), schedules Shorts into Buffer, and starts new ones when fewer than 42 are ready. Its state lives in the repository (`status/`, `content/`, `strategy/`); its keys in the Modal secret `creature-receipts-studio` (`pipeline/modal_secret.py`). GitHub's `studio` workflow is the backup: its schedule is 2 hours behind, and it works only when Modal's last run failed or is over 8 hours old. The Mac isn't needed | free: about $1 a month of Modal's credit. The Modal workspace (`akshshivam5`, $30 of credit a month, spend limit $0) is shared with Universe Receipts, and both studios read the workspace's total spend |
| Research, scripts, image picks, reviews | Gemini's free tier first (AI Studio project `creature-receipts` on akshshivam5@gmail.com), about 15 seconds a prompt: every step starts on the six Flash models (20 requests a day each), except the picture checks, which start on the Flash-Lite models (500 a day each). Once Flash is spent, scripts go to Flash-Lite, and the other steps to Flash-Lite and then to other providers' free models through their OpenAI-compatible APIs (`llm.PROVIDERS`; one whose key isn't set is skipped): OVHcloud AI Endpoints without an account (Qwen3.5-397B and two Qwen 27B models; 2 requests a minute per model, shared by everyone on the same address, so best effort), Mistral's free plan (Ministral 14B, 30 requests a minute, key in the `YTC_MISTRAL_API_KEY` secret; it researches, picks, and checks, but broke the script rules in testing, so it writes nothing), and OpenRouter's free Dots3-Note Preview (50 requests a day for the account, key in the `YTC_OPENROUTER_API_KEY` secret; it writes and researches after Qwen3.5-397B and ahead of Gemma, but doesn't judge). Gemma 4 31B, in the same Gemini project, takes prompts under its 16,000-token-a-minute cap. So no Short is held for Gemini's reset. The review, which decides what gets published, uses a Flash model while 9 or more are ready: a Short finished after Flash is spent waits for the reset (12:35 IST, 13:35 in winter) and is reviewed first after it. With fewer than 9 ready, Qwen3.5-397B or Cursor judges (a backup model passes only a Short it finds nothing to fix in), and with fewer than 3, Gemma. When nothing else can answer (or Gemini refuses a prompt), Cursor's agent models do, through the Cursor SDK (`cursor_llm.py`, key in the `YTC_CURSOR_API_KEY` secret), in 2 to 5 minutes a prompt. Each Cursor prompt goes to a fresh agent with no tools, so it can only answer in text. Cursor takes the best model the key allows: Opus, Sonnet, GPT, Gemini, then Grok, newest first. Apart from prompts Gemini refuses, Cursor answers only while fewer than 9 are ready. `YTC_LLM_FIRST=cursor` puts Cursor first | Gemini, OVHcloud, Mistral, OpenRouter: free; Cursor: counts against the key's Cursor plan (optional) |
| Making each Short | A Modal worker (`studio_episode`, a quarter CPU, since it mostly waits on the language models) makes one Short end to end: research, script, images, render, review, fixes, and hosting. The run that starts it exits at once, and the next run collects the result. Runs start as many as the credit covers after a $2 reserve for the runs themselves. Only GitHub's backup makes Shorts on its runner, once Modal's credit is used up: three at a time (they mostly wait on the language model, so the waits overlap and renders take turns), within a share of the Actions minutes paced over the month | free: about $0.12 per Short; the shared $30 covers about 230 Shorts a month across both channels, and GitHub's runner makes them after that |
| Voice | Kokoro-82M, `af_heart` (Apache-2.0) | free |
| Visuals | Found from each beat's named subjects first (`sources.py`: the Wikipedia article's pictures, Wikidata's image, Commons category and "depicts" statements, then searches; for a living species, iNaturalist's curated and most-voted research-grade photos, CC0 and CC BY only), with Openverse, Wellcome Collection, The Met, and the Art Institute of Chicago for weak beats; public domain, CC0, and CC BY only. SigLIP (`google/siglip-base-patch16-224`, Apache-2.0) ranks them against each beat on Modal (`rank_pictures`), a Gemini model picks from the top six and marks the detail to show, and a second model checks the picks. A beat no picture fits gets a designed title card (a date, a number, or a quote the script cites; `plates.py`). No AI-generated pictures | free |
| Render | `pipeline/` (FFmpeg, libass captions, two-pass loudness) on Modal (8 CPUs) for Modal workers, on the runner for Shorts made there. Each shot is a plate: a tall picture fills the screen, others sit as a framed print over a blurred copy, long beats cut to a close-up, with an eased camera, a warm grade and grain, and the hook as on-screen text in the first seconds. Fonts: Anton, Montserrat, DM Serif Display (all OFL) | free |
| Watching | `monitor/monitor.py` (read-only): the studio's status and run history, Buffer, Cloudinary, Modal credit, YouTube's public feed. GitHub's `watchdog` workflow runs it every 3 hours and pushes each new alert to the owner's phone through ntfy (topic in the `YTC_NTFY_TOPIC` secret and `pipeline/.env`), plus a summary each morning; a run on Modal that fails or can't save pushes at once. On the Mac it runs every 15 minutes (launchd) with notifications and `monitor/out/dashboard.html`, reading Buffer at most every 2 hours (Buffer's API allows 250 requests a day) | free |
| Speech check | faster-whisper `small.en` (MIT) in the same Modal job; `ytc check` lists words it heard differently from the script | free, inside the render's cost |
| Publishing | Buffer free plan API, official YouTube partner; queue of up to 10. Buffer fetches each video from Cloudinary when the post goes out and never retries a post it fails, so `slot_watch` on Modal looks 5, 20, and 40 minutes after each slot hour (ET) and sends a post that just failed again under the same id, 5 minutes out, after checking its video downloads. A failure over an hour old goes back to waiting at the next studio run | free: about 15 of Buffer's 250 requests a day |
| Video hosting for Buffer | Cloudinary free plan | free |
| Analytics and playlists | YouTube Data and Analytics APIs through the owner's own Google Cloud app (project `shorts-studio-two`): `ytc stats` writes `analytics/<date>.json` with per-Short retention; `ytc playlists` adds each live Short to its series playlist | free |
| App home page and privacy policy | <https://ashivam-dot.github.io/creature-receipts-site/> on GitHub Pages (public repo `ashivam-dot/creature-receipts-site`, source in `site/`), required by Google for the app | free |
| GPU models (voice tests, later) | Modal, same account and credit | free within credit |

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-09-30 | Built the studio from Universe Receipts' code (a `git archive` of its main branch), with its content, status, analytics, and reports emptied | That studio already runs a channel unattended on free tiers; its decision log and `reference/days-of-odd/CHANNEL.md` explain the design |
| 2026-09-30 | Niche: true stories of strange animals, extreme biology, and deep-sea life, English, US audience | Six candidate niches were measured against the pipeline, not just ranked by demand (`research/channel/pipeline-fit-and-policy.md`): the median topic had 99 usable openly licensed pictures for animals, 89 for disasters, 50 for the deep ocean, 43 for archaeology, 10 for aviation, and 6 for frauds. The market report's first pick, failure analysis, was rejected: too few free pictures, and a feed of accidents is the "off-putting" content the July 2026 monetization update names. Animals are also evergreen, safe for advertisers, and don't overlap Universe Receipts. Animal-fact Shorts convert viewers to subscribers poorly (`research/channel/niche-market.md`, section 3), so every Short is a sourced story in a named series |
| 2026-09-30 | Name: Creature Receipts (@CreatureReceipts) | A sister brand to Universe Receipts: "receipts" means every claim is backed by sources listed in the description, which is also the defense against the inauthentic-content review. The handle returned 404 on YouTube before it was claimed |
| 2026-09-30 | Six series: Built Different, Deep Sea Files, Back From Extinction, Evolution Got Weird, Nature's Record Breakers, Animal Myths, Busted | They cover the animal hooks that travel (impossible bodies, the deep sea, rediscoveries, strange evolution, records with numbers, myth-busting); promises in `strategy/STRATEGY.md` |
| 2026-09-30 | Day 0 is 2026-10-01 (Day 100 is 2027-01-09); first hashtag `#animals`; the calendar seeded with 14 anniversaries (Oct 3 to Nov 28) and about 100 backlog topics, each starting with an English Wikipedia title checked against Wikipedia's API | Three days to set up and fill the inventory before the first post, and still about 70 days to reach YPP's 10M-view bar before a mid-December application, ahead of the 20M bar from 2027-02-01 |
| 2026-09-30 | Pictures: iNaturalist added as a source for any subject Wikidata marks as a taxon (curated photos, then most-voted research-grade observations, CC0 and CC BY only); a picture may be reused at most once per Short. Built here and ported to Universe Receipts | Universe Receipts' reviews rejected Shorts for repeating one photo when a subject had few pictures; living species are this channel's subjects, and one mantis-shrimp beat got 32 usable iNaturalist photos in testing |
| 2026-09-30 | Pace earned per Short, evening slots, five rotating script structures with a sameness check, and the hook on screen from frame 0 (details in Universe Receipts' decision log of the same date; the code is shared) | YouTube's July 2026 inauthentic-content update names templated, mass-produced uploads; YPP counts engaged views, which exclude loops; Shorts views peak 6 to 11 p.m. ET (`research/channel/growth-playbook-2026.md`) |
| 2026-09-30 | The agent created every account in the owner's Chrome Profile 5 (the channel and handle, the Google Cloud project and OAuth app, the Gemini key, Cloudinary, and Buffer by email sign-up, with its password generated inside the page and never seen or stored), connected Buffer to the channel, and signed the studio in as the channel. Keys went straight from each page into `pipeline/.env` through `kit/setkey.py` | The owner asked for the whole setup to be done for him, and never with his work account |
| 2026-09-30 | Modal: this studio uses Universe Receipts' Modal workspace and token instead of its own account, with `YTC_MODAL_CREDIT=30` | Modal's credit is per workspace, and that workspace already has a card with a $0 spend limit and a $30 usage cap, so both channels together can never be charged. The studios read the workspace's total spend, so they share the $30 (about 230 Shorts a month) rather than each assuming its own |
| 2026-09-30 | The OAuth app's home page and privacy policy are on GitHub Pages (<https://ashivam-dot.github.io/creature-receipts-site/>, public repo `ashivam-dot/creature-receipts-site`), with relative links so they work under the project path | Google requires them to publish the app to production, which keeps the YouTube sign-in from expiring after 7 days |
| 2026-09-30 | Channel description, keywords, country India, language English, banner, and not-made-for-kids set through the YouTube Data API; the picture and watermark uploaded in Studio | One-time channel setup; the API can't set the picture. The art is from NOAA public-domain photos and a CC BY 2.0 mantis shrimp photo (`brand/CREDITS.md`) |
| 2026-09-30 | Gemini key moved to a new AI Studio project, `creature-receipts`, on akshshivam5@gmail.com (the owner's other personal account), and `llm.py` now treats a refused key (401/403) like spent quota, so the ladder goes on to the other providers | The first 3 Shorts failed: every Gemini model answered 403 "Your project has been denied access", and AI Studio marked the aksha.shivam18 project "Restricted: set up billing to continue", even for new projects. Billing would make the key paid, so the owner decides that. Free quota is per project, so the new project doesn't share Universe Receipts' daily allowance |
| 2026-09-30 | The repository is public (secret scanning and push protection on), after a scan of every blob in its history found no key, token, sign-in file, deploy key, ntfy topic, or phone number | The owner asked for each rate-limited service to be separate per channel. Public repositories get unlimited free Actions minutes, so the watchdog and the `studio` backup, which renders on GitHub's runner when Modal's credit is spent, no longer share `ashivam-dot`'s 2,000 private-repo minutes with Universe Receipts. No workflow runs on pull requests, so forks never see the secrets |
| 2026-09-30 | Modal: an account for aksha.shivam18@gmail.com was requested (Modal put the Google sign-up under manual review; the form was filled with the channel's details and no work email). Until it's approved the studio stays on Universe Receipts' workspace | Its own workspace gives this channel its own  a month (with a card and a -- spend limit) instead of sharing one  |
| 2026-09-30 | Writer: a draft that breaks the script rules is rewritten up to 3 times (was 2), each time from the draft with the fewest problems, and the word-count and hook problems say exactly how many words to add or cut, beat by beat. Ported to Universe Receipts | The first two Shorts that got through research were lost at 103 of the 105 minimum words and a 13-word hook; "Use 105 to 135 words (you have 103)" didn't get a backup model to add 2 words in two tries |
| 2026-09-30 | Day 0 moved from 2026-10-03 to 2026-10-01 | The owner wanted Shorts from today or tomorrow. Publishing never waited for Day 0 (a Short goes to the next free evening slot once it passes); moving it keeps the plan's day numbers and pace in step with the first posts |
| 2026-09-30 | Pictures: an animal a line only compares the subject to is not its subject | ep005 (platypus) was rejected after every round showed a mallard for "a duck's beak onto a beaver-like body": the picker took the comparison literally and its alternates were more mallards. The pick and check prompts now say so, and a redo skips alternates of the species the reviewer rejected. Platypus and giant squid (ep004, failed on the old writer) are back in the queue |
| 2026-09-30 | Research reads any source-label format, and asks again when every claim loses its citations | Narwhal (ep010) and hippo (ep014) were dropped with "0 claims have two different sites" though 5 to 7 sources were read: the answer's citations didn't match the plain labels, so every claim was discarded. Labels are now read from "[S1]" or "S2 (site)" too, and an answer citing nothing usable leaves the Short unfinished for the next run instead of dropping the topic. Both are back in the queue, and so is the Winnipeg bear (ep007, 3 bad frames) for its Oct 3 date |
| 2026-09-30 | Format: real footage for living-animal beats, archival pictures for receipts, depth motion on every still | Every beat had been a still photo with a camera move, which reads as a slideshow next to the big animal channels. Footage-only was rejected: the rarest subjects (platypus, coelacanth, colossal squid, Cher Ami, the 1914 bear) have little or no good footage, stock titles are loose enough to show the wrong species, and archival pictures are what sets the channel apart. The picker now also searches Pexels and Pixabay for each beat's subject (HD or better, 6–90 s), prefers exact-species footage for living-animal beats and the hook, and judges clips by their frame; the 2.5D depth motion that was built but off is on for every still. Wikimedia Commons video was tested and not used: mostly 240–720p and share-alike. See `strategy/PLAN-100.md`, "What every Short looks like" |
| 2026-09-30 | Footage from Pixabay (key on aksha.shivam18); Pexels waits | Pexels "paused new API key issuance", so its code stays ready for when it reopens. Pixabay's search matches any one word ("Great white shark" returned the Great Wall, "Giant squid" squid in a wok, "Sperm whale" a whale shark), so a clip is kept only when every word of the animal's name is in its tags and none of food, fishing, dead, toy, cartoon, or festival is. In a test of 11 of our animals, axolotl, octopus, hippo, and jellyfish had footage; platypus, narwhal, tardigrade, coelacanth, sperm whale, giant squid, and great white shark keep archival pictures with depth motion |
| 2026-09-30 | Deploy from the Mac only with `python3 pipeline/deploy.py` | `cloud.studio_secret` is built from the deploying environment, and a bare `modal deploy` reads no `pipeline/.env`: it publishes workers without their keys until the next studio run redeploys with its own secret. `deploy.py` loads `.env` first. The footage keys were also missing from `modal_secret.py`'s list |
| 2026-09-30 | Modal account under review | Its signup check flagged the new account; the review form was sent, and a fuller note with the public repo went to support@modal.com from aksha.shivam18. Approved the same evening; adding a card then failed ("Your card was declined") on two Indian cards, and support was asked for the decline reason. Channel 2 keeps using the shared Modal account until a card is on file |
| 2026-09-30 | Phone verification deferred | It needs the SMS code on the owner's phone. Shorts don't need it; the Partner Program application does. Tracked in `OWNER-CHECKLIST.md` |

## Layout

- `strategy/`: strategy, 100-day plan, calendar, script rules
- `brand/`: avatar, banner, watermark (`brand/out/`), channel copy, image credits
- `content/episodes/<id>/`: spec, research, render, publish record, one folder per Short
- `content/rejected/<id>/`: episodes that failed the quality gate twice, kept for learning
- `pipeline/`: the `ytc` production and publishing code (`ytc auto` is the cloud studio's run)
- `pipeline/src/ytc/cloud.py`: the Modal app (`studio_run`, `studio_episode`, `render_episode`, `slot_watch`); `pipeline/modal_secret.py` makes its deploy key, ntfy topic, and secret
- `.github/workflows/`: `studio.yml` (the backup for Modal's runs, gated by `.github/backup_gate.py`), `watchdog.yml` (alerts to the owner's phone), and `selftest.yml` (renders an existing Short on a runner)
- `status/`: the last run's `status.json`, every run in `history.jsonl`, and `state.json` (daily routine, quota hold)
- `monitor/`: the read-only monitor (the watchdog's, and the Mac's with its launchd job)
- `analytics/`: daily snapshots from the YouTube Analytics API
- `reports/`: daily reports `day-NNN.md`, weekly reviews, `BLOCKERS.md`
- `kit/`: the setup guide's helpers and notes (`configure.py`, `setkey.py`, `push_secrets.py`, `verify.py`)
- `reference/days-of-odd/`: the documents of the channel this studio was built for
- `research/`: research notes and tool sweeps
- `site/`: the analytics app's public home page and privacy policy; to change them, push the files to
  `ashivam-dot/creature-receipts-site` (GitHub Pages serves its `main` branch)
- `secrets/` and `pipeline/.env`: credentials (git-ignored)
