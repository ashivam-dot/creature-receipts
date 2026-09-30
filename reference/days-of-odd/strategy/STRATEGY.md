# Days of Odd: strategy

Last revised 2026-09-26 (Day 0). Evidence for each choice is in `research/`.

## Goal and honest odds

- **Goal:** 100,000 subscribers and YouTube Partner Program (YPP) approval on Shorts by Day 100 (2027-01-04).
- **What 100k takes:** Shorts convert roughly 0.15–0.36% of viewers to subscribers, so 100k needs about
  28–67 million views in 100 days. Only 1.3% of channels ever reach 100k, and there's no verified
  example of a non-spam channel doing it this fast in 2025–26. It needs several breakout Shorts.
- **What YPP takes:** 1,000 subscribers plus 10 million engaged Shorts views in 90 days. From
  2027-02-01 new applicants need 20 million, so we apply by about 2026-12-15 (Day 80). Review takes about a month.
- **Plan:** maximize the number of well-made attempts, measure fast, and put volume behind whatever
  breaks out. Never use tactics that put the channel at risk (see Hard rules in `CHANNEL.md`).

## Niche and audience

- **Niche:** strange-but-true history. One surprising true story per Short, researched and sourced.
- **Why:** proven Shorts demand (Historically has 1.43M subscribers from Shorts), above-average subscriber
  conversion, endless free public-domain imagery, low policy risk, and evergreen topics that keep getting
  views for months.
- **Audience:** English-speaking adults 18–44, mostly the US, then the UK, Canada, and Australia. US Shorts pay
  about $0.33 per 1,000 views, versus $0.008 in India.
- **Not doing:** long-form (owner requirement), Hindi (1/40th the revenue per view), gore, true crime,
  present-day politics, and AI "slop" formats.

## Format

- **Length:** 40–50 seconds (105–135 spoken words). vidIQ's 331M-Short study found 45–59 s gets the most
  views; staying under 60 s keeps us clear of the rule that blocks longer Shorts with a copyright claim.
- **Structure:** hook in the first sentence, 2–3 escalating beats, a twist, and a last line that loops into
  the first. Full rules are in `strategy/SCRIPT-RULES.md`.
- **Visuals:** period artwork, engravings, photographs, and maps from Wikimedia Commons (public domain, CC0,
  and CC BY only), The Met and the Art Institute of Chicago (CC0), and NASA. Slow Ken Burns moves. No stock
  clips unless a beat needs them.
- **Captions:** burned in, 2–3 words at a time, Montserrat Black, white with the current word in yellow.
  Sized to fit inside the Shorts safe area.
- **Voice:** Kokoro-82M (`af_heart`, Apache-2.0), a warm American narrator. Re-evaluated in a blind test against
  Chatterbox and other open models once the first analytics arrive. The owner's own voice would be the
  strongest originality signal and is an option if YouTube ever questions the channel.
- **Audio:** narration mixed to -14 LUFS with synthesized whooshes and pops. No licensed music, so nothing
  gets claimed and no music share comes out of the revenue pool.

## Series

Named series make the channel look curated rather than templated, and give viewers a reason to follow.

| Series | Promise |
|---|---|
| Wait, That Happened? | Events so strange they sound made up |
| History's Luckiest People / Unluckiest People | Improbable fortune and misfortune |
| Hoaxes That Fooled Everyone | Frauds and pranks that fooled the public |
| Trials You Won't Believe | The strangest courtrooms in history |
| Bad Ideas That Seemed Good | Plans that backfired |
| History Got It Wrong | Famous "facts" that never happened |

## Publishing

- **Cadence:** 3 Shorts a day from Day 1, rising to 4 and then 5 when the data allows (see
  `strategy/PLAN-100.md`). Production checks every hour and keeps a week of finished Shorts ready.
