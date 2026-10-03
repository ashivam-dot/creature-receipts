# ep027 Chicago rights candidate QA — 2026-10-04 IST

## Exact private media

- Local, unhosted file: [ep027-rights-candidate.mp4](ep027-rights-candidate.mp4). MP4 files are ignored by Git; the file is present in this isolated worktree for review and its exact bytes have an independently verified [private Modal backup](private-modal-backup.json).
- SHA-256: `551a99ab4c3dea20de9b9fbf50c0816e33620fe9ea66f3aec5d8b1317baea436`, also recorded in `work/manifest.json` and `hold.json`.
- 25.167 seconds; 11,282,901 bytes; H.264, 1080 × 1920, 30 fps; AAC, 48 kHz stereo. FFmpeg decoded the complete video and audio without an error.
- `ytc.check` measured −14.4 LUFS integrated and −1.7 dBFS true peak, 62 spoken words and no automated warning. Its seven beat frames are in [sheet.jpg](sheet.jpg). At 0.1 and 1.5 seconds, the cow illustration and “THE COW STORY” are visible; the final “EXONERATED / Chicago City Council · 1997” card is legible at 540 × 960.
- `small.en` on the **finished MP4** heard all seven claim beats, including “no proven cause,” “no proof against her,” “Ahern boasted,” and the 1997 exoneration. It missed unstressed “the” and “a” and normalized two possessive endings as “is”; no factual phrase was missing. This machine check does not judge pronunciation, music, pacing or full-motion playback.
- A separate [blind audio-only Gemini screen](independent-audio-screen.json) of the same finished MP4 transcribed all seven material statements without a supplied script. It reported no uncertain words, glitches, pronunciation concerns or music masking, and heard sound effects between some sentences. It dropped a few unstressed articles. This is supporting machine evidence, not native listening or release approval.

## Source and rights recheck

The [Chicago Fire history project's O’Leary account](https://greatchicagofire.org/oleary-legend/) directly says she testified she was in bed, the inquiry found no proof of guilt, and Ahern *boasted* that he and two others invented the story. It also records disputed authorship and an unknown cause. The project's [conflagration](https://greatchicagofire.org/great-conflagration/) and [ruins](https://greatchicagofire.org/ruined-city/) pages directly support the barn vicinity and “one hundred thousand Chicagoans lost their homes.” All three returned HTTP 200 on this recheck.

The [October 28, 1997 City Council journal](https://cdn-web-main.bibliocms.com/wp-content/uploads/sites/3/2014/09/counciljournal10281997.pdf) returned HTTP 200, SHA-256 `562b0e77866baa004f5a144a9688685ae3dadaa76ba50588021b57e9acd39377`. Its scanned pp. 54829–54830 show the substitute resolution adopted 47–0 and say the mayor and council “do hereby forever exonerate Mrs. O’Leary and her cow from all blame.” The Chicago Public Library article linked in the package returned HTTP 202 with an empty body in this environment; the accessible primary journal supports the spoken claim directly.

The old opening `Mrs OLeary's cow.jpg` is absent from this candidate. Its [Commons metadata](https://commons.wikimedia.org/wiki/File:Mrs_OLeary%27s_cow.jpg) calls the purported *Harper's Magazine* 1871 source dubious and links a Bettmann/Getty copy. The replacement [NYPL stereograph](https://digitalcollections.nypl.org/items/8e370600-c53b-012f-ff21-58d385a7bc34) has a direct catalog record, Copelin & Hine credit, and NYPL's public-domain-in-the-US assessment. NYPL catalogs an 1871 issue date, while the printed card has an 1872 copyright notice; no exact year is asserted on screen. Beat 1 crops one side for phone legibility, beat 4 shows the full artifact labeled “LEGEND ILLUSTRATION,” and beat 6 returns to the crop. This remains illustrative art, not a portrait or evidence of the cause.

The [Currier & Ives fire lithograph](https://commons.wikimedia.org/wiki/File:Chicago_in_Flames_by_Currier_%26_Ives,_1871.jpg) is listed by Commons as 1871/public domain and credited to the Chicago Historical Society original. The [courthouse ruins stereograph](https://commons.wikimedia.org/wiki/File:West_entrance_to_Court_House._%2821462112062%29.jpg) is cataloged as 1871 by SMU and marked “No restrictions.” The final two fact cards are designed in the pipeline. `short.yaml`, `visuals.json`, and the new manifest carry these credits and visual choices.

## Release state and remaining gate

The candidate has **not** been hosted on a public CDN, uploaded to YouTube, scheduled or published. It was copied only to the private Modal volume for preservation. The existing Cloudinary `hold.json` URL still serves the withdrawn 11,937,837-byte MP4 (SHA-256 `59fbb6b0defe6c907f4dac75f34571e92ffe5dd642925bec8202cb5b6d2ee7c9`), which does not match this candidate and must never be reused. The per-episode editorial hold remains.

An independent reviewer still needs to listen to the complete **exact-hash** MP4 and watch it in motion at phone size, particularly O’Leary and Ahern, the “boasted” qualification, the three uses of the same legend art, and the music/caption transitions. After approval, any hosted copy needs a byte-for-byte hash match and fresh scheduling review under the channel hold.
