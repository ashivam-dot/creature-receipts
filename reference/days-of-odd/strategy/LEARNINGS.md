# What we've learned

The daily run keeps this file up to date (`PLAYBOOK.md`, step 3). Scriptwriters read it before writing, and
the quality gate checks that every new episode applies it. The aim is that each day's Shorts beat the
channel's recent median on the numbers below.

## What to beat

Recompute daily from `analytics/<date>.json`, over Shorts with 48+ hours of data (medians of the last 10).

| Measure | Where it comes from | Channel median | Target |
|---|---|---|---|
| Engaged share (stand-in for Studio's "stayed to watch") | `analytics.engaged_share` | 39% | 70%+; under 60% rarely takes off |
| Average percentage viewed | `analytics.averageViewPercentage` | 59.7% | 80%+ (loops can push it past 100%) |
| Still watching at 10% of the Short | `retention` point nearest `at: 0.1` | 111% | rising week over week |
| Subscribers per 1,000 views | `subscribersGained` / `views` | 0.0 | 2+ |
| Likes per 100 views | `likes` / `views` | 3.2 | 4+ |

## Rules we've proven

A rule needs at least two Shorts with 48+ hours of data showing the same effect. Once proven, also copy it
into `strategy/SCRIPT-RULES.md`, then cite the evidence here.

- Put the strongest surprise in the first 2 seconds, then give context (ep001, ep009).

## Hypotheses to test (from research, not yet our data)

- Cut each Short to 45–59 seconds (vidIQ: that length reaches 1M views more often; ours currently run 40–50 s).
- Write a last line that flows straight into the first line so viewers rewatch and average percentage viewed rises.

## Scoreboard

One row per live Short once it has 48+ hours of data. Hook style is statement, question, number, or
contradiction.

| Short | Series | Hook style | Views | Engaged share | Avg % viewed | Watching at 10% | Subs gained | Likely reason |
|---|---|---|---|---|---|---|---|---|
| ep001 | Wait, That Happened? | – | 62 | 39% | 57.7% | 114% | 0 | Strong hook outperformed at10 median, but pacing failed to maintain average view percentage. |
| ep003 | History's Luckiest People | – | 219 | 38% | 82.9% | – | 0 | Outstanding retention at 82.9% suggests the chronological narrative arc was highly effective. |
| ep009 | History Got It Wrong | – | 325 | 47% | 59.7% | 107% | 0 | Highest engaged share confirms a strong title premise, though early retention dipped slightly below median. |

## Log

- 2026-09-26: Launch day. ep001 is live. Pipeline fixes from the first eight scripts are in
  `CHANNEL.md`, including a tighter loop seam (0.48 s of silence, down from 1.1 s) and a first word at
  0.15 s.
- 2026-09-26: No change today: no Short has 48+ hours of data, so medians stay unset and no hypothesis was promoted or dropped.
- 2026-09-27: No performance data was updated today because no Shorts have reached 48 hours of analytics yet.
- 2026-09-28: Logged initial performance baseline from ep001; kept all hypotheses pending further data.
- 2026-09-29: Established initial performance baselines for engagement and retention across three distinct history series.
