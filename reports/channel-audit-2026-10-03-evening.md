# History's Last Hours channel audit — 2026-10-03 22:02 IST

The owned YouTube Data API returned channel `UC6e6OB3iw3yp8JnnBYxLItA`,
**one public video, 10 channel views, and zero subscribers**. The only public
Short, Winton `v4rp0oWvgSI`, had four public video views and zero likes. The
Analytics API returned no per-video engaged-view or retention row for that
Short. Its available channel traffic-source row was `YT_CHANNEL: 6 views`;
there is no measured Shorts-feed sample to compare hooks, posting times, or
audience preferences yet.

The repaired Winton replacement and other pilots remain private drafts under
the editorial scheduling hold. The next meaningful growth test is a verified
release batch with comparable 24- and 72-hour metrics, followed by a decision
based on actual feed traffic. These numbers do not support a claim that the
topic or channel has failed, or that a particular upload time is best.

## Update — 2026-10-03 22:27 IST

A direct review of the public Winton upload found a material source problem:
at 19.66–23.18 seconds it states that almost none of the 250 children due on
the cancelled train survived the war. [Winton's family exhibition](https://www.nicholaswinton.com/exhibition/kindertransport)
qualifies its account with “It is thought” and describes deportation to camps;
the inspected [USHMM account](https://encyclopedia.ushmm.org/content/en/article/nicholas-winton-and-the-rescue-of-children-from-czechoslovakia-1938-1939)
does not give a survival count. The old upload was made private via the owned
YouTube Data API. A fresh `videos.list(part=status)` read returned `private`
for all six uploads; `channels.list(part=statistics)` returned **zero public
videos, 10 channel views, and zero subscribers**. The corrected Winton draft
omits the fate count and remains a local private review asset. The exact action
receipt is in `content/episodes/ep045/withdrawal.json`.

The Buffer API returned six recent `sent` posts and **zero queued posts** at
the 22:10 IST check. A direct, paginated `status: scheduled` query rechecked
the YouTube queue at 22:35 IST and still found **zero scheduled posts**. The
channel hold says that the queue must stay empty; the watchdog alerts if one
appears. The hold cannot stop a post already queued in Buffer. If one appears,
pause the YouTube queue in Buffer immediately and remove it there. The Mac
watchdog can use a Buffer response for up to two hours, so its alert is not an
instant queue stop.

A separate Modal slot watcher had no `status/` directory in its image, so it
now clones the current `main` branch through the existing authenticated deploy
key before attempting a failed-post resend. It pauses if the clone or hold read
fails. This watcher protection takes effect only after the updated Modal app
is deployed. The refreshed `analytics/2026-10-03.json` snapshot was taken at
16:57:09 UTC and contains no Winton per-video retention row.
