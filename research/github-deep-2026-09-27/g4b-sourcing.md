# G4b: finding the right, license-safe picture for each beat

Scope: picture sourcing for one-still-per-beat Shorts (pick.py / visuals.py). Everything below was tested live
on 2026-09-27 with `curl`/Python from this Mac (User-Agent `days-of-odd-research/0.1 (<owner-email>)`),
except where marked "documented" or "estimate". No signups; only the providers' public demo keys
(api.data.gov `DEMO_KEY`, Europeana `api2demo`) were used, for a handful of requests.

Evidence files (scripts write their own JSON) are in `.scratch/deep/g4b/`:
`wm_techniques.py` → `wm_techniques.json` (Part A, 7 topics x 12 techniques), `wm_beats.py` → `wm_beats.json`
(38 beats, keyword vs entity route), `wm_beats2.py` → `wm_beats2.json` (full candidate rows, 23 beats),
`clip_rerank.py` → `clip_rerank.json` + `sheets/*.jpg` (SigLIP ranking, contact sheets I judged by eye),
`wm_gains.py`, `wm_years.py`, `wm_timecats.py`, `wm_checks.py`, `archives.py`, `clip_bench.py`.

## TL;DR

- Our keyword search is the bottleneck, not the picker. Over 38 real and writer-style beats, today's route
  (3 LLM queries + a shortened one, top 12 each) found 137 usable files and left 9 beats with none. An
  **entity route** (each beat names Wikipedia articles → Wikidata QID → the item's image (P18), its Commons
  category, and files tagged "depicts" that item) found 948, leaving 3 beats with none.
- Relevance, judged by eye on 23 beats: keyword top-1 was acceptable on 10 (7 exact), entity top-1 ranked by
  SigLIP on 21 (10 exact), and the two routes combined gave 21 acceptable, 13 of them exact. 13 of 23 beats
  had *no* acceptable keyword candidate at all: 8 had nothing usable, and 5 had only wrong pictures, several
  of them homonyms ("Lewis" gun → Lewis Powell, "Koepcke" → a 2023 US official). On the entity route,
  only 2 beats had none.
- Wrong period is the entity route's weakness: for ep035's Regency beats only 9% of dated candidates fall in
  1760-1880. The fix is cheap: Commons' **time-scoped categories** ("Philadelphia in the 1810s": 62 files,
  27 of the first 30 usable, dated 1811), plus the file's date and a zero-shot SigLIP "historical vs modern"
  check (agrees with file dates 85% / 91%).
- SigLIP ViT-B/16 (Apache-2.0 weights) runs at 37 ms per image on 4 CPU threads (M3). It is a cheap
  pre-ranker before Gemini, and its score doubles as a "nothing here fits" signal.
- Safe license widening recovers real event pictures: Flickr-Commons "No restrictions" scans only when dated
  1930 or earlier, TIFF/WebP via Commons' JPEG thumbnails, and small (450-1199 px) PD event photos in a
  framed treatment instead of dropping them.
- Other archives: Wellcome (keyless, license filter works) and Openverse (`license=cc0,pdm,by`) are worth
  adding as role-based sources. loc.gov/Chronicling America answers 403 from here (Cloudflare) and is
  documented as blocking datacenter IPs. Trove, Flickr API, NYPL and DPLA need keys or approvals. Skip them
  and use their Commons mirrors.

---

## 1. Where today's sourcing fails (from our own code and episodes)

- `pick.py:240-247` `first_round`: per beat, `beats[n-1]["queries"][:3] + [_shorter(...)]`, 5 candidates kept
  per beat (`PER_BEAT = 5`), plus a shared pool of 18 from research visuals' first queries.
- `pick.py:68-107` `candidates()`: Commons `generator=search`, `"{query} filetype:bitmap"`, `gsrlimit=12`, then
  the renderer's exact filter: jpeg/png, long side ≥ 1200 (`MIN_SIDE`), `LicenseShortName` matching
  `_COMMONS_OK` (`visuals.py:31`).
- The render step re-runs a *query* and takes `candidates[0]` (`visuals.py:157-199`); `pin()` (`pick.py:118-127`)
  must find an `intitle:` query that returns the chosen file first. Files that can't be pinned are dropped
  (`pick.py:230-231`).
- ep035 (Princess Caraboo) round 1 scored visuals 3: "Duplicate art on early beats and an off-topic male
  portrait in beat 5". In the live re-run of ep035's real beat queries, 5 of 8 beats had **zero** usable
  keyword candidates (B2, B3, B6, B7, B8), and beat 5's 7 usable hits were pages of an NYPL sheet-music score.
  Empty beats force the picker into the 18-image pool, which is mostly Caraboo portraits. That is the
  duplicate-art failure.

## 2. Part A: Wikimedia techniques, tested live on 7 topics

### 2.1 Topic-level counts (returned / usable under our exact filter / usable and on-topic by regex)

| technique | Emu War | Cottingley | Piltdown | Spaghetti | Koepcke | Dancing | Norton |
|---|---|---|---|---|---|---|---|
| kw top 12 (today) | 12/1/1 | 12/5/5 | 12/6/6 | 11/1/1 | 9/0/0 | 8/6/6 | 12/6/6 |
| kw top 50 | 18/3/3 | 22/7/7 | 50/16/15 | 11/1/1 | 9/0/0 | 8/6/6 | 50/23/23 |
| `"phrase"` top 50 | 15/3/3 | 19/7/7 | 45/16/15 | 0/0/0 | 8/0/0 | 7/5/5 | 50/20/16 |
| kw + `fileres:>800` + SDC license | 4/3/3 | 5/3/3 | 12/12/11 | 1/1/1 | 0/0/0 | 1/1/1 | 50/37/24 |
| REST `page/media-list` | 4/1/0 | 10/1/1 | 7/4/4 | 1/1/1 | 1/0/0 | 1/1/1 | 7/6/6 |
| Action API `prop=images` | 5/1/0 | 14/1/1 | 7/4/4 | 1/1/1 | 3/0/0 | 1/1/1 | 13/7/6 |
| Wikidata P18 | 1/1/1 | 1/0/0 | 2/0/0 | 0/0/0 | 1/0/0 | 1/1/1 | 1/0/0 |
| `haswbstatement:P180=<Q>` (depicts) | 0/0/0 | 5/4/4 | 4/3/2 | 1/1/1 | 8/0/0 | 3/3/3 | 2/0/0 |
| `incategory:` (P373 / sitelink) | 9/1/1 | 19/7/7 | 30/14/14 | - | 8/0/0 | - | 32/17/17 |
| `deepcat:` | 48/29/29* | 19/7/7 | 34/15/15 | - | 10/0/0 | - | 36/21/21 |
| other-language media lists (10 wikis) | 12/3/3 | 33/4/3 | 5/0/0 | 5/0/0 | 8/0/0 | 5/4/4 | 17/4/4 |

