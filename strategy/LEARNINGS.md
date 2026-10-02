# What we've learned

The daily run keeps this file up to date (`PLAYBOOK.md`, step 3). Scriptwriters read it before writing, and
the quality gate checks that every new episode applies it. The aim is that each day's Shorts beat the
channel's recent median on the numbers below.

## What to beat

Recompute daily and after each Short's 24- and 72-hour reviews, over Shorts with 24+ hours of data (medians of the last 10).

| Measure | Where it comes from | Channel median | Target |
|---|---|---|---|
| Engaged share (stand-in for Studio's "stayed to watch") | `analytics.engaged_share` | not enough data yet | 70%+; under 60% rarely takes off |
| Average percentage viewed | `analytics.averageViewPercentage` | not enough data yet | 80%+ (loops can push it past 100%) |
| Still watching at 10% of the Short | `retention` point nearest `at: 0.1` | not enough data yet | rising week over week |
| Subscribers per 1,000 views | `subscribersGained` / `views` | not enough data yet | 2+ |
| Likes per 100 views | `likes` / `views` | not enough data yet | 4+ |

## Rules we've proven

A rule needs at least two Shorts with 24+ hours of data showing the same effect. Once proven, also copy it
into `strategy/SCRIPT-RULES.md`, then cite the evidence here.

- None yet.

## Hypotheses to test (from research, not yet our data)

- Put the strongest surprise in the first 2 seconds, then give context.
- Cut each Short to 17–27 seconds to match top-performing competitors.
- Title as a question the Short answers, with one emoji at the end.
- Write a last line that flows straight into the first line to encourage seamless rewatching.
- End on a line that makes viewers want to answer or rewatch, not a passive closing statement: Universe Receipts'
  best Short so far (689 views, 3.8 likes per 100) drew 1 comment because it closed on a statement (2026-10-02).
- Choose topics whose key moments have strong period pictures: weak visuals caused 7 of the 8 latest history
  rejections, and each rejection spends a day's free model quota (2026-10-02).

## Scoreboard

One row per live Short once it has 24+ hours of data. Hook style is statement, question, number, or
contradiction.

| Short | Series | Hook style | Views | Engaged share | Avg % viewed | Watching at 10% | Subs gained | Likely reason |
|---|---|---|---|---|---|---|---|---|

## Log

- Day 0: the studio is set up. Nothing to learn from yet.
- 2026-10-01: the channel moved from animals to historical tragedies as History's Last Hours. Its two animal
  Shorts (1 view each, never shown in the Shorts feed) were made private, and their numbers don't count here.
- 2026-10-01: Initialized the learning log with preliminary research hypotheses; no performance data available yet.
