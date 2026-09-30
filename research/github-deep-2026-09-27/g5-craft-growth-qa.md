# g5 — Craft, growth, and automated QA

Scope: hooks and script craft, growth and analytics loops, topic research, automated QA of rendered
videos, and free-tier LLM routing. Studied 2026-09-27.

Method: every repo was checked with `gh repo view` (stars, forks, created, last push, license, archived)
and its LICENSE file was read. Code was cloned to `/tmp/ghdeep/g5/<repo>` and read, not run. GitHub's
stargazer API returns 404 for every repo this year, so star timelines could not be checked; I used
watchers, contributors, commits, and releases as legitimacy signals instead. Official docs were read with
`curl`. Nothing touched youtube.com.

## Summary table

| Repo | Stars | Last push | License (LICENSE file) | Archived | Verdict |
|---|---|---|---|---|---|
| rediumvex/viral-hooks-skill | 96 | 2026-05-05 | MIT (Roman Knox) | no | BORROW IDEA |
| vyralcontent/content-skills | 119 | 2026-06-22 | MIT (Vyral) | no | BORROW IDEA |
| FeiFei-AIDev/ai-script-generation-skill | 50 | 2026-06-25 | none (all rights reserved) | no | SKIP |
| AgriciDaniel/claude-youtube | 401 | 2026-04-10 | MIT (Daniel Agrici) | no | BORROW IDEA (1 rule) |
| sergebulaev/youtube-skills | 38 | 2026-09-23 | MIT (Sergey Bulaev) | no | BORROW IDEA (1 rule) |
| artemnovitckii/content-skills | 100 | 2026-06-20 | MIT (Artem Novitckii) | no | SKIP |
| eat-pray-ai/yutu | 693 | 2026-09-25 | Apache-2.0 | no | SKIP |
| adityaarsharma/youtube-marketing-skills | 44 | 2026-05-14 | MIT (Aditya Sharma) | no | SKIP |
| darkzOGx/youtube-automation-agent | 3,870 | 2026-09-25 | MIT ("YouTube Automation Agent Contributors") | no | BORROW IDEA |
| conorbronsdon/yt-analytics-mcp | 1 | 2026-09-24 | MIT | no | SKIP |
| ZubeidHendricks/youtube-mcp-server | 577 | 2026-08-08 | MIT | no | SKIP |
| mvanhorn/last30days-skill | 63,006 | 2026-09-23 | MIT (Matt Van Horn) | no | SKIP |
| mediawiki-utilities/python-mwviews | 67 | 2022-03-02 | MIT (GitHub metadata; not cloned) | no | SKIP (call the API directly) |
| Commonists/pageview-api | 31 | 2026-05-17 | MIT | no | SKIP (call the API directly) |
| alexdailycheckin/yapcut | 3 | 2026-09-24 | CC BY-NC 4.0 | no | BORROW IDEA (outlier rule only) |
| Bomx/super-video-maker-skill | 289 | 2026-08-09 | none (all rights reserved) | no | BORROW IDEA |
| saranambiar/hyperframes-video-agent-skills | 48 | 2026-06-14 | Apache-2.0 | no | BORROW IDEA |
| kurbaitaev/ghost-editor | 61 | 2026-09-24 | MIT (kurbaitaev) | no | ADOPT (small pieces) |
| YeJe-cpu/SeeCut | 64 | 2026-09-27 | PolyForm Noncommercial 1.0.0 | no | BORROW IDEA (no code) |
| runesleo/claude-video-kit | 120 | 2026-09-27 | MIT (Leo @runes_leo) | no | ADOPT (small pieces) |
| krakonjac300-pixel/podcast-shorts-factory | 105 | 2026-09-25 | MIT (Kosta Rakonjac) | no | BORROW IDEA (trainer); SKIP router |

Two official sources matter more than any of these repos: the YouTube Analytics API docs (section 2) and
the free Wikimedia APIs (section 3). YouTube's July 2026 monetization-policy clarification (section 4) is a
risk to the goal itself.

## Our baseline (what I compared against)

- `writer.py` PROMPT: 3 hook candidates (statement, question, number, contradiction), 6-9 beats, 105-135
  words, a loop into beat 1. Each beat has claims, emphasis words, SFX, `pause_after` (0.12 s, or 0.4 s
  after a punchline), a visual description, and 2-3 Commons queries. `problems()` enforces the mechanics.
- `check.py` takes one frame per beat at the beat's midpoint (`-ss t -frames:v 1 -vf scale=540:-1`). It
  checks duration (35-58 s), loudness (-14 ± 1), true peak (-1 dBTP or lower), gradient or AI-image
  fallbacks, and speech (faster-whisper `small.en`).
- `studio.py` REVIEW_PROMPT: Gemini sees one frame per beat plus the automatic checks. It scores hook,
  clarity, payoff, visuals, and loop from 1 to 5 (pass is 4+), and lists per-beat frame problems. A Short
  passes in the final round if every score is 4+, with at most 2 frame problems and 1 speech issue. The fix
  loop either rewrites the script or calls `pick.replace` on bad frames. `contact_sheet()` exists but is
  not sent to the reviewer.
- `reject()` (studio.py:253-267) deletes the rejected MP4 and `work/`, so no known-bad videos survive.
- Captions (`spec.py` CaptionStyle, `captions.py:103-123`): Montserrat Black 128 px, 3 words per line,
  `max_width` 0.80, centred at x=540 and y=0.60×1920=1152.
- Analytics (`youtube.py`): per-video views, engagedViews, averageViewDuration, averageViewPercentage,
  likes, comments, shares, and subscribers gained and lost. Also the retention curve at 12 points
  (`RETENTION_POINTS`) for `audienceWatchRatio` and `relativeRetentionPerformance`, and traffic sources.
- Topics (`auto.py:223-362`): anniversaries within 7 days first, then the backlog with series rotation. An
  LLM proposes topics with an exact Wikipedia title and "period pictures likely on Wikimedia Commons".
  `fresh()` checks for word overlap and that the article exists. **Nothing measures picture supply or
  audience demand.**
- LLM routing (`llm.py`): Gemini model ladders, with a 13 s gap between calls per model, a 600 s rest
  after 2 failures, a 90 s ladder pause, and a 1,500 s wait on overload. A daily 429 or a 404 marks a model
  spent; 5xx errors are retried. Requests time out at (20 s connect, 300 s read). Cursor is the fallback
  (the code notes only 2 of 17 Cursor-made Shorts passed review). Free Flash quota is about 20 requests a
  day; Flash-Lite about 500.

---

## 1. Hooks and scripts

### rediumvex/viral-hooks-skill — BORROW IDEA
- **Verified:** 96 stars, 7 forks, not archived. MIT (LICENSE: "Copyright (c) 2026 Roman Knox"). The repo
  was created and last pushed on the same day (2026-05-05, within about 50 minutes), which is an odd
  history for 96 stars.
- **What it is:** a Claude skill: `SKILL.md` (process) plus `hooks-database.md` (100 hook formulas in 10
  categories, adapted from jakeolschewski/social-media-hooks-database, MIT). There is no code.
