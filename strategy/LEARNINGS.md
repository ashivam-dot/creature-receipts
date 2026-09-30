# What we've learned

The daily run keeps this file up to date (`PLAYBOOK.md`, step 3). Scriptwriters read it before writing, and
the quality gate checks that every new episode applies it. The aim is that each day's Shorts beat the
channel's recent median on the numbers below.

## What to beat

Recompute daily from `analytics/<date>.json`, over Shorts with 48+ hours of data (medians of the last 10).

| Measure | Where it comes from | Channel median | Target |
|---|---|---|---|
| Engaged share (stand-in for Studio's "stayed to watch") | `analytics.engaged_share` | not enough data yet | 70%+; under 60% rarely takes off |
| Average percentage viewed | `analytics.averageViewPercentage` | not enough data yet | 80%+ (loops can push it past 100%) |
| Still watching at 10% of the Short | `retention` point nearest `at: 0.1` | not enough data yet | rising week over week |
| Subscribers per 1,000 views | `subscribersGained` / `views` | not enough data yet | 2+ |
| Likes per 100 views | `likes` / `views` | not enough data yet | 4+ |

## Rules we've proven

A rule needs at least two Shorts with 48+ hours of data showing the same effect. Once proven, also copy it
into `strategy/SCRIPT-RULES.md`, then cite the evidence here.

- None yet.

## Hypotheses to test (from research, not yet our data)

- Put the strongest surprise in the first 2 seconds, then give context. It was the first rule proven on
  Days of Odd, the channel this studio was built for.
- Cut each Short to 45–59 seconds (vidIQ: that length reaches 1M views more often).
- Write a last line that flows straight into the first line, so viewers rewatch and average percentage
  viewed rises.

## Scoreboard

One row per live Short once it has 48+ hours of data. Hook style is statement, question, number, or
contradiction.

| Short | Series | Hook style | Views | Engaged share | Avg % viewed | Watching at 10% | Subs gained | Likely reason |
|---|---|---|---|---|---|---|---|---|

## Log

- Day 0: the studio is set up. Nothing to learn from yet.
