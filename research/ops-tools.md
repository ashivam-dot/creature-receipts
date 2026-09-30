Open source is strong for most jobs but weak for outlier-finding and A/B testing, where free SaaS or YouTube's own tool wins. Two platform rules matter more than any tool:
- Uploads from an unaudited Google Cloud project [stay private](https://developers.google.com/youtube/v3/docs/videos/insert), so apply for YouTube's API audit on day one.
- TikTok's unaudited apps can [only post privately](https://developers.tiktok.com/doc/content-sharing-guidelines).

Repo data is from `gh api` on 2026-09-26. "Comm." means the license allows commercial use; platform terms still apply.

### 1. Niche discovery and outliers
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [kirbah/mcp-youtube](https://github.com/kirbah/mcp-youtube) | 29 | 2026-09-11 | MIT | Yes | Agent-ready; has an outlier-channel finder (needs MongoDB) |
| [ZubeidHendricks/youtube-mcp-server](https://github.com/ZubeidHendricks/youtube-mcp-server) | 577 | 2026-08-08 | MIT | Yes | Read-only search with channel-size filters |
| [yuben-app](https://github.com/shkuratovdesigner/yuben-app) | 16 | 2026-09-21 | MIT | Yes | Local outlier app; created July 2026 |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 194k | 2026-09-16 | Unlicense | Yes | DIY: video views ÷ channel median |

No outlier repo has more than about 30 stars.
- **Free tiers:** [1of10](https://1of10.com) (outlier search, 3 tracked channels), [ViewStats](https://www.viewstats.com) (per-video outlier scores), [Social Blade](https://socialblade.com), [Playboard](https://playboard.co) (5 reports/day), [vidIQ](https://vidiq.com) and [TubeBuddy](https://www.tubebuddy.com) (both limited).
- **Paid:** [NexLev](https://www.nexlev.io) (€13–42/mo), 1of10 Basic ($29/mo), vidIQ Boost ($199/yr).

### 2. Keyword and topic research
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| YouTube autocomplete endpoint* | – | tested today | Unofficial | ToS risk | Real YouTube queries |
| [trendspyg](https://github.com/flack0x/trendspyg) | 50 | 2026-09-10 | MIT | Yes | Maintained pytrends successor with CLI and MCP; Explore needs Chrome |
| [pytrends-modern](https://github.com/yiromo/pytrends-modern) | 66 | 2026-09-05 | MIT | Yes | Revives pytrends' API |
| [trends-checker](https://github.com/akvise/trends-checker) | 392 | 2026-04-08 | MIT | Yes | Rate-limited CLI |

\*`suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=en&gl=US&q=…`. Without `gl=US` it returned India-localized suggestions.

The official [Google Trends API](https://developers.google.com/search/apis/trends) is still an application-only alpha. [pytrends](https://github.com/GeneralMills/pytrends) (3.7k★, Apache-2.0) is archived and its trending methods return 404. [AnswerThePublic](https://answerthepublic.com)'s free tier gives 3 searches/day.

### 3. Audience research
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [BERTopic](https://github.com/MaartenGr/BERTopic) | 7.9k | 2026-09-24 | MIT | Yes | Clusters comments into labeled topics |
| `commentThreads.list` API | – | – | API terms | Yes | 1 quota unit per 100 comments; compliant |
| [youtube-comment-downloader](https://github.com/egbertbouman/youtube-comment-downloader) | 1.3k | 2026-07-30 | MIT | Yes | No quota, but it scrapes (ToS risk) |
| [PRAW](https://github.com/praw-dev/praw) | 4.3k | 2026-09-25 | BSD-2 | Code only | New Reddit API apps [need approval](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy) (policy since Nov 2025); the free tier is non-commercial |

Reddit fallback: public RSS via [reddit-rss-mcp](https://github.com/ninjackster/reddit-rss-mcp) (14★, MIT). It returns no scores.

### 4. Format mix and packaging
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| Data API `playlistItems` + `videos.list` | – | – | API terms | Yes | Lengths, dates, titles, thumbnails; 1 unit per 50 videos (yt-dlp scrapes instead) |
| [open_clip](https://github.com/mlfoundations/open_clip) | 14.2k | 2026-09-08 | MIT (check weight licenses) | Yes | Thumbnail embeddings for clustering; BERTopic also has an image backend |
| [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) | 8.4k | 2026-09-10 | MIT | Yes | Analyze competitors' hooks (ToS risk) |

Skip CTR or title-performance predictors. The repos I found have 0–12 stars and no validation, and no public CTR ground truth exists. Use your own CTR data and native tests.

### 5. Channel naming
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [sherlock](https://github.com/sherlock-project/sherlock) | 92.7k | 2026-09-25 | MIT | Yes | Standard handle check |
| [maigret](https://github.com/soxoj/maigret) | 38.0k | 2026-09-25 | MIT | Yes | Covers more sites; slower |
| [user-scanner](https://github.com/kaifcodec/user-scanner) | 5.0k | 2026-09-25 | MIT | Yes | Checks 880+ platforms; has an MCP server |
| [domain-check](https://github.com/saidutt46/domain-check) | 309 | 2026-05-14 | MIT/Apache-2.0 | Yes | Bulk domain lookup across 1,200+ TLDs |

Generate names with an LLM, then filter. A handle these tools don't find may still be taken; only Studio confirms it. For trademarks, search [USPTO](https://tmsearch.uspto.gov), the [WIPO Global Brand Database](https://branddb.wipo.int), and [IP India](https://tmrsearch.ipindia.gov.in/tmrpublicsearch/) (free, but now needs an OTP login) in Nice classes 9, 38, and 41.

### 6. Title and thumbnail testing
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [YouTube Test & Compare](https://support.google.com/youtube/answer/13861714) | – | – | Native | Free | Titles supported since the December 2025 global rollout. Up to 3 variants; long-form, desktop, and Advanced-features channels only; picks the winner by watch time |
| TubeBuddy A/B | – | – | SaaS | Paid (Star tier) | Also tests descriptions and tags |
| [thumbnail-tester extension](https://github.com/bdebon/youtube-thumbnail-tester-chrome-extension) | 131 | 2025-09-17 | MIT | Yes | Previews how a title and thumbnail look in the YouTube feed |

I found no API for Test & Compare, so the owner runs it in Studio. Rotating thumbnails through the API isn't a real A/B test.

### 7. Analytics and reporting
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [analytix](https://github.com/parafoxia/analytix) | 45 | 2026-05-06 | BSD-3 | Yes | Thin Analytics API SDK that returns DataFrames |
| [google-api-python-client](https://github.com/googleapis/google-api-python-client) | 8.9k | 2026-09-24 | Apache-2.0 | Yes | Official client; covers the Reporting API |
| [Evidence](https://github.com/evidence-dev/evidence) | 7.0k | 2026-09-25 | MIT | Yes | SQL-and-markdown dashboards |

Simplest daily report is a cron job running one Python script:
1. Pull per-video views, watch time, subscribers, and revenue for the newest complete day with analytix. Data lags by about a day or more.
2. Add impressions and CTR from the Reporting API's [`channel_reach_basic_a1`](https://developers.google.com/youtube/reporting/v1/reports/channel_reports) CSV. The Analytics API lacks these (checked its metrics docs).
3. Email the result as Markdown.

Publish the OAuth app to Production, because refresh tokens in Testing mode expire after 7 days.

### 8. Automation and orchestration
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [pauling-ai/youtube-mcp-server](https://github.com/pauling-ai/youtube-mcp-server) | 21 | 2026-09-04 | MIT | Yes | 40 tools covering upload, metadata, analytics, and reporting; created February 2026 |
| [youtube-uploader-mcp](https://github.com/anwerj/youtube-uploader-mcp) | 55 | 2026-09-20 | MIT | Yes | Upload, scheduling, thumbnails, and captions |
| [n8n](https://github.com/n8n-io/n8n) | 206k | 2026-09-25 | [Sustainable Use](https://docs.n8n.io/privacy-and-security/sustainable-use-license) | Own channel only | Native YouTube upload and update node; [377 YouTube templates](https://n8n.io/integrations/youtube/). The license bars reselling or hosting it for others |
| [Activepieces](https://github.com/activepieces/activepieces) | 24.7k | 2026-09-25 | MIT (non-EE) | Yes | Fully open-source alternative to n8n |

Avoid [jayadevrana/youtube-mcp-server](https://github.com/jayadevrana/youtube-mcp-server) (paid source-available) and [darkzOGx/youtube-automation-agent](https://github.com/darkzOGx/youtube-automation-agent) (3.8k stars, but its README header shows what looks like a pump.fun token address).

### 9. Cross-posting
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [Postiz](https://github.com/gitroomhq/postiz-app) | 36.3k | 2026-09-25 | AGPL-3.0 | Yes | 30+ networks including Reels, TikTok, Facebook, and X, plus an agent CLI. Runs in Docker with Postgres, Redis, and Temporal |
| [BrightBean Studio](https://github.com/brightbeanxyz/brightbean-studio) | 2.4k | 2026-09-25 | AGPL-3.0 | Yes | Lighter (Django + Postgres); no X |
| [Mixpost Lite](https://github.com/inovector/mixpost) | 3.7k | 2026-03-16 | MIT | Yes | Facebook Pages, X, and Mastodon only; Instagram, TikTok, and YouTube need Pro ($299) |

With self-hosting you register every platform's developer app yourself. TikTok's app audit rejects personal-use apps. X charges $0.015 per post, or $0.20 with a link. Avoid uploaders that use cookies or private APIs ([social-auto-upload](https://github.com/dreammis/social-auto-upload) 15.2k★, [instagrapi](https://github.com/subzeroid/instagrapi) 6.8k★), since they risk account bans.

### 10. Curated lists
| Tool | ★ | Push | License | Comm. | Why |
|---|---|---|---|---|---|
| [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | 95.5k | 2026-09-23 | MIT | Yes | Find YouTube and social MCP servers |
| [awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates) | 25.6k | 2026-09-12 | CC-BY-4.0 | Yes | Workflows |
| [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | 322k | 2026-09-25 | CC-BY-SA-3.0 | Yes | Self-hosted alternatives |
| [awesome-faceless](https://github.com/sasharun/awesome-faceless) | 31 | 2026-07-11 | CC0 | Yes | The only creator-specific list; small |

### Recommended toolkit
| Job | Pick |
|---|---|
| 1 Niche | kirbah/mcp-youtube, with 1of10's free tier as a cross-check |
| 2 Keywords | Autocomplete (`gl=US`) plus trendspyg |
| 3 Audience | `commentThreads` API plus BERTopic |
| 4 Packaging | Data API plus open_clip |
| 5 Naming | sherlock plus domain-check, USPTO, WIPO, and IP India |
| 6 Testing | Test & Compare |
| 7 Analytics | analytix plus the Reporting API reach report, via cron |
| 8 Automation | pauling-ai MCP plus n8n |
| 9 Cross-post | Postiz, self-hosted |
| 10 Lists | awesome-mcp-servers |

**Unverified:**
- SaaS free-tier limits come from third-party reviews, and reported ViewStats prices conflict.
- Reddit's block on `.json` access (reported since May 2026) and pytrends' broken trending methods come from third-party tests.
- MCP features come from READMEs; I didn't run any of them.
- Star counts can be gamed.
