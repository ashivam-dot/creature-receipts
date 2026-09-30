# Channel 2 niche audit: pipeline fit and YouTube policy

Researched 2026-09-30 for the second faceless Shorts channel built from the `youtube-studio` kit. Space and
astronomy are excluded because the sister channel covers them. All picture and Wikipedia numbers below were
measured today against the live Wikimedia APIs. The scripts and raw JSON are in `research/pipeline-fit-data/`,
so they can be run again.

## Bottom line

1. **Best fit: extreme animals and biology, archaeology and ancient mysteries, and natural disasters (historical
   only).** All three had enough pictures for every topic tested (median 43 to 99 usable Commons files per
   topic, and no topic under 35), long, well-cited Wikipedia articles, strong reader demand, and low
   advertiser risk if handled as described below. Deep-ocean creatures come next: the animals are well covered,
   but place and abstract topics (Challenger Deep: 5 usable files) are thin.
2. **Poor fit for this pipeline: frauds and heists, aviation incidents, Cold War secrets, and engineering
   disasters.** Most topics in these niches have fewer than 15 usable pictures (median 6 to 14). With 6 to 9
   beats, that means one portrait or one wreck photo shown again and again, which is exactly what the quality
   gate rejects.
3. **Policy:** an AI-narrated, sourced, picture-based channel can be monetized. The risks are the
   "inauthentic content" rules (template sameness, "distress bait", and AI personas giving health or finance
   advice) and advertiser suitability for death and tragedy. The disclosure label is **not** required for a
   generic TTS narrator reading real archival pictures. It **is** required for any photorealistic AI image
   of a real event, place, or person. Keep Cloudflare AI images off, or limit them to clearly non-photorealistic
   title cards.
4. **YPP clock:** the current ad tier is 1,000 subscribers plus 10M Shorts views in 90 days. **From
   2027-02-01, new applicants need 20M Shorts views in 90 days (or 8,000 hours).** Channels already in YPP
   keep their place, but earning from the Shorts Creator Pool will also require 10M Shorts views in any rolling
   90 days. A channel that launches in October 2026 has about 4 months to qualify under the easier rule.
5. **Sources to add, top 3:** iNaturalist (no key, CC0/CC BY filter, 2048 px originals), Smithsonian Open
   Access (CC0, free api.data.gov key), and Europeana (free key, filter rights to PD/CC0/CC BY). Library of
   Congress returned Cloudflare 403 challenges to headless requests from this machine, and NARA's catalog API
   needs an issued key, so neither is a drop-in source. Their public-domain images already reach the
   pipeline through Commons mirrors, which hold 631k LoC files and 468k NARA files.

---

## 1. How the pipeline constrains a niche (from the code)

- **Topics:** each topic needs an English Wikipedia article. Research (`research.gather`) reads Wikipedia first,
  then cited and searched pages (at most 7 sources), preferring `TRUSTED` domains. A claim counts only when two
  different sites state it, and a topic with fewer than 8 such claims is dropped. So an article with few
  citations, or a topic that only fringe sites cover, gets dropped.
- **Pictures (`sources.gather`):** for each beat's Wikipedia subjects, the pipeline pulls the Wikidata image,
  the P373 Commons category, P180 "depicts" files, period categories ("X in the 1870s"), the article's own
  media, and keyword search. Beats left weak then get candidates from Openverse, Wellcome, the Art Institute of
  Chicago, and the Met (`extras`).
- **License filter (`visuals._COMMONS_OK`):** public domain, PD-*, CC0, and CC BY only. **CC BY-SA is
  excluded**, and so is Flickr "no known copyright restrictions" unless the date is before 1931. Size filter:
  long side of at least 600 px (a framed card only), at least 1200 px for full screen, and a short side of at
  least 300 px.
- **Reuse:** `pick._reuse_of` fills a beat with an earlier beat's picture when nothing new fits. The reviewer
  (`studio.REVIEW_PROMPT`) then marks visuals down, and anything under 4/5 fails after two fix rounds. The
  number of distinct usable pictures per story is therefore the main feasibility number.
- **Period bias:** `pick.MODERN_BEFORE = 1945` and `rank.HISTORICAL` penalize modern color photos in beats set
  before 1945. For animal or ocean niches this should be set to 0; otherwise it fights the best material.
- **Stock and AI (`visuals._pexels`, `_pixabay`, `_ai`):** these exist but stay off without keys.

## 2. Measured picture depth and Wikipedia depth

Method (`pipeline-fit-data/measure.py`): for each topic, resolve the English Wikipedia article, then its
Wikidata P373 Commons category. List files in that category and its direct subcategories (capped at 600).
Apply **the pipeline's exact license and size rules** to count *usable* files and *usable at 1200 px or more*.
Also count files tagged with US-government, NOAA, USGS, NARA, Navy, USAF, or LoC categories; CC BY-SA files
the pipeline throws away (extra run only); P180 "depicts" hits; article size; `<ref>` count; and average
daily pageviews over the last 90 days.

