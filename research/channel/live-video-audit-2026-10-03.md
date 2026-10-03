# History's Last Hours: sent-video audit (2026-10-03)

Read-only audit of local `publish.json`, `short.yaml`, `work/manifest.json`, downloaded public Cloudinary upload files, YouTube's public oEmbed endpoint, and linked institutional/history sources. Frame sheets: `../../reports/previews/history-live-ep009-frames.jpg`, `ep013_frames.jpg`, `ep025_frames.jpg`, `ep031_frames.jpg`, `ep042_frames.jpg`, `ep045_frames.jpg`. Times below are from final render manifests; images are sampled from the exact CDN MP4 in each sent record. No platform state changed. No retention inference is possible yet: local `performance.json` has no average viewed, engaged share, or 5-second retention for these clips.

## Which sent records are publicly resolvable

| Episode | YouTube ID | Public oEmbed | Render length |
|---|---|---:|---:|
| ep009 | X8MhmozMp0o | 403 | 47.15 s |
| ep013 | zX1VUGHLb0o | 403 | 47.33 s |
| ep025 | qtmFWWw0npA | 200, channel and title resolve | 29.67 s |
| ep031 | jl-V7yPkbkU | 200 | 32.53 s |
| ep042 | Jts8c-u_96U | 200 | 22.74 s |
| ep045 | v4rp0oWvgSI | 200 | 27.32 s |

The two 403s do not prove deletion/private status, but the six sent records should not be described as six currently public videos without a manual platform check. Test used `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json` with no login.

## Published, currently oEmbed-resolvable

### ep025 — `qtmFWWw0npA` — make private pending corrected reupload

