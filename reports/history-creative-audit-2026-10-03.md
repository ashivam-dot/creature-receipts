# History's Last Hours: media and packaging audit — 2026-10-03 22:30 IST

## Evidence and limits

I reviewed the exact Cloudinary MP4 referenced by Winton's sent `publish.json`
(SHA-256 `f231970ffe1caab2b420c05c4adb92932bae7a52210c173fce25d13348db1b03`),
the local corrected Winton draft (SHA-256 `f89475bf5bea7dc7000b5c664be40892c6bac17cb1768d0f8dcd80d0918b597f`),
the public video's `maxres` thumbnail returned by owned YouTube metadata, and
the first 0.1 and 1.5 seconds of nine local corrected drafts. The
[first-two-second Winton comparison](previews/history-winton-first-2s-20261003.jpg),
[nine-draft opening grid](previews/history-private-draft-openings-20261003.jpg),
and [public thumbnail](previews/history-winton-public-thumbnail-20261003.jpg)
are direct image receipts. The thumbnail is a 1280 × 720 JPEG, SHA-256
`85b5653b68110dd6291688569bec504d5b80b6721f60da01598503201feaf09a`.

FFprobe measured the MP4 lengths; FFmpeg measured integrated loudness and true
peak. Local `small.en` ASR provided word and phrase times from the final MP4s.
These checks do not replace native listening or full-motion editorial review.
The owned channel has zero public videos, 10 total channel views and no Winton
per-video retention row as of `analytics/2026-10-03.json` at 16:57:09 UTC.
There is no performance sample for a claim about viewer preference or optimal
format. Buffer had no queued posts at the 22:10 IST read or the direct,
paginated scheduled-post recheck at 22:35 IST.

## Public Winton upload versus corrected private draft