Caveats:
- Taxon categories (animals) include every subcategory, which inflates their counts compared with a
  single-event category.
- Phineas Gage shows 0 `<ref>` tags because the article uses `{{sfn}}` citations. It is well cited.
- A Short also draws on people, places, and equipment named in beats, so the real pool is somewhat larger
  than one category. The *minimum* and the thin-topic share are the best signals of reuse risk.

### Per-topic results (48 topics)

| Niche | Topic | Article KB | Refs | Views/day | Cat files (depth 1) | **Usable** | Usable ≥1200px | US-gov PD | BY-SA dropped | Depicts |
|---|---|---|---|---|---|---|---|---|---|---|
| Deep ocean | Giant squid | 73 | 119 | 2,223 | 294 | **78** | 63 | 8 | – | 82 |
| Deep ocean | Challenger Deep | 173 | 249 | 1,129 | 9 | **5** | 4 | 0 | – | 3 |
| Deep ocean | Anglerfish | 66 | 138 | 1,161 | 34 | **16** | 12 | 5 | – | 2 |
| Deep ocean | Trieste (bathyscaphe) | 25 | 39 | 256 | 77 | **63** | 57 | 33 | 10 | 4 |
| Deep ocean | Hydrothermal vent | 129 | 209 | 285 | 599 | **309** | 232 | 126 | 221 | 11 |
| Deep ocean | Coelacanth | 60 | 102 | 1,323 | 92 | **36** | 33 | 1 | 44 | 7 |
| Engineering | Tacoma Narrows Bridge (1940) | 54 | 59 | 472 | 24 | **12** | 8 | 8 | – | 5 |
| Engineering | Hyatt Regency walkway collapse | 38 | 77 | 1,188 | 12 | **4** | 4 | 4 | – | 1 |
| Engineering | St. Francis Dam | 81 | 75 | 354 | 25 | **13** | 13 | 10 | – | 16 |
| Engineering | Great Molasses Flood | 36 | 92 | 1,664 | 23 | **15** | 12 | 13 | 3 | 1 |
| Engineering | Quebec Bridge | 31 | 36 | 147 | 112 | **57** | 35 | 19 | 46 | 106 |
| Engineering | Johnstown Flood | 61 | 87 | 901 | 162 | **135** | 77 | 108 | 17 | 3 |
| Aviation | Flight 19 | 37 | 46 | 346 | 16 | **6** | 3 | 2 | – | 1 |
| Aviation | Hindenburg disaster | 123 | 84 | 2,588 | 47 | **31** | 23 | 22 | – | 6 |
| Aviation | D. B. Cooper (NWA Flight 305) | 213 | 313 | 4,368 | 25 | **6** | 3 | 2 | – | 3 |
| Aviation | Amelia Earhart | 147 | 189 | 4,242 | 600 | **502** | 425 | 393 | 11 | 54 |
| Aviation | Lady Be Good (aircraft) | 25 | 31 | 178 | 37 | **13** | 9 | 13 | 13 | 14 |
| Aviation | 1945 Empire State Building B-25 crash | 16 | 25 | 921 | 7 | **7** | 1 | 7 | 0 | 0 |
| Medical history | Trepanning | 55 | 98 | 890 | 198 | **136** | 116 | 2 | – | 8 |
| Medical history | Radium Girls | 37 | 57 | 965 | 67 | **4** | 1 | 4 | – | 2 |
| Medical history | Phineas Gage | 148 | (sfn) | 1,262 | 84 | **30** | 18 | 10 | – | 9 |
| Frauds/heists | Victor Lustig | 21 | 45 | 219 | 8 | **3** | 2 | 2 | – | 7 |
| Frauds/heists | Gardner Museum theft | 54 | 19 | 565 | 44 | **38** | 34 | 0 | – | 1 |
| Frauds/heists | Great Train Robbery (1963) | 146 | 193 | 699 | no category | **0** | 0 | 0 | – | 0 |
| Frauds/heists | Charles Ponzi | 44 | 52 | 662 | 7 | **6** | 4 | 6 | 0 | 3 |
| Frauds/heists | Piltdown Man | 52 | 54 | 322 | 35 | **18** | 15 | 8 | 7 | 4 |
| Frauds/heists | Cardiff Giant | 19 | 40 | 208 | 14 | **6** | 5 | 4 | 2 | 1 |
| Money | Tulip mania | 56 | 84 | 725 | 87 | **25** | 22 | 6 | – | 5 |
| Money | Rai stones | 25 | 62 | 144 | 49 | **30** | 27 | 2 | – | 4 |
| Money | Weimar hyperinflation | 36 | 55 | 303 | 329 | **260** | 74 | 93 | – | 6 |
| Animals | Tardigrade | 73 | 157 | 2,572 | 177 | **116** | 109 | 8 | – | 25 |
| Animals | Axolotl | 75 | 140 | 3,796 | 296 | **99** | 71 | 8 | – | 68 |
| Animals | Mantis shrimp | 60 | 94 | 1,017 | 134 | **89** | 62 | 18 | – | 16 |
| Geography | Baarle-Hertog | 19 | 11 | 253 | 234 | **103** | 8 | 1 | – | 1 |
| Geography | Bir Tawil | 14 | 18 | 545 | 26 | **8** | 7 | 2 | – | 2 |
| Geography | Northwest Angle | 28 | 26 | 334 | 42 | **6** | 4 | 1 | – | 1 |
| Geography | Point Roberts, Washington | 57 | 74 | 559 | 89 | **35** | 22 | 12 | 47 | 3 |
| Geography | Kaliningrad Oblast | 80 | 122 | 1,093 | 125 | **60** | 48 | 0 | 42 | 7 |
| Geography | Four Corners Monument | 29 | 34 | 199 | 103 | **60** | 58 | 2 | 39 | 16 |
| Cold War | Project Azorian | 41 | 51 | 342 | 28 | **13** | 7 | 5 | – | 4 |
| Cold War | Duga radar | 25 | 27 | 668 | 197 | **21** | 20 | 0 | 173 | 172 |
| Cold War | 1961 Goldsboro B-52 crash | 55 | 20 | 482 | 14 | **10** | 4 | 9 | – | 0 |
| Cold War | Operation Ivy Bells | 11 | 12 | 182 | no category | **0** | 0 | 0 | 0 | 0 |
| Cold War | Castle Bravo | 82 | 113 | 1,000 | 44 | **29** | 15 | 25 | 0 | 2 |
| Archaeology | Antikythera mechanism | 139 | 359 | 2,720 | 143 | **43** | 37 | 0 | – | 19 |
| Archaeology | Terracotta Army | 88 | 123 | 1,786 | 600 | **219** | 214 | 2 | – | 88 |
| Archaeology | Göbekli Tepe | 84 | 12 | 3,450 | 175 | **35** | 28 | 0 | – | 61 |
| Disasters/weather | 1900 Galveston hurricane | 121 | 231 | 866 | 113 | **58** | 53 | 54 | – | 29 |
| Disasters/weather | 1980 Mount St. Helens eruption | 79 | 106 | 2,299 | 176 | **123** | 75 | 108 | – | 4 |
| Disasters/weather | Dust Bowl | 62 | 80 | 1,585 | 110 | **89** | 82 | 85 | – | 2 |
| Inventions | Mauveine | 11 | 24 | 90 | 30 | **7** | 1 | 0 | – | 1 |
| Inventions | Microwave oven | 95 | 143 | 710 | 346 | **102** | 78 | 7 | – | 51 |
| Inventions | Post-it note | 40 | 117 | 208 | 538 | **138** | 118 | 11 | – | 71 |

