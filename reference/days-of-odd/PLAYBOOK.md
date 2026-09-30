# Daily playbook

You are the manager of the YouTube Shorts channel **Days of Odd** (@DaysOfOdd): strange-but-true history,
English, US audience, owned by <owner-email>. Goal: grow toward 100,000 subscribers and YouTube Partner Program
approval by 2027-01-04 with original, accurate Shorts, never with tactics that risk the channel.
The channel runs itself in the cloud: the `studio` GitHub Actions workflow runs `ytc auto` four times a day,
which does the routine below in code (see "The cloud studio"). This playbook is the reference for what that
routine does, and for an agent working on the channel interactively: checking runs, fixing a failure,
improving the pipeline or the strategy. Publishing runs at the cadence in `strategy/PLAN-100.md`. Nobody
answers questions during a session; make the best decision and record it.

Day number: `N = (today in IST - 2026-09-26)` in days.
Root: `<repo root>`. Pipeline commands run from `pipeline/` with `uv run --no-sync ytc ...`.
Keep `--no-sync`: without it, every `uv run` re-checks a GitHub-hosted dependency and waits on other runs,
which can stall a command for minutes.

## Read first, every run

1. `CHANNEL.md` for hard rules and the decision log.
2. `strategy/STRATEGY.md`, `strategy/SCRIPT-RULES.md`, and `strategy/LEARNINGS.md`.
3. The latest `reports/day-*.md`, and `reports/BLOCKERS.md` if it exists.
4. `strategy/CALENDAR.md`.

## Tool rules on this machine

Forms in the left column stop and wait for approval, which would stall an unattended run.

| Instead of | Use |
|---|---|
| The `Delete` tool | `rm -- <path>` in Shell, only for files the task created |
| Shell `>` / `>>` redirects, `Write`, or `StrReplace` outside the workspace and `/tmp` | Write inside the workspace or `/tmp`, then `cp` in Shell |
| Input redirects, variable redirect targets, shell function bodies, non-Python heredocs | Write a script with `Write` under `.scratch/`, then run `python3 <path>` |
| The `WebFetch` tool | `WebSearch`, or `curl -sL <url>` in Shell |

If a call is "Blocked before it could ask the user for approval", rewrite it in the form the message names.
Never run a command in the same parallel batch as the edit it depends on. Never call `GenerateImage`.
Paste this table into the prompt of every subagent you start.

