# ep027 Chicago phone-visuals candidate QA — 2026-10-04 IST

**Status:** Private local candidate only. The ep027 editorial hold stays in place. Nothing was hosted, uploaded, scheduled or published. The earlier private candidate (SHA-256 `551a99ab4c3dea20de9b9fbf50c0816e33620fe9ea66f3aec5d8b1317baea436`) and its receipts in [rights-candidate-qa-2026-10-04.md](rights-candidate-qa-2026-10-04.md) are unchanged. That file stays in the `audit/ep027-image-rights-20261004` worktree and is untouched. Its audio and video screens do not apply to this new file.

## What changed and why

| Beat | Before | Now | Evidence |
|---|---|---|---|
| 1, 6 | Small framed card cut from a 1920 px thumbnail of the NYPL stereograph | Full-frame cow from one stereo half of the 3072 × 1962 NYPL scan | [source receipt](assets/innocent-cause-nypl-left-half.source.json) |
| 3 | Small framed card from a 960 px thumbnail of a 1000 × 518 courthouse stereo pair | Full-frame 1871 C. R. Clark photograph of the burned district (Newberry Library), labeled "RUINS • 1871 PHOTO" | [source receipt](assets/chicago-ruins-1871-clark-nby1495.source.json) |
| 4 | The whole stereograph card, tiny, with "LEGEND ILLUSTRATION" | The same stereo half cropped to the caricature's sprawled milkmaid, still labeled "LEGEND ILLUSTRATION" | same receipt as beats 1 and 6 |
| 6 (spoken) | "Years later, Michael Ahern boasted…" | "Forty years later, reporter Michael Ahern boasted that he and others invented the cow story." | O’Leary Legend ("on the fortieth anniversary … a reporter named Michael Ahern … boasted"); DNAinfo Chicago (the 1911 Tribune anniversary story, "cooked [it] up with some colleagues"); MSU Libraries' Tribune record of October 8, 1911 (seen in the search index only) |
| 7 (spoken) | "Chicago’s council exonerated her in 1997." | "In 1997, Chicago’s council exonerated her and her cow." | 1997 council journal: "forever exonerate Mrs. O’Leary and her cow from all blame" |

Why it matters: the renderer fills the phone frame only with a portrait crop at least 1200 px tall. Both earlier images were thumbnails below that, so they appeared as small framed prints over a blur. The two spoken changes follow the script rules. Ahern is now introduced as a reporter. The last line echoes the hook's cow, so the Short loops. The "boasted" attribution and "he and others" keep the disputed authorship open. The fuller notes are in [research.md](research.md).

The legend asset is a derivative of one stereo half: cropped inside the printed arch, resized ×1.25 with Lanczos and given 1.35× contrast around the mean, because the faded scan was hard to read at phone size. Nothing was generated, retouched or composited. The ruins asset is a byte-identical copy of the Commons original. `short.yaml` binds both files by path, and `work/manifest.json` records their credits. The renderer's copies hash to the committed files: `841903fd292a67f36a6796e4dfa76b86968ebd3cb04c40d616201b9275bf2c24` (legend half) and `1878461211e986d1ecbf830b425cb147fd72497d1e1d405defac2fdb2d5c5cf5` (ruins).

## Exact private media

| Check | Result |
|---|---|
| File | `ep027-phone-visuals-candidate.mp4` in this worktree's episode folder (ignored by Git; not hosted) |
| SHA-256 | `9477f4ccd2e38841f05b5ea30e4741c72eca9f33e3b4fb2963bd8e727743dfd5`, also in `work/manifest.json` |
| Streams | H.264 1080 × 1920, 30 fps; AAC 48 kHz stereo; 26.9 s; 12,447,751 bytes |
| Decode | Full FFmpeg decode of video and audio, no errors |
| Audio | −14.4 LUFS integrated, −1.9 dBFS true peak; `ytc check` warnings `[]` |
| Words | 67 spoken (rule: 55–72) |
| Speech recognition | `small.en` on the finished MP4 heard every beat, including "forty years later", "reporter", "Michael Ahern boasted" and "her and her cow". Differences: the possessive "’s" heard as "is" after "Catherine O’Leary" and after "Chicago", and one dropped "the" after "barn"; the earlier candidate showed the same pattern. This is a machine check, not native listening |
| Frames | [14-frame beat sheet](phone-visuals-sheet.jpg) and [one-frame-per-second grid](../../../reports/previews/ep027-phone-visuals-1fps-grid.jpg) cover all 27 seconds. The hook card, ruins label, "LEGEND ILLUSTRATION" label and every caption were read at 540 × 960; no blank frame or text collision was seen in the samples |
| Render | Local Mac (`ytc make --where local`), Kokoro `am_fenrir` at 1.15×, 81.5 s wall time for the first pass, 3.3 GB peak memory |

## Final-media QA still required

On this exact SHA-256, before any hosting or scheduling:

1. **Native listening** of the full 26.9 s, especially "Forty years later, reporter Michael Ahern", whether "boasted" is clearly stressed, "O’Leary", the possessives the recognizer heard as "is", and the music and sound effects under the new beat 6 and 7 timings.
2. **Full-motion phone review**: the pan across the legend drawing in beats 1 and 6, the jump from the Currier & Ives card to the ruins, and the milkmaid crop in beat 4. Judge whether the warmer contrast of the legend art still reads as a period print.
3. **Editorial signoff** that "Forty years later" and "her and her cow" are acceptable as sourced, and that one drawing appearing in beats 1, 4 and 6 is acceptable as labeled legend art.
4. After approval, a new hosted copy must match this SHA-256 byte for byte, followed by a fresh scheduling review under the channel hold. The superseded Cloudinary URL in `hold.json` must never be reused.