"–" means not measured in the first run. The BY-SA column comes from the second run only.

### Per-niche summary

| Niche | Topics | Usable median | Min | Topics under 15 usable | US-gov PD median | Article KB median | Refs median | Views/day median |
|---|---|---|---|---|---|---|---|---|
| Extreme animals / biology | 3 | 99 | 89 | 0/3 | 8 | 73 | 140 | 2,572 |
| Natural disasters / weather | 3 | 89 | 58 | 0/3 | **85** | 79 | 106 | 1,585 |
| Accidental inventions | 3 | 102 | 7 | 1/3 | 7 | 40 | 117 | 208 |
| Deep ocean / sea creatures | 6 | 50 | 5 | 1/6 | 7 | 70 | 129 | 1,145 |
| Geography / borders | 6 | 48 | 6 | 2/6 | 2 | 29 | 30 | 440 |
| Archaeology / ancient | 3 | 43 | 35 | 0/3 | 0 | 88 | 123 | 2,720 |
| Money / economic oddities | 3 | 30 | 25 | 0/3 | 6 | 36 | 62 | 303 |
| Bizarre medical history | 3 | 30 | 4 | 1/3 | 4 | 55 | 57 | 965 |
| Engineering disasters | 6 | 14 | 4 | 3/6 | 12 | 46 | 76 | 687 |
| Cold War / military | 5 | 13 | 0 | 3/5 | 5 | 41 | 27 | 482 |
| Aviation incidents | 6 | 10 | 6 | 4/6 | 10 | 80 | 65 | 1,755 |
| Frauds / scams / heists | 6 | 6 | 0 | 4/6 | 3 | 48 | 49 | 444 |

### Where the "same photo reused" problem will hit

- **Frauds/heists:** a con man usually has 1 to 3 portraits and a courthouse or newspaper scan. Lustig had 3
  usable files, Ponzi 6, and the Cardiff Giant 6. The Great Train Robbery has no Commons category at all.
  This is the worst fit.
- **Aviation incidents:** single-event categories hold 6 to 13 files (Flight 19, D. B. Cooper, the B-25
  crash, Lady Be Good). Famous people (Earhart: 502) and famous airships are the exceptions, and those are
  already heavily covered topics.
