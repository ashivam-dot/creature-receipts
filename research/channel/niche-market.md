# Niche market research: YouTube Channel 2 (Sep 30, 2026)

**Bottom line:** Launch a **failure-analysis channel: true disasters and near-misses in aviation, ships, bridges, dams, buildings and factories, each told as "the tiny cause, and the rule we all live with because of it."** Working name: **The Rule Came After** (`@TheRuleCameAfter`, handle returns 404, so it's probably free). It scored highest (3.90 of 5) because it combines strong demand, the deepest public-domain image archives of any niche (NTSB, Library of Congress engineering surveys, US Coast Guard, NOAA, Chemical Safety Board), long-form proof at million-subscriber scale, and a constructive "lesson" angle that keeps it advertiser-friendly. **Runner-ups:** (2) money and economic history, which has the best RPM and subscriber conversion but the thinnest topic demand and weaker pictures; (3) deep-ocean discovery stories, which has the biggest audience but is the most crowded.

Builds on `YouTube-100-Day-Autopilot/youtube-studio/research/` (niche-selection, shorts-strategy, policy-factsheet). Space is excluded (the sister channel Universe Receipts covers it), and so is the strange-but-true history identity (Days of Odd).

---

## 1. What changed since the earlier research, and why it matters here

- **Shorts pay about the same in every niche. The niche premium only shows up in long-form.** Shorts ad revenue is pooled and split by each channel's share of engaged views per country ([YouTube Help 12504220](https://support.google.com/youtube/answer/12504220)). Across 274 channels, Shorts RPM clustered at $0.07–$0.20 in most niches, at 3–14% of long-form RPM ([AIR](https://air.io/en/air-data-findings/youtube-shorts-rpm-vs-long-form-how-much-do-shorts-earn-in-2026)). US viewers pay $0.328 ([AIR](https://air.io/en/monetization/what-rpm-can-you-expect-from-shorts-in-2026)). For a Shorts-first channel, then, the niche matters mostly through **how American the audience is** and what the **long-form compilations** earn later, not through ad rates on the Shorts themselves.
- **Pictures are the pipeline's real bottleneck.** Days of Odd rejected 14 of its first 15 failed Shorts for their visuals: the mean visual score was 2.9, against 4.6 for accepted Shorts (`reference/days-of-odd/CHANNEL.md`, decision log 2026-09-27/28). A niche whose every story has abundant PD/CC0/CC BY photos directly raises the pass rate. CC BY-SA isn't allowed, and that rules out most modern Commons photos of aircraft and places.
- **Advertiser rules on death were clarified in August 2026.** In educational or documentary content, *implied* death (for example, the aftermath of a building collapse) can earn full ads; visibly injured bodies get limited ads; extreme suffering earns none ([summary](https://quasa.io/media/depictions-of-death-can-earn-ads-context-still-decides-the-icon), [YouTube ad-guideline updates](https://support.google.com/youtube/answer/9725604), [EDSA context](https://support.google.com/youtube/answer/6345162)). The context has to be in the audio or video itself. Disaster stories work if they stay non-graphic and centered on the lesson.
- **The July 2026 inauthentic-content split** targets templated content, shock content, and AI personas giving advice on health, legal, finance or politics ([TechCrunch](https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/)). That argues against psychology and health-advice angles, and against horror-style framing of disasters.

## 2. Method

- **RPM:** 2025–26 aggregator benchmarks: AIR (verified Analytics API data from 274 channels), Admetrics (50K channels), LensPOV (142 creator disclosures), TubeAnalytics and vidIQ planning ranges, NicheRPM, and GhostShorts/Virvid for Shorts. These are directional, not guarantees.
- **Demand:** (a) median English-Wikipedia pageviews over 60 days (Aug 1–Sep 29, 2026) for 10 flagship articles per niche. This is a free, repeatable proxy for how many people care about the topics; script at `research/scripts/wiki_demand.py`. (b) Live subscriber, video and view counts read from 60+ channels' public pages on Sep 30, 2026 (`yt_stats.py`, `yt_video.py`, `yt_tabs.py`). (c) Top Shorts returned by YouTube search per niche (`yt_search.py`).
- **Limits:** Searches ran from an Indian IP, so results over-represent India-focused channels. Wikipedia readership is a proxy for curiosity, not for Shorts views. Handle checks only show whether a page exists: a 404 means probably free, but reserved or terminated handles also return 404.

## 3. Scored comparison (16 candidates)

Scores run 1–5 (5 = best). Weights: RPM 15%, Demand 20%, Competition/angle 15%, Advertiser safety 15%, Pipeline fit (Wikipedia + free images) 20%, Subscriber conversion and long-form potential 15%. The RPM and demand columns are sourced; the scores are my judgment.

| # | Niche | US long-form RPM est. | Shorts RPM (all-geo) | Wiki demand (median 60-day views) | Live evidence (Sep 30, 2026) | RPM | Dem | Comp | Safe | Fit | Conv | **Score** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Failure analysis: aviation + ships + structures + industry, "the rule it created"** | $4–8 (AIR Transport median $5.69, P25–75 $3.17–9.81) | $0.04–0.15 | 99K aviation / 50K maritime / 27K engineering | Mentour Pilot 2.51M; Fascinating Horror 1.46M; Plainly Difficult 1.1M; Oceanliner Designs 970K; Green Dot Aviation 622K (joined Oct 2021, 101 videos); Brick Immortar 401K from 53 videos; WindyAviation 250K Shorts channel (joined Jun 2024) | 4 | 4 | 3 | 3 | 5 | 4 | **3.90** |
| 2 | Money & economic history | $6–12 (LensPOV finance $16.12; Admetrics finance $9.90, business $7.70; AIR Business & Finance only $2.01) | $0.05–0.30 | 12.7K (lowest) | Wealth Mode Mentality 86.6K from 75 Shorts and 4.56M views (joined Mar 2, 2026); Economics Explained 2.88M; MagnatesMedia 1.86M; Business Casual 1.15M from 91 videos | 5 | 2 | 4 | 5 | 3 | 4 | **3.70** |
| 3 | Engineering disasters alone | $4–8 | $0.04–0.15 | 27K | same long-form channels; new 2026 Shorts entrants at ~1K views | 4 | 3 | 3 | 3 | 5 | 4 | 3.70 |
| 4 | Archaeology & ancient mysteries | $3–5 (LensPOV History $3.03) | $0.04–0.12 | **113K (highest)** | Ancient Architects 640K; Zenn 193K from 37 videos | 3 | 5 | 2 | 4 | 4 | 3 | 3.60 |
| 5 | Deep ocean & sea creatures | $3–8 (AIR Education & Science $10.22 median, wide spread; LensPOV Science $3.85) | $0.04–0.15 | 72K | BeyondTheBlue 223K long-form (joined Dec 2024); Mr. Science 255K from 20 videos; Seekers of the Cosmos 967K; FactoHolic 22.4M (India); "Why Deep Sea Creatures Are Giant" 42M views | 3 | 5 | 2 | 5 | 3 | 3 | 3.55 |
| 6 | Shipwrecks & maritime | $4–8 | $0.04–0.15 | 50K | Oceanliner Designs Titanic Short 10.1M; NorthAmericaShipwrecks 4.6K (Jul 2024) | 4 | 3 | 3 | 3 | 4 | 4 | 3.50 |
| 7 | Cold War & military secrets | $3–6 | $0.04–0.12 | 38K | Dark Docs 1.2M; Simple History 5.11M; new Cold War Shorts mostly under 2.5K views | 4 | 2 | 3 | 3 | 5 | 4 | 3.50 |
| 8 | Bizarre medical history | $2–6 (AIR Health $1.23; NicheRPM Health $6–12) | $0.04–0.12 | 70K | Blue Shorts History 30.9K from 86 Shorts (joined Feb 2025); Helix² 230K from 53 | 3 | 4 | 3 | 2 | 5 | 3 | 3.45 |
| 9 | Inventions & accidental discoveries | $4–8 | $0.05–0.15 | 22.6K | Top Shorts are Hindi (7.6M, 22M); English mostly under 11K | 4 | 2 | 3 | 5 | 4 | 3 | 3.45 |
| 10 | Weather & natural disasters | $3–6 (AIR News $2.60) | $0.03–0.12 | 60K (off-season Oct–Jan) | Ryan Hall Y'all 3.5M, Max Velocity 2.17M (both face/live); tornado Shorts 1–7M | 3 | 3 | 3 | 3 | 5 | 3 | 3.40 |
| 11 | Aviation alone | $4–8 | $0.04–0.15 | 99K | WindyAviation 250K but only 0.57 subs per 1K views; many crash Shorts use news footage | 4 | 4 | 3 | 2 | 3 | 3 | 3.20 |
| 12 | Geography & border oddities | $3–7 | $0.04–0.15 | 21.7K | Geo Bytes 95.5K from 66 Shorts (joined May 2024); Reed Schultz Geo 572K from 84 | 3 | 4 | 3 | 4 | 2 | 3 | 3.15 |
| 13 | Food history | $2–4 (AIR Food $2.25) | $0.02–0.10 | 43K | Tasting History 4.48M (face); Absolute History trench-food Short 520K | 2 | 3 | 3 | 5 | 3 | 3 | 3.15 |
| 14 | Frauds, scams & heists | $3–7 | $0.03–0.12 | 58K | Coffeezilla 4.72M (face); new heist Shorts mostly under 5K; overlaps Days of Odd's "Hoaxes" series | 4 | 3 | 2 | 3 | 2 | 4 | 2.95 |
| 15 | Extreme animals & biology | $1.5–4 | $0.02–0.04 | 67K | doggyzuko 303K from 60 Shorts (joined May 2025); Infinite Fact 142K (Dec 2024) | 2 | 5 | 1 | 4 | 3 | 2 | 2.95 |
| 16 | True crime lite | $2–5 (limited ads) | $0.03–0.12 | 87K | An AI true-crime channel was [terminated](https://www.tubefilter.com/2025/02/14/youtube-true-crime-case-files-ai-crime-channel-terminated/) | 2 | 5 | 2 | 1 | 3 | 4 | 2.95 |
| 17 | Psychology & brain | $2–6 | $0.04–0.12 | 29.5K | UnordinaryMind 123K; search results flooded with "psychology facts about girls" | 3 | 4 | 1 | 2 | 1 | 3 | 2.35 |

RPM sources: [AIR long-form by niche](https://www.overseeros.com/blog/youtube-rpm-by-niche) (AIR dataset), [Admetrics](https://useadmetrics.com/benchmarks/youtube-cpm-by-niche-2026), [LensPOV](https://lenspov.com/research/youtube-cpm-by-niche-2026/) (Q4 lifts CPM about 1.62×), [TubeAnalytics](https://www.tubeanalytics.net/resources/research/youtube-cpm-rpm-benchmarks-q2-2026) (Education $3.50–9, Finance $8–18), [NicheRPM](https://www.nicherpm.com/youtube-rpm-by-niche), and Shorts ranges from [GhostShorts](https://ghostshorts.com/blog/youtube-shorts-rpm-how-much-shorts-pay-by-niche-2026) and [Virvid](https://virvid.ai/blog/most-profitable-ai-youtube-shorts-niches-2026-rpm-data). Channel figures come from public channel pages on Sep 30, 2026.

**Sensitivity:** if RPM alone mattered, money would win. It drops to second because its topics draw a tenth of the readers and its beats are harder to illustrate, which is exactly where this pipeline fails. Ranks 3–5 are within scoring noise.

### Subscriber conversion (subscribers ÷ lifetime views, public counts)

| Channel (format) | Subs per 1K views |
|---|---|
| Wealth Mode Mentality (money/business Shorts, 100% Shorts) | **19.0** |
| Brick Immortar (engineering disasters, long-form) | 6.9 |
| Plainly Difficult / Green Dot Aviation / Fascinating Horror (long-form) | 5.1 / 4.9 / 4.4 |
| BeyondTheBlue (ocean, long-form) | 4.7 |
| Helix² / Blue Shorts History / Reed Schultz Geo (Shorts) | 1.9 / 1.8 / 1.7 |
| doggyzuko / Geo Bytes / Infinite Fact (Shorts) | 1.3 / 1.0 / 0.9 |
| WindyAviation / The Outliners (Shorts, meme or facts) | 0.6 / 0.5 |

Takeaways: story and money channels convert far better than generic fact feeds, and failure analysis has the strongest long-form conversion of any niche with enough free visuals. The earlier brief's 0.17% baseline ([PublishPress](https://news.thepublishpress.com/p/are-shorts-worth-it)) sits in the middle of the Shorts rows.

---

## 4. Ranked top 3

### #1: Failure analysis, "the disaster that wrote the rule" (recommended)

**Why it wins**
1. **Demand:** aviation disasters are the second most-read niche on Wikipedia (99K median). Maritime adds 50K and engineering 27K, so the combined pool is large and evergreen. Long-form proof is abundant: five channels between 622K and 2.5M subscribers, plus Brick Immortar at 401K from just 53 videos.
2. **Shorts ceiling from tiny channels:** a Vajont Dam Short reached 147K views in under 2 days on a 2.4K-subscriber channel (FactNestYT). A container-ship-failure Short reached 331K in 3 days on a 2.7K-subscriber channel (SurvivalSerg). Oceanliner Designs' Titanic-wreck Short has 10.1M.
3. **Best picture fit of any niche.** Every story has official public-domain imagery: NTSB and FAA "Lessons Learned" (aviation), Library of Congress HAER/HABS measured drawings and photos (bridges, dams, buildings), US Coast Guard and NOAA (wrecks), USGS (dams), the Chemical Safety Board (industrial), National Archives, and pre-1931 public-domain photos on Commons. Beats with no picture become numbers (loads, bolt sizes, dates), which suit the pipeline's designed title cards.
4. **A differentiated, advertiser-safe angle.** Fascinating Horror and Plainly Difficult sell *dread*. We sell *the fix*: every Short ends with the rule, code or design you encounter today ("…and that's why airplane windows have rounded corners"). That's the educational context YouTube's implied-death guidance rewards, and a genuine value-add against the inauthentic-content policy: each episode delivers a distinct lesson, not a template.
5. **US-skewed, TV-friendly audience:** adult, male-leaning, engineering and aviation fans, with a Transport-category RPM around $5.69. Compilations like "7 Disasters That Rewrote Building Codes" at 8–12 minutes are natural and earn watch hours.
6. **No overlap** with Universe Receipts (space failures such as Challenger and Columbia stay with the sister channel) or Days of Odd (none of the 15 topics below appears in its calendar).

**Risks, and how to handle them**
- **Tragedy.** Never show bodies or victims' faces. State deaths once, factually. Keep horror words ("terrifying", "horrifying") out of titles, and keep the lesson in the narration (context must be in the audio or video, per the [EDSA rules](https://support.google.com/youtube/answer/6345162)). Exclude disasters from the last 10 years: Surfside 2021, Titan 2023, the Key Bridge 2024, Jeju Air 2024 and Air India 171 in 2025 are sensitive and poorly licensed.
- **New automated rivals.** Four channels appeared in 2026: Margin of Error (Sep 27; 8 Shorts, best 1.1K views), The Inquiry Room (`@WrittenInWreckage`, Sep 19), Why It Broke (May), and Root Cause Media (Apr). None has traction yet, but the window is closing. Differentiate with the "rule came after" payoff, named series, and faster volume.
- **Median early views are low** in any niche (vidIQ: median 1,362 views for a new channel's first Short). **Day-21 check:** if median views per Short stay under 1K and no Short passes 20K after about 45 uploads, add the money strand's best hooks as a test series before any pivot.

**Channel name ideas** (checked with `curl … https://www.youtube.com/@HANDLE` on Sep 30, 2026; a random control handle, `@qzx7vk29plmw3rt`, returned 404)

| Name | Handle | HTTP | Note |
|---|---|---|---|
| **The Rule Came After** (pick) | @TheRuleCameAfter | 404 (likely free) | The promise is the name; also free: @RuleCameAfter |
| Wreckage Receipts | @WreckageReceipts | 404 | Family branding with Universe Receipts, good for Collab Shorts |
| Failure Receipts | @FailureReceipts | 404 | Same family, broader |
| Lessons in Rubble | @LessonsInRubble | 404 | Structures-leaning |
| Blueprint to Rubble | @BlueprintToRubble | 404 | Engineering-leaning |

Taken (200): @WrittenInWreckage (The Inquiry Room), @WhyItBroke, @RootCauseStories, @BlackBoxStories, @FailurePoint, @HindsightFiles.

**Six series**
1. **The Rule Came After:** disaster, then the law or code it created (fire exits, boiler codes, bridge inspections).
2. **One Small Part:** a single bolt, rod, crack or unit conversion that brought everything down.
3. **Black Box Notes:** airliner accidents retold from official investigation reports.
4. **Taken by the Water:** ships, floods and dams.
5. **It Almost Happened:** near-misses and saves (Citicorp, the Gimli Glider, the Goldsboro bomb).
6. **Myth vs. Report:** famous "facts" the official findings contradict (the Comet's "square windows", the Iron Ring legend, Tacoma "resonance").

**Target audience:** US adults 25–54, male-leaning. Engineers, tradespeople, pilots and aviation fans, safety professionals, STEM students, and documentary viewers who watch on the TV.

**Tone:** calm investigator, never horror. It opens on the tiny cause ("84 of the 90 bolts were too thin"), states the human cost once and plainly, explains the mechanism in everyday words, and lands on the rule the viewer lives with. Respectful, precise, a little wry about bureaucracy; no dread music; the last line loops back to the first.

**15 example topics** (all exact English Wikipedia titles verified on Sep 30, 2026 via `action=query`: each returned a page ID and none is a redirect. Twists were spot-checked against the article text with `research/scripts/facts.py`.)

| # | Story (year): twist | Series | Exact Wikipedia title (pageid) |
|---|---|---|---|
| 1 | Comet jetliner breakups (1954): the fatal crack started at a square-cornered roof antenna window, not the passenger windows, yet it's why every window you fly past is rounded | Myth vs. Report | `De Havilland Comet` (182728) |
| 2 | Hyatt Regency walkways (1981): a "simpler" rod change hung two walkways from one set of nuts, and 114 died | One Small Part | `Hyatt Regency walkway collapse` (938573) |
| 3 | Citicorp tower (1978): a student's question led to secret night-time welding of a Manhattan skyscraper, kept quiet until 1995 | It Almost Happened | `Citicorp Center engineering crisis` (68289612) |
| 4 | Air Canada 143 (1983): fuel figured in pounds instead of kilograms left a 767 empty at 41,000 ft, and it glided onto a racetrack | It Almost Happened | `Gimli Glider` (160797) |
| 5 | BA 5390 (1990): 84 windscreen bolts were 0.026 in too thin, and the captain was blown half out of the cockpit and survived | One Small Part | `British Airways Flight 5390` (1347221) |
| 6 | Aloha 243 (1988): 89,680 short island hops fatigued a lap joint until the roof tore away mid-flight, and the jet still landed | Black Box Notes | `Aloha Airlines Flight 243` (478114) |
| 7 | Tacoma Narrows (1940): "Galloping Gertie" fell and its only death was a dog named Tubby; the textbook "resonance" story is wrong | Myth vs. Report | `Tacoma Narrows Bridge (1940)` (301135) |
| 8 | Silver Bridge (1967): a flaw 0.1 in deep dropped a whole bridge, and America's first national bridge inspections followed | The Rule Came After | `Silver Bridge` (23804840) |
| 9 | Quebec Bridge (1907, 1916): it collapsed twice, and no, Canada's engineering rings aren't made from its steel | Myth vs. Report | `Quebec Bridge` (514037) |
| 10 | Cocoanut Grove (1942): 492 died behind a jammed revolving door, which is why one sits beside a swing-out door today | The Rule Came After | `Cocoanut Grove fire` (186805) |
| 11 | SS Eastland (1915): the post-Titanic lifeboat law helped make it top-heavy, and it rolled over at the dock, killing 844 | Taken by the Water | `SS Eastland` (42107) |
| 12 | St. Francis Dam (1928): its builder inspected the leaks and called them normal; about 12 hours later it failed | Taken by the Water | `St. Francis Dam` (425061) |
| 13 | Therac-25 (1985–87): typing too fast triggered a software race that fired up to 250× the intended radiation dose | One Small Part | `Therac-25` (315212) |
| 14 | Tenerife (1977): neither jumbo was meant to be there, since a bomb had diverted both, and the crash rewrote cockpit radio language | Black Box Notes | `Tenerife airport disaster` (92734) |
| 15 | Grover Shoe Factory (1905): one boiler blast flattened a factory, and today's national boiler safety code followed | The Rule Came After | `Grover Shoe Factory disaster` (18622408) |

Verified backups: `Air Canada Flight 797`, `United Airlines Flight 232`, `1961 Goldsboro B-52 crash`, `Iroquois Theatre fire`, `Ronan Point`, `Texas City disaster`, `Sultana (steamboat)`, `SS Edmund Fitzgerald`, `Johnstown Flood`, `Air Transat Flight 236`. Avoid these three, which are redirects: `Kemper Arena`, `Hartford Civic Center`, `British Airways Flight 9`. Aloha's link to the FAA's aging-aircraft program isn't in its Wikipedia article, so leave it out unless the article gains it. Two facts to carry into scripts: NIST later judged Citicorp's quartering winds less dangerous than feared, and the Tacoma "resonance" claim needs careful wording (the bridge failed from aeroelastic flutter).

**Format and cadence (inherits the Days of Odd pipeline):** 45–55 s, 6–9 beats, 3 a day, no licensed music. Weekly from week 4: one 8–12-minute compilation per series, with a new intro and transitions narrated for the compilation, to earn watch hours. Apply for YPP by mid-December, before the Feb 1, 2027 doubling to 20M Shorts views or 8,000 hours ([policy-factsheet](../../YouTube-100-Day-Autopilot/youtube-studio/research/policy-factsheet.md)).

### #2: Money & economic history, "what it cost, what it's worth"

- **Upside:** the highest long-form RPM ($6–12 est.; finance is the top niche in every benchmark), and the best measured Shorts conversion (Wealth Mode Mentality: 86.6K subscribers from 4.56M views in 7 months, all Shorts). Zero violence risk. Strong US hooks: Executive Order 6102, the 1933 double eagle, Silver Thursday, the Panic of 1907, the $100,000 bill, the end of the penny.
- **Downside:** the lowest topic demand (12.7K median readers). Money-history Shorts in search mostly get 1K–270K views. Wealth Mode's hits are modern aspirational business stories, whose visuals (logos, living founders) break our licensing rules. Abstract beats also strain the two-title-card-per-Short limit.
- **Must avoid:** anything that sounds like advice (AI finance personas are demonetized). Tulip mania, the Darien scheme and the Gold Rush are already taken by Days of Odd.
- **Free handles:** @PricedInHistory, @OddDollars, @LegalTenderTales, @MintConditionTales, @TheMoneyTrailHistory.

### #3: Deep-ocean discoveries, "how we found it"

- **Upside:** 72K median demand, the widest audience (a single Short has 42M views), public-domain NOAA Ocean Exploration imagery, and no policy risk. Frame each Short as a true discovery story (the coelacanth in 1938, the Bloop in 1997, the Challenger Deep dives) rather than listicles.
- **Downside:** the most crowded feed (FactoHolic 22.4M, LIGHTS ARE OFF 5.6M, and endless 3D/AI "thalassophobia" channels), a globally mixed audience that lowers US share, and many species photos under CC BY-SA or non-commercial licenses (MBARI's are copyrighted).
- **Close 4th:** archaeology (113K demand, CC0 imagery from the Met and Art Institute of Chicago). It lost because it sits next to Days of Odd's history identity and carries pseudo-archaeology risk.

---

## 5. Reproducing this

All scripts are in `research/scripts/`: `wiki_demand.py` (niche demand), `yt_stats.py` / `yt_video.py` / `yt_tabs.py` / `yt_search.py` (one-off public-page reads, not for recurring use under YouTube's terms), `handles.py` (handle HTTP status), `verify_titles.py` (exact Wikipedia titles), `facts.py` (twist spot-checks). Re-run the handle check just before creating the channel; a 404 isn't a guarantee.