- **Clear falsehood at beat 7, 22.32–25.64 s:** “The only survivors were engineers riding in external engine cars.” Six survived; four engineers were in engine cars. Foreman engineer Harry Leech and wireless operator Arthur Disley escaped from within the main cabin. Even local `research.json` claim 9 says “Four of the six survivors.” The Airship Heritage Trust confirms Leech rescued Disley from the wreck; a survivors list supplied by the Trust names all six. Suggested line: **“Six survived: four in engine cars, and two from the cabin.”** Sources: [Airship Heritage Trust, Harry Leech](https://airshipsonline.com/people/harry-leech/), [GENUKI, R101 survivors, supplied by Airship Heritage Trust](https://www.genuki.org.uk/big/Indexes/R101Survivors), [R101 overview with cabin detail](https://en.wikipedia.org/wiki/R101).
- **Overcertain causal account, beats 1 and 5, 0.08–3.30 s and 15.24–18.38 s:** “deadline forced” and “gales ... forced ... two steep ... dives” imply a settled single cause. The official inquiry's cause is still debated; the record does support political pressure, incomplete post-extension trials, bad weather, and two dives. Suggested framing: **“Under pressure to fly to India, R101 departed after limited trials. In rain and wind over France, it twice dived and crashed; the precise trigger remains disputed.”** Source: [R101 detailed history and inquiry summary](https://en.wikipedia.org/wiki/R101); [UK National Archives, public inquiry papers](https://discovery.nationalarchives.gov.uk/details/r/C5317784). This is a caution about certainty, not a proven false statement.
- **Frame receipt:** `../../reports/previews/history-live-ep025-frames.jpg`; 0.2–1.5 s R101 image with “RUSHED TO FLY”; 3.5–6 s pure date card delays the actual stakes, and 19.3 s says “48 DEAD.” Date card duration 4.2 s is a plausible retention risk, not measured drop-off.

### ep031 — `jl-V7yPkbkU` — make private pending corrected reupload

- **Clear incorrect opening text:** `hook_text` **“TWO GROUND ZEROS”** stays on screen from 0–4.8 s. Ground zero is the explosion point; beat 3 states he was about 3 km away in Hiroshima and beat 7 states 3 km away in Nagasaki. HISTORY puts him under two miles from each blast; the Guardian says *close to* ground zero, not at it. Suggested hook: **“SURVIVED TWO ATOMIC BOMBS”** or **“TWO BLASTS, ONE SURVIVOR.”** Sources: [HISTORY, Yamaguchi account](https://www.history.com/articles/the-man-who-survived-two-atomic-bombs), [Guardian, double survivor](https://www.theguardian.com/world/2009/mar/25/hiroshima-nagasaki-survivor-japan), [BBC, official recognition](https://news.bbc.co.uk/2/hi/asia-pacific/8443295.stm).
- **Source/visual mismatch, beat 2, 4.80–8.80 s:** displayed 1937 Mitsubishi employee photo identifies Yoshitoshi Sone and Jirō Horikoshi, not Yamaguchi. Narration identifies Yamaguchi as naval engineer. This is representative footage without a label, not an explicit on-screen identity claim. Replace with a verified Yamaguchi portrait or a neutral Mitsubishi/location card. [Wikimedia Commons file metadata](https://commons.wikimedia.org/wiki/File:Employees_of_the_Mitsubishi_Heavy_Industries_193707.jpg).
- **Frame receipt:** `../../reports/previews/history-live-ep031-frames.jpg`; 0.2, 1.5, 3.5 s are black text cards dominated by **“EXPLAINING”**, with no person/atomic-bomb visual until 4.8 s. This is a strong visual-hook risk but cannot be linked to retention without analytics.

### ep042 — `Jts8c-u_96U` — recommend private pending corrected reupload if on-screen factual accuracy is the standard

- **Misleading/false duration label:** `hook_text` **“52 YEARS OF DARKNESS”** appears from 0–3.3 s and again on the ending loop. The New Fire Ceremony happened **once every 52 years**; hearths were extinguished for the ceremonial night. This label naturally reads as darkness lasting 52 years, contradicting beat 2's “before midnight.” Suggested hook: **“ONE NIGHT, EVERY 52 YEARS.”** The spoken New Fire story is broadly consistent with the source. [World History Encyclopedia, New Fire Ceremony](https://www.worldhistory.org/article/866/the-aztec-new-fire-ceremony/).
- **Visual provenance caution:** opening and closing “Tenochtitlán” aerial is a 2023 reconstruction; beat 3 (6.58–9.96 s) uses Diego Rivera's 1945 mural, not a 1507 scene. They are usable as labeled illustrations, but should not be implied to be archival evidence of the ceremony. [Commons reconstruction](https://commons.wikimedia.org/wiki/File:Vista_completa_de_Tenochtitl%C3%A1n.jpg), [Commons Rivera mural](https://commons.wikimedia.org/wiki/File:Murales_Rivera_-_Markt_in_Tlatelolco_3.jpg).
- **Frame receipt:** `../../reports/previews/history-live-ep042-frames.jpg`; hook at 0.2/1.5 s, mural at 9 s, return to same opening aerial at 21.7 s. Source describes children kept awake, Pleiades at zenith, chest fire, torch relays; no other clear script falsehood found.

### ep045 — `v4rp0oWvgSI` — keep public with a visual-source clarification; correct in next version

- **Core rescue claim supported:** Winton's organization saved approximately 669 children; the planned largest transport of 250 was cancelled on 1 September 1939 after Germany invaded Poland. [USHMM](https://encyclopedia.ushmm.org/content/en/article/nicholas-winton-and-the-rescue-of-children-from-czechoslovakia-1938-1939), [Nicholas Winton exhibition](https://www.nicholaswinton.com/exhibition/kindertransport). The script does not assert that children had boarded.
- **Beat 2, 4.02–8.06 s, illustrative photo is off-event:** the photo named in the render is *Jewish children from Nazi Germany arriving in Stockholm in 1939*, not Winton's 669 rescued to Britain. Display beside “He was a hero for the 669 children he saved” may imply these are his children. Replace with a documented Winton transport image, or label the photo “Kindertransport to Stockholm, 1939; illustration.” [Commons file metadata](https://commons.wikimedia.org/wiki/File:Judiska_barn_fr%C3%A5n_Nazi-Tyskland_som_kommer_till_Stockholm_1939.jpg).
- **Beat 5, 15.35–19.42 s:** image `Pol5.jpg` is a *Polish Army* 7TP tank, displayed while narration says Germany invaded Poland. It is war-period imagery, but invites mistaken identification as a German invading tank. [Commons file metadata](https://commons.wikimedia.org/wiki/File:Pol5.jpg).
- **Beat 1 and ending, 0.08–4.02 s and 23.84–26.97 s:** “Many believe [he] rescued every child on his list” is an unsourced strawman; “For fifty years, even his wife never saw the list” overstates a simple secret. USHMM says his wife Grete found the scrapbook in 1988; his family's exhibition says Winton himself sought a home for his scrapbook in 1987. Direct replacement: **“One train of 250 children never left Prague.”** Ending: **“The scrapbook surfaced publicly nearly fifty years later.”** Sources: [USHMM](https://encyclopedia.ushmm.org/content/en/article/nicholas-winton-and-the-rescue-of-children-from-czechoslovakia-1938-1939), [Winton family exhibition, recognition](https://www.nicholaswinton.com/exhibition/recognition-1988).
- **Frame receipt:** `../../reports/previews/history-live-ep045-frames.jpg`; title/hook “THE MISSING LIST” and “Many believe” at 0.2–3.5 s; Stockholm photo at 6 s; Polish tank at 17.8 s. Main 250-child stakes do not arrive until 11–19 s, a plausible opening pacing risk without measured retention.

## Sent records with oEmbed 403

### ep013 — `zX1VUGHLb0o` — do not republish without rewrite

- Title and beats 1/7 call the death **accidental**. Bangor University's own statement says the researchers intentionally collected live specimens, could not determine age without opening the shell, and **“The notion that scientists knew in advance ... and then deliberately destroyed it is plainly incorrect.”** A Bangor student paper quotes the professor saying **“Ming was definitely not killed by accident”**: the death was an expected part of sampling, while the extraordinary age was unknown. The script's simple “accidentally killed” misstates the distinction. [Bangor University statement](https://www.bangor.ac.uk/news/archive/clam-found-to-be-over-500-years-old-16781), [Bangor student report](https://www.seren.bangor.ac.uk/discovery/science/2013/12/11/507-year-old-clam-found-by-bangor-scientists/).
- Beat 6, 35.34–42.12 s says precise carbon-14 dating **proved** 507 years. The 507 estimate came from counting and cross-matching shell growth increments; carbon-14 evidence supported it. Use **“Later shell-ring analysis revised Ming's age to 507 years.”** [Primary 2013 research DOI](https://doi.org/10.1016/j.palaeo.2012.01.016), [Bangor University](https://www.bangor.ac.uk/news/archive/clam-found-to-be-over-500-years-old-16781). The frozen-on-boat detail (beat 3) appears in secondary sources but is not documented by Bangor's own public account; avoid treating it as established.
- Beat 3's image is an Ifremer robot recovery in **August 2026**, twenty years after the 2006 Iceland cruise, shown under “they collected ... froze it.” Replace with a sourced research-vessel image or clearly label as illustration. [Commons Ifremer file metadata](https://commons.wikimedia.org/wiki/File:R%C3%A9cup%C3%A9ration_du_HROV_Ariane_%C3%A0_bord_de_l%27Atalante_durant_la_campagne_REDECOR_2026_(Ifremer_01084-119565_-_513491).jpg).
- Frame receipt: `../../reports/previews/history-live-ep013-frames.jpg`; opening clam at 0.2–3.5 s, 2026 research ship at 18.9 s, Ming-era ruler at 30.8 s. 47.33 s and repeated opening sentence at end make it long and repetitive for a short curiosity story; no measured retention yet.

### ep009 — `X8MhmozMp0o` — no urgent fact correction found; verify access status

- Key regeneration, neoteny, wild-population range and critically endangered claims match the [Natural History Museum](https://www.nhm.ac.uk/discover/axolotls-amphibians-that-never-grow-up.html). “Current surveys” is overprecise without a survey date; the museum says **“50–1,000 adults thought to be living in the wild,”** so use that attribution instead.
- Frame receipt: `../../reports/previews/history-live-ep009-frames.jpg`; opening axolotl plus “BRAIN REGENERATOR”; 1864 card at 18.9 s; aquarium animal again at 46.2 s. 47.15 s, static picture cards, and animal biology topic dilute the history channel's tragedy premise. These are editorial risks, not factual failures.

## Actions taken after audit

On 2026-10-03, the agent verified the exact six video IDs against the authenticated owned YouTube channel. ep009 and ep013 were private already. ep025, ep031, and ep042 were switched from public to private through the YouTube Data API; each change was read back and recorded in the episode's `withdrawal.json`. ep045 remains public. Its description now explicitly says the Stockholm arrivals photo is not Winton's Prague-to-Britain group and that the displayed 7TP is a Polish tank. The exact description hash and time are in `public_clarification.json`.

This is a factual correction hold, not a performance judgment. The withdrawn versions cannot be replaced in place on YouTube. Corrected source, visual, voice and MP4 evidence are required before any new upload.