\* 28 of Emu War's deepcat hits come from its only subcategory, "George Pearce (Australian politician)":
useful for the Pearce beat, not "the Emu War".

What each technique is good for:

- **Category (`incategory:`) is the precision tool** once you have the right category. Norton: 17/17
  on-topic (Norton-1…10 portraits, Wasp caricatures) versus keyword top 50's 557 total hits full of other
  Nortons. Piltdown 14, Cottingley 7/7.
- **`deepcat:` is recall with risk.** It follows every subcategory. That's good when subcategories are facets
  of the topic (Piltdown) and bad when they are side entities (Pearce). "Strasbourg in the 16th century" via
  deepcat returned 2023 photos of museum paintings. Use subcategories as *labeled sub-pools*, not one bag.
- **Wikipedia media lists / `prop=images`** return what editors chose to illustrate the article, with
  captions (REST gives `caption.text` and a `leadImage` flag). They're small (1-14) and also include local
  non-Commons files and icons. Good seeds, and the captions are useful context for the picker.
- **Wikidata P18** is a single file. Emu War's is `TheGreatEmuWarcolage.png` (2441x3037, PD, a 2021
  collage of the real 1932 photos); it's the *only* full-size on-topic Emu War image. Fine as a seed; not
  a strategy.
- **Depicts (P180)** is spotty for events but strong for things: at beat level, *Hirudo medicinalis* 19/50,
  bagpipes 26/50, pineapple 9/50.
- **Precision operators** that work in `gsrsearch`: `fileres:>800` (sqrt of w×h), `filew:`/`fileh:`,
  `filemime:`, `intitle:`, `insource:`, `hastemplate:`, and `haswbstatement:` OR-ed with `|`. The structured
  license filter
  `haswbstatement:P6216=Q19652|P275=Q6938433|P275=Q20007257|P275=Q14947546|P275=Q18810333|P275=Q19125117|P275=Q30942811`
  (PD, CC0, CC BY 4.0/3.0/2.5/2.0/1.0) made Piltdown 12/12 usable, but misses files without structured
  license statements. Use it as a precision variant, not the only query.
- **Lead image with `pilicense=free` is not "Commons-free"**: for Cottingley it returned an English-Wikipedia
  local *PD-US* file. For the Emu War it returned "Deceased emu during Emu War.jpg", a dead bird our Never
  list forbids. Every seed still goes through the license and content checks.

Topic notes (ids verified live): Emu War Q14665, category "Emu War" (10 files); Cottingley Q1136743, category
"Cottingley fairies" (21); Piltdown Q244937 (31 files, subcategory "Piltdown Man (pub)"); spaghetti hoax
Q185736 (no P18, no category); Koepcke Q95273 (8 files, all CC BY-SA); dancing plague Q3295141 (no P373,
but Commons has "Category:Dancing plague of 1518" with the same 3 files keyword search finds); Norton
category "Joshua Abraham Norton" (32 files).

### 2.2 Per-beat test: keyword route vs entity route (`wm_beats.py`, 38 beats, 5 episodes)

The entity route used here: for each Wikipedia title the beat names, resolve the QID and take the lead
image + P18, then `incategory:"<P373 or commonswiki sitelink>" filetype:bitmap` (50) and
`haswbstatement:P180=<QID> filetype:bitmap` (50). The keyword route is exactly pick.py's (each query, top 12).

| episode | keyword usable per beat | entity usable per beat |
|---|---|---|
| ep035 Caraboo (real queries) | 6, 0, 0, 5, 7, 0, 0, 0 = 18 | 4, 2, 24, 18, 33, 4, 26, 34 = 145 |
| ep001 Emu War | 3, 0, 4, 1, 3, 5, 5, 7 = 28 | 25, 37, 24, 29, 25, 28, 42, 2 = 212 |
| ep005 Dancing plague | 7, 7, 3, 0, 3, 5, 8, 4 = 37 | 54, 3, 21, 89, 16, 62, 26, 6 = 277 |
| Koepcke (hypothetical beats) | 0, 2, 1, 4, 0, 4, 1 = 12 | 0, 12, 21, 42, 1, 34, 38 = 148 |
| Spaghetti hoax (hypothetical) | 3, 4, 10, 1, 7, 6, 11 = 42 | 30, 0, 0, 45, 37, 26, 28 = 166 |
| **total (38 beats)** | **137, 9 beats with none** | **948, 3 beats with none** |

The routes barely overlap, so run both. Entity examples: Lewis gun (Q373396, category "Lewis Gun") 22/50;
emu (Q93208, "Dromaius novaehollandiae") 18/50; George Pearce 28/39; Strasbourg 34/50; Sebastian Brant
33/50; Lockheed L-188 Electra 10/42; Bristol Royal Infirmary 13/48.

### 2.3 Relevance by eye: 23 beats, SigLIP-ranked (`clip_rerank.py`, `sheets/top1_part*.jpg`)

I compared the first keyword result (what the picker sees first) against the entity candidate that SigLIP
ranked first for the beat's intended picture. ✅ = shows the line, ~ = related (right subject, wrong era or
place), ❌ = wrong subject.