- **Times:** 2 p.m., 8 p.m. and 10 p.m. US Eastern: the evening peak plus a daytime slot.
  - Until Oct 31 that's 11:30 p.m., 5:30 a.m. and 7:30 a.m. IST.
  - From Nov 1 (US daylight saving ends) it's 12:30 a.m., 6:30 a.m. and 8:30 a.m. IST.
  - After 28 days we switch to Studio's "When your viewers are on YouTube" report.
- **How:** Buffer's free plan (official YouTube API partner) publishes from a queue of up to 10 posts.
  The agent keeps that queue full (about 3 days) and the rest of the week's Shorts ready on disk, so a
  missed run never breaks the schedule.
- **Metadata:**
  - **Title:** 60 characters or fewer, accurate curiosity.
  - **Description:** summary, sources, image credits, and 3 hashtags (`#history` plus two specific ones).
  - **Category:** Education.
  - **Settings:** not made for kids.
  - **AI disclosure:** only when a Short contains realistic AI imagery. None is planned; narration by a
    non-impersonating synthetic voice doesn't require it.
- **Anniversaries:** stories tied to "on this day" dates go out on the date (see `strategy/CALENDAR.md`).

## Originality safeguards (YPP review)

YouTube's July 2026 policy targets templated, mass-produced content, so every Short must be clearly original:

- Each script is written from primary and reputable secondary sources, with a claims table in its folder.
- Varied hooks, structures, series, and imagery. No two Shorts share a storyline.
- Project files (research, script, render manifest) are kept for every Short, to show in any appeal.
- No reused footage from other creators, no reading of text we didn't write.

## Growth levers, in order of expected impact

1. **Hooks and retention:** the first 2 seconds decide "viewed vs swiped". Test hook styles weekly.
2. **Topic selection:** feed the algorithm topics with proven curiosity (anniversaries, famous oddities),
   then follow the data to the series that convert.
3. **Series binge:** end some Shorts with a pointer to a related episode, and use playlists per series.
4. **Volume with quality:** about 190 Shorts by Day 100. Every one is fact-checked.
5. **Cross-posting (an optional extra in the owner checklist):** native, watermark-free Instagram Reels through Buffer.
6. **Community:** reply to real comments; turn good viewer questions into episodes.

## KPIs

| Metric | Healthy | Action if below |
|---|---|---|
| Viewed vs swiped away | 60%+ (winners 70–90%) | Rework hooks and first frames |
| Average percentage viewed | 80%+ | Tighten scripts, cut slow beats |
| Subscribers per 1,000 views | 2+ | Strengthen series identity and endings |
| Likes per 100 views | 4+ | Better payoffs |
| Views per Short (7-day median) | Rising week over week | Change topics or formats |

## Weekly experiments

One variable at a time, judged on at least 10 Shorts per arm:

- Hook style: statement vs question vs "number" hook.
- Length: 40 vs 50 seconds.
- On-screen hook text in the first 2 seconds vs none.
- Pacing: about 0.8 s of silence between beats (mostly Kokoro's own padding) vs about 0.4 s.
- Voice: `af_heart` vs a male narrator vs the voice-test winner.
- Posting time: 8 p.m. vs 6 p.m. Eastern.
- Title style: plain claim vs curiosity gap.

## Promotion rules

Allowed: native cross-posts, collaborations with other history creators (YouTube's Collab feature),
genuine participation in communities with self-promotion under 10%, and replies to comments.
Never: bought views or subscribers, sub-for-sub, engagement pods, bots, comment spam, misleading titles.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Rejected for "inauthentic content" | Sourced original scripts, varied series, saved project files, owner voice as fallback |
| A factual error goes viral | Two-source rule per claim, attribution for disputed details, quick correction via pinned comment |
| Copyright claim on an image | Only public-domain, CC0, or CC BY images, with credits in every description |
| Buffer or Cloudinary outage | 2–4 days of queue; manual Studio upload as a fallback |
| Laptop off or asleep at run time | The queue covers gaps; the run catches up when the Mac wakes |
| Views plateau | Weekly experiments; pivot series based on data by Day 30 |