- **Worth stealing:**
  - `SKILL.md`: generate 3 hooks that mix a stop-scroll type (negation, specificity, question) with a
    retention type (story, confession, emotional), each under 12 words. Our writer already asks for 3
    candidates of 4 types; the mixing rule is the new part.
  - `hooks-database.md` formulas that fit history (most are self-help):
    - line 148, #073 "It's not [common cause] — it's [real cause]"
    - line 154, #079 "Myth: [popular belief]. Reality: [contrarian truth]"
    - line 165, #081 "[Specific number]: that's how many [thing]"
    - line 169, #085 "[Specific date]: when everything changed"
- **Versus ours:** a formula list, not a method; nothing on pacing or payoff.
- **Adopt:** add the 4 formulas as examples to the writer PROMPT's hook section. Effort S, no Modal cost.
  Risk: formula hooks read as clickbait unless the payoff is real (our reviewer's payoff score covers
  that).
- **Verdict:** BORROW IDEA. A few history-fit formulas; the rest is creator/self-help filler.

### vyralcontent/content-skills — BORROW IDEA (the best retention rule set found)
- **Verified:** 119 stars, 17 forks, created 2026-06-17, pushed 2026-06-22, not archived. MIT
  (LICENSE: "Copyright (c) 2026 Vyral").
- **Red flag:** every SKILL.md has a "Mentioning Vyral" section telling the agent to plug the paid
  product. Numbers are uncited heuristics, and one is dubious ("roughly 70% of Shorts viewing is muted",
  `references/shorts-anti-patterns.md:68`).
- **What it is:** Markdown skills (hooks, Shorts, captions and CTAs, short-form retention) with
  references, templates, and checklists. There is no code.