| beat: wanted picture | keyword #1 today | entity route, SigLIP #1 |
|---|---|---|
| 035-1 Caraboo portrait | ✅ Edward Bird portrait 1817 | ✅ same |
| 035-2 19th-c. Knole Park, Glos. | none usable | ~ Almondsbury aerial 2005 |
| 035-3 botanical pineapple | none usable | ✅ Blanco, *Flora de Filipinas* plate, 1880 |
| 035-4 19th-c. ship in rough sea | ✅ *Wreck of the William and Mary* 1817 | ~ naval capture painting |
| 035-5 Regency archery/fencing | ❌ NYPL sheet-music page | ~ 1902 archer drawing (period kermis archery print #2) |
| 035-6 1817 engraving of Caraboo | none usable | ✅ Caraboo engraving (1908 book, Caraboo category) |
| 035-7 19th-c. Philadelphia street | none usable | ~ Peace Jubilee stereograph 1898 |
| 035-8 leech jar | none usable | ~ leech anatomy plate 1876 |
| 001-1 soldiers, Lewis gun, emus | ✅ Emu War collage | ~ Lewis gunners 1941 |
| 001-2 WA wheat farm, 1930s | none usable | ~ wheat field 2018 |
| 001-3 Australian soldiers, Lewis gun | ✅ SLNSW Australian infantry 1930 | ~ Lewis gunners 1941 |
| 001-4 flock of emus | ✅ emus 2010 | ✅ emus 2009 |
| 001-5 jammed machine gun, 1932 | ❌ Lewis Powell (Lincoln conspirator) | ~ Lewis gunners 1941 |
| 001-6 George Pearce | ✅ Jensen, Pearce and Hughes 1916 | ✅ Pearce portrait 1910 |
| 001-7 Parliament House 1930s | ~ close-up of Parliament 1935 | ✅ opening of Old Parliament House 1927 |
| 001-8 wheatbelt landscape | ~ wheatbelt panorama 2008 | ~ Emu War collage |
| K-1 Juliane Koepcke | none usable | none usable (all CC BY-SA) |
| K-2 Lima airport c. 1971 | ❌ Robert T. Koepcke, US official, 2023 | ✅ Lima airport aerial |
| K-3 Lockheed L-188 Electra | ❌ 1931 magazine page | ✅ L-188 Electra photo 1987 |
| K-4 Amazon rainforest | ✅ rainforest near Puerto | ✅ rainforest aerial 2014 |
| K-5 H.-W. Koepcke at Panguana | none usable | ❌ a beetle from Panguana |
| K-6 river in Amazon jungle | ~ Río Pachitea 1905 | ✅ Río Tambo/Ucayali aerial 2019 |
| K-7 loggers, Peruvian Amazon | ❌ Pucallpa airport 2015 | ~ bulletwood logging, Guyana 2006 |

Totals: keyword #1 was ✅ 7, ~ 3, ❌ 5, empty 8; entity #1 was ✅ 10, ~ 11, ❌ 1, empty 1; the better of the two
was ✅ 13, ~ 8, ❌/empty 2. Beats with no acceptable candidate anywhere in their pool: keyword 13/23, entity 2/23.
Caveat: one judge (me), 23 beats, and the real picker sees 5 candidates, not 1. The pool-level number
(13 vs 2) is the fairest comparison.

SigLIP absolute scores separate good from wrong fairly well: matches scored about 0.10-0.16 (pineapple plate
0.112, archer 0.135, L-188 0.138, Lima airport 0.145), wrong ones -0.14 to 0.03 (Koepcke homonym hits -0.12/-0.14,
sheet music -0.04, beetle -0.03, leech anatomy 0.02). A starting "weak beat" threshold of about 0.06 is
plausible; calibrate on the 15 rejected Shorts before trusting it.

### 2.4 Period: the entity route's weakness, and three fixes

Year spread of usable candidates (`wm_years.py`; year from `DateTimeOriginal`):

| episode (era window) | keyword: usable / dated / in era | entity: usable / dated / in era / dated ≥1990 |
|---|---|---|
| ep035 (1760-1880) | 18 / 9 / 5 (56%) | 136 / 124 / 11 (9%) / 94 (76%) |
| ep001 (1890-1950) | 28 / 27 / 15 (56%) | 132 / 127 / 80 (63%) / 45 (35%) |
| Koepcke (1955-1990) | 13 / 13 / 0 | 148 / 132 / 18 (14%) / 72 (55%) |

"Dated ≥1990" also includes modern scans of old art (the scan date lands in `DateTimeOriginal`), so the
date alone over-rejects. Fixes:

1. **Time-scoped Commons categories** (`wm_timecats.py`). One `prop=categoryinfo` call probes the naming
   patterns "<Place> in the <decade>s", "<year> in <Place>", "<Place> in the <Nth> century":

   | category | files | subcats | sample usable |
   |---|---|---|---|
   | Philadelphia in the 1810s | 62 | 16 | 27/30 usable, dated 1811 (Krimmel street scenes) |
   | Strasbourg in the 16th century | 19 | 14 | 16/19 usable: Hans Baldung Grien 1520, a Strasbourg print 1517 |
   | San Francisco in the 1870s | 53 | 21 | (Norton's city and decade) |
   | 1971 in Lima / 1971 in Peru | 17 / 11 | 0 / 6 | (Koepcke's year) |
   | 1957 in London | 8 | 22 | (spaghetti hoax year) |
   | Western Australia in the 1930s / 1932 in WA | 11 / 5 | 15 / 2 | 1932 in WA: 4 small, 1 BY-SA |
   | 1810s fashion | 116 | 25 | (Regency costume beats) |
   | Bristol in the 1810s, 1518 in Strasbourg, Piltdown | missing | | fall back to "<Place> in the 19th century" (Bristol: 57) |

   Use `incategory:` on these, not `deepcat:`.
2. **Metadata year window** when a year exists (`DateTimeOriginal`, or structured data P571 inception).
3. **Zero-shot SigLIP "historical vs modern"**: the prompts "a modern color photograph" vs "a historical
   image: an old engraving, painting, drawing, or black-and-white photograph". Called 84.8% of 230 pre-1945
   files "historical" and 91.4% of 266 post-1990 files "modern", and some "misses" are modern scans of old
   art, where the classifier is actually right. Drop only when the beat is historical, the classifier is
   confident it's modern (p < 0.2), and no in-window date exists.

### 2.5 What our strict filter throws away (on-topic files found by topic-aware techniques, `wm_gains.py`)

| topic | on-topic files | usable now | only "No restrictions" | only format (tiff/webp/gif) | only small: 800-1199 / 600-799 / <600 | BY-SA or NC | local to a Wikipedia |
|---|---|---|---|---|---|---|---|
| Emu War | 54 | 32* | 0 | 1 | 8 / 2 / 7 | 3 | 0 |
| Cottingley | 47 | 11 | 0 | 1 | 2 / 3 / 6 | 11 | 13 (6 enwiki PD-US) |
| Piltdown | 37 | 16 | 4 | 0 | 2 / 1 / 0 | 12 | 0 |
| Spaghetti | 6 | 1 | 0 | 0 | 0 | 4 | 1 |
| Koepcke | 15 | 0 | 0 | 0 | 1 / 0 / 0 | 14 | 0 |
| Dancing | 7 | 6 | 0 | 0 | 0 | 1 | 0 |
| Norton | 40 | 22 | 0 | 0 | 4 / 4 / 4 | 6 | 0 |

\* includes the Pearce subcategory. The actual 1932 Emu War photos are all PD and **all small**: Lewis gun
480x360, Ray Owen 450x306, soldiers resting 900x522, emus coming to drink 450x299, McMurray 450x270, fallow
field 450x299. Today we can never show a real Emu War photo.

- Cottingley: the famous photos are English-Wikipedia-only "PD-US" (CottingleyFairies2.jpg 1308x1789; others
  381-623 px). They are PD in the US (published 1920) but likely not in the UK, where the girls who took
  them died in the 1980s; that is the likely reason Commons doesn't host them. "Cottingley Fairies 1.webp" (1200x900, PD) fails only on format.
- Piltdown: 4 on-topic scans fail only on "No restrictions", and 17 were rejected for it in the keyword top 50.
  These are Internet Archive Book Images (American Museum Journal, *Popular Science Monthly* 1913) mirrored
  from Flickr Commons with `{{Flickr-no known copyright restrictions}}`, all dated 1900-1918.
- BY-SA is the biggest single loss and must stay excluded (Koepcke's entire category).

## 3. Part B: other free archives

| archive | key | limits (observed / documented) | from this machine | license fields | relevance to our topics | verdict |
|---|---|---|---|---|---|---|
| **Openverse** | none (free OAuth app registration raises limits) | anon live headers: 20/min burst, 200/day; `page_size` > 20 → HTTP 401; max 240 results. Registered: 100/min, 10,000/day; "enhanced" 200/min, 20,000/day (`api/conf/settings/rest_framework.py:35-38`) | 200 | `license`, `license_version`, `license_url`, `creator`, `source`, `foreign_landing_url`, and a ready `attribution` sentence | timeless/modern subjects. `license=cc0,pdm,by`: Emu War 16, Piltdown 173 (mostly modern pond photos), Cottingley 1, Norton 75, spaghetti tree 49 (CC BY recreations), dancing mania 13 (Wellcome Hondius 2823x3723). Flickr images ≤ 1024 px. "Lockheed Electra" returns 1930s Electra 10E/12A, a homonym | BORROW (secondary source) |
| loc.gov JSON / Chronicling America | none | documented: JSON 20/min with a 1-hour block; images 150/min | **403 (Cloudflare) on every JSON call**; `tile.loc.gov` images 200; `chroniclingamerica.loc.gov` → 308 to loc.gov | `rights`, `rights_advisory` | high in theory (US newspapers, OCR, word coordinates for headline crops). Datacenter blocks reported: searxng #4810, congress.gov #437, api.congress.gov #412 | SKIP (unreachable); use Commons DPLA/LoC mirrors |
| Smithsonian Open Access | api.data.gov key (free signup) | `DEMO_KEY` header limit 10 | 200 with `DEMO_KEY` | `metadata_usage.access`, media `usage.access` (CC0) | natural history and objects ('emu AND online_media_type:Images' matched 119,522 rows, a broad match dominated by NMNH bird records); odd events weak (Piltdown 3 records, no media) | BORROW for animals/objects (optional key) |
| Europeana | free key | `api2demo` shared quota | 200 | per-item `rights` URL; `reusability=open` **includes BY-SA** | Piltdown 9 (Wellcome mirrors), Norton 0, dancing mania 2, emu 314 | WATCH |
| Rijksmuseum | none (new Linked Art search) | - | 200 | via Linked Art objects | search returns bare IDs ("emu" 0, "dansen" 538); images largely on Commons | SKIP |
| Cleveland Museum of Art | none | - | 200 | per-item `share_license_status` (`cc0=1` changed nothing: dance 357, fairy 38, emu 0) | generic art; web images 600-1,263 px wide | SKIP (Met/AIC already cover art) |
| **Wellcome Collection** | none | no rate headers | 200 | `locations[].license.id`; filter `locations.license=pdm,cc-0,cc-by` drops NC and "in copyright" | medicine and science: leech 138 filtered (leech jars, ep035 beat 8), Piltdown CC BY items, dancing mania Hondius. Gore noise (a hanging) | **ADOPT** as the medicine/science source |
| Internet Archive | none | - | 200 | rights fields mostly empty (0 of 15 Piltdown items had a license URL) | scans exist, rights unknown | SKIP direct; use the Commons "IA Book Images" mirror (NKCR rule, §7) |
| Trove (NLA) | key, 7-28 day approval; commercial use needs an exemption | - | 401 | - | Australian papers (Emu War!) | SKIP |
| NYPL Digital Collections | token | - | 401 | - | PD items mirrored on Commons | SKIP |
| Flickr Commons | API key needs Flickr Pro; commercial key needs approval | - | - | license 7 = "no known copyright restrictions" | Openverse doesn't ingest license 7 (`catalog/dags/providers/provider_api_scripts/flickr.py:31-40` maps only 1-6, 9, 10) | SKIP direct; Commons mirrors only |
| DPLA | key (email signup) | - | 403 | per-item rights | DPLA newspaper pages are uploaded to Commons (Boston Evening Transcript 1925, 7542x10373, PD) | SKIP direct |
| NGA open data | none (GitHub CSV, 832★, CC0-1.0, pushed 2026-09-27) | - | - | CC0 dataset | no search API; open images mirrored on Commons | SKIP |

## 4. Part C: repos

### 4.1 louisedesadeleer/b-roll-finder: BORROW IDEA

119★, last push 2026-06-11, MIT (LICENSE: "Copyright (c) 2026 Louise de Sadeleer"), not archived.

What it is: an agent skill (methodology plus one script), not a pipeline. Stages: (1) classify each moment
into a route; (2) interpret "what is this line actually about?"; (3) source by source rather than by beat;
(4) vet with a rubric; (5) place on the word; (6) the user picks. Key files: `SKILL.md` (278 lines),
`TASTE.md` (profile), `scripts/zoom_still.py` (42 lines).

Techniques worth stealing:
- **Routing per moment** (`SKILL.md:121-134`): Receipts / Entity / Concept / Meme, with the litmus
  "*Happening now?* → Receipts. *A person / product / event?* → Entity (official source). *An abstract idea?*
  → Concept." For us: Entity → Commons entity route; Concept → designed shot.
- **"Every beat passes a per-citation interpretation — write 'what is this line actually about?' first,
  then source THAT"** (`SKILL.md:78`). Maps to a writer field (`entities`, `era`) instead of free-text queries.
- **"⛔ Cards never replace real footage of a literal thing"** (`SKILL.md:129`): a designed card is a failure
  when a real picture of the named thing exists.
- **"NO RETRIES — first failure switches, second failure drops"** (`SKILL.md:64`): switch *method or source*
  instead of re-querying the same source. Our `second_round` (`pick.py:254-272`) asks the LLM for three more
  Commons keyword searches, which is exactly the retry it warns against.
- **Sub-pixel still motion** (`scripts/zoom_still.py:36-40`): each frame is
  `base.resize((W,H), Image.LANCZOS, box=(x0,y0,x0+bw,y0+bh))` with a float box and scale
  `s = 1 + rate*t` (~1.5%/s). `zoompan` is banned as stuttery (`SKILL.md:169-173`). **Blurred fill**
  (`zoom_still.py:24-28`): fit the source at 88% over a `GaussianBlur(45)` cover copy. That's exactly the
  treatment for our small PD event photos.
- Vetting rubric (`SKILL.md:183-`): recency fit, source authority, relevance, recognizability, format fit.

Better than ours: route thinking and the switch-don't-retry rule. Worse or irrelevant: YouTube-first via
yt-dlp (forbidden for us) and a human makes the final pick.
Adoption: idea only; the zoom script is small enough to rewrite (S, CPU-only, pennies). Risk: frame
rendering in PIL is slower than zoompan (1080x1920x30 fps; test the cost on Modal).

### 4.2 joeseesun/qiaomu-cut-skill: BORROW IDEA

338★, last push 2026-07-19, MIT (LICENSE "Copyright (c) 向阳乔木"), not archived. JavaScript skill for
"governed sourcing" of video clips.

Key files: `references/source-selection-gate.md`, `references/licensing.md`, `scripts/ingest_asset.js`,
`scripts/license_report.js` (71 lines), `scripts/source_review.js` (contact sheets).

Techniques worth stealing:
- **Visual contract before searching** (`source-selection-gate.md:7-18`): subject, appearance, action,
  camera, light, `setting: 场景、背景复杂度、年代和地域` (scene, background, **era and region**), continuity,
  `reject:` list.
- **"The target count is a maximum, not a KPI; 7/10 unique good assets beat 10/10 with repeats"** (`:21`).
  SHA-256 dedupe after download (`:23`), perceptual hashes of sampled frames for near-duplicates (`:24`).
  ep035's two files of the same Edward Bird painting are this case.
- **Pool 2-3x the target, thumbnail pre-filter before download** (`:49`); **"two weak rounds → switch
  provider"** (`:53`); "search titles and tags can't replace visual review" (`:54`).
- **License status per asset** (`licensing.md:8-14`): `provider` + `licenseStatus` from `verified |
  verify_at_provider | user_provided | ai_generated | unknown`; discovery sites are "discovery only" (`:29`),
  never license proof. `license_report.js:38-39` writes `sourcePage` and `licenseStatus || 'unknown'` into
  a per-project table.

Better than ours: explicit license states, a hash-based duplicate gate, an era/region contract. Worse: clip
discovery goes through ClipSeek (a Chinese aggregator), and a human is in the loop.
Adoption: idea (S): add `licenseStatus` and `sha256`/`phash` to our credit dict, plus a license report per
Short. No Modal cost.

### 4.3 AIScientists-Dev/WorldSeed, `skills/asset-sourcing`: BORROW IDEA

821★, last push 2026-05-08, MIT ("Copyright (c) 2026 AIScientists Inc."), not archived.

Pipeline: entities with roles → literal/related/vibe query triads per role → source order per role →
candidate board (HTML) → human or agent review. Key files: `SKILL.md`, `references/source-catalog.md`,
`scripts/search_candidates.py`.

Techniques worth stealing:
- Roles and templates (`SKILL.md:95-115`): `agent` → `{label} portrait` / `{label} figure` /
  `{label} painting`; `item` → `{label}` / `{label} still life` / `{label} object`; `zone` →
  `{label} interior` …
- Source order per role (`SKILL.md:124-127`): agent → openverse, aic, wellcome; item → openverse, aic,
  cleveland; symbolic → openverse, wikimedia, nasa.
- **"Treat metadata as recall only. Final retention and top picks must be image-verified"** (`:64`) and
  **"Reject obvious homonym and name-collision matches when the image subject is wrong, even if the title
  contains the entity token"** (`:65`, `:142`). This is precisely our Lewis Powell / Robert T. Koepcke failure.

A caution, not something to copy: `cleveland_search` (`search_candidates.py:484-523`) sends
`{"q", "has_image", "limit"}` with no CC0 filter, yet labels every result `rights_text="Open Access / CC0"`
(`:521`). Wellcome and Openverse searches record the license but don't filter on it (`:400-444`, `:256-286`).
Never trust a source adapter's hard-coded rights string.

Better than ours: role-based routing, homonym rule. Worse: no Wikidata/category use; license labeling bug.
Adoption: idea (S).

### 4.4 WordPress/openverse (API and catalog code): BORROW IDEA (as a source)

379★, last push 2026-09-25, MIT, not archived. Read `api/conf/settings/rest_framework.py` and
`catalog/dags/providers/provider_api_scripts/flickr.py`. Code defaults are anon 5/hour burst and 100/day
(`rest_framework.py:10-11`); production headers seen live were 20/min and 200/day. OAuth apps get 100/min and
10,000/day (`:35-36`). Flickr ingestion excludes license 7 "no known copyright restrictions" and 8 "US
Government Work" (`flickr.py:31-40`). Use `license=cc0,pdm,by`, not `license_type=commercial,modification`,
which admits BY-SA. Adoption: S, a 40-line adapter; register a free app for production limits.

### 4.5 CLIP-style reranking: mlfoundations/open_clip + SigLIP weights: ADOPT

open_clip: 14,170★, pushed 2026-09-25, LICENSE is MIT text (GitHub shows "other"), not archived.
Weights (Hugging Face model cards, checked live): `timm/ViT-B-16-SigLIP` **apache-2.0**,
`timm/ViT-B-16-SigLIP2` apache-2.0, `laion/CLIP-ViT-B-32-laion2B-s34B-b79K` MIT. Avoid:
`apple/MobileCLIP2-*` and `apple/DFN2B-*` (`apple-amlr`, research license), `facebook/metaclip-*`
(cc-by-nc-4.0), and OpenAI CLIP: the repo is MIT, but its model card says "**Any** deployed use case of
the model - whether commercial or not - is currently out of scope."

CPU benchmark (`clip_bench.py`, Apple M3, torch 2.14, open_clip 3.3, batch 16, 224 px):

| model | params | image ms (4 threads) | image ms (1 thread) | text ms | load |
|---|---|---|---|---|---|
| ViT-B-32 / openai | 151 M | 12.0 | 12.1 | 10.2 | 2 s |
| **ViT-B-16-SigLIP / webli** | 203 M | **37.4** | 51.6 | 11.4 | 7 s |

At about 300 thumbnails per Short (≈35 per beat): ~11 s here; estimate 25-60 s on a 2-vCPU Modal
container (x86 is slower per core than M3), well under a cent. Bake the ~0.8 GB weights into the image or a
Volume. Relevance results are in §2.3; the period classifier in §2.4. Adoption: code (M): a
`rank(beat_text, thumbs)` helper, SigLIP scores stored per candidate, the top 6-8 sent to Gemini.
Risks: SigLIP can't read captions or text in images and can't judge "is this the *right* Pearce". It
pre-filters; Gemini still decides.

### 4.6 erfsalehi/B-Roll-Finder: BORROW IDEA (one)

4★, last push 2026-09-27, **no license** (all rights reserved; don't copy code), not archived. A local
"AI director" over Pexels, Pixabay and YouTube, plus Google Images via Serper (`core/related_images.py`),
which is license-agnostic. One good idea: `review_timeline` (`core/director_rank.py:245-314`), a single
"executive producer" LLM pass over the chronological list of picks that flags "thematic breaks, repetition,
continuity/pacing problems, and intent mismatches", each pinned to a slot and ignoring hallucinated slot
ids (`:292-293`). We have a whole-video review. A cheap *text-only* pre-render pass over the pick list
(beat line → chosen file title, date, caption) would catch repeats and period breaks before rendering. S.

### 4.7 Smaller repos

| repo | ★ / last push / license (LICENSE file) / archived | what the code does | verdict |
|---|---|---|---|
| mnalis/commons_check_search_api | 1 / 2024-06-03 / Apache-2.0 / no | compares Commons category-search APIs for the Commons Android app. `action=opensearch&namespace=14` matches case-insensitive prefixes best (`output.md`). Live: "Dancing plague" → Category:Dancing plague of 1518 (Wikidata has no category link); "Knole Park" → the *Kent* estate (homonym) | BORROW IDEA: category-name fallback, exact-label match only |
| sasoder/stockpile | 36 / 2025-07-20 / none / no | Gemini turns a transcript into ≥10 phrases of 2-6 words naming "a tangible scene, person, object or event" (`src/services/ai_service.py:65-97`), searches YouTube (yt-dlp), and scores results on title and description only (`:203-225`) | SKIP (YouTube, text-only scoring, no license) |
| touge1618/touge-collage-video | 1 / 2026-07-26 / MIT / no | AI paper-collage B-roll via paid OpenRouter models (gpt-image-2, seedance) behind human approval pages | SKIP (paid, human in loop) |
| neno-is-ooo/mcp-openverse | 18 / 2025-06-12 / MIT / no | thin MCP wrapper; claims `page_size` up to 500 (anon fails above 20); no license enforcement | SKIP |
| mehdidc/clip_rerank | 15 / 2021-05-03 / none / no | a script that ranks a folder of images by CLIP similarity to text | SKIP (use open_clip directly) |
| JYNIDA/broll-finder | 0 / 2026-03-29 / none / no | Korean-language skill; saves a `sources.md` per episode (`SKILL.md:264-268`) | SKIP |
| CharlesPikachu/imagedl | 167 / 2026-09-27 / Apache-2.0 / no | multi-site downloader for training sets (Google, Bing, Baidu, Yandex… plus AIC, Cleveland, Met, Openverse, Wellcome) with no license logic | SKIP |
| NationalGalleryOfArt/opendata | 832 / 2026-09-27 / CC0-1.0 / no | CSV dumps with IIIF image URLs, no search API | SKIP |

Seen in search but not read (descriptions only; none targets historical stills): andriidrok1/autobroll
(12★, MIT), AbdullahNaveed/ai-shorts-generator (11★, MIT), nitishlakra1952/broll-finder-ai (0★, MIT),
rebellovandana65-cmd/space-chronicles-ai (NASA + Gemini, 0★), himax12/ClipSync, nikbearbrown/brutalist.art.
Searches for "stock footage search llm", "image search clip rerank" and "historical image search" returned
nothing relevant.

## 5. Proposed sourcing strategy for pick.py

Principle: **name the subject, then fetch the thing, and only then search words.** Keyword search stays as
a fallback and a complement, since it won 3 beats outright in §2.3.

### 5.1 Writer / research change (small)

Each beat gets, alongside `visual` and `queries`:
`entities: [{"title": "<exact English Wikipedia title>", "role": "person|place|object|animal|event|artwork"}]`
(1-3), `year` or `era: [from, to]`, and `timeless: true|false` (animals, landscapes, aircraft types).
Research gets the topic's article title. The prompt should say: "name the thing the viewer should *see*,
as a Wikipedia article".

### 5.2 Per topic, once per episode (≈4 API calls)

1. English Wikipedia, batched titles (topic + every beat entity, ≤50 per call):
   `GET en.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&redirects=1&titles=A|B|…&prop=pageprops|pageimages&ppprop=wikibase_item&piprop=name&pilicense=free`
   → QID and free lead image per title; missing titles go back to the writer for one retry.
2. `GET en.wikipedia.org/api/rest_v1/page/media-list/<Topic_Title>` → editor-chosen files **with captions**
   (drop svg/icons), for the topic article only.
3. Wikidata, batched (≤50 ids):
   `GET www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=Q…|Q…&props=claims|sitelinks&sitefilter=commonswiki`
   → P18 files, category = P373 or `sitelinks.commonswiki.title`, P571/P585 dates.
4. Missing category → `GET commons.wikimedia.org/w/api.php?action=opensearch&format=json&namespace=14&limit=5&search=<label>`,
   accepting only an exact case-insensitive label match.
5. Time-scoped categories for place entities with a year, all in one call:
   `action=query&prop=categoryinfo&titles=Category:<Cat> in the <decade>s|Category:<year> in <Cat>|Category:<Cat> in the <Nth> century`
   → keep the ones with `files > 0`.

### 5.3 Per beat (≈2-4 searches; results cached per episode)

All searches use pick.py's existing call (`generator=search&gsrnamespace=6&gsrlimit=50&prop=imageinfo&iiprop=url|size|mime|extmetadata&iiurlwidth=330`),
adding `LicenseUrl|Artist|DateTimeOriginal|ImageDescription` to `iiextmetadatafilter` (plus `titles=` for
P18 and lead files):

6. `incategory:"<entity category>" filetype:bitmap`, and `incategory:"<time category>" filetype:bitmap` when one exists.
7. `haswbstatement:P180=<QID> filetype:bitmap` (depicts).
8. Keyword complement: the beat's existing queries as `"<query>" filetype:bitmap` (top 12), plus a precision
   variant `<query> filetype:bitmap fileres:>800 haswbstatement:P6216=Q19652|P275=Q6938433|P275=Q20007257|P275=Q14947546|P275=Q18810333|P275=Q19125117|P275=Q30942811`.
9. Role-based extras, **only if the beat is still weak** after step 11 (best SigLIP < ~0.06, or fewer than 3
   in-period candidates):
   - medicine/science/objects → Wellcome `GET api.wellcomecollection.org/catalogue/v2/images?query=<q>&locations.license=pdm,cc-0,cc-by`
   - timeless things/places/aircraft → Openverse `GET api.openverse.org/v1/images/?q=<q>&license=cc0,pdm,by&page_size=20`
   - animals/natural history → Smithsonian (free key; both usage fields CC0)
   - art → the existing Met (`isPublicDomain`) and AIC (`is_public_domain`) adapters

### 5.4 Filter, dedupe, rank

10. Filter (license rules in §7), then size tier: ≥1200 px full-bleed; 450-1199 px only in a framed/blurred-fill
    treatment (or a collage of several small period photos); below that, reject. Format: jpeg/png, or
    tiff/webp/gif through Commons' JPEG thumbnail at a standard step (960/1280/1920). Period: in-window year →
    keep; historical beat + SigLIP "modern" p < 0.2 + no in-window year → drop. Content: the Never list,
    and seeds such as the "Deceased emu" lead image are not exempt.
11. Dedupe across the whole episode: file title, then perceptual hash (`imagehash`, BSD-2, pHash distance
    ≤ 8) on the 330 px thumbnails. That catches two uploads of one painting.
12. SigLIP score against the beat's `visual` text; small boosts for entity-route hits, in-period, full-size.
    Keep the top 6-8 per beat (instead of the first 5 in search order) and a pool of 12.
13. Gemini pick as today, with each candidate's caption/description, entity label, year and size tier.
14. Store the **file title** (`"file": "File:…"`) and the license record, and have the renderer fetch by title
    (`prop=imageinfo&titles=File:…`) and re-check the license. That retires `pin()`'s "can't pin" losses.

### 5.5 Picture-poor beats (Koepcke beat 1, spaghetti's BBC beats)

After the extras: (a) a real small photo in the framed treatment; (b) a collage of several small period
photos (the pattern of `TheGreatEmuWarcolage.png`); (c) a designed shot (map, date card, document or quote
card) built from real material; (d) AI images only with disclosure (CONTEXT rule), never a realistic picture
of a real person.

Cost: `wm_beats2` used 145 calls for 3 episodes (≈48 per Short including keyword searches), about 1-2 min
at polite pacing with ≤4 parallel requests. Add SigLIP at 25-60 s CPU (estimate). Gemini sees about the same
number of thumbnails as today, or fewer.

## 6. Expected gains (from the live counts)

- Candidate volume: 137 → 948 usable across 38 beats (≈7x); beats with nothing usable: 9 → 3.
- Relevance: pools with no acceptable candidate: 13/23 → 2/23; acceptable top-1: 10/23 → 21/23; exact
  top-1: 7 → 13 (combined routes). Time categories and Wellcome upgrade at least two more of the "related"
  beats to exact (ep035 beat 7: Krimmel's 1811 Philadelphia; beat 8: Wellcome leech jars).
- Fewer duplicates: fewer empty beats means less fallback into the shared pool (ep035's failure), and pHash
  catches the rest.
- Period: time categories give in-era sets directly (Philadelphia 1811; Strasbourg 1517-1520).
- Topic-level additions from license rules and treatment: Emu War gains its 6 real (small) 1932 photos;
  Piltdown +4 on-topic from the category route (its keyword top 50 also rejected 17 "No restrictions"
  scans, all dated 1900-1918) and Wellcome CC BY items; Cottingley +1 (webp) plus 6 PD-US files if the
  owner opts in.
- No gain for Koepcke portraits (all BY-SA) or the BBC broadcast itself: those beats need designed shots.

## 7. License-handling rules

| case | rule |
|---|---|
| PD (`Public domain`, `PD-*`), CC0, PDM | accept |
| CC BY 1.0-4.0, including ported versions (`CC BY 2.0 de`) | accept, with credit |
| `No restrictions` (Flickr Commons NKCR) | accept **only if** a publication year ≤ 1930 appears in `DateTimeOriginal`, the title, or P571 (US PD); otherwise reject |
| English-Wikipedia-local `PD-US` | off by default; allowed per topic only with `licenseStatus: pd_us_only` and never for the thumbnail. Likely not PD in the UK (the probable reason Commons doesn't host them) |
| BY-SA, NC, ND, GFDL, LGPL, "copyrighted", non-free, empty or unknown | reject |
| TIFF/WebP/GIF | accept via Commons JPEG thumbnails at a standard width |
| a source adapter's hard-coded rights text | never trusted; read the per-item field |

Per-source checks: Commons `LicenseShortName` (plus `LicenseUrl`), or structured data P6216/P275; Openverse
`license in {cc0, pdm, by}`; Europeana `rights` URL must contain `publicdomain/mark`, `publicdomain/zero` or
`licenses/by/` (not `by-sa`); Wellcome `locations[].license.id in {pdm, cc-0, cc-by}`; Cleveland
`share_license_status == "CC0"` per item; Smithsonian `metadata_usage.access` and media `usage.access` both
`CC0`; Met `isPublicDomain`; AIC `is_public_domain`.

Record per asset (extend `visuals.py:190-196`'s credit dict): `source`, `file`/id, `page` (source page URL),
`creator` (`Artist`, HTML stripped), `license`, `license_url`, `date`, `retrieved` (ISO date), `licenseStatus`
(`verified | pd_by_date_nkcr | pd_us_only | ai_generated`), `sha256`, `phash`, and a credit line
("Title" by Creator, CC BY 2.0, via Wikimedia Commons; cropped and zoomed). Put CC BY credits in the video
description, and write one license table per Short next to `visuals.json`.

Keep the Wikimedia etiquette: descriptive User-Agent with contact, ≤4 parallel requests, back off on 429
using `Retry-After`, cache per episode.

## Top insights for Days of Odd

1. **Entity-first retrieval per beat** (writer names Wikipedia titles → QID → P18, category, depicts). The
   largest measured win: usable candidates 137 → 948; pools with no acceptable picture 13/23 → 2/23.
   Effort M, zero cost.
2. **Time-scoped Commons categories plus a period filter** (date window, and SigLIP "historical vs modern"
   for undated or re-scanned files). Fixes wrong-period pictures; "Philadelphia in the 1810s" alone gives
   27 usable 1811 images. Effort S.
3. **SigLIP ViT-B/16 (Apache-2.0) pre-rank on CPU**: send Gemini the best 6-8 of 30-60 per beat, not the
   first 5 in search order, and use the score as a "weak beat" trigger. 37 ms per image; under a cent per
   Short (estimate). Effort M.
4. **Store the chosen file title and a full license record; render by title.** Removes `pin()` losses and
   gives an auditable per-Short license table (qiaomu pattern). Effort S.
5. **Safe license widening**: NKCR only when dated ≤1930; TIFF/WebP via JPEG thumbnails; PD-US-only off by
   default. Recovers Piltdown scans and similar. Effort S.
6. **Framed or blurred-fill treatment (and small-photo collages) for real 450-1199 px photos** instead of
   dropping them. It lets us show the actual 1932 Emu War photos. Blurred fill as in
   `b-roll-finder/scripts/zoom_still.py:24-28`. Effort S.
7. **Episode-wide dedupe by title and perceptual hash**, and treat the 18-image pool as a last resort. Fixes
   the ep035-style duplicate-art rejection. Effort S.
8. **Switch sources instead of retrying keywords**: replace `second_round`'s three new Commons keyword
   searches with Wellcome (medicine/science), Openverse `license=cc0,pdm,by` (timeless subjects), Met/AIC
   (art), then a designed shot. Effort S-M.
9. **Homonym guard**: reject candidates whose only link to the beat is a shared surname or word unless the
   entity route or the image confirms them (WorldSeed `SKILL.md:65`). The category and depicts routes do
   most of this for free. Effort S.
10. **Sub-pixel Ken Burns** (PIL float-box Lanczos) instead of integer-step `zoompan`: removes stutter on
    slow zooms (`zoom_still.py:36-40`). Motion, not sourcing, but it came with the best-sourcing repo.
    Effort S; test render cost on Modal.
