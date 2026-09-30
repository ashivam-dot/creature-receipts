# Faceless narrated Shorts: growth playbook and 15 pipeline upgrades

Written 2026-09-30. Builds on `YouTube-100-Day-Autopilot/youtube-studio/research/shorts-strategy.md`,
`strategy/STRATEGY.md`, `strategy/SCRIPT-RULES.md`, `strategy/PLAN-100.md`, and `pipeline/src/ytc/publish.py`.
It doesn't repeat what those already establish (YPP thresholds, the Feb 1, 2027 change to 20M, RPM by country, the
music revenue split, the 331M-Short vidIQ length study, and the Instagram and Facebook originality rules) unless new
evidence changes them.

**Evidence grades used below:** **[O]** official YouTube, Meta, or Buffer documentation; **[D]** a large dataset from a
creator-tools company (correlational, published by vendors); **[A]** anecdote or a single-channel claim. Most "magic
numbers" circulating in 2026 are [A] or unsourced, and I say so where it matters.

---

## Bottom line

1. **What YouTube actually ranks on is unchanged and simple:** whether people choose to watch or swipe away, then
   how long they stay (average view duration and percentage viewed), plus satisfaction signals (likes, surveys)
   [O: [Help 11914225](https://support.google.com/youtube/answer/11914225)]. There is **no official "viewed vs
   swiped" threshold**. The widely quoted "60% floor, 70–90% for winners" comes from one 2023 study of 5,400 Shorts
   [D: [Galloway](https://en.rattibha.com/thread/1646898356419981315)], and 2026 explainers explicitly call specific
   cutoffs informal ([Monitor YT](https://monitoryt.com/blog/youtube-shorts-algorithm),
   [Creator Essentials](https://www.creatoressentials.com/glossary/stayed-to-watch/)). YouTube's own advice is to
   compare a Short with your other Shorts of similar length. **Upgrade the pipeline to channel-relative benchmarks.**
2. **Views vs engaged views:** since Mar 31, 2025 a Shorts view counts from the first frame, including replays, and
   on Aug 24, 2026 every format moved to first-frame counting. The old definition is now "engaged views": staying
   past the initial seconds, **excluding loops**. Recommendations, CTR, AVD, retention, YPP eligibility, and earnings
   all stay on engaged or qualified views [O: [Blog](https://blog.youtube/inside-youtube/engaged-views-youtube-explained/),
   [Help 12220281](https://support.google.com/youtube/answer/12220281)]. So:
   - Loops inflate the public count and raise average percentage viewed past 100%, but **don't add paid or
     qualifying views**. Engineer loops for watch time and satisfaction, not for YPP arithmetic.
   - The Analytics API exposes `engagedViews`. **Stayed to watch ≈ engagedViews / views** for Shorts, which the
     pipeline already computes as "engaged share".
3. **Length:** vidIQ's July 2026 data (331M Shorts) shows like rate rising steadily with length, from 1.05% under
   15 s to 2.79% at 2–3 min. 45–59 s had the highest average views, and 2–3 min had the highest share of Shorts
   reaching 100K+, "but retention becomes much harder" [D: [vidIQ](https://www.linkedin.com/posts/vidiq_we-analyzed-331-million-youtube-shorts-published-activity-7478837949355388930-moa_)].
   **35–58 s stays the right default; add a 60–90 s test arm for story-type episodes.** Shorts revenue is split by
   engaged views, not minutes watched, so longer Shorts don't raise RPM; length only affects reach and subscribers.
4. **Cadence:** YouTube says there's no boost for uploading more [O: Creator Insider, already cited in the existing
   research]. Third-party 2026 guides converge on 1–3 a day for new channels [A/D:
   [FluxNote](https://fluxnote.io/guides/youtube-daily-upload-limit-shorts-2026),
   [ThumbnailMakerr](https://thumbnailmakerr.com/blog/how-many-youtube-shorts-per-day)]. There's a vivid [A] report
   of a channel that collapsed from 75K daily views to near zero after going from 3 to 5 a day
   ([Reddit](https://www.reddit.com/r/NewTubers/comments/1rsn8gg/from_75k_daily_views_to_nearly_zero_retention_is/)).
   Its causes are unproven; replies point to many small tests replacing fewer big pushes. **Volume only helps while
   per-Short engaged views hold.** Step-ups should be gated on the per-Short median, not only on engaged share.
5. **New since the existing research (Made on YouTube, Sep 23, 2026, and July 2026):**
   - **Shorts Series:** seasons and episodes with sequential playback, rolling out to YPP creators [O:
     [Blog](https://blog.youtube/news-and-events/made-on-youtube-creators-shorts-series-tv-features/),
     [TechCrunch](https://techcrunch.com/2026/09/23/youtubes-new-short-series-feature-brings-episodic-viewing-to-shorts/)].
   - **Video A/B testing of up to three cuts** ("which holds audience attention best") [O:
     [Blog](https://blog.youtube/news-and-events/innovation-youtube-era-made-on-viewers-creators/)]. One outlet says
     it arrives for Shorts in 2027 ([80.lv](https://80.lv/articles/youtube-adds-a-b-testing-for-video-cuts-expanding-studio-s-toolkit)).
   - **Posts are now recommended in the Shorts feed** [O: Blog, same post].
   - **Custom thumbnails for Shorts** (July 25, 2026): YPP first, desktop only, no A/B testing [O via
     [PPC Land](https://ppc.land/youtube-ends-2-year-wait-for-shorts-thumbnails-but-blocks-a-b-testing/)].
   - **Title and thumbnail Test & Compare still excludes Shorts** [O: [Help 13861714](https://support.google.com/youtube/answer/13861714)].
   - **The Related Videos link** is now officially promoted as the Shorts-to-long-form bridge, with a spoken or
     visual CTA and a long-form video whose first 5–10 seconds deliver the Short's promise [O:
     [Blog, Jul 14 2026](https://blog.youtube/creator-and-artist-stories/youtube-related-videos-traffic-guide/)].
   - **Auto-dubbing is open to all creators in 27 languages** (Feb 4, 2026) and "has no negative impact on your
     original video's discovery" [O: [Blog](https://blog.youtube/news-and-events/youtube-auto-dubbing-expressive-speech/)].
     Whether it applies to Shorts is unclear: a third-party summary says long-form only, so verify in Studio.
   - **YouTube Shopping affiliate** opened to YPP channels with 500+ subscribers (Mar 25, 2026), including the US and
     India [O: [Blog](https://blog.youtube/creator-and-artist-stories/youtube-shopping-expansion-500-subscribers/),
     [Help 13376398](https://support.google.com/youtube/answer/13376398)].
6. **AI and faceless risk:** the July 2026 clarification names three demonetizable buckets:
   - generic, repetitive, or template-based content;
   - unsatisfying or off-putting content;
   - AI personas giving health, legal, finance, or political advice.

   Channels with "too much" of any of them lose monetization
   [O via [TechCrunch](https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/),
   [Tubefilter](https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/)].
   YouTube's 2025 statement named "narrated stories and slideshows with only superficial differences and the same
   narration" as mass-produced [O via [ThePrint](https://theprint.in/world/youtube-cracks-down-on-inauthentic-content-with-monetisation-policy-update-what-new-guidelines-say/2691562/)].

   A synthetic voice over an original, researched script isn't a violation, and generic TTS doesn't need the AI
   label; only realistic, meaningfully altered or generated content does [O: [Help 14328491](https://support.google.com/youtube/answer/14328491)].
   Non-disclosure can lead to penalties, and YouTube auto-labels content carrying C2PA metadata. **The existential
   risk for an automated pipeline is looking templated, not using AI.**

---

## Evidence by question

### 1. How the 2025–2026 Shorts algorithm ranks

- **Signals [O]:** choose to view vs swipe away, AVD, percentage viewed, likes, dislikes, surveys, and "not
  interested". Comments and shares aren't named as ranking signals (Help 11914225). The Shorts player redesign
  (Jul 2026) retired public dislikes ([PPC Land](https://ppc.land/youtube-counts-views-from-the-first-frame-across-all-formats-on-august-24/)).
- **Engaged view [O]:** "viewers stayed to watch past the initial seconds, not including any loops". YouTube won't
  say how many seconds, because "it can vary across surfaces" ([Creator Insider video](https://www.youtube.com/watch?v=HI03HqWdX0k)).
  Practically, the first ~1–3 s decide the engaged view.
- **Benchmarks:**
  - [D] Galloway 2023: under 60% viewed-vs-swiped rarely performed; winners ran 70–90%.
  - [D] OpusClip, as reported by Creator Lane: Reels holding over 60% at 3 s out-reach those under 40% by 5–10x
    ([Creator Lane](https://creatorlanehq.com/blog/pattern-interrupts-when-they-backfire-2026)).
  - "APV above 80% expands reach past subscribers" circulates widely but is unsourced
    ([Aibrify](https://aibrify.com/blog/youtube-shorts-retention-curve-playbook)).
  - **Use them as rough guides; rank against your own trailing median.**
- **Loops:** APV over 100% is normal for looping Shorts [O: YouTube notes segment views can exceed video views].
  Loops add watch time but not engaged views.

### 2. Length

- Shorts can run up to 3 minutes (since Oct 2024). **Past 60 s, any active Content ID claim blocks the Short
  worldwide** [O: Help 15424877, already cited]. That's safe here, with public-domain and CC BY images and no
  licensed music.
- [D] vidIQ, Jul 2026: like rate climbs with length; 45–59 s has the best average views; 2–3 min has the best
  100K+ rate. [D] OpusClip, Apr 2026: 40% of 2.88M clips are 30–60 s (that's production volume, not performance;
  [Bytecap](https://www.bytecap.io/research/best-youtube-shorts-length)).
- **Decision:** 40–55 s stays the default. Test 60–90 s only for narrative series such as Mission Files, where a real
  story arc exists. Judge each length bucket against its own median, never across buckets (Bytecap and YouTube
  both advise similar-length comparisons).

### 3. Hooks, captions, pacing, music, loops

- **Hook:** the first frame acts as the thumbnail. Open inside the story, with no intro card or greeting. On-screen
  text and the spoken line should arrive together in the first second. OpusClip's 13.5M-clip analysis (Q1 2026)
  finds Shock/Surprise, Direct Address, and Question hooks at the top [D:
  [OpusClip](https://www.opus.pro/research/how-to-make-viral-video),
  [benchmarks](https://www.opus.pro/research/engagement-benchmarks-short-form)]. The existing hook-formula table
  already matches this.
- **Captions:** animated word-by-word captions appear in 78.6% of 13.5M clips [D:
  [OpusClip caption study](https://www.opus.pro/research/best-caption-strategy-short-form)]. Claims that captions
  add about 80% watch time are vendor-reported. OpusClip advises centre or upper-third placement to avoid platform
  UI. The existing style (2–3 words, highlighted current word) is right.
- **Pacing:** 2026 guides recommend a visual change every ~1.5–2.5 s [A:
  [Aibrify](https://aibrify.com/blog/youtube-shorts-retention-curve-playbook)]. The counter-evidence is that
  repeated interrupts habituate: "your 14th whoosh does nothing", so cut where the story turns [A: Creator Lane].
  Aim for motivated motion every ~2 s (a push-in, reframe, or overlay swap), with hard cuts at beats.
- **Music:** evidence is mixed.
  - A preregistered academic study of six data videos found no consistent engagement effect from background music
    ([paper](https://city-ref-test.eprints-hosting.org/id/eprint/37604/1/3772318.3791466.pdf)).
  - One creator test found a silent open beat a music open by 5.8 points of 15-second retention [A:
    [allin1panel](https://allin1panel.com/i-tested-intro-music-vs-no-music/)].
  - Audio Library tracks aren't claimed, and music doesn't cut your own pool share (existing research).
  - **Keep narration-first. A very low ambient bed is a test arm, not a default.**
- **Loops:** the last line flows into the first, and the last frame matches the first. That's already in
  SCRIPT-RULES; add automated seam checks.

### 4. Posting frequency and timing

- **Frequency:** no official boost for volume [O]. The 2026 consensus for a new channel is 1–3 a day, spaced so each
  Short gets its first test [A/D]. Vendor studies cite 12+ uploads a month and 30–80 uploads before traction
  (vidIQ; [tugan.ai summary](https://tugan.ai/blog/how-to-start-a-faceless-youtube-channel-with-ai)).
- **Case studies from 2026:** fast channels won on a **fresh, repeatable concept**, not volume. All [A], compiled by
  a tool vendor:
  - Bernard Films: history "What if…" Shorts, about 93.8K subscribers and 70M+ views from **19 Shorts** in 5 weeks
    ([Reddit](https://www.reddit.com/r/ReelFarmer/comments/1rlkw19/a_faceless_channel_got_93k_subs_70m_views_in_5/)).
  - Helix²: skeleton-anatomy Shorts, 238K subscribers and 119M views from 54 Shorts, with the owner reporting a
    $0.25 RPM ([AITuber](https://aituber.app/blog/skeleton-channel-case-study-million-views/)).
  - Wealth Mode Mentality: 300 to 66K subscribers in about 60 days from 75 Shorts
    ([Reddit](https://www.reddit.com/r/ReelFarmer/comments/1tjnqr7/how_a_faceless_youtube_channel_hit_66k_subs_in_2/)).
- **Timing:**
  - [D] Buffer, 1.8M videos (2026): Shorts peak 6–11 p.m. local; the best slots are Friday 4, 6, and 7 p.m.; the
    best days are Friday, Saturday, then Thursday; weekday afternoons (12–5 p.m.) are the weakest, except Friday
    ([Buffer](https://buffer.com/resources/best-time-to-post-on-youtube/)).
  - [D] SocialPilot, 301K videos: 12–3 p.m. and 7–9 p.m. ([RecurPost summary](https://recurpost.com/schedule-youtube-videos/best-time-to-post-on-youtube/)).
  - The current `SLOTS` puts the second Short at 2 p.m. ET, which is Buffer's weakest window.
- **Batching:** render ahead (the pipeline already keeps up to 14 days of stock), but don't publish in bursts.

### 5. Titles, descriptions, hashtags, playlists, and long-form bridges

- **Search:** Shorts surface in YouTube search, Shorts shelves, and Google's mobile Shorts carousel. YouTube says
  Shorts are ranked **primarily on performance, not metadata**, so metadata matters mainly for search and for
  seeding the right first audience ([CRKLR](https://crklr.com/news/how-to-optimise-youtube-shorts-for-seo/),
  [TubeAI](https://learn.tubeai.app/blog/youtube-seo-metadata-optimization/youtube-shorts-metadata-seo-discoverability)).
  Practical rules:
  - front-load the searchable entity in about the first 40 characters of the title;
  - put the keyword in the first description sentence (the first ~125 characters show in previews);
  - use 3–5 specific hashtags (more than 60 and YouTube ignores all of them). `#shorts` isn't needed.
- **Pinned comments:** links there aren't clickable in Shorts. The Data API can post a comment but **can't pin it**,
  so pinning is a Studio action.
- **Related video:** the one clickable bridge [O: Blog, Jul 2026]. It can point to a long video, a live stream, or
  another Short on the same channel. Studio doesn't report it as its own traffic source
  ([NBK Social](https://www.nbksocial.com/journal/convert-youtube-shorts-views-into-long-form-growth/)). Click-rate
  claims from 1.5% to 6.8% are vendor numbers, not YouTube telemetry. I found no Data API field for it, so it's set
  in Studio.
- **Compilations of your own Shorts** are generally allowed but must add significant value:
  - YouTube Support told a creator reused own content needs "substantive modifications… unique context,
    commentary, or engaging storytelling" and must not be "uploaded in an automated, spammy manner" [O-ish, a
    support email quoted on [Reddit](https://www.reddit.com/r/PartneredYoutube/comments/1vt6278/follow_up_youtube_supports_stance_on_making_a/)].
  - Plain stitch-together compilations risk the repetitive and inauthentic rules.
  - Payoffs: watch hours count toward the 4,000-hour path (a hedge against the 20M Shorts bar from Feb 2027),
    long-form RPM in Education is many times Shorts RPM, and long-form gets auto-dubbing and title A/B testing.
  - Caveat: Shorts audiences don't transfer automatically, and mismatched pacing hurts long-form
    ([EvolvedLotus](https://blog.evolvedlotus.com/blog/2026-06-17-youtube-shorts-vs-long-form-which-strategy-wins-in-2026/)).
    An 18,000-channel study found mixing helps most in educational niches
    ([ytgrowth](https://ytgrowth.io/blog/shorts-vs-long-form)).

### 6. Subscriber conversion

- Conversion is mostly an upstream effect of completion: viewers who reach the end are the ones who subscribe.
  Specific, series-based reasons beat a generic "subscribe"
  ([Retensis](https://retensis.com/blog/youtube-shorts-subscriber-conversion-rate-2026),
  [Virvid](https://virvid.ai/blog/turning-shorts-views-into-subscribers-2026)).
  - The "series convert 67% better" figure remains unverified.
  - Benchmarks of 0.5% "good" and 1% "strong" per view are vendor claims. Public channel math earlier gave 0.15–0.36%.
- Levers: named series with visible episode numbers, Shorts Series once in YPP, series playlists as channel-page
  sections, a channel description that states the promise, and the related link to the next episode. End screens
  don't exist on Shorts. A channel trailer only plays for non-subscribers on the channel page, so it's low leverage
  for a Shorts-only channel.

### 7. Cross-posting (Buffer free plan)

- **Buffer free [O]:** 3 connected channels (a Start Page counts as one), 10 scheduled posts per channel at a time,
  refilling on publish, and a lifetime limit of 8 unique channels per network
  ([Pricing](https://buffer.com/pricing), [Help](https://support.buffer.com/en-us/articles/connecting-your-channels-to-buffer-HvWLgAJvL9)).
  A third-party guide says the API allows 1 key and 3,000 requests a month
  ([use-apify](https://use-apify.com/blog/buffer-free-plan-guide)). Instagram needs a Business or Creator account,
  and TikTok a business profile. **With YouTube taking one slot, the free plan fits Instagram and TikTok; Facebook
  needs Meta's own Instagram-to-Facebook Reels sharing, not Buffer.**
- **Identical content is fine across platforms, as long as it's your own and clean:**
  - Platforms don't share fingerprints. What gets penalized is other apps' watermarks and unlicensed platform audio.
  - Instagram requires "no visible watermarks" for recommendation, and non-originals lose reach
    [O: [Instagram](https://creators.instagram.com/blog/recommendations-and-originality)].
  - Facebook doubled views of original Reels in the second half of 2025 and deprioritizes stitched or merely
    narrated third-party clips [O: [Meta, Mar 2026](https://about.fb.com/news/2026/03/rewarding-original-creators-on-facebook/)].
  - Facebook Content Monetization is invite-only, and qualified views exclude repeats and views under 5 s [O:
    [Facebook](https://creators.facebook.com/blog/new-tips-to-help-you-earn-on-facebook-content-monetization/)].
- **Captions:** vary them per platform rather than pasting the same one everywhere [A: Socialync].

### 8. Monetization beyond the Shorts ad share (all compatible with a faceless channel)

| Step | Requirement | Fit for a faceless space channel |
|---|---|---|
| YPP fan funding (memberships, Super Thanks, Super Chat) | 500 subscribers, 3 uploads in 90 days, and 3M Shorts views in 90 days [O] | Low revenue, but it's a YPP entry. Whether it locks in the pre-2027 ads bar is unverified |
| YouTube Shopping affiliate | In YPP, 500+ subscribers, based in the US or India, among others [O] | Only on Shorts that genuinely feature a product (telescopes, star maps, books). Tagging unrelated products breaks the guidelines and can cost access |
| Long-form ads | 4,000 watch hours in 12 months, or the Shorts path | A higher-RPM hedge; compilations with added value (upgrade 7) |
| Affiliate links (Amazon Associates and similar) | Your own program rules | Description links aren't clickable on Shorts; put them in long-form descriptions only |
| Facebook Content Monetization | Invite-only [O] | Register interest once the Page has original Reels |
| Brand deals (BrandConnect) | YPP | Later |

### 9. Staying safe as an AI-narrated channel

- The current policy targets **templating and repetition regardless of how content was made**. Allowed: AI used "to
  enhance storytelling", original research, and distinct storylines [O].
- Enforcement is channel-level ("too much" of the bad buckets), so a single weak Short isn't fatal, but a uniform
  catalog is.
- **Disclose realistic AI imagery only.** The pipeline's `synthetic_media` flag and the "Narrated with a synthetic
  voice" line are correct and more than required. Never add C2PA-tagged AI images without setting the flag, because
  YouTube auto-detects C2PA.
- Keep project files for appeals (already in place). The owner's own voice stays the strongest fallback.

---

## 15 prioritized upgrades

Impact scale: **H** = likely to move views or YPP odds materially, **M** = a solid lift, **L** = cheap hygiene.
Effort assumes the existing `ytc` package (Python, FFmpeg via `ff.py`, captions in `captions.py`, analytics in
`youtube.py`, scheduling in `publish.py`, orchestration in `auto.py`).

### 1. Channel-relative scoring and a hook "bandit" (H)

- **What:** replace fixed KPI thresholds such as "60%+ viewed" with each Short's percentile against the trailing
  30-Short median in the same length bucket. Automatically shift future scripts toward winning hook formulas,
  first-frame types, and series.
- **Why:** YouTube publishes no universal benchmark and advises comparing similar-length Shorts [O]. The popular
  thresholds are one 2023 dataset [D]. Growth in this niche comes from a few breakouts (Cosmic Lens, Bernard Films),
  so allocating attempts to what works compounds.
- **How:**
  - Add `hook_formula`, `first_frame_kind` (`object` | `diagram` | `card`), `length_bucket`, and `voice` to
    `short.yaml`; the writer fills them.
  - In `youtube.stats`, which already pulls `views`, `engagedViews`, and `audienceWatchRatio` at 0/5/10%, compute:
    - `stayed = engagedViews/views`;
    - `hold5` = retention at 5%;
    - `apv`;
    - `subs_per_1k`;
    - a composite z-score within the bucket.
  - In `auto.py`, run Thompson sampling (a Beta posterior on "beat the median") per hook formula and series. Keep a
    floor of 10% exploration per arm, and let the posterior weights drive `writer.py`'s formula choice.
  - Use each Short's 72-hour numbers, and re-score at 7 days.
- **Impact:** H. It turns the weekly manual experiments into continuous ones.

### 2. Frame-zero hook enforcement (H)

- **What:** guarantee that at t = 0.00 s the Short shows its strongest real image already in motion, with the
  `hook_text` overlay fully visible (no fade-in) and narration starting within 150 ms.
- **Why:** engaged views, which drive distribution and pay, are decided in the "initial seconds" [O]. A 3-second
  hold above 60% goes with 5–10x reach [D, OpusClip via Creator Lane]. Intro silence and fade-ins cost early
  retention [A].
- **How:**
  - `check.py`: run `ffmpeg -af silencedetect=n=-40dB:d=0.1` and fail if the first non-silence is after 0.15 s.
  - Extract frame 0. Fail if its mean luma is under ~40 or its contrast (standard deviation) is low, which catches
    black or gradient openers, or if `hook_text` isn't present. `captions._hook_event` should start at 0 with no
    `\fad`.
  - `render.py`: trim the TTS leading pad, and start beat 1's Ken-Burns move at 1.03x scale so it's moving on frame 0.
- **Impact:** H on stayed-to-watch. It's cheap.

### 3. Loop seam and tail trim (M–H)

- **What:** make the last ~0.5 s hand off seamlessly to frame 0, and cut dead air at the end.
- **Why:** loops raise watch time and APV past 100%, but don't add engaged views [O]. A clean seam also avoids the
  "finished" cue that prompts a swipe [A].
- **How:**
  - Enforce the loop line's `visual: {reuse: 1}` onto the hook image, ending on the same framing as frame 0 (reverse
    the motion so the last frame equals the first).
  - Trim trailing silence to ≤ 0.25 s, and add a 60 ms audio crossfade at the seam.
  - `check.py`: compute SSIM between the last and first frames (`ffmpeg -lavfi ssim`) and warn under 0.6. Compare the
    transcripts of the last and first lines to keep the rule against dangling endings.
- **Impact:** M–H on APV and rewatches. It feeds the ranking, not the 10M count.

### 4. Gate cadence on per-Short output, not only engaged share (H, protective)

- **What:**
  - Start at 2 a day for Days 1–14. Step to 3 only if the 7-day median engaged views per Short is flat or rising
    and at or above the prior 7 days.
  - Step to 4 under the same test. Cap at 4 until the channel passes 10K subscribers.
  - Auto-step down one level if the per-Short median falls 30% or more over 10 Shorts.
- **Why:** there's no algorithmic volume boost [O]. The 2026 new-channel consensus is 1–3 a day [A/D], and there's a
  documented crash after 5 a day [A]. The current `PACE_STEPS` checks engaged *share*, which can stay flat while
  views per Short fall, the cannibalization pattern.
- **How:** in `auto.py`, replace the share-only test with `median(engagedViews, last 10) >= 0.9 * median(prior 10)`
  and `share >= 0.9 * prior`. Add the step-down rule. Keep the 14-day render buffer, so fewer posts only grows stock.
- **Impact:** H as insurance. It also buys time for the writer to spend on quality per Short.

### 5. Retime `publish.SLOTS` to evidence (M)

- **What:** use `SLOTS = (19:00, 21:30, 12:30, 16:30, 22:30)` ET, best first. Add a weekday weight: on Thursday,
  Friday, and Saturday, use one extra slot when stock allows (Friday 16:30 is Buffer's top slot). Keep at least
  2.5 h between Shorts.
- **Why:** Buffer's 2026 data (1.8M videos) puts Shorts peaks at 6–11 p.m. and Friday 4–7 p.m., with weekday 12–5
  p.m. weakest [D]. SocialPilot adds 12–3 p.m. [D]. The current second slot, 14:00, falls in Buffer's weakest window.
- **How:** edit the tuple. In `next_slots`, allow `per_day + 1` when `day.weekday() in (3, 4, 5)` and the stock is
  over 7 days. After Day 28, the nightly job pulls the "when your viewers are on YouTube" data. It isn't in the
  public API, so the owner exports a CSV, or you use the `day` × `views` split. Then re-rank slots by median 24-hour
  engaged views per slot.
- **Impact:** M (typically a 10–20% first-day difference; a vendor estimate).

### 6. Originality guard against templating (H, existential)

- **What:** before publishing, reject a Short that's too similar to the last 50 in script, structure, or visual
  sequence. Rotate structural templates.
- **Why:** the July 2026 policy demonetizes channels with "too much" generic, repetitive, template-based content,
  including "narrated stories and slideshows with only superficial differences and the same narration" [O].
  Reviewers judge the whole channel [O]. A one-voice, one-caption-style, one-structure automated channel is exactly
  the profile at risk.
- **How:**
  - Embed each script with the pipeline's existing LLM or SigLIP stack (any sentence-embedding model on CPU works).
    Reject when cosine similarity to any of the last 50 is ≥ 0.85, or to the same series' last 10 is ≥ 0.8.
  - Keep a `structure` enum (chronological story, countdown, myth vs fact, scale ladder, "what if", Q&A) and prevent
    more than 2 identical structures in a row.
  - Hash the first-frame image and the beat-image sequences to block recycled visuals.
  - Log the checks into each episode's `research.md` as appeal evidence.
- **Impact:** H. It protects the entire YPP outcome.

### 7. A weekly long-form "episode" built from a series, with new value (H for revenue and the YPP hedge)

- **What:** each week, an 8–12 minute horizontal video per top series, such as "Mission Files: 8 missions that
  almost didn't come home". It reuses the week's researched beats, but with:
  - new connective narration (about 40% or more new script: context, transitions, "what happened next");
  - chapters;
  - a new 16:9 layout;
  - a researched segment not in any Short.

  Every Short in that series sets its Related video to it.
- **Why:**
  - Watch hours count toward the 4,000-hour path, the only realistic hedge if the Shorts 90-day bar rises to 20M on
    Feb 1, 2027.
  - Long-form Education RPM is roughly 30x Shorts RPM (existing research).
  - Long-form gets Test & Compare and auto-dubbing in 27 languages [O].
  - YouTube's Jul 2026 guide makes the related link to long-form the recommended bridge [O].
  - Own-content reuse is allowed only with substantive new value, not automated stitching [O-ish, a Support email].
  - Mixing helps most in educational niches [D].
- **How:**
  - `render.py` adds a `--format long` path: 1920x1080, with the image full-bleed or as a framed print over a blur
    (already implemented for wide images).
  - Captions go off-burn; upload an SRT instead.
  - Chapters come from beat groups, and the first 10 s restate the Short's promise (YouTube's advice).
  - The writer produces a new "bridge script", held to the claims-table rule.
  - `check.py` computes the fraction of new narration and fails under 40%.
  - Uploads go through Buffer's YouTube channel if it supports long-form; otherwise use the Data API
    (`videos.insert`, 1,600 quota units, fine at 1–2 a week).
- **Impact:** H on revenue potential and YPP resilience. The subscriber effect is uncertain.

### 8. Motivated micro-motion every ~2 seconds (M)

- **What:** within each beat, add a change every 1.8–2.5 s: a push-in to the named detail, a focus shift, a caption
  color swap, or an overlay of a number. Use hard cuts only at beat boundaries. Cap SFX as SCRIPT-RULES does (at
  most 3 whooshes).
- **Why:** 2026 guides target a visual change every 1.5–2.5 s [A]. Habituation evidence argues against
  unmotivated interrupts [A]. Beats now average 5–7 s, with one close-up cut at about 3 s or more.
- **How:** in `render.py`, split any beat over 3.5 s into sub-shots of about 2.2 s:
  - shot A: the full frame with the current motion;
  - shot B: a `box` close-up (the pipeline already supports `box`);
  - shot C: a reverse drift.

  Use `zoompan` or `crop` expressions with ease-in-out. Report `max_static_seconds` in `check.py` and warn over 3.0 s.
- **Impact:** M on mid-video retention.

### 9. A 60–90 s length test arm for story series (M)

- **What:** 20% of Mission Files and Near Misses scripts target 65–85 s (170–210 words); everything else stays 40–55 s.
- **Why:** vidIQ's Jul 2026 data shows engagement rising with length and 2–3 min having the best 100K+ rate, with
  45–59 s best on average [D]. The 60 s claim-block rule doesn't bite on this pipeline's rights-clean assets [O].
- **How:** add a `length_bucket` to the spec. Widen the `ytc check` bounds per bucket (35–58 s by default, 60–90 s
  for the test). Score within bucket via upgrade 1. Kill the arm after 20 Shorts if its bucket-relative median
  engaged views and subscribers per 1,000 views both lag.
- **Impact:** M, with upside for subscriber conversion. It doesn't raise RPM per view.

### 10. Search and text layer: spoken keyword, safe-zone captions, SRT upload (M)

- **What:**
  - Say the subject's searchable name within the first 5 s.
  - Keep burned captions in the band from 55% to 75% of frame height, clear of the right-hand action rail and the
    bottom title and handle area.
  - Upload the exact SRT as a caption track.
- **Why:** Shorts rank in YouTube and Google search. Titles, descriptions, and speech seed topic matching,
  although performance dominates [A/D]. Captions need to be readable over the platform UI [D, OpusClip].
- **How:**
  - `SCRIPT-RULES`: the hook or beat 2 must contain the primary entity (the writer checks it).
  - `captions.py`: add an `MarginV` preset for the safe band, and a 6–8 px outline.
  - After Buffer publishes, a job in `youtube.py` calls `captions.insert` with `write_srt` output (400 units; at
    4 a day that's 1,600 of the 10,000 daily units).
- **Impact:** M in search long-tail over months. L in the feed.

### 11. Search-demand titles and first description lines (L–M)

- **What:** pick title phrasing from real queries. Front-load the entity in the first 40 characters, and repeat the
  primary keyword in the first description sentence.
- **Why:** titles truncate at about 40 characters in Shorts placements, and the first ~125 characters of the
  description appear in previews [A/D]. Shorts can't be title-A/B tested [O], so pick the best phrasing up front.
- **How:** query YouTube autocomplete (`suggestqueries.google.com/complete/search?client=firefox&ds=yt&q=<entity>`,
  keyless and public) and Wikipedia pageviews (already in `growth.py`). Have the LLM choose among three accurate
  titles that contain a top suggestion. Keep the existing honesty rules and at most 3 hashtags; drop any `#shorts`.
- **Impact:** L–M, and cheap.

### 12. Series identity: episode numbering, Shorts Series readiness, next-episode links (M–H for subscribers)

- **What:**
  - Every Short carries a small persistent series tag, for example "MISSION FILES · #14", in a top corner from
    frame 0.
  - Descriptions start with the series line.
  - The related video points to the next episode in the same series (or to the long-form episode from upgrade 7).
  - On YPP approval, bulk-organize into Shorts Series seasons.
- **Why:** Shorts Series (Sep 23, 2026) gives sequential playback, but only in YPP [O]. Named series give a concrete
  reason to subscribe [A/D]. The related link is the only clickable bridge [O].
- **How:**
  - Track `episode_no` per series in `auto.py`, and render the tag in `plates.py` or ASS.
  - I found no Data API field for the related video, so `auto.py` writes a daily "Studio to-do" list
    (Short → target) to the report, and the owner applies it in about 2 minutes. Alternatively, drive the Studio
    web UI in a background tab under the headless-automation rule.
  - Playlists already fill automatically (`file_into_playlists`).
- **Impact:** M–H on subscribers per 1,000 views.

### 13. A specific, loop-safe subscribe CTA, as a test arm (M)

- **What:** in 50% of Shorts, show a visual-only end strip over the final ~1.2 s, for example "New Mission File
  daily · Follow", with no spoken CTA, so the audio loop stays intact. Compare subscribers per 1,000 views against
  the no-CTA arm.
- **Why:** content-specific CTAs beat generic ones, and conversion lives at the end of the video [A/D]. The loop
  rule rules out a spoken CTA at the end. Evidence strength is weak, so test it.
- **How:** use an ASS overlay event in `captions.py` keyed by `cta_arm`. `auto.py` alternates arms and scores via
  upgrade 1.
- **Impact:** M if it wins. It's reversible.

### 14. Native cross-posting to Instagram Reels and TikTok, and Facebook through Meta's own sharing (M)

- **What:**
  - Turn on the existing `crosspost_scheduled` for Instagram and TikTok (the 2 remaining Buffer free channels).
  - Enable Instagram-to-Facebook Reels sharing in Meta Accounts Center, which needs no third Buffer channel.
  - Use per-platform captions, and post in each platform's peak window.
- **Why:**
  - Own, clean masters aren't penalized. Watermarks and non-original reposts are [O: Instagram, Meta].
  - Buffer free allows 3 channels with 10 queued each [O].
  - It gives more reach, a second shot at Shorts YouTube passed over, and a path to Facebook Content Monetization
    (invite-only) [O].
- **How:**
  - `publish.crosspost`: add caption variants. Instagram gets a 1–2 line hook, 3–5 hashtags, and "sources in
    comments". TikTok gets a question plus 3 hashtags.
  - Schedule Instagram at 18:00 and TikTok at 19:00–22:00 in the audience time zone (Buffer 2026 [D]).
  - Leave AI labels off unless `synthetic_media` is set.
  - Watch Buffer's API budget, about 3,000 requests a month [A]: batch queue refills and cache `channels()`.
- **Impact:** M. It's audience diversification rather than YouTube growth.

### 15. A monetization-ladder tracker, plus localized metadata and dubbing for long-form (M)

- **What:** a nightly eligibility panel:
  - subscribers;
  - 90-day engaged Shorts views against the 3M and 10M bars;
  - days left before Feb 1, 2027;
  - the watch-hours trend from upgrade 7;
  - reminders when fan funding (500 subscribers and 3M views) and Shopping become available.

  Also add `localizations` (es, pt, hi, de, fr titles and descriptions) to long-form uploads, and turn on
  auto-dubbing for them.
- **Why:**
  - YPP timing is the channel's biggest money decision (existing research).
  - Shopping opened to YPP channels with 500+ subscribers, US and India included [O].
  - Auto-dubbing is free to all and doesn't hurt the original's discovery [O].
  - Translated titles and descriptions are YouTube's own tip for better dub performance [O].
- **How:**
  - `youtube.stats` already returns `last_90_days.engagedViews`. Add a `watch_hours_12m` query
    (`estimatedMinutesWatched` over 365 days, long-form filter) and render both in the daily report.
  - Localizations go through `videos.update` with `localizations` (50 units).
  - Shopping: only tag products a Short genuinely features (a "what a $200 telescope shows you" series). Never
    blanket-tag.
- **Impact:** M on revenue timing. It avoids missing the pre-February window.

---

## What not to change

- Keep **no licensed music**, with public-domain and CC BY imagery only (the claim-block and revenue logic still
  hold). Treat a very quiet, ducked Audio Library bed as a later test arm; the evidence is mixed.
- Keep the **2-source claims table, the disclosure line, and saved project files**. They're what separates this
  channel from the "templated AI" bucket the July 2026 policy targets.
- Don't re-upload underperforming Shorts with small edits. It's the "superficial differences" pattern.
- Don't buy engagement, and don't use "comment to win" prompts (existing rules).

## Open questions to verify live

- Whether auto-dubbing now covers Shorts. The Feb 2026 blog is silent; one third-party says long-form only.
- Whether Shorts Series reaches non-YPP channels later, and whether the Data API ever exposes the related video or
  series fields.
- When "video A/B testing of cuts" reaches Shorts; one outlet says 2027. When it arrives, render three hook variants
  per Short. Upgrade 2 already produces the building blocks.
- Buffer's current API request limit on the free plan. The 3,000-a-month figure is third-party.