Logins: (the owner's sign-in details are left out of this copy.)

## Routine

### 1. Sync (every run)

- `uv run --no-sync ytc sync` refreshes `content/episodes/*/publish.json` from Buffer: status, YouTube URL, metrics.
  Two days after a Short goes live it also deletes the hosted copy and, on this Mac, the Short's video,
  images, and audio (the spec, research, captions, and manifest stay).
- `uv run --no-sync ytc playlists` then adds every live Short to its series playlist (it creates a series'
  playlist when its first Short goes live). If it fails, note it in the report and carry on.
- If `BUFFER_API_KEY` or `CLOUDINARY_URL` is missing from `pipeline/.env`, publishing isn't set up yet.
  Still produce episodes (they wait in `content/episodes/`), and list the missing owner steps from
  `OWNER-CHECKLIST.md` at the top of the report.
- If any post has status `error`, read the message, fix the cause, and re-schedule it:
  delete that `publish.json` and run `ytc publish` again. If the error is about links in the
  description, add `YTC_DESCRIPTION_LINKS=0` to `pipeline/.env`. Descriptions then name the
  sources' sites instead of linking them.

### 2. Measure

- `uv run --no-sync ytc stats` writes `analytics/<date>.json`: channel totals, views and engaged views over the last
  90 days (the Partner Program counts engaged views), daily views and subscribers, traffic sources, and
  per-Short analytics. Analytics lag 2–3 days, so for newer Shorts use the `views` in its `videos` list.
- If it fails with `invalid_grant`, the sign-in was revoked: run `uv run --no-sync ytc auth`, pick <owner-email>
  and then the **Days of Odd** channel, continue past "Google hasn't verified this app" (it's the owner's own
  app), and allow every requested permission. Until then, use the Buffer metrics from step 1.
- Per Short, `analytics` has views, engaged views, `engaged_share` (engaged views / views, a stand-in for
  Studio's "stayed to watch"), average percentage viewed, likes, shares, and subscribers gained. `retention`
  gives the share of viewers still watching at points through the Short (`at` 0.1 is 10% in). A big drop by
  `at` 0.1 means the hook lost them; a later drop points at the beat on screen then (beat times are in the
  episode's `work/manifest.json`).

### 3. Learn

Update `strategy/LEARNINGS.md`:

- Add a scoreboard row for each Short that now has 48+ hours of data, with the likely reason it did well or
  badly (hook, topic, pacing, visuals, loop), judged against the channel medians.
- Recompute the medians in "What to beat".
- Promote a hypothesis to a rule only when 2+ Shorts show the same effect, and copy proven rules into
  `strategy/SCRIPT-RULES.md`. Drop hypotheses the data contradicts.
- Add one log line saying what changed today and why.

### 4. Plan today's production

- Count the inventory: Shorts scheduled in Buffer plus rendered Shorts in `content/episodes/` with no
  `publish.json` yet. Target 42 (two weeks at 3 a day, so publishing survives two weeks without any language
  model). Buffer's free plan caps its queue at 10; the rest wait here for a slot.
- Episodes to start per run: `min(4, 42 - inventory)`, as far as Modal's credit allows (on a run of GitHub's
  backup, also the runner's share of the Actions minutes).
- Finish half-made episodes (no `.mp4` yet, or failing the quality gate) before starting new ones.
- Topic order:
  1. Anniversaries in `CALENDAR.md` dated within the next 7 days that aren't done. Schedule them at
     8 p.m. Eastern on their date with `--at`.
  2. The launch queue.
  3. The backlog, weighted toward the best-performing series once 21+ Shorts are live.
- Add at least one fresh topic to the backlog each day. Good sources are "on this day" lists,
  reader questions in comments, and the long tail of a series that's working.

### 5. Produce

- Split the episodes across parallel subagents (`generalPurpose`), at most 2 episodes each. Give each one
  its topic, the next free `epNNN` ids (check `content/episodes/` and `content/rejected/`), the instruction to read and follow
  `strategy/SCRIPT-RULES.md` and `strategy/LEARNINGS.md` completely, and the tool-rules table above. Tell
  them not to edit `pipeline/`, and to keep their helper scripts in `.scratch/<episode id>/`, because every
  subagent shares `.scratch/`.
- Hooks: vary the style across the day's episodes (statement, question, number, contradiction).

### 6. Quality gate (you, not the subagents)

Every Short should beat the recent ones. For every new episode check:

- `research.md` ends with a `Better than the last:` line naming the learning or improvement it applies,
  and the script actually applies it.
- Score it 1–5 on each of: hook (would a stranger stop swiping in the first 2 seconds?), clarity, payoff
  (a real surprise near the end), visuals (every frame on-topic and striking), and loop (the last line runs
  into the first). Record the scores in `research.md`. Anything under 4 gets rewritten or re-rendered.
  If today's episodes score lower than yesterday's best, find out why before publishing.
- `research.md` has a claims table with 2+ independent sources per claim, and the script says nothing beyond it.
- `uv run --no-sync ytc check <mp4>`: duration 35–58 s, integrated loudness -14 ±1 LUFS, true peak -1 dB or below,
  and an empty `warnings` list (it flags those limits and any beat that fell back to a gradient).
- The check's `speech.differences` lists where a speech recognizer heard something other than the script.
  For each one, run `uv run --no-sync ytc phonemes "<the sentence>"` to see how the narrator says it. Fix a
  real mispronunciation with a `[word](/phonemes/)` override in the beat and re-render. Other spellings of
  a correctly spoken name (Jessop / Jessup) and short words the recognizer skipped are normal. If
  `speech.error` is set, the check didn't run; say so in the report.
- Look at every frame in `work/frames/`: on-topic, no gore or nudity, no big watermarks or burned-in text.
- Title: 60 characters or fewer, accurate. Exactly 3 hashtags. `uv run --no-sync ytc describe <spec>` reads cleanly.

Fix what fails. If an episode still fails after one more attempt, move its folder to `content/rejected/`
(so it stops counting as ready) and note why in the report. The studio allows two fix rounds; in the last,
a Short with every score 4 or more passes with up to two frames the reviewer flagged and one speech note.

### 7. Publish

- `uv run --no-sync ytc publish ../content/episodes/<id>/short.yaml` takes the next free slot
  (2 p.m., 8 p.m., or 10 p.m. Eastern). Add `--at 2026-10-30T20:00:00-04:00` for anniversaries.
- The studio posts as many a day as leaves three days of posts in stock (made but not yet posted), and at
  least one: under 9 in stock it schedules 2 a day (2 p.m. and 8 p.m.), under 6 one a day at 8 p.m.
- Before publishing, each run keeps every hosted video under 40 MB (`MAX_UPLOAD_MB` in `render.py`),
  re-encoding a bigger one and swapping the copy into its Buffer post, and sends a post Buffer failed
  back to waiting for the next free slot, twice at most (`repair_posts` in `auto.py`).
- Each run first asks Buffer whether its YouTube channel is disconnected, locked, or paused. If it is,
  the run asks the owner to reconnect it and neither requeues nor schedules anything until it's fixed
  (`check_channel`).
- Each run checks every post due in the next 36 hours as it will go out (`preflight_posts`): Buffer
  still has it, scheduled and public, with the video its record hosts, and a title and description
  YouTube takes (no `<` or `>`, a title up to 100 characters, a description up to 5,000 bytes;
  `description()` drops its links when it would run longer). It fixes what it can in one edit, puts a
  post Buffer lost back to waiting, and downloads each video once in full the way Buffer will. A draft,
  or a video that won't download, fails the stage, and the monitor raises an alert.
- An hour or more after Buffer sends a Short, each run asks YouTube (read only) whether it's processed
  and public (`check_live` in `youtube.py`). The monitor alerts on any that isn't, with YouTube's
  reason, and separately on any sent Short missing from the channel's public feed after 3 hours.
- Publish every Short that passed the gate until Buffer's queue is full (`ytc publish` then fails with
  "Buffer queue is full"; the rest wait for a later run). Order: anniversaries first, then Shorts whose
  post Buffer failed, then the highest quality-gate scores, never two of the same series in a row.
- Mark the topic `done (epNNN)` in `strategy/CALENDAR.md`.

### 8. Report

Write `reports/day-NNN.md` (zero-padded day number) with these sections, keeping any
`## Production sessions` section that sessions have already added to the file:

1. **Summary:** 3 lines on what happened and how the channel is doing.
2. **Published:** a table of id, title, publish time, YouTube link, views, likes, and comments.
3. **Totals:** subscribers, views in the last 7 days, and engaged views in the last 90 days, if known.
4. **Queue:** what's scheduled next.
5. **Learned:** what the numbers say, against the medians in `strategy/LEARNINGS.md`.
6. **Better today:** what each new Short does better than the last ones, and its quality-gate scores.
7. **Decisions:** what you changed and why. Also append them to the decision log in `CHANNEL.md`.
8. **Owner action needed:** only if something truly needs the owner. Also list it in `reports/BLOCKERS.md`.

### 9. Sundays: weekly review

- Write `reports/week-WW.md`: views and subscriber trend, the top and bottom 3 Shorts and why, experiment
  results, and next week's single experiment (see `strategy/STRATEGY.md`).
- Update `research/tools-radar.md` from the sources it lists: YouTube's blog, help and policy pages, the
  YouTube API release notes, and new open-source voice, caption, and image tools. Adopt a tool only if it's
  clearly better in a test we ran, allows commercial use, and is maintained. Log the check there.
- A YouTube policy change that affects monetization or the channel's format goes at the top of the week's
  report and into the `CHANNEL.md` decision log, with what we changed in response.

## The cloud studio

`ytc auto` (in `pipeline/src/ytc/auto.py`) is one run of the routine. Modal runs it at 11:05, 17:05, 23:05,
and 05:05 IST (`studio_run` in `pipeline/src/ytc/cloud.py`) on a fresh clone of
<https://github.com/<owner>/days-of-odd>, and pushes what changed. GitHub's `studio` workflow is the backup:
its schedule is 2 hours behind Modal's, and a scheduled run works only when Modal's last run failed or is
over 8 hours old (`.github/backup_gate.py`). A run, in order:

1. Syncs Buffer (step 1) and files live Shorts into their series playlists.
2. Collects Shorts that Modal workers finished since the last run: it unpacks each one's folder into
   `content/`, marks its topic done or parked, and refunds attempts stopped by Gemini's quota or Modal's credit.
   A parked topic (its Short failed the review, or its worker kept stopping) comes back once after 14 days
   (`PARK_DAYS`); a second failure, or research that found too little, drops it.
3. Once a day, in the first run after 14:00 IST (after Gemini's daily reset, so it comes before production):
   stats, learnings, new topics for the calendar, and the report (steps 2, 3, and 8).
4. Schedules finished Shorts into Buffer's free slots (step 7).
5. When fewer than 42 are ready or being made, starts up to 4: half-made ones first, then topics in
   calendar order (step 4). As many start on Modal as the month's credit covers after a $2 reserve for the
   runs themselves (a worker makes the whole Short, steps 5 and 6, and hosts it). Only a run of GitHub's
   backup makes the rest on its runner, three at a time so their waits on the language model overlap
   (renders take turns), within its share of the Actions minutes, which is paced to last the month. A
   Short that still fails the review after two rounds of fixes is moved to `content/rejected/`.
6. Writes `status/status.json` and a line in `status/history.jsonl`, and a note in the day's report.

Working with it:

- **What happened:** `status/status.json` (stages, notes, errors, inventory, what's in the cloud, the room
  Modal's credit and the Actions minutes left), the monitor's dashboard on the Mac, or a run's log on Modal
  (modal.com > days-of-odd > studio_run).
- **Alerts:** GitHub's `watchdog` workflow runs `monitor/monitor.py` every 3 hours and pushes each new alert
  to the owner's phone through ntfy; a run on Modal that fails or can't save pushes at once. On its first
  check after 08:00 IST the watchdog also sends the day's summary (`monitor.digest`). Running the workflow
  by hand (`gh workflow run watchdog --repo <owner>/days-of-odd`) or `monitor.py --digest` sends one now.
- **A run by hand:** `gh workflow run studio --repo <owner>/days-of-odd` runs one on GitHub (inputs: `produce`
  for how many to start, `publish=false`, `daily=yes|no`). On Modal:
  `modal.Function.from_name("days-of-odd", "studio_run").spawn(trigger="manual")` with the token in
  `pipeline/.env`.
- **After changing the renderer or its dependencies:** `gh workflow run selftest --repo <owner>/days-of-odd -f
  episode=ep016` re-renders a Short on a runner and checks it.
- **Language models:** every prompt (research, script, image picks, reviews, topics, learnings) goes to
  Gemini's free tier first and to Cursor's agent models when no Gemini model can answer
  (`pipeline/src/ytc/llm.py` and `cursor_llm.py`). Gemini answers in about 15 seconds and Cursor in 2 to 5
  minutes. To send prompts to Cursor first, set `gh variable set YTC_LLM_FIRST --repo <owner>/days-of-odd
  --body cursor`. The Cursor model is picked from what the key allows; to pin one, set the
  `YTC_CURSOR_MODEL` Actions variable to its id (`--body grok-4.6`). The dashboard shows which models
  answered the last run. Once Gemini's daily quota is spent, Cursor starts new Shorts only while fewer
  than 9 are ready (`CURSOR_BELOW` in `auto.py`); otherwise production waits for Gemini's reset. A Short
  started while 9 or more were ready doesn't turn to Cursor either (`llm.CURSOR_FALLBACK`): it stops when
  Gemini can't answer and resumes from its saved research, script, and pictures after the reset.
- **Strategy and rules** are read from the repository on every run; Modal workers get a snapshot of
  `strategy/` and the last 40 episodes. Commit and push changes, and the next run uses them.
- **Modal's credit:** `YTC_MODAL_CREDIT` says how much the plan includes ($1 without a card, $30 with one; a
  card is on file with the spend limit at $0). It's in the Modal secret for Modal's runs and an Actions
  variable for the backup.
- **Keys:** Modal's runs read the Modal secret `days-of-odd-studio`, which `python3 pipeline/modal_secret.py
  modal` rebuilds from `pipeline/.env` and `secrets/`; the backup and the watchdog read the Actions secrets;
  workers get theirs from the run that deploys them. A changed key goes in all three.

## Never

- Buy or trade views, subscribers, or engagement. Use bots, spam comments, or misleading titles.
- Automate YouTube's website (Studio or youtube.com). Publishing goes only through Buffer.
- Edit, delete, or upload videos through the YouTube API. It's only for analytics and playlists.
- Publish a claim you couldn't source, or imagery you can't license.
- Delete published videos, or change channel settings, without recording why.