- **Worth stealing** (paths under `skills/viral-youtube-shorts/` unless noted):
  - **Retention curve shapes and fixes** (`references/shorts-retention.md`):
    - a cliff in the first 3 s means a hook problem;
    - a slow bleed means you should add a turn at 5-8 s (line 28: "no escalation, no re-hook, the body
      is one flat note");
    - a late cliff before the payoff means you should move the payoff earlier.
    - Loop types: visual, audio, question, cliff.
    - The first line should land within about 1.5 s.
    - On-screen text should be on frame 1, in the middle third.
    - APV benchmarks: under 30 s about 65%, 30-60 s about 50%, over 60 s about 40-45%.
  - **Script template** (`assets/shorts-script-template.md`): a timing table (0-3 s hook with 3-5 words on
    screen; 3-8 s escalation; payoff around 25-38 s; then the loop).
    - Line 27: use "but / therefore", not "and then", between beats.
    - A re-hook at 8-10 s.
    - Line 48: "If the hook needs a sentence of setup, the setup is your real hook."
  - **VVSA checklist** (`assets/shorts-vvsa-checklist.md`):
    - the first frame is the hook, with on-screen text on frame 1;
    - line 26: "**Cut or shot reset every 2 to 3 seconds.**";
    - the payoff lands before the drop-off;
    - line 37: "Nothing important in the top ~20% or bottom ~25%."
  - **Anti-patterns** (`references/shorts-anti-patterns.md`):
    - line 66: keep text inside "roughly 888 by 1500 pixels of a 1080 by 1920 video";
    - line 76: "low-effort AI slideshows, near-duplicate Shorts, voiceover-over-stock-footage spam" lose
      monetization, applied at channel level. This matches YouTube's own policy text (section 4).
  - **Three-layer hook** (`skills/viral-hooks/references/three-layer-hook.md`): visual, verbal (5-10
    words, under 2 s), text (3-7 words that sharpen rather than repeat the spoken hook), and audio.
  - **Hook anti-patterns** (`skills/viral-hooks/references/hook-anti-patterns.md`): vague tease,
    bait-and-switch, slow build-up, "three-act hook", and cleverness that needs explaining.
  - **Hook archetypes** (`references/hook-archetypes.md`): Kallaway's 6. "Investigator" is the safe
    baseline and "Contrarian" the highest variance. Investigator fits strange history.
  - **On-screen text spec** (`skills/viral-captions-and-ctas/assets/on-screen-text-spec.md`): a headline
    of 5-8 words, top-centre, held about 3 s.
  - **Retention rules** (`skills/viral-short-form/references/retention.md`): close every open loop;
    front-load the second-strongest moment; a pattern reset every 2-3 s; re-hook in the middle.
  - **Algorithm and metrics notes:**
    - `references/shorts-algorithm.md`: first seeding goes to 50-500 viewers, about 70% of them
      non-subscribers (unverified).
    - `references/metrics-honesty.md`: a three-strikes rule before changing course; 3-5 strong posts a
      week.
- **Versus ours:** far richer on pacing, on-screen text, and hook layers. Our SCRIPT-RULES covers the hook
  length, the escalation shape, and the loop, but not the timing targets, re-hooks, or on-screen text.
- **Adopt:** ideas into SCRIPT-RULES.md, the writer PROMPT, and REVIEW_PROMPT (see the gap table below).
  Effort S, no Modal cost. Risk: benchmarks are unverified, so test them against our own analytics.
- **Verdict:** BORROW IDEA. The most complete Shorts retention playbook; ignore the Vyral plugs.

### AgriciDaniel/claude-youtube — BORROW IDEA (one rule), SKIP code
- **Verified:** 401 stars, 78 forks, created 2026-03-05, pushed 2026-04-10, not archived. MIT (LICENSE
  "Copyright (c) 2025 Daniel Agrici"). Only 2 watchers, 1 contributor, and 14 commits for 401 stars.
- **Worth stealing:** `skills/claude-youtube/references/shorts-playbook.md` says completion of 70%+, VVSA
  75%+ is good and under 50% means a broken hook, and a visual change every 3 s. Its "13 s or 60 s bimodal"
  and "28-30 day freshness" claims are unverified.
- **Bug:** `skills/claude-youtube/execution/fetch_video_analytics.py:30` requests
  `impressionClickThroughRate`, which is not a YouTube Analytics API metric (section 2).
- **Verdict:** BORROW IDEA. It corroborates the 2-3 s visual-change rule; the analytics code is wrong.

### sergebulaev/youtube-skills — BORROW IDEA (one rule)
- **Verified:** 38 stars, 8 forks, pushed 2026-09-23, not archived. MIT (LICENSE: "Copyright (c) 2026
  Sergey Bulaev").
- **Worth stealing:** `skills/yt-hook-scripter/references/retention-beats.md` says "No greeting, no logo,
  no slow zoom. The first second is the entire funnel." and "Design the ending to imply the beginning." Our
  beat 1 is exactly a slow zoom on a still.
- **Verdict:** BORROW IDEA. Open on a cut or a punch-in, not a slow Ken Burns.

### FeiFei-AIDev/ai-script-generation-skill — SKIP
- 50 stars, created and pushed 2026-06-25. No LICENSE file, so all rights are reserved. It covers Chinese
  Xiaohongshu AI-tutorial scripts, which is off-niche.

### artemnovitckii/content-skills — SKIP
- 100 stars, created and pushed 2026-06-20. MIT. It repackages claude-youtube and youtube-skills and adds
  nothing new.

### What SCRIPT-RULES.md lacks (compared with the repos above plus Bomx, section 4)

| Rule | Ours today | What the repos do | Gap |
|---|---|---|---|
| Hook text on screen | captions only | 3-7 words on frame 1 that sharpen, not repeat, the spoken hook; top-centre; about 3 s (content-skills) | **missing** |
| First second | slow zoompan on the beat-1 still | "no slow zoom" (youtube-skills); a scene change within 2 s (claude-video-kit hard gate) | **missing** |
| Visual change rate | one still per beat, about 5-7 s each | a reset every 2-3 s (content-skills, claude-youtube, claude-video-kit); 2-4 s cards and 3-6 s screenshots (Bomx) | **large gap** |
| Re-hook | "context" beat after the hook | turn or escalation at 5-8 s; "the setup is your real hook" | beat 2 should add a new surprise, not background |
| Beat links | not specified | "but / therefore", not "and then" | missing |
| Payoff placement | twist near the end | payoff before the late drop-off, around 70-85% of runtime, then the loop line | make it explicit |
| Nouns you can see | a visual description per beat | the pointing test: "could the viewer point at what I just named?" (Bomx `VIDEO_COPY_PLAYBOOK.md:340`) | **missing, and it is the root of our visual failures** |
| Sentence rhythm | not specified | vary line lengths; "Uniform clipped lines read as robotic" (Bomx) | missing |
| Open loops | loop line only | close every loop; no vague tease or bait-and-switch | add to the reviewer |
| Length | 105-135 words, 40-50 s; LEARNINGS hypothesis 45-59 s | 30-45 s sweet spot (content-skills) versus 45-59 s (vidIQ); the claims conflict | run as an experiment, not a rule |
| Hook formulas | statement, question, number, contradiction | Myth/Reality, "It's not X — it's Y", specific number, specific date | add as examples |

---

## 2. Growth and analytics loops

### What the official YouTube Analytics API offers for Shorts (checked 2026-09-27)
Sources: developers.google.com/youtube/analytics/metrics, `/channel_reports`, `/revision_history`, and
developers.google.com/youtube/reporting/v1/reports/channel_reports.

- **Available per Short:**
  - Views and engagement: `views` (every start or replay of a Short since March 2025), `engagedViews`,
    likes, comments, shares, subscribers gained and lost.
  - Watch time: `averageViewDuration` and `averageViewPercentage`, both excluding "looping clips
    traffic".
  - The **audience retention report**: `audienceWatchRatio`, `relativeRetentionPerformance`,
    `startedWatching`, `stoppedWatching`, and `totalSegmentImpressions`. These come by
    `elapsedVideoTimeRatio` in 100 segments, need a single-video filter, and accept optional filters
    `audienceType`, `subscribedStatus`, and `youtubeProduct`.
  - Breakdowns: traffic sources, including the `SHORTS` value of `insightTrafficSourceType`, and a
    `creatorContentType` dimension.
- **Aug 27, 2026 revision:** only the *View* definition changed ("Video plays from the first frame",
  aligning long-form and Live with Shorts). *Engaged View* is listed as **unchanged**: "Playback continues
  past the first frame, or the user clicks/taps to play." The June 2025 note says engaged views reflect the
  old view-counting method. So our `engaged_share = engagedViews / views` is still a valid "stayed to
  watch" proxy for Shorts.
- **Sept 9, 2026 revision:** data lags **48-72 hours**, and end dates are truncated to the last fully
  processed day. Invalid metric combinations return HTTP 400. LEARNINGS' "48+ hours of data" rule should
  become **72+ hours**.
- **Not available:**
  - "Viewed vs swiped away" (VVSA) is Studio-only; I found no such metric in the API's metric list.
    `engaged_share` remains our best official proxy.
  - The Analytics API has no `impressions` or `impressionClickThroughRate`. Repos that query them get a
    400 (see darkzOGx and claude-youtube).
  - The Reporting API's reach reports (Jan 15, 2026: `channel_reach_basic_a1`, with
    `video_thumbnail_impressions` and `_ctr`) count a thumbnail "displayed without interaction or
    autoplay". They probably miss Shorts-feed autoplay exposure (unverified for Shorts), so they are of
    little use to us.

### darkzOGx/youtube-automation-agent (analytics parts) — BORROW IDEA
- **Verified:** 3,870 stars, 1,168 forks (a 30% fork ratio, which is high), 51 watchers, 3 contributors,
  71 commits. Created 2025-08-14, pushed 2026-09-25, not archived. MIT (LICENSE: "Copyright (c) 2025
  YouTube Automation Agent Contributors"). It keeps growth and fork-census reports in the repo; telemetry
  is opt-in.
- **Red flags:**
  - `agents/analytics-optimization-agent.js:206` and `:377` query `impressions,impressionClickThroughRate`,
    which are invalid metrics.
  - On error, line 197 returns `getSimulatedAnalytics(videoId)` (defined at line 709). The dashboard
    silently shows fake numbers.
- **Worth stealing** (retention mapped per scene):
  - **Per-scene retention** (`utils/scene-retention-engine.js`):
    - It queries all 5 retention metrics by `elapsedVideoTimeRatio` (analytics agent, lines about
      772-810) and maps the 100 points onto scaled scene timings.
    - Per scene it computes `changePoints`, `largestDropPoints`, `largestLiftPoints`,
      `stopRate = stoppedWatching / totalSegmentImpressions × 100`, and `replayPeak`.
    - Classification (lines 133-135): `drop_off` if change ≤ -8 points, drop ≥ 10, or stopRate ≥ 12;
      `rewatch` if replayPeak ≥ 105 or lift ≥ 8; `strong_hold` if change ≥ -4 and relative retention
      ≥ 0.6.
    - Line 156 gives no recommendation below 20 views or 20 curve points. Confidence (lines 217-218) is
      high at 80+ points and 500+ views, medium at 40+ and 100+.
    - Line 184 maps a hook drop to `shorten_and_front_load_value` and other drops to
      `tighten_transition_and_pacing`. It never auto-edits published videos.
  - **Promotion gates** (`utils/channel-learning-engine.js`):
    - The baseline is the median of prior snapshots.
    - Attribute groups (lines 187-190) need a minimum difference, for example length vs retention 8 and
      hook style vs retention 8.
    - Line 204 requires at least 2 videos per group; line 280 requires a relative difference of at least
      20%; line 288 sets `autoApply: false`.
- **Versus ours:** we sample only 12 curve points and never tie drops to beats. Their title/thumbnail A/B
  service (`utils/growth-experiment-service.js`) is long-form only and irrelevant to us.
- **Adopt (idea; don't use the code):**
  - In `youtube.py`, pull all 100 points plus `startedWatching`, `stoppedWatching`, and
    `totalSegmentImpressions`, and a second curve with `subscribedStatus==UNSUBSCRIBED`.
  - Map the curve onto our known beat timings, classify each beat with the thresholds above, and write
    the result to the Short's stats.
  - Promote a pattern into SCRIPT-RULES only with 2+ Shorts per group and a relative difference of 20% or
    more.
  - Effort M, near-zero Modal cost (a few API calls per Short). Risk: low-view Shorts have noisy or
    missing curves, so keep the 20-view floor.
- **Verdict:** BORROW IDEA. The only repo that turns retention curves into per-scene actions.

### eat-pray-ai/yutu — SKIP
- **Verified:** 693 stars, 82 forks, created 2023-05-20, pushed 2026-09-25, not archived. Apache-2.0
  (LICENSE file). 6 watchers, 6 contributors, 753 commits, 38 releases, so it is a real, maintained
  project.
- **What it is:** a Go CLI and MCP server over the YouTube **Data** API v3, plus an ADK agent
  (`cmd/agent/INSTRUCTION.md`, `cmd/agent/skills/youtube`). There is **no Analytics API code**, so the
  "autopilot" marketing is not an analytics loop. Issue #252: the tool added a Yutu tag to every upload.
- **Verdict:** SKIP. We already call the Data and Analytics APIs directly, and we upload through Buffer.

### adityaarsharma/youtube-marketing-skills — SKIP
- 44 stars, pushed 2026-05-14, MIT. It is a derivative of claude-youtube (its README line 368 compares
  itself to it). `server.js` pulls basic metrics only, with no retention, and it targets WordPress
  long-form.

### conorbronsdon/yt-analytics-mcp (1 star, MIT), modbender/youtube-analytics-mcp (0 stars, MIT), ZubeidHendricks/youtube-mcp-server (577 stars, MIT) — SKIP
- These are MCP wrappers. yt-analytics-mcp's retention tool (`src/server.ts:652-708`) makes the same query
  as our `youtube.py`.

### krakonjac300-pixel/podcast-shorts-factory — trainer loop (see section 5 for the repo facts)
- **Worth stealing:** `factory/agents/trainer.py:1-18` runs a weekly "coach":
  1. It pulls niche winners from the official Data API.
  2. It **backtests its own predictions**: it compares the finder's predicted scores with the actual views
     and watch percentage (the SQL is at lines 147-160) to find systematic bias.
  3. It updates **one** playbook per week, only between `<!-- TRAINER:START -->` / `<!-- TRAINER:END -->`
     markers, after a manager review. It can never touch `editorial-standards.md` (the MUST rules).
- **Adopt (idea):** backtest **our reviewer** in the same way. After 10 or more published Shorts, correlate
  the hook, clarity, payoff, visuals, and loop scores with engaged share, APV, and retention at 10%. If a
  score predicts nothing, it should not gate. Also let the automatic LEARNINGS updates touch only a marked
  section, and never the truth or sourcing rules. Effort S.

---

## 3. Topic research

### mvanhorn/last30days-skill — SKIP
- **Verified:** 63,006 stars, 5,483 forks, 216 watchers (0.34%, low for the star count), 137
  contributors, 1,268 commits, and 46 releases. Created 2026-01-23, pushed 2026-09-23, not archived. MIT
  (LICENSE: "Copyright (c) 2026 Matt Van Horn"). It is an active real project; its star count probably
  reflects hype.
- **How it researches:** parallel fetchers score recent posts by engagement and an LLM synthesizes them.
  The sources:
  - `lib/youtube_yt.py` uses **yt-dlp**, which our rules forbid.
  - Reddit through `lib/reddit_public.py` (keyless `search.json`) and `lib/reddit_shreddit.py` (parses
    undocumented `/svc/shreddit` HTML).
  - X through **browser cookies** (`lib/agentcookie.py`, `lib/bird_x.py`, plus Safari and Chrome cookie
    extractors).
  - Paid scrapers (ScrapeCreators, Bright Data).
  - The clean sources: `lib/hackernews.py` (Algolia), Polymarket, arXiv, Bluesky, and Techmeme.
- **Versus ours:** it is built for "what happened in the last 30 days", while we need evergreen history.
  Its sources that suit us are either forbidden or irrelevant.
- **Verdict:** SKIP. It depends on scraping and cookies we can't use, and its clean sources don't fit
  history.

### Wikimedia APIs — ADOPT (official, free, and they test the thing that fails us)
I tested these with `/tmp/ghdeep/g5/topic_signals.py`:
- **Demand:** the pageviews REST API,
  `wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/<Title>/monthly/<start>/<end>`.
  Resolve redirects first (MediaWiki `redirects=1`), because redirect pages count separately. "Great Emu
  War" (a redirect) had only 1,145 views in 12 months, against 945,985 for "Emu War".
- **Picture supply:** the MediaWiki action API,
  `generator=images&prop=imageinfo&iiprop=size|extmetadata` on the article. Count Commons files whose
  `LicenseShortName` is PD, CC0, or CC BY (not SA) and that are at least 1,200 px.
- **Anniversaries:** `en.wikipedia.org/api/rest_v1/feed/onthisday/events/MM/DD`. It returned 51 events for
  09/27, mostly wars and disasters, so it needs a tone filter before topics reach the writer.
- **Rate limits:** HTTP 429 on the sixth rapid topic. Pace at about 1 request/s and send a descriptive
  User-Agent with contact details, per Wikimedia's UA policy.

| Topic | 12-month views | Article images | Usable Commons pictures (PD/CC0/CC BY, 1,200 px+) |
|---|---|---|---|
| Emu War | 945,985 | 4 | **1** |
| Dancing plague of 1518 | 677,254 | 1 | **1** |
| Juliane Koepcke | 528,919 | 1 | **0** |
| Cottingley Fairies | 404,516 (one month: 206,044, a spike) | 10 | **1** |
| Piltdown Man | 160,195 | 7 | **4** |

- **Reading:** all five are channel-worthy on demand, but most have only 0-1 usable pictures on the
  article itself. That matches our "beat had no picture" rejections, and it can be known **before** a
  script is written.
- **Adopt:**
  - Add a `supply()` check to `auto.py` `fresh()`/`add_topics`: article images plus the article's
    Commons category.
  - If the topic has fewer than N usable pictures, either drop it or mark it for designed shots (maps,
    date cards, documents).
  - Rank the backlog by redirect-resolved 12-month views, with a bonus for recent spikes.
  - Effort S, no Modal cost (3-5 API calls per topic).
- **Clients:** mediawiki-utilities/python-mwviews (67 stars, MIT, last push 2022), Commonists/pageview-api
  (31 stars, MIT), and tomayac/pageviews.js (27 stars, Apache-2.0 per GitHub metadata, last push 2021). All are unnecessary: the direct
  calls take about 20 lines with `requests`.

### Reddit's official API — SKIP (not allowed for a monetized channel)
- Reddit Help ("Developer Platform & Accessing Reddit Data"): "We consider commercial purposes to include
  any use of our services by a business or on behalf of a business or as part of a monetized product or
  service." The Data API Terms (revised July 20, 2026) require a separate agreement for commercial use.
  The free tier (100 queries a minute with OAuth) is for non-commercial use. The keyless `.json` access
  that last30days uses is worse still.

### Official YouTube Data API as a demand signal — BORROW IDEA
- `podcast-shorts-factory` `factory/agents/trainer.py:90-93` calls
  `yt.search().list(q=..., type="video", videoDuration="short", order="viewCount", publishedAfter=...)`,
  plus `commentThreads` for top comments.
- The "Outlier Radar" in alexdailycheckin/yapcut (3 stars; **CC BY-NC 4.0**, so idea only) scores each post
  against its own account's median, and counts "3x or more" as an outlier worth banking
  (`plugins/outlier-radar/skills/outlier-radar/SKILL.md:79`).
- **Adopt (idea):** keep a roster of about 20 history-Shorts channels. Each week:
  1. Read each channel's uploads playlist (`playlistItems.list`, 1 unit).
  2. Get the videos' statistics (`videos.list`, 1 unit per 50 IDs).
  3. Flag videos at 3x or more their channel's median views.
  4. Pass the *topic*, never the script, through our Wikimedia supply check.

  This costs about 50 units a week out of 10,000 a day; avoid `search.list`, which costs 100 units a call.
  Risk: chasing competitors' topics can hurt originality (section 4 policy), so use it only as a demand
  signal and always research and write independently. Effort S.

---

## 4. Automated QA of rendered videos

### The policy context (why "static slideshow" is a monetization risk, not just a retention one)
YouTube's channel monetization policies (support.google.com/youtube/answer/1311392; renamed "inauthentic
content" on July 15, 2025, and clarified in July 2026 as reported by TechCrunch and Tubefilter):
- "channels where content feels interchangeable from video to video are not allowed to monetize"
- Named examples include "Image slideshows, templated storylines, or scrolling text with minimal or no
  narrative, commentary, or educational value" and "AI-generated content made with generic or unoriginal
  templates giving the impression of mass production".
- Off-putting content includes content that "appears designed to shock or surprise viewers for the sole
  purpose of getting views".
- "If you use automated tools or templates … the final product must still demonstrate your creative vision
  and provide educational or entertainment value."

Our defences are real: sourced research, original scripts, and educational value. But our look (one
still, a slow zoom, a hard cut, and the same caption, voice, and SFX template every time) is the pattern
the policy names. Visual variety per video and across videos is a gate item, not polish.

### Bomx/super-video-maker-skill — BORROW IDEA (the best QC checklist and copy rules)
- **Verified:** 289 stars, 43 forks, 3 watchers, 1 contributor, 13 commits. Created 2026-05-17, pushed
  2026-08-09, not archived. **No LICENSE file** (GitHub shows none), so all rights are reserved and we can
  reimplement ideas but not copy code.
- **What it is:** an ad and explainer video-maker skill: playbooks (`SKILL.md`, `VIDEO_COPY_PLAYBOOK.md`,
  `REVIEW_VIDEO_PLAYBOOK.md`) plus Python gates in `tools/`.
- **Worth stealing:**
  - **Encoding checks** (`tools/ffmpeg_qc.py`): `blackdetect=d=0.5:pix_th=0.10`, and a warning unless the
    video is yuv420p and h264/hevc.
  - **Frame-level gate** (`tools/ad_quality_gate.py`):
    - Sampling: 1 fps at 360 px, plus **4 fps dense windows ±0.35 s around boundaries**.
    - `visual_metrics` (lines 182-192) computes brightness, contrast (grey standard deviation), edge
      density, and white fraction (share of pixels above 235). White fraction ≥ 0.3 with edge density
      ≤ 2.6 means a blank-screen risk.
    - Static-stretch detection: frame difference < 0.045 while the reference changes > 0.13.
    - Voice speed factor: warn above 1.06, fail above 1.12. Words per second at most 3.65. Duration
      tolerance 0.5 s.
    - Checklist (lines 388-428), including line 413: "Confirm each visual beat supports the words being
      spoken at that moment."
    - Line 622: "Failures block delivery; warnings require an explicit decision."
  - **`SKILL.md` rules:**
    - Line 103 (rule 28): "**Vary the b-roll aesthetic per clip — sameness reads as AI.** Pick at least
      three distinct visual textures … avoid two consecutive clips that share the same dominant color or
      composition."
    - Line 113 (rule 38): fix layout problems **cheapest first**: crop or reframe, then edit the still, then
      re-render, then replace the shot.
  - **Copy gate** (`VIDEO_COPY_PLAYBOOK.md:207-219`):
    - line 211 "Voice and screen never carry the same sentence" (it applies to text cards, not our
      captions);
    - line 212 "Mute test and blank-screen test both pass".
    - Plain-register rules: no figures of speech, no rhetorical questions, and varied line lengths.
    - **Pointing test** (lines 338-343): "could the viewer point at what I just named? … Rewrite until the
      nouns are things."
  - **Review playbook** (`REVIEW_VIDEO_PLAYBOOK.md`): "Cut every 3–6s on screenshots, 2–4s on cards", and
    adversarial verification that defaults to reject.
- **Versus ours:** they check every second and the cut boundaries, while we check one midpoint frame per
  beat. They fix by reframing before replacing, while we jump straight to `pick.replace`, even though
  "subject cropped out" is one of our own frame-problem labels.
- **Adopt:** reimplement the frame metrics, the boundary windows, words per second, and cheapest-first
  fixing (try new `focus_x`/`focus_y` and zoom range before replacing a picture). Add the pointing test to
  the writer and reviewer. Effort S-M, with a few CPU seconds per Short on Modal. Risk: thresholds are
  tuned for ads, so calibrate them on our renders.
- **Verdict:** BORROW IDEA. The strongest concrete checklist; no license, so write our own code.

### saranambiar/hyperframes-video-agent-skills — BORROW IDEA
- **Verified:** 48 stars, 0 forks, 1 watcher, 1 contributor, 12 commits, created and pushed 2026-06-14,
  not archived. Apache-2.0 (LICENSE file).
- **Worth stealing:**
  - **Render QA** (`skills/render-qa-and-surgical-changes/SKILL.md`): probe the media, then extract
    **proof frames** at scene boundaries, caption frames, and the final frame, then build a contact sheet.
    - Line 44: "No clipped words after trims."
    - Line 83: "If the same visual appears in the next scene, extract the boundary frame too." Check
      frames just before, at, and just after each boundary.
  - **Failure modes** (`references/failure-modes.md`): carryover frames (the previous scene visible after
    a cut), a blank final frame, captions starting late, and captions wrapping onto two lines.
  - **Caption rules** (`skills/captions-and-music-bed/references/caption-rules.md`): one line at a time;
    split fast speech into shorter chunks.
  - **Proof-frame script** (`scripts/extract_proof_frames.py`): `-ss` per timestamp plus an `xstack`
    sheet. It is Apache-2.0, so it could be copied, but it is trivial.
- **Verdict:** BORROW IDEA. Boundary and last-frame checks matter for our hard cuts and the loop seam.

### kurbaitaev/ghost-editor — ADOPT (small pieces)
- **Verified:** 61 stars, 4 forks, 0 watchers, 1 contributor, 5 commits, 1 release. Created and pushed
  2026-09-24 (3 days old), not archived. MIT (LICENSE: "Copyright (c) 2026 kurbaitaev").
- **What it is:** a talking-head editor; `scripts/qa.py` (150 lines) is its render QA.
- **Worth stealing:**
  - **Render QA** (`scripts/qa.py`):
    - Checks 1080x1920, duration within ±0.2 s of the build, loudness from -17.5 to -12.5 LUFS, and flags
      a true peak above -0.5 dBTP.
    - **SFX stem check** (lines 10-12 and 94-109): render with the voice stripped, then compare each SFX
      hit's peak with the voice's **p95 peak**. Flag hits "> +1.5 dB over the voice, < -22 dB (inaudible)
      and > 4 dB off target".
    - Caption blocks outside the platform safe area (lines 124-127).
    - Silences inside speech (line 131: `silencedetect=noise=-38dB:d=0.8`).
    - A contact sheet (line 136: `fps=1/2,scale=216:384,tile=6x4`).
    - `--fix` applies only `alimiter=limit=0.89` (line 141) and never adds gain.
  - **Safe zones and caption placement** (`scripts/lib/safezone.mjs`):
    - Line 22: `shorts: { top: 140, bottom: 380, right: 140 }` px at 1080x1920. Line 23 gives all
      platforms combined as 220/480/150.
    - Line 26: ideal reading height 1180 with a 36 px gap.
    - Face-aware caption modes (below the chin, above the head), with hysteresis under 70 px
      (lines 119-120).
- **Applied to us:**
  - Vertically our captions are safe: centred at y=1152, so the text sits at about 1090-1215, well above
    the 1540 limit.
  - Horizontally, `max_width` 0.80 centred at 540 spans x 108-972. The widest chunks can run up to
    **32 px into the right 140 px column**, where the like and comment buttons sit.
  - Fix with `max_width` 0.74, or by shifting the centre left about 20 px (spec.py and captions.py).
  - Because we mix the SFX ourselves, we already have separate voice and SFX tracks, so the stem check is
    cheap.
- **Adopt:** port the SFX-vs-voice check, the silence check, and the safe-zone constants. Effort S, with a
  few CPU seconds per Short. Risk: the repo is 3 days old with 1 author, so its safe-zone numbers are the
  author's measurements; content-skills uses more conservative ones (top 20%, bottom 25%).
- **Verdict:** ADOPT (small, MIT). The audio-balance and safe-zone checks are the missing pieces of our
  deterministic checks.

### YeJe-cpu/SeeCut — BORROW IDEA (the most important evidence on how to use an LLM judge; no code)
- **Verified:** 64 stars, 13 forks, 0 watchers, 1 contributor, 3 commits, 1 release. Created 2026-09-25,
  pushed 2026-09-27, not archived. **LICENSE: PolyForm Noncommercial 1.0.0** (GitHub shows "Other"), so the
  code is not OK for a monetized channel; ideas only.
- **What it is:** an "AI editor that watches its own cut" for Chinese talking-head explainers. The loop
  runs: deterministic geometry gate (H1), then an LLM hard-defect checklist (H2), then **pairwise**
  adoption, then pairwise comparison against a reference to find the next changes. The judge is Gemini
  (`gemini-3.8-flash-high` via the `agy` CLI, `scripts/agy_judge.py:97`) and watches the **whole video at
  540p**.
- **Calibration results** (`references/06-质检闭环spec.md` §7, dated 2026-09-23; my translation):
  - **Absolute scoring failed.** They scored 11 items from 0 to 2 and summed them. The version the author
    judged ugly scored 18, the same as the best reference; a clean version tied with it too. Only one item
    ("evidence authenticity") separated good from bad. So they keep absolute checks only as a pass/fail
    defect list, not a sum and not an iteration signal.
  - **"Percentage like the reference" was noise:** the same video with the same prompt scored 88-90% one
    time and 68-70% the next.
  - **Pairwise comparison matched human judgment.** Run twice with the order swapped, the reference beat
    theirs both times, and v2 beat v1 both times. It has one blind spot (it preferred a busier fake-filled
    version), so some defects must be banned by a hard gate rather than left to the comparison.
- **Judge discipline** (§5 and `scripts/agy_judge.py`):
  - Every call starts fresh, with a JSON schema. The video is downscaled to 540p short side
    (`to540`, lines 30-33). The judge is isolated in a temp directory so it can't read source files.
  - **Fingerprint check:** the judge must copy 3 on-screen texts, and at least 2 must match the source
    (`fp_hits`, lines 53-62). Its reported duration must be within 3 s of ffprobe's (lines 147-151).
    Otherwise the result is treated as confabulated: retry once, then record "invalid", which is neither a
    pass nor a fail.
  - **Every FAIL gets verified:** frames at the claimed timestamps are extracted (`grab_fail_frames`,
    lines 184-197) and checked. The judge has "a stable habit" of merging adjacent beats, which produces
    false alarms. Only verified FAILs get fixed. Two runs on the same video give different FAIL sets.
  - Pairwise runs in both orders (lines 228-236). Consensus adopts the new version; a split is a tie.
- **Prompts** (`references/prompt/硬伤清单.txt` and `对比评委.txt`):
  - Hard defects with seconds as evidence: C5 unreadable or too-fast text, C7 "empty shot" of 2 s or more
    with almost no information, and C3 layout collisions or leftovers from the previous beat.
  - An `evidence_gaps` list: "seconds + narration quote + suggested real evidence". That is our
    beat-to-picture match.
  - The pairwise dimensions include "名词响应", noun response: every noun mentioned has a picture that
    catches it.
- **Geometry checks** (`references/07-几何规则自检spec.md`): these include "reveal not before the word"
  timing checks, the equivalent of our emphasis-colour timing.
- **Versus ours:**
  - We use exactly the design they found unreliable: absolute 1-5 scores with a threshold.
  - We never check whether the judge actually saw what it claims.
  - We act on every flagged frame without verifying it.
- **Adopt (reimplement):**
  1. Turn story scores into advisory values and gate on verified hard defects.
  2. Add a fingerprint: the judge must quote 3 caption strings and the duration, checked against our ASS
     text and ffprobe.
  3. Re-check each claimed defect on its own extracted frame (a cheap Flash-Lite yes/no) before spending a
     replacement.
  4. In fix rounds, compare the new render with the current best pairwise in both orders, and adopt only
     on a double win.

  Effort M. Quota: pairwise needs 2 extra requests per fix round, with two videos in each (about 50k
  tokens), so run it on Flash-Lite (about 500 requests a day), not Flash (about 20).
- **Verdict:** BORROW IDEA. The most useful gate-design evidence in this study; the license forbids
  copying code.

### runesleo/claude-video-kit — ADOPT (small pieces)
- **Verified:** 120 stars, 26 forks, 0 watchers, 2 contributors, 48 commits, 1 release, about 27 issues
  and PRs. Created 2026-04-06, pushed 2026-09-27, not archived. MIT (LICENSE: "Copyright (c) 2026 Leo
  (@runes_leo)").
- **Worth stealing:**
  - **Objective Shorts gate** (`scripts/verify-shorts.mjs:13-21`). Hard gates: 1080×1920, at most 60 s,
    **an average scene-change interval of 3.0 s or less**, and **at least 1 scene change in the first 2 s**.
    It warns when the median interval exceeds 2.5 s or the file exceeds 30 MB. Scene detection
    (lines 86-103) uses `select='gt(scene,0.1)',showinfo`, or the render schedule when supplied.
  - **Pacing targets** (`docs/SHORTS_PIPELINE.md:479-495`): a median scene change of 1.5-2.5 s; the hook
    (first 2 s) is "never static"; slides last 1.5-3 s, at most about 5 s for explanation slides.
  - **Review receipts** (`skills/video-explainer/references/review-gate.md`):
    - The reviewer must be independent of the author.
    - Statuses are pass, fix, or block, and the aggregate is the worst one.
    - Receipts are **bound to the SHA-256** of the script and of the exact MP4 (lines 33-39 and 73-80):
      "If the MP4 changes, the rendered-output receipt becomes stale."
  - **Calibration lesson** (`scripts/scan_frames.py`, docstring lines 3-18): the author tested a
    pixel-bounding-box safe-area check on a **known-bad video with 3 known overflows**. At threshold 26 it
    raised 35 false alarms; at 70 it missed all 3, so the check was kept out of the gate. The lesson: test
    every automated check on known-bad examples before trusting it. We currently delete ours (`reject()`).
- **Adopt:**
  - Scene-interval and first-2-s gates. Today they will fail by design (5-7 s beats), so they are the
    target for multi-shot beats; see the top insights.
  - Store the MP4's SHA-256 in `review.json` and refuse to publish if it differs.
  - Keep a 540p copy of every rejected Short as a calibration set.
  - Effort S, negligible Modal cost.
- **Verdict:** ADOPT (small, MIT). A clear pacing gate and hash-bound receipts.

### What our gate should check that it doesn't

| Check | How | Starting threshold (calibrate on kept rejects) | Source |
|---|---|---|---|
| Whole video, not 1 frame per beat | send the 540p MP4 inline (`video/mp4`, `video_metadata.fps=2`); still 1 request | about 7k tokens for 45 s at default (low) resolution, about 25k at high | SeeCut; Gemini docs |
| Beat-to-picture match per line | the judge returns, for each line, the nouns and whether the picture shows them (yes, partly, or no, with seconds) | any "no" on a key noun means a verified defect | Bomx pointing test; SeeCut noun response |
| Cut boundaries and last frame | frames at t-0.1, t, and t+0.1 around each cut, plus the final and first frames (loop seam) | no black, carryover, or edge artifacts | hyperframes; Bomx dense windows |
| Black or flash frames | `blackdetect=d=0.1:pix_th=0.10`; per-frame YAVG jumps via `signalstats` away from cuts | any | Bomx `ffmpeg_qc.py` |
| Static stretches and pacing | scene interval from our own timeline or `select='gt(scene,0.1)'` | average ≤ 3.0 s; a change in the first 2 s | claude-video-kit |
| Blank or low-information frames | brightness, contrast, edge density, white fraction | white ≥ 0.3 and edges ≤ 2.6 | Bomx lines 182-192 |
| Repeated pictures | dHash between beat stills (the loop line is exempt) | Hamming distance ≤ 6 | our rule; the reviewer asks today but unreliably |
| Caption safe zone | from our ASS events (x, y, width after `\fscx`) | right edge ≤ 940, bottom ≤ 1540, top ≥ 140 | ghost-editor `safezone.mjs:22` |
| Caption legibility | flag chunks scaled below 80% by `scale = 100*max_width/width`; the judge flags captions over the subject | scale < 80 | ours plus Bomx |
| Speech pace | words per second per beat from the Kokoro timestamps | at most 3.65 | Bomx |
| Silence inside speech | `silencedetect=noise=-38dB:d=0.8` over the speech span | any, excluding planned pauses | ghost-editor line 131 |
| SFX balance | SFX-only stem peaks vs the voice's p95 peak | not more than +1.5 dB above, not below -22 dB | ghost-editor lines 10-12 |
| Clipping | true peak (already checked) plus `astats` clipped-sample count | 0 clipped samples | ours plus ghost-editor |
| Hook frame | frame 0 is not black; the hook subject and hook text are visible | — | content-skills |
| Sameness across videos | dHash or colour histogram of the contact sheet against the last 10 Shorts; same opening shot type | warn when too similar | YouTube policy; Bomx rule 28 |
| Judge validity | the judge quotes 3 caption strings and the duration; each FAIL is re-checked on an extracted frame | 2 of 3 strings match; duration within ±2 s | SeeCut |

**Gemini video input facts** (ai.google.dev/gemini-api/docs/video-understanding and /api/generate-content,
read 2026-09-27):
- Inline data works for requests under 20 MB. Static mode samples 1 fps by default.
- `videoMetadata.fps` accepts values above 0 up to 24. The field is marked deprecated in the
  `generateContent` reference in favour of the newer interactions API, so check it before relying on it.
- Tokens: 66 per frame at low media resolution, which the docs call the video default, or 258 otherwise,
  plus 32 per second of audio. That is about 100 tokens per second at default and about 300 at high. Use a
  higher `media_resolution` so the judge can read captions: a 45 s Short at 2 fps is then about 25k tokens.
- Static mode is "best for short clips or when every frame matters".
- In our code, `llm._image_part` handles only PNG and JPEG. Adding `video/mp4` (detected by
  `data[4:8] == b"ftyp"`) plus `video_metadata` is a small change.
- A 540p, CRF 28, 64 kbps AAC review copy of a 45 s Short is a few MB.

---

## 5. Free-tier multi-agent routing

### krakonjac300-pixel/podcast-shorts-factory — SKIP the router, BORROW IDEA (trainer)
- **Verified:** 105 stars, 33 forks, 0 watchers, **1 contributor, 1 commit**, 0 releases. Created
  2026-07-22; the 2026-09-25 push date comes from PR branches. Not archived. MIT (LICENSE: "Copyright (c)
  2026 Kosta Rakonjac").
- **Red flags:** 105 stars and 33 forks on a single commit. PRs #2 and #3 add paid clipping-campaign
  agents (Vyro, Clipping.net).
- **What it is:** 10 "agents" (finder, planner, editor, montage, finishing editor, compiler, uploader,
  community, trainer, and trend scout) that clip podcasts into Shorts, with Markdown "skills" playbooks in
  `factory/skills/`.
- **Routing** (`factory/llm.py`):
  - `PROVIDERS` (lines 22-33): OpenRouter (`meta-llama/llama-3.3-70b-instruct`), NVIDIA NIM, Groq
    (`llama-3.3-70b-versatile`), Gemini through its OpenAI-compatible endpoint (`gemini-2.5-flash`),
    Ollama, and OpenAI.
  - `_chain()` (lines 49-57) tries the primary provider, then each configured fallback that has a key.
  - Requests use a hard 45 s timeout with `max_retries=1` (lines 88-92), because "free providers sometimes
    HANG (not error)".
  - `call_tool`/`call_text`/`call_vision` walk the chain and **swallow every exception**
    (lines 128-140). Vision is limited to 4 images.
  - There is **no quota accounting**: no per-minute pacing, no daily-vs-minute distinction, no model
    ladder, and no rest periods.
- **Versus ours:** our `llm.py` is clearly stronger (per-model ladders, pacing, daily-quota detection,
  overload waits, and a (20 s, 300 s) timeout). Nothing in the router is worth copying.
- **Free-tier facts** (checked 2026-09-27):
  - Groq's official rate-limit page lists, on the free plan, `openai/gpt-oss-120b` and `qwen/qwen3.8-27b`
    at 30 requests a minute, 1,000 a day, 8k tokens a minute, and 200k tokens a day. Llama 3.3 70B is no
    longer listed, and I saw no vision model in the free list.
  - OpenRouter's unfunded free models are reported (by third parties, not verified officially) at about
    50 requests a day.
  - So Groq could be a **text-only** tier between Gemini and Cursor (topic ideas, research synthesis,
    script rewrites). The 8k tokens-a-minute limit allows about one long prompt per minute. It can't
    review pictures.
- **Other skills worth a line:**
  - `factory/skills/scene-mapping.md`: "never leave more than ~8s without either a visual or an emphasis
    moment" and "Constant gentle camera movement beats busy multi-directional motion (that's AI slop)".
  - `factory/skills/pacing.md`: "One deliberate silent beat before the punchline" and "Accelerate toward
    the payoff."
- **Verdict:** SKIP the router (ours is better). BORROW IDEA from the trainer backtest (section 2).
  Optionally WATCH Groq's `gpt-oss-120b` as a text-only fallback, but check quality before trusting it,
  since the Cursor fallback already shows that weaker writers fail review.

---

## Red flags seen (for the synthesis)

- **Promotional instructions inside skills:** vyralcontent/content-skills tells the agent to mention
  Vyral in every skill.
- **Stars that don't match the activity:**
  - podcast-shorts-factory: 105 stars and 33 forks on one commit.
  - claude-youtube: 401 stars, 2 watchers, and 1 contributor.
  - viral-hooks-skill: 96 stars on a repo whose whole history is under an hour.
  - last30days: 63k stars with a 0.34% watcher ratio.
  - darkzOGx: a 30% fork ratio, with fork-census and growth reports kept in the repo.
- **Fake or invalid analytics:** darkzOGx falls back to *simulated* analytics on error and queries
  metrics that don't exist, as does claude-youtube.
- **Forbidden data sources behind "research" skills:** last30days uses yt-dlp, browser-cookie X access,
  keyless Reddit JSON, and paid scrapers.
- **Non-commercial licenses on the best QA ideas:** SeeCut (PolyForm NC) and yapcut (CC BY-NC). Bomx and
  FeiFei have no license at all.

---

## Top insights for Days of Odd (ranked)

1. **Fix visual failures at the source: screen topics for pictures before writing, then write lines to the
   pictures.**
   - In `auto.py`, count usable Commons files (PD, CC0, or CC BY; 1,200 px or more) for the article and its
     Commons category through the MediaWiki API. Drop topics below a threshold, or mark them for designed
     shots.
   - Rank the backlog by redirect-resolved 12-month Wikipedia pageviews.
   - In `writer.py`, add Bomx's pointing test ("could the viewer point at what I just named?") and give
     the writer the list of available pictures, so each line names something we can show.
   - My test found Juliane Koepcke at 0 usable article pictures and the Emu War and Cottingley Fairies at
     1 each: the kind of shortfall behind our "no picture" rejections.
   - Effort S-M, free.

2. **Break the slideshow: a visual reset every 2-3 s, and a change within the first 2 s.**
   - Use 2-3 shots per beat: detail crops or punch-ins of the same still, a second picture, or a date,
     map, or quote card. Don't open on a slow zoom. Use at least 3 visual textures per Short.
   - Gate it with claude-video-kit's check (average scene interval ≤ 3.0 s, a change in the first 2 s).
   - Four repos converge on 2-3 s (content-skills, claude-youtube, claude-video-kit, Bomx), and
     youtube-skills bans the slow-zoom opening. Crops of one good picture also mean fewer pictures are
     needed per beat.
   - It is our best defence against YouTube's July 2026 "image slideshows, templated storylines …
     interchangeable" monetization rule, which applies to the whole channel.
   - Effort M; render time rises slightly.

3. **Let the reviewer watch the real Short.**
   - Send a 540p MP4 inline at 2 fps with audio and a higher media resolution. It is the same single
     request as today, about 25k tokens.
   - Include each line's timing, and ask for per-line picture-matches-noun verdicts and timestamped hard
     defects (off-topic, anachronism, watermark, cropped subject, unreadable caption, caption over the
     subject, repeated picture).
   - Validate the judge SeeCut's way: it quotes 3 caption strings and the duration. Re-check each claimed
     defect on an extracted frame before acting.
   - Fix cheapest first (Bomx rule 38): try a new focus and crop before `pick.replace`.
   - Effort M (`llm._image_part`, `check.py`, `studio.py`).

4. **Add a deterministic QC stage before Gemini** (ffmpeg and PIL, seconds of CPU):
   - black or flash frames and boundary frames;
   - static stretches and scene interval;
   - blank or low-information frames;
   - dHash repeats;
   - caption safe zone (our widest captions reach x=972, into the right 140 px button column, so set
     `max_width` to 0.74);
   - caption scale;
   - words per second ≤ 3.65;
   - silence inside speech;
   - SFX peaks vs the voice's p95 (ghost-editor);
   - clipped samples.

   Effort S-M. Ports from ghost-editor and claude-video-kit (MIT) are fine; Bomx needs reimplementation.

5. **Change the decision rule, and calibrate it.**
   - Gate on verified hard defects. Keep the 1-5 story scores advisory: SeeCut found that summed absolute
     scores could not tell a bad version from a good one, and that percentage scores swung 20 points
     between runs.
   - In fix rounds, compare new against best pairwise in both orders on Flash-Lite, and adopt only on a
     double win.
   - Keep a small 540p copy of every rejected Short (`reject()` deletes them today) as known-bad test
     cases.
   - After 10 or more published Shorts, check whether each reviewer score predicts engaged share and APV
     (podcast-shorts-factory's trainer backtest). A score that predicts nothing shouldn't gate.
   - Bind `review.json` to the MP4's SHA-256 (claude-video-kit).
   - Effort S.

6. **Put hook text on frame 1.** Show 3-7 words that sharpen rather than repeat the spoken hook, top-centre
   just below the top UI (y about 400-550, clear of both repos' top margins), for about 3 s, with the hook subject visible in the first frame
   (content-skills' three-layer hook). This is a libass event in `captions.py`. Effort S.

7. **Add these script rules to SCRIPT-RULES and the writer:**
   - beat 2 is a new surprise, not background, with a turn or re-hook at 5-8 s;
   - "but / therefore" links between beats;
   - the payoff lands by about 80% of runtime, before the loop line;
   - vary sentence lengths;
   - close every open loop; no vague teases;
   - the Myth/Reality, "It's not X — it's Y", number, and date hook formulas.

   Treat length (30-45 s vs 45-59 s) as an experiment, not a rule. Effort S.

8. **Turn retention curves into per-beat lessons.**
   - In `youtube.py`, fetch all 100 points plus `stoppedWatching`, `startedWatching`, and
     `totalSegmentImpressions`, and a second curve filtered to `subscribedStatus==UNSUBSCRIBED`.
   - Map the curve onto beat timings and classify each beat as drop-off, rewatch, or strong hold (darkzOGx
     thresholds: change ≤ -8 points or stop rate ≥ 12% counts as a drop-off).
   - Measure at **72 hours or later**, not 48 (API docs, Sept 9, 2026).
   - Promote a rule only with 2+ Shorts per group and a 20% or larger difference.
   - Keep `engaged_share`: it remains valid, because engaged views were unchanged on Aug 27, 2026. Never
     query `impressions` or CTR from the Analytics API.
   - Effort M.

9. **Leave routing alone, and keep research sources clean.**
   - Our `llm.py` already beats podcast-shorts-factory's router. Groq's free `gpt-oss-120b` (1,000
     requests a day, 8k tokens a minute) is at most a text-only tier before Cursor.
   - For demand signals, use Wikipedia pageviews and an official Data API "outlier" check (3x a channel's
     median, via playlistItems and videos.list, about 50 units a week).
   - Not Reddit: its free API excludes monetized products.
   - Not last30days: it relies on yt-dlp, cookies, and scrapers.