| Check | Former public upload, now private | Corrected local draft |
|---|---|---|
| First two seconds | Winton holds an unidentified child; `THE MISSING LIST` sits across their faces. Narration starts “Many believe…” and gives neither the planned train nor the 250-child stake. | Cropped 1938 Winton portrait leaves his face clear. `TRAIN NEVER LEFT` is on screen from frame zero. Narration says “250” at 1.46–2.12 seconds and “never left Prague” by 3.58 seconds. |
| Title and cover | Published title: “Why Nicholas Winton’s Largest Rescue Train Never Left 💔”. YouTube selected a generic 1931 Prague station aerial captioned `RESCUE MISSION` as its actual cover. It omits Winton and the cancelled-train hook. | Draft title: “The Winton Rescue Train That Never Left Prague”. No platform thumbnail exists for this unuploaded draft. Use a reviewed Winton-and-250 cover frame if YouTube permits selection; do not reuse the old station cover. |
| Picture identity | Stockholm Kindertransport children and a Polish Army tank illustrate Winton's Britain rescue and Germany's invasion. A public description clarification was added earlier, but it did not change those frames. | The off-event Stockholm and tank images are absent. The Prague 1931 location view and 2015 memorial are labeled as such; the child in the original Winton image is cropped away. |
| Source fidelity | The old narration says “Almost none of those final 250 children survived the war” at 19.66–23.18 seconds. [Winton's family](https://www.nicholaswinton.com/exhibition/kindertransport) says only that it is *thought* nearly all due to leave were sent to Terezín and Auschwitz; [USHMM](https://encyclopedia.ushmm.org/content/en/article/nicholas-winton-and-the-rescue-of-children-from-czechoslovakia-1938-1939) gives no survival count. | The 250-child transport is described as planned and cancelled, without a boarding claim or individual survival count. Winton's team receives credit for the 669 earlier rescues. |
| Voice and pace | 67 script words in 27.32 seconds, about 147 words per full minute. ASR heard the unsupported line in the rendered MP4. Integrated −14.4 LUFS; true peak −1.8 dBFS. | 73 script words in 29.49 seconds, about 149 words per full minute. ASR heard all six beats in order. Integrated −14.3 LUFS; true peak −1.8 dBFS. Both use Kokoro `am_fenrir` at speed 1.15. |

The improvement in the first two seconds is concrete: the corrected draft
names the planned train and its stakes while showing Winton. Both edits still
show a single portrait through the whole opening beat, and ASR shows pauses of
roughly 0.9–1.3 seconds between the corrected beats. A reviewer should watch
the full draft on a phone and listen to the name, delivery, pauses and music
before considering release. The old upload was made private through the owned
API; [its withdrawal receipt](../content/episodes/ep045/withdrawal.json)
records the action. The corrected MP4 remains unhosted and unscheduled.

## Corrected draft opening frames

The grid compares each candidate at 0.1 and 1.5 seconds, at 180 × 320 phone
scale. It tests immediate picture identity and text legibility, not retention.

| Draft | Direct frame finding | Editorial action before release |
|---|---|---|
| ep025 R101 | The actual wreck gives relevant period evidence, but sits as a small wide print above a large dim backing. `SIX SURVIVED` and the narrated count are immediate. | Check visual variety across the full video; the wreck and airship recur. A closer source crop may improve small-screen detail without inventing footage. |
| ep026 Peshtigo | The opening image is a September 1871 **before-the-fire** town lithograph, labeled honestly. The spoken opening reports up to 2,500 deaths, yet no fire is visible in the first two seconds. | Test an event-specific fire or river engraving as the first image, preserving its source label, then rerender and recheck the whole Short. The current pronunciation of Peshtigo and Father Pernin still needs a native ear check. |
| ep027 Chicago | The cow engraving immediately identifies the legend; `THE COW STORY` is legible. The line says no cause was proven, a sourced correction. | Keep the image's illustrative role clear; review the full narration and 1997 exoneration payoff on a phone. |
| ep031 Yamaguchi | The Nagasaki mushroom-cloud photograph is labeled `NAGASAKI • AUG 9, 1945` while narration introduces the second blast. `TWO BLASTS, ONE SURVIVOR` is immediate and avoids the old false “two ground zeros” claim. | Review the later Hiroshima/Nagasaki transitions and source labels; the opening alone is not release approval. |
| ep035 Galveston | Isaac Cline's portrait fills the frame. `THE WARNING CAME` and the revised flags line now reflect NOAA's account instead of blaming him for a warning he did give. | Check the full video's handling of the disputed warning record and the narration on a phone. |
| ep038 Empire State | The actual crash aftermath fills the phone frame; the building and smoke appear immediately, with a dated label. This is visibly stronger than the earlier small landscape plate. | Watch the authored camera path and the labeled representative aircraft/rescue images in motion; do not imply the wreckage depicts Oliver's elevator. |
| ep042 New Fire | `ONE NIGHT, EVERY 52 YEARS` removes the old false duration implication. The small aerial is visibly labeled as a **2023 reconstruction**, but no ritual fire is visible yet. | Check whether a more specific first-period image can carry the ceremony, while preserving honest labels; review the sequence and narration. |
| ep045 Winton | The portrait and `TRAIN NEVER LEFT` align with the first spoken line; the 250 count lands by 2.12 seconds. | Review a closer portrait crop or selected cover frame at phone size. Keep the local draft private until full review. |
| ep047 Alamo | The first two seconds contain only a `NEARLY 200 / NO QUARTER GIVEN` number card. There is no Alamo picture and no `hook_text`; the current script rules call for an image in the hook. | Try a sourced, visibly labeled later Alamo depiction or a period document behind the opener, then rerender. Keep the uncertainty around the defender count and final-assault duration explicit. |

The first-frame improvements for Winton, Yamaguchi, Galveston and Empire State
are visually evident in these assets. None of these drafts has passed the final
independent listening and full-video review gate. The channel-wide and
per-episode editorial holds remain in place.
