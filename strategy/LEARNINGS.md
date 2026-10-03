# What we've learned

The daily run keeps this file up to date (`PLAYBOOK.md`, step 3). Scriptwriters read it before writing, and
the quality gate checks that every new episode applies it. The aim is that each day's Shorts beat the
channel's recent median on the numbers below.

## What to beat

Recompute daily and after each Short's 24- and 72-hour reviews, over Shorts with 24+ hours of data (medians of the last 10).

| Measure | Where it comes from | Channel median | Target |
|---|---|---|---|
| Engaged share (stand-in for Studio's "stayed to watch") | `analytics.engaged_share` | 67% | 70%+; under 60% rarely takes off |
| Average percentage viewed | `analytics.averageViewPercentage` | 82.8% | 80%+ (loops can push it past 100%) |
| Still watching at 10% of the Short | `retention` point nearest `at: 0.1` | not enough data yet | rising week over week |
| Subscribers per 1,000 views | `subscribersGained` / `views` | 0.0 | 2+ |
| Likes per 100 views | `likes` / `views` | 0.0 | 4+ |

## Rules we've proven

A rule needs at least two Shorts with 24+ hours of data showing the same effect. Once proven, also copy it
into `strategy/SCRIPT-RULES.md`, then cite the evidence here.

- None yet.

## Hypotheses to test (from research, not yet our data)

- Put the strongest surprise in the first 2 seconds, then give context.
- Cut each Short to 17–27 seconds to match top-performing competitors.
- Title as a question the Short answers, with one emoji at the end.
- Write a last line that flows straight into the first line to encourage seamless rewatching.
- End on a line that makes viewers want to answer or rewatch, not a passive closing statement.
- Choose topics whose key moments have strong period pictures to prevent visual drop-off.

## Scoreboard

One row per live Short once it has 24+ hours of data. Hook style is statement, question, number, or
contradiction.

| Short | Series | Hook style | Views | Engaged share | Avg % viewed | Watching at 10% | Subs gained | Likely reason |
|---|---|---|---|---|---|---|---|---|
| X8MhmozMp0o | ? | –, story | 3 | 67% | 91.1% | – | 0 | Topic curiosity and tight pacing drove above-median retention (91.1% vs 82.8% median), though views remain low. |
| ep031 | Sole Survivors | statement, story | 10 | – | – | – | – | Strong question hook and dramatic tragedy topic generated highest view count (10), but retention metrics are still populating. |
| zX1VUGHLb0o | ? | –, story | 3 | 67% | 74.6% | – | 0 | Irony hook matched median engagement (66.7%), but below-median retention (74.6%) suggests mid-video pacing slackened or loop failed. |

## Log

- Day 0: the studio is set up. Nothing to learn from yet.
- 2026-10-01: the channel moved from animals to historical tragedies as History's Last Hours. Its two animal
  Shorts (1 view each, never shown in the Shorts feed) were made private, and their numbers don't count here.
- 2026-10-01: Initialized the learning log with preliminary research hypotheses; no performance data available yet.
- 2026-10-02: Maintained existing hypotheses without promotion as initial Shorts (X8MhmozMp0o, zX1VUGHLb0o) lack sufficient view volume and retention telemetry.
- 2026-10-03: Established baseline medians across initial 3 Shorts; kept existing hypotheses pending deeper retention metrics.
