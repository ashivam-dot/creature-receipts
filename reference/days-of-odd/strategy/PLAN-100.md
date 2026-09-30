# 100-day plan

Day 0 is 2026-09-26; Day 100 is 2027-01-04. Three Shorts a day adds up to about 290 Shorts. Production runs
around the clock and keeps a week of finished Shorts ready; publishing follows the cadence below.

| Phase | Days | Dates | Focus | Exit milestone |
|---|---|---|---|---|
| 0. Build | 0–1 | Sep 26–27 | Pipeline, brand, first 8 episodes, channel created, Buffer connected | First Shorts scheduled |
| 1. Launch | 1–21 | Sep 27–Oct 17 | 3 a day across all 7 series; learn what hooks and topics work | 60+ Shorts live, first KPI baseline |
| 2. Double down | 22–50 | Oct 18–Nov 15 | Put 70% of output into the top 2–3 series; weekly experiments; Instagram cross-posting | 1,000 subscribers; 1M+ views in a 28-day window |
| 3. YPP push | 51–80 | Nov 16–Dec 15 | Holiday anniversaries, 4–5 a day if quality holds; apply for YPP the day we qualify | YPP application submitted before Feb 1 rules |
| 4. Scale | 81–100 | Dec 16–Jan 4 | Monetization setup, best formats at full volume, Day 100 review | Day 100 report |

## Targets

These are the targets we steer by. They aren't promises.

| By | Base case | Stretch (on track for 100k) |
|---|---|---|
| Day 21 | 60 Shorts, 100k total views, 300 subscribers | 1M views, 3,000 subscribers |
| Day 50 | 150 Shorts, 1M views, 1,500 subscribers | 10M views, 25,000 subscribers |
| Day 80 | 240 Shorts, 10M views in 90 days, YPP applied | 30M views, 60,000 subscribers |
| Day 100 | 290 Shorts, YPP approved or in review | 45M+ views, 100,000 subscribers |

## Decision points

- **Day 7:** Retire hook styles whose engaged share (engaged views / views, the API's stand-in for Studio's
  "stayed to watch") is below 50%.
- **Day 14:** Pick a voice from the blind test plus the retention data.
- **Day 21:** Rank series by views per Short and subscribers per 1,000 views. Keep the top 3–4.
- **Day 30:** If the 7-day median views per Short is still under 1,000, change the format (on-screen hook text,
  faster pacing, a different voice) before adding volume. Otherwise go to 4 a day if the 14-day median engaged
  share is 60% or more and every Short still scores 4+ at the quality gate. Add a fourth slot in
  `pipeline/src/ytc/publish.py` and raise the inventory target in `automation/daily.py` to a week's worth.
- **Day 50:** 5 a day on the same test.
- **Cadence ceiling:** 5 a day. More than that starts to look mass-produced, which the Partner Program's
  inauthentic-content rule rejects, and YouTube gives no boost for volume.
- **Day 60–80:** Apply for YPP as soon as Studio shows eligibility.
- **Every Sunday:** weekly review in `reports/`, next week's experiments, and a check for better open-source tools.

## Owner touchpoints

- **Done on Day 0:** phone verification, with advanced features now enabled. The agent did all other setup with
  the owner's Google login.
- **When eligible:** the YPP application, AdSense, and tax form (about 20 minutes).
- Nothing else is required. Daily reports land in `reports/`.