- **Cold War secrets:** by definition few photos were released. Ivy Bells has no category, and the Duga
  radar's files are mostly CC BY-SA (173 dropped, 21 kept).
- **Engineering disasters:** US events recorded by the government (Johnstown: 135 usable; St. Francis: 13;
  Molasses: 15) do fine or passably. Modern or private-building failures (Hyatt Regency: 4) are thin.
- **Geography oddities:** the counts look fine, but most of the pool is **maps and look-alike border-marker
  photos**. Baarle-Hertog has 103 usable files, only 8 of them at 1200 px or more. Visually similar pictures
  across beats are the reviewer's "repetitive visuals" complaint in another form. Many of the best files are
  CC BY-SA (Point Roberts: 47 dropped).
- **Deep ocean:** creatures are deep. *Places* in the deep sea (Challenger Deep: 5) are thin, and topics
  drift toward the same few NOAA ROV frames. NOAA Ocean Exploration imagery is US-government public domain,
  and much of it is on Commons.
- **Accidental inventions:** the counts are high, but the pool is dominated by **modern product photos**
  (microwaves, Post-it pads) that look alike from beat to beat. The discovery moment itself (Perkin 1856,
  Spencer 1945) usually has a single portrait. Mauveine had 7 usable files.

### Wikipedia and research depth

Every niche's typical topic clears the "8 two-source claims" bar, except that **geography oddities** (median
29 KB and 30 refs, with Bir Tawil at 14 KB and 18 refs) and **Cold War secrets** (median 27 refs; Ivy Bells
has 12) will often drop below it. Animals, archaeology, disasters, and deep ocean have the richest articles
(median 70 to 88 KB and 106 to 140 refs) and the highest reader demand (1,100 to 2,700 daily views per topic),
which also feeds `auto.demand`, since the backlog's most-read articles go first.

## 3. Ranking: feasibility and policy safety

Scores run from 1 to 5 (5 is best). Visuals: median usable files, share of thin topics, quality at 1200 px or
more. Sourcing: article length and citations, plus trusted outlets. Policy: advertiser-friendly guidelines
and inauthentic-content risk. Demand: pageviews. **Overall = 2 x Visuals + Sourcing + Policy + Demand (out
of 25).** Visuals count double because weak or repeated pictures are the quality gate's most common rejection
reason. Ties are broken by Visuals, then Policy.

| Rank | Niche | Visuals | Sourcing | Policy safety | Demand | Overall /25 | Main risk / condition |
|---|---|---|---|---|---|---|---|
| 1 | **Extreme animals / biology** | 5 | 5 | 5 | 5 | **25** | Saturated "animal facts" template genre, so each Short needs a real story (discovery, record, experiment) to avoid "interchangeable" content. Set `MODERN_BEFORE = 0`. Add iNaturalist. |
| 2 | **Archaeology / ancient mysteries** | 4 | 5 | 5 | 5 | **23** | Pseudo-archaeology ("aliens built it") fails the 2-site rule. Keep to evidence. The Met, AIC, and Europeana fit. Few US-gov PD files. |
| 3 | **Natural disasters / extreme weather (historical)** | 5 | 5 | 3 | 4 | **22** | Death and tragedy: only non-graphic, educational coverage is ad-safe. No bodies, no events from the last ~10 years. Under the 2026 "off-putting" bucket, don't make a feed of loss. NOAA/USGS PD depth is the best of any niche. |
| 4 | **Deep ocean / sea creatures** | 4 | 5 | 5 | 4 | **22** | Tied with disasters, below on Visuals. Place topics are thin, and the same NOAA ROV frames recur. With iNaturalist added, it is effectively 3rd and the safest of the top four. |
| 5 | Accidental inventions / discoveries | 3 | 4 | 5 | 2 | 17 | Modern product-photo sameness, single-portrait discovery moments, low demand. Overlaps the Days of Odd strange-history format. Smithsonian (NMAH) helps. |
| 6 | Money / economic oddities | 3 | 4 | 4 | 2 | 16 | Low demand. The "AI persona giving financial advice" bucket means historical framing only, never tips. Smithsonian National Numismatic Collection helps. |
| 7 | Bizarre medical history | 3 | 4 | 2 | 3 | 15 | Shocking and medical imagery; "AI persona giving health advice" bucket. Wellcome is deep, but many plates are anatomical or gory and get vetoed. Overlaps Days of Odd. |
| 8 | Aviation mysteries / incidents | 2 | 4 | 3 | 4 | 15 | 4 of 6 topics thin (6 to 13 files). Air-crash deaths are ad-sensitive, and recent crashes are sensitive events. |
| 9 | Engineering disasters | 2 | 4 | 3 | 3 | 14 | Half the topics are thin, and tragedy rules apply. Workable only for US-government-documented events (Johnstown, St. Francis Dam). |
| 10 | Geography / border oddities | 2 | 2 | 4 | 2 | 12 | Maps and look-alike markers, thin articles (8-claim drops), CC BY-SA heavy. Avoid live territorial disputes. |
| 10 | Cold War / military secrets | 2 | 2 | 4 | 2 | 12 | The secrecy that makes these topics interesting also means few released photos and few independent sources. |
| 12 | Frauds / scams / heists | 1 | 3 | 5 | 2 | 12 | One portrait per story. Hoaxes are already a Days of Odd series ("Hoaxes That Fooled Everyone"), so this would cannibalize it. |

