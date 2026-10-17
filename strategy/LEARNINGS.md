# What we've learned

This file is the learning log for Atlas in Numbers (from 2026-10-08). Record each Short's 24- and 72-hour numbers
here, and promote a rule only when the evidence below supports it. The aim is that each new Short beats the
channel's recent median.

## What to beat

Recompute after each Short's 24- and 72-hour reviews, over Atlas Shorts with 24+ hours of data (medians of the last 10).

| Measure | Where it comes from | Channel median | Target |
|---|---|---|---|
| Engaged share (stand-in for Studio's "stayed to watch") | `analytics.engaged_share` | no Atlas data yet | Track after three Atlas Shorts each pass 100 views |
| Average percentage viewed | `analytics.averageViewPercentage` | no Atlas data yet | Track after three Atlas Shorts each pass 100 views |
| Still watching at 10% of the Short | `retention` point nearest `at: 0.1` | no Atlas data yet | rising week over week |
| Shares per 1,000 views | `shares` / `views` | no Atlas data yet | 3 or more |
| Comments per 1,000 views | `comments` / `views` | no Atlas data yet | 3 or more |
| Subscribers per 1,000 views | `subscribersGained` / `views` | no Atlas data yet | Track after three Atlas Shorts each pass 100 views |

## Rules we've proven

A rule needs at least four Shorts with 24+ hours of data and a measured difference. Universe Receipts promoted
rules from two Shorts each and ended up with rules that contradict each other; don't repeat that.

- None yet.

## Hypotheses to test (from research and channel 1, not yet our data)

- A fully coloured map and the claim on frame 1 hold more viewers than a slow reveal.
- Beat 2 should escalate (a second, bigger number) rather than give background. Universe Receipts loses most
  viewers when beat 2 is a date or catalogue name.
- "Where does your country rank?" endings earn more comments than generic questions.
- Topics where India or the US is a surprising outlier get more shares.

## Scoreboard

Refreshed by every producer run (`atlas.stats`) from the channel's public feed or Atlas's cloud public-count snapshot. Views per hour is over the Short's whole life so far, so compare Shorts of similar age.

| Short | Topic | Published | Views | Likes | Views per hour |
|---|---|---|---|---|---|
| atlas001 137 Places Have More Mobile Subscriptions Than People | map_reveal | 2026-10-08 16:01 UTC | 1323 | 17 | 6.6 |
| atlas002 45 places with Falling Populations | map_reveal | 2026-10-09 16:02 UTC | 976 | 15 | 5.5 |
| atlas003 Below the fertility benchmark in 2024 | rank_ladder | 2026-10-08 20:01 UTC | 132 | 2 | 0.7 |
| atlas004 47 places Where Life Expectancy Reaches 80 | map_reveal | 2026-10-08 23:01 UTC | 162 | 2 | 0.8 |
| atlas011 Money Sent Home Equals 58% of GDP in Tajikistan | map_reveal | 2026-10-10 16:01 UTC | 148 | 1 | 1.0 |
| atlas014 Finland Rates Life at 7.8 out of 10 | rank_ladder | 2026-10-10 23:00 UTC | 1043 | 9 | 7.2 |
| atlas016 How Many Calories Each Country Has On Its Plate | map_reveal | 2026-10-10 20:00 UTC | 1130 | 16 | 7.6 |
| atlas017 The Youngest and Oldest places on Earth | map_reveal | 2026-10-11 16:01 UTC | 1338 | 21 | 10.4 |
| atlas019 The Emptiest and Most Crowded places | map_reveal | 2026-10-11 20:00 UTC | 1765 | 20 | 14.2 |
| atlas021 Cuba has 9.5 doctors while Niger has 0.0 | rank_ladder | 2026-10-11 23:00 UTC | 1046 | 14 | 8.6 |
| atlas023 France has 49 fixed broadband lines per 100 people | map_reveal | 2026-10-12 16:02 UTC | 259 | – | 2.2 |
| atlas024 Where 30% of People are 65 or Older | map_reveal | 2026-10-12 20:01 UTC | 1218 | – | 10.8 |
| atlas025 Qatar has 108 micrograms of particles | map_reveal | 2026-10-12 23:01 UTC | 1213 | – | 11.0 |
| atlas026 The Global Gap in Basic Drinking Water Access | map_reveal | 2026-10-13 16:03 UTC | 767 | – | 8.2 |
| atlas027 Women in the labor force: 83% to 5% | rank_ladder | 2026-10-13 20:01 UTC | 143 | – | 1.6 |
| atlas028 61 places Still Have Most People Outside Cities | rank_ladder | 2026-10-13 23:01 UTC | 1155 | – | 13.4 |
| atlas030 places Where One City Holds 92% of City Dwellers | rank_ladder | 2026-10-14 16:02 UTC | 1320 | – | 19.1 |
| atlas031 In Qatar, 77% of people were born abroad | rank_ladder | 2026-10-14 20:01 UTC | 2 | – | 0.0 |
| atlas032 Health Spending: The $10,550 to $13 Divide | map_reveal | 2026-10-14 23:01 UTC | 1101 | – | 17.7 |
| atlas033 Japan Has 51 Seniors per 100 Working-Age People | map_reveal | 2026-10-15 16:03 UTC | 1092 | – | 24.2 |
| atlas037 Colombia Rains 180 Times Egypt's Annual Precipitation | map_reveal | 2026-10-15 20:01 UTC | 1031 | – | 25.1 |
| atlas039 Ireland Produces $131,592 per Person | map_reveal | 2026-10-15 23:01 UTC | 1035 | – | 27.1 |
| atlas040 Romania Drinks 16.8 Liters of Pure Alcohol per Adult | map_reveal | 2026-10-16 16:02 UTC | 965 | – | 45.7 |
| atlas042 Powering Life: Electric Consumption Per Person | map_reveal | 2026-10-16 20:01 UTC | 411 | – | 24.0 |
| atlas047 Freshwater Per Person: From Iceland to Kuwait | map_reveal | 2026-10-16 23:01 UTC | 926 | – | 65.5 |

## Log

- 2026-10-08: channel 2 was rebuilt as Atlas in Numbers. The four public History's Last Hours Shorts
  (nsIV96pvg_0, fG5iWshCAOM, gbhhEU5wfZk, GeYxkROXScI) were made private; no History or animal Short counts here.
- 2026-10-08 (process): History's Last Hours failed on supply, not ideas. Most drafts were blocked by the
  event-picture check, and the private control repo stopped publishing when its GitHub Actions billing ran out.
  Atlas draws every frame from licensed data and publishes from Modal, so neither failure can recur the same way.

## Before 2026-10-08 (History's Last Hours and animals)

- 2026-10-01: the channel moved from animals to historical tragedies; the two animal Shorts were made private.
- 2026-10-03: an early baseline mixed animal and history Shorts with a handful of views and was withdrawn.
- 2026-10-04: holds stopped all but one Short, and the image check sank four drafts over a single wrong picture each.