**Strong option:** combine niches 1 and 4 (animals and deep ocean) as a single "strange living things / weird nature" channel.
Pictures come from Commons taxon categories, iNaturalist, NOAA, and the Biodiversity Heritage Library's old
plates on Commons. Weird-but-true stories (the coelacanth rediscovery, the giant squid's first photo in 2004,
tardigrades surviving space) carry the "story, not fact list" angle that the inauthentic-content rules reward.

## 4. New image sources to integrate

### Tested status of every candidate (today, from this Mac, headless)

| Source | Tested result | License filter | Key? | Verdict |
|---|---|---|---|---|
| **iNaturalist API** | 200. Vampire squid: 1 CC BY obs, 2048×1536 original. Mantis shrimp (*O. scyllarus*): 144 research-grade CC0/CC BY obs. Giant squid: 2. | `photo_license=cc0,cc-by` | No | **Top 3.** Best for animals and ocean. |
| **Smithsonian Open Access** | 200 with `DEMO_KEY`. "Hindenburg" 72, "Wright Flyer" 15, "Titanic" 31, "typewriter" 34 CC0 hits. Hit `OVER_RATE_LIMIT` after about 10 calls. Image fetch at `&max=1600` returned 858×1599. | `media_usage:"CC0"` in `q` | Free api.data.gov key (DEMO_KEY is for testing only) | **Top 3.** Aviation (NASM), inventions (NMAH), natural history (NMNH), money (NNC). |
| **Europeana** | 200 with `api2demo`. "zeppelin" 210 PD, "tulip" 2,398, "Vesuvius eruption" 47, "anglerfish" 81 PD/CC0/BY. Multi-word queries are strict ("diving bell": 1). | `qf=RIGHTS:(*publicdomain* OR *licenses/by/*)`. `reusability=open` alone lets in BY-SA, so don't use it by itself. | Free key (demo key for tests) | **Top 3.** European history, archaeology, science, natural-history plates. |
| Openverse (already used) | Axolotl 240 (Flickr CC BY). `source=inaturalist` works (mantis shrimp: 240). | `license=cc0,pdm,by` | No | Keep. The iNaturalist mirror is keyword-only, so direct taxon queries are more precise. |
| Library of Congress JSON API | **403 Cloudflare "Just a moment..." challenge** for `loc.gov/photos/?fo=json` and `/pictures/` with both a custom and a browser UA. | `rights` fields vary | No | Not usable headless from here. 631k LoC files are already on Commons (`Category:Images from the Library of Congress`). |
| NARA Catalog v2 | Without `x-api-key` it returns the HTML app, not JSON. | Mostly PD | Key by email request | Skip. 468k NARA files are on Commons. |
| Cleveland Museum of Art | 200 (volcano, tulip: 41 CC0). One call returned non-JSON once, then worked on retry. | `cc0=1&has_image=1` | No | Optional, art-only. |
| Rijksmuseum (new Linked Art API) | 200 `data.rijksmuseum.nl/search/collection?title=tulp`: 249 items, but the results are IDs that need a second Linked Art lookup to reach images. | CC0/PD | No | Optional for tulip mania and Dutch topics. More integration work. |
| NOAA Photo Library | No public search API. The Commons category `Images from NOAA` has 1,266 files and 27 subcategories. NOAA PD files are also spread through event categories (Galveston: 54 US-gov of 58 usable). | PD (US gov) | – | Reached through Commons. Add NOAA terms to writer `queries`. |
| USGS | Commons `Category:PD USGS` has **274,461 files**. | PD | – | Reached through Commons. Mount St. Helens: 108 of 123 usable are US-gov. |
| US Navy | Commons `Category:Photographs by the United States Navy` has 15,495 files. | PD | – | Through Commons. |
| NIH/NLM | No matching Commons category found. Wellcome (already integrated) covers medical history better. | – | – | Skip. |
| Flickr Commons, NYPL, BHL API, DVIDS | Not tested; each needs a key or token. BHL and NYPL PD scans are largely mirrored to Commons and Openverse. | – | Yes | Later, if needed. |
| Pexels / Pixabay | Code exists (`visuals._pexels`, `_pixabay`). | Own licenses (not CC), free use | Free key | Only for b-roll texture in animal or ocean niches. Generic stock across many Shorts looks templated, which is an inauthentic-content risk. Never use for historical beats. |

### Top 3: exact tested usage

**1. iNaturalist (no key; CC0 and CC BY only; credit is the `attribution` string)**

```bash
# 1) taxon id from a common or scientific name
curl -s -A "YourApp/0.1 (https://your.site; you@mail)" \
  "https://api.inaturalist.org/v1/taxa?q=vampire%20squid&rank=species&per_page=1"
#   -> id 253737, Vampyroteuthis infernalis, "Vampire Squid"
# 2) best-voted observations with openly licensed photos
curl -s -A "YourApp/0.1 (...)" \
  "https://api.inaturalist.org/v1/observations?taxon_id=253737&photo_license=cc0,cc-by&order_by=votes&per_page=30"
#   results[].photos[]: license_code ("cc-by"/"cc0"), attribution, original_dimensions,
#   url ".../photos/519660742/square.jpg" -> replace "square" with "original" (2048 px)
# species with many research-grade photos:
curl -s "https://api.inaturalist.org/v1/observations?taxon_name=Odontodactylus%20scyllarus&photo_license=cc0,cc-by&quality_grade=research&per_page=5&order_by=votes"
#   -> total_results 144
```

Notes: add `captive=any` for species mostly seen captive (axolotl: 0 research-grade observations, 73 with
`captive=any`). `taxon_name` matches reliably at species level; for higher ranks (Stomatopoda returned 0),
resolve to `taxon_id` first. Keep request rates low (iNaturalist asks for about 1 request per second). Map
`cc-by` to "CC BY 4.0" (check `license_code` on each photo) and put `attribution` in the credit line.

**2. Smithsonian Open Access (CC0; free api.data.gov key)**

```bash
curl -s "https://api.si.edu/openaccess/api/v1.0/search?q=Hindenburg+AND+online_media_type:%22Images%22+AND+media_usage:%22CC0%22&rows=30&api_key=$SI_API_KEY"
#   -> response.rowCount 72; rows[].content.descriptiveNonRepeating:
#      unit_code (NASM, NPM, NMAH, NMNH...), metadata_usage.access "CC0",
#      online_media.media[0].content = "https://ids.si.edu/ids/deliveryService?id=NPM-2011_2034_1"
curl -s -o out.jpg "https://ids.si.edu/ids/deliveryService?id=NASM-NASM2022-00100A-000001&max=1600"
#   -> image/jpeg 858x1599 (the 1903 Wright Flyer)
```

Notes: `DEMO_KEY` hit `OVER_RATE_LIMIT` after about 10 calls. A free key from api.data.gov allows about
1,000 requests per hour. Search is full-text, so irrelevant botany records come back ("Bromus arduennensis" for
Hindenburg): filter on `unit_code` and require the query terms in `title`, the way `visuals._matches` already
does for the Met. Accept only `media[].usage.access == "CC0"`. Coverage is strong for objects (aircraft,
inventions, coins and banknotes, specimens) and weak for events (Galveston hurricane: 0).

**3. Europeana (free key; filter rights URLs)**

```bash
curl -s "https://api.europeana.eu/record/v2/search.json?wskey=$EUROPEANA_KEY&query=zeppelin&media=true&qf=TYPE:IMAGE&qf=RIGHTS:(*publicdomain*%20OR%20*licenses/by/*)&rows=30&profile=minimal"
#   -> totalResults 210; items[].rights[0] e.g. http://creativecommons.org/publicdomain/mark/1.0/
#      items[].title[0], items[].edmIsShownBy[0] = direct image (often 1200 px, e.g. staatsbibliothek-berlin.de .../1200/0/...jpg)
#      items[].guid = landing page for the credit
```

Notes: `reusability=open` alone lets **CC BY-SA** through (seen: "Golden Tulip", by-sa/3.0/nl), so use the
`RIGHTS` filter and re-check `rights[0]` in code: accept `publicdomain/mark`, `publicdomain/zero`, and
`licenses/by/` only. Multi-word queries are strict ANDs over sparse metadata, so query by the subject's
simple name. Image hosts vary by institution; check the size after download (the pipeline already enforces
`SMALL_SIDE` and `FULL_SIDE`).

### Other pipeline observations

- **User-Agent:** a bare `curl` with no UA, and a UA with no real contact ("... contact: local"), got
  **HTTP 429** from both Wikipedia and Commons today. The pipeline's default (`ytc-shorts-pipeline/0.1
  (personal project)`) returned 200. Still, set `YTC_CONTACT` to a real URL or email, as Wikimedia's UA
  policy asks.
- **CC BY-SA exclusion** costs the most in the geography, deep-ocean, and Cold War niches (hydrothermal vent:
  221 BY-SA files dropped; Duga: 173; Point Roberts: 47). Keep it excluded. ShareAlike would apply to the
  finished video as an adaptation, which conflicts with the standard YouTube license. Instead, favor niches
  whose best pictures are PD or CC BY.
- **For animal or ocean niches**, also set `pick.MODERN_BEFORE = 0` and rewrite `rank.HISTORICAL`, or the
  SigLIP "historical" score will penalize exactly the modern color photos these niches depend on.

## 5. Policy: what this channel must do to stay monetizable

### 5a. Inauthentic content (formerly "repetitious"), July 2025, clarified July 2026

Official: [YouTube channel monetization policies (answer 1311392)](https://support.google.com/youtube/answer/1311392).

- **2025-07-15:** "repetitious content" was renamed **"inauthentic content"** to "better clarify this
  includes content that is repetitive or mass-produced". YouTube calls this a clarification, not a new
  restriction. The reused-content policy is unchanged.
- The policy page now names three kinds of ineligible content. They were set out in a Creator Insider
  explainer on **2026-07-16**, as reported by [Tubefilter, 2026-07-13](https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/)
  and [WinBuzzer, 2026-07-23](https://winbuzzer.com/2026/07/23/youtube-draws-three-monetization-lines-around-ai-slop-xcxwbn/):
  1. **Generic or repetitive content.** Examples include "image slideshows, templated storylines, or scrolling
     text with minimal or no narrative, commentary, or educational value", "similar or repetitive content
     with low educational value... or minimal variation across videos", and "AI-generated content made with
     generic or unoriginal templates giving the impression of mass production without adding the creator's
     original, authentic insights or perspective".
  2. **Unsatisfying or off-putting content.** This covers "emotionally manipulative formulas" and content
     "designed to shock or surprise viewers for the sole purpose of getting views". Specifically: "content
     that repeatedly uses disturbing themes (such as violence or loss) without building a cohesive
     narrative", and "realistic visuals tricking viewers into believing a fake... natural disaster has
     occurred".
  3. **AI personas on sensitive topics.** This means "content that presents itself as a human expert
     providing advice to viewers on topics such as health, legal issues, finances, or politics".
- Allowed, per the same page: "using creative tools to assist in delivering a unique, well-researched, or
  creative narrative, like using AI to edit your video scripts or generate a unique background visual".
- Enforcement is **channel-level**. Reviewers judge the channel as a whole, and removed channels generally
  have 21 days to appeal (WinBuzzer).

**What this means for this pipeline:** the pipeline's picture-slideshow-plus-TTS format is the exact shape the
policy names. It stays eligible only through *narrative and educational value that varies across videos*.

- Keep the enforced story arc (hook, turn, payoff, loop) and the 2-source claims table. Those are the
  pipeline's "well-researched narrative" evidence.
- Vary structure across series: not every Short "Did you know…", with a rotating hook type and different
  beat counts.
- Avoid the "same template" signal: rotate title-card styles and motion, and don't reuse a stock intro or
  outro.
- Keep the per-Short source links in the description (the pipeline already writes the credits).
- Disasters and medical niches: build every Short around cause, science, and aftermath, not the death toll.
  Don't post tragedy after tragedy in a row. Mix in rescues, survivals, and science.
- The narrator must never give health, finance, or legal advice and must never pose as a doctor or expert
  (bucket 3). "In 1880 doctors believed..." is fine; "you should..." is not.

### 5b. Advertiser-friendly guidelines (yellow-icon risk)

Official: [Advertiser-friendly content guidelines (6162278)](https://support.google.com/youtube/answer/6162278);
[How monetization reviews work (9269751)](https://support.google.com/youtube/answer/9269751): "The most
important principle is **context**. What's the intention... to inform and educate, or to shock and incite?"
Reviewers also weigh focus, tone, realism, and graphicness.

Lines that matter for these niches (quoted from 6162278):
- **Can earn** (green), Death & tragedy: "Educational or historical content with: non-graphic depictions of
  dead bodies... coverage of tragedies involving one or more deaths (excluding sensitive events such as mass
  shootings or terrorist attacks) with limited or no display of violent acts or their results." Also,
  "Educational... containing: implied moment of death or severe bodily harm; severe property damage where
  death or severe bodily harm likely occurred."
- **Limited ads:** "Dead bodies with obvious injury or damage in educational or documentary settings (such as
  a history learning channel)"; "reporting of tragedies involving multiple casualties which include graphic or
  gruesome details."
- **No ads:** "Display of unprepared dead bodies or those with ultra-graphic injuries"; "visible display of
  the moment of death."
- **Shocking content, can earn:** "Medical or cosmetic procedures that are educational, focusing on the
  procedure itself rather than on bodily parts, liquids, or waste"; "accidents and injuries that are presented
  in a news, documentary, or artistic context."
- **Animal violence, can earn:** "non-graphic depictions of animal violence in the natural world". Limited
  when "focal, prolonged graphic animal injuries... are the focal subject."
- **War & conflict:** "non-graphic educational coverage or discussion of war" can earn.

Practical rules: the picker already vetoes gore and nudity (`pick.VERIFY_PROMPT`). Also keep bodies, victims'
faces, and injury photos out of disaster, aviation, and medical Shorts. Put educational context in the title
and description ("How…", "Why…", year, place). Avoid sensitive recent events (roughly the last decade, or any
event still in the news).

### 5c. AI disclosure ("AI use" / altered or synthetic label)

Official: [Disclosing use of GenAI content (14328491)](https://support.google.com/youtube/answer/14328491);
[YouTube Blog, "Improving AI labels for viewers and creators", 2026-05-27](https://blog.youtube/news-and-events/improving-ai-labels-viewers-creators/).

- Disclosure is required for GenAI content that "makes a real person appear to say or do something they
  didn't do", "alters footage of a real event or place", or "generates a realistic scene that didn't actually
  occur". "Realistic AI content and meaningful changes require disclosure, while non-realistic or minor edits
  don't."
- The setting is in YouTube Studio: upload, then **Attributes, then "AI use"**, set to Yes or No. The Data API
  upload path should set the equivalent flag. Check the API field before automating, and record the answer
  in the publish step.
- **Since May 2026**, YouTube applies labels automatically when "our systems detect significant photorealistic
  AI use". Labels are permanent for YouTube-tool content and for files whose C2PA metadata marks them as fully
  generative. For Shorts, the label is now an on-video overlay. YouTube says "these labels alone do not affect
  how our videos are recommended or whether they can earn money" (Rene Ritchie, YouTube Creator Liaison, in
  the announcement video).

**For this pipeline:**
- Kokoro TTS narration (a generic voice that is not a clone of a real person) over real archival and
  open-licensed photos does **not** require disclosure.
- Keep Cloudflare Flux images **off** for real events, places, and people. A photorealistic AI "Galveston 1900
  flood" would require disclosure, and it also matches the "fake natural disaster" example in the
  inauthentic-content policy. If AI imagery is ever used, keep it clearly illustrative or non-photorealistic
  (the description still notes it), or set "AI use" to Yes.
- Strip C2PA metadata only if it is inaccurate. Never use it to evade labeling.

## 6. YPP in 2026 and what changes on 2027-02-01

Official: [YPP overview & eligibility (72851)](https://support.google.com/youtube/answer/72851);
[Expanded YPP (13429240)](https://support.google.com/youtube/answer/13429240);
[YouTube Blog, 2026-08-10, "New opportunities to earn and changes to the YouTube Partner Program"](https://blog.youtube/news-and-events/youtube-partner-program-updates-2027-new-opportunities-earn/);
[Shorts monetization policies (12504220)](https://support.google.com/youtube/answer/12504220).

| Tier | Through 2027-01-31 | New applicants from 2027-02-01 |
|---|---|---|
| Fan funding (memberships, Supers, Shopping), expanded-YPP countries | 500 subs + 3 public uploads in 90 days + (3,000 watch hours in 12 months **or 3M Shorts views in 90 days**) | Unchanged |
| Ads + Premium revenue share | 1,000 subs + (4,000 watch hours in 12 months **or 10M Shorts views in 90 days**) | 1,000 subs + (8,000 hours in 365 days **or 20M Shorts views in 90 days**) |
| Shorts Creator Pool (existing partners too) | Any YPP partner with ad terms | Only while the channel has **10M qualified Shorts views in a rolling 90 days**. Shorts revenue resumes automatically above that. |

- Existing partners are grandfathered for *entry*. New terms must be accepted in Studio (reported deadline
  2027-01-31).
- Shorts views in the Shorts feed do **not** count toward the 4,000 or 8,000 watch hours (72851).
- **Shorts revenue share (12504220):** Shorts-feed ad revenue is pooled monthly. The share tied to Shorts
  with music goes partly to licensing (1 track: half to the Creator Pool; 2 tracks: one third). The pool is
  split by each monetizing creator's share of *engaged views* per country, and the creator keeps **45%**.
  Premium revenue for Shorts is paid at 45% of net. **This pipeline's Shorts have no licensed music tracks**,
  so all of their associated revenue enters the pool.
- The fan-funding tier is limited to the countries in the expanded-YPP list; check Studio's Earn tab for the
  owner's country.

**Timing:** to enter under the 10M rule, the channel must *apply* by 2027-01-31, about 17 weeks after
launch. After that, the bar is 20M Shorts views in 90 days, and staying in the Shorts pool needs 10M per 90
days. Pick the niche with the highest views per Short (animals and archaeology lead on demand) and a posting
cadence the picture supply can sustain.

## 7. Reproduce

- `research/pipeline-fit-data/measure.py results.json` for the 36 base topics, and
  `measure.py extra.json extra` for the 18 extra topics. Uses Wikipedia, Wikidata, Commons, and the pageviews
  API with a contact User-Agent and 4 workers.
- `research/pipeline-fit-data/sources_test.py` probes iNaturalist, Europeana, Cleveland, Smithsonian
  (DEMO_KEY), Rijksmuseum, Openverse, and the sizes of the US-government Commons categories.
