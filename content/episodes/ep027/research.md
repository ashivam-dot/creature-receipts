# ep027: Chicago cow legend — repair receipt (2026-10-03)

**Editorial status:** Held. The corrected narration is a local draft; do not schedule or publish. The original rendered Short and its prior quality scores apply only to the withdrawn script.

## Source receipts

| Source | Directly checked evidence | Access note |
|---|---|---|
| [The O’Leary Legend](https://greatchicagofire.org/oleary-legend/) | Catherine O’Leary gave sworn testimony that she was in bed; the official inquiry found no proof of guilt. On the fire’s fortieth anniversary Michael Ahern *boasted* that he and two colleagues made the cow story up. The page also records rival authorship and ghostwriting claims, and says the cause is unlikely ever to be known. | HTTP 200, text inspected 2026-10-03. |
| [The Great Conflagration](https://greatchicagofire.org/great-conflagration/) | Fire began near the O’Leary barn on October 8, 1871. | HTTP 200, text inspected 2026-10-03. |
| [The Ruined City](https://greatchicagofire.org/ruined-city/) | Roughly 100,000 Chicagoans were left homeless. | HTTP 200, text inspected 2026-10-03. |
| [Chicago City Council journal, October 28, 1997](https://cdn-web-main.bibliocms.com/wp-content/uploads/sites/3/2014/09/counciljournal10281997.pdf) and [Chicago Public Library explanation](https://www.chipublib.org/blogs/post/whodunit-the-mystery-of-mrs-olearys-cow/) | The committee recommended exoneration; on October 28 the full council adopted the substitute resolution by 47 yeas and no nays. Its text says the mayor and council “do hereby forever exonerate Mrs. O’Leary and her cow from all blame.” | The library page linked the accessible CDN PDF. Direct HTTP 200, three scanned pages inspected by OCR on 2026-10-03; PDF SHA-256 `562b0e77866baa004f5a144a9688685ae3dadaa76ba50588021b57e9acd39377`. |

## Spoken claim map

| Beat | Claim | Source |
|---|---|---|
| 1 | Cow blamed; cause unproved | O’Leary Legend |
| 2 | 1871 fire began near O’Leary barn | Great Conflagration |
| 3 | About 100,000 homeless | Ruined City |
| 4 | O’Leary testified she was in bed | O’Leary Legend |
| 5 | Inquiry found no proof against her | O’Leary Legend |
| 6 | Forty years later, reporter Ahern *boasted* that he and others invented the story | O’Leary Legend; DNAinfo Chicago; MSU Libraries Tribune record |
| 7 | In 1997 the City Council exonerated her and her cow | Directly read council journal, pp. 54829–54830; O’Leary Legend |

### Phone-visuals revision, 2026-10-04

Two spoken lines changed, and only to state what the sources already say:

- **Beat 6** now says "Forty years later, reporter Michael Ahern boasted…". The O’Leary Legend page says that "on the fortieth anniversary of the great conflagration a reporter named Michael Ahern … boasted in the Tribune that he and two now-deceased cronies made the whole thing up". [DNAinfo Chicago](https://www.dnainfo.com/chicago/20151006/downtown/5-things-you-probably-didnt-know-about-great-chicago-fire/) (HTTP 200 on 2026-10-04, body SHA-256 `d4ce3c9cbb4b30d2caa650228ba6f31c96014123296c48a2ed6f4fbcbe661e7b`) quotes what he "wrote for the Chicago Tribune in 1911 as part of an anniversary story". It calls him "a Chicago journalist" who claimed he "cooked [the O'Leary story] up with some colleagues", and it says his story changed over the years. [Michigan State University Libraries](https://lib.msu.edu/branches/dmc/tribune/detail.jsp?id=6012) catalogs the Ahern item from the *Chicago Sunday Tribune*, October 8, 1911, Part 1, p. 2. That page blocked direct fetching here, so its record is cited from the search index as corroboration only. Only one source gives "two" collaborators, so the line keeps "he and others". "Boasted" keeps the claim attributed and leaves the disputed authorship open.
- **Beat 7** now says "In 1997, Chicago’s council exonerated her and her cow." The journal resolution reads "forever exonerate Mrs. O’Leary and her cow from all blame". The line now echoes the hook's cow, so the Short loops back to its first line.

Script total: 67 spoken words, within the 55–72 rule.

## Visual evidence and limits

The opening now uses a cropped half of [NYPL's *The Innocent Cause* stereograph](https://digitalcollections.nypl.org/items/8e370600-c53b-012f-ff21-58d385a7bc34), also listed on [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:View_of_a_drawing%29_%22The_Innocent_Cause-_or_the_Origin_of_Chicago_Fire%22_%28showing_Mrs._O%27Leary_and_her_cows%29_%28NYPL_b11707459-G90F182_013ZF%29.tiff). NYPL identifies Copelin & Hine, catalogs it as issued in 1871, and says it believes the item is public domain under US law. The card itself carries an 1872 copyright notice, so the package calls it **period legend art** without assigning an exact year. Beat 4 shows the full stereograph with a visible “LEGEND ILLUSTRATION” label. Beat 6 returns to the opening crop during Ahern’s attributed boast. These pictures illustrate the **legend**; they are neither evidence of the fire’s cause nor portraits of Catherine O’Leary.

The prior hook image, [*Mrs OLeary's cow.jpg*](https://commons.wikimedia.org/wiki/File:Mrs_OLeary%27s_cow.jpg), was removed. Its Commons metadata calls the proposed *Harper's Magazine* 1871 source “dubious” because the image was not found in the relevant issues and links a Bettmann/Getty copy. That record did not establish a sufficiently clear original source for public use. The 1871 Currier & Ives blaze image is an illustration; the courthouse ruins are a period stereograph from SMU's collection marked “No restrictions” on Commons. The designed cards present the inquiry and council findings. The selected image pages and license metadata are recorded in `visuals.json`.

The new exact render and contact sheet are documented in [rights-candidate-qa-2026-10-04.md](rights-candidate-qa-2026-10-04.md); this source and rights review does not remove the editorial hold.

**Phone-visuals revision (2026-10-04).** That candidate drew beats 1, 4 and 6 from a 1920 px Commons thumbnail, and beat 3 from a 960 px thumbnail of a 1000 × 518 courthouse stereo pair. Neither image was tall enough for the renderer's full-frame layout (portrait, at least 1200 px tall), so both showed as small framed cards. The revision binds exact local files, each with a source receipt:

- **[`assets/innocent-cause-nypl-left-half.jpg`](assets/innocent-cause-nypl-left-half.source.json)** (beats 1, 4 and 6). This is the left view of the same NYPL card, cut from the 3072 × 1962 Commons TIFF at pixels (415, 530, 1499, 1628), inside the printed arch. It was resized ×1.25 with Lanczos resampling, with no retouching, tone change or generated content. The Commons record credits NYPL capture [`510d47e0-5e56-a3d9-e040-e00a18064a99`](https://digitalcollections.nypl.org/items/510d47e0-5e56-a3d9-e040-e00a18064a99) (b11707459, image G90F182_013ZF) and marks it public domain. NYPL's pages served a bot challenge here; the earlier candidate's NYPL check stands. The drawing itself is inscribed "W. O. Mull, artist, 1871". Beat 1 frames the kicking cow. Beat 4 frames the sprawled milkmaid figure and keeps "LEGEND ILLUSTRATION".
- **[`assets/chicago-ruins-1871-clark-nby1495.jpg`](assets/chicago-ruins-1871-clark-nby1495.source.json)** (beat 3). This is a byte-identical copy of the 3498 × 3600 Commons original. The source is Charles R. Clark's 1871 photograph *Chicago Fire of 1871: From Michigan Ave. Hotel North from Congress St.* at the [Newberry Library](https://collections.carli.illinois.edu/digital/collection/nby_chicago/id/1495) (Midwest MS Clark Box 2 Folder 167). Newberry's rights field allows "any lawful purpose, commercial or non-commercial, without licensing or permission fees", and Commons marks it public domain. It replaces the low-resolution courthouse card with a full-frame view of the burned district, labeled "RUINS • 1871 PHOTO". It shows destroyed buildings, not identified homeless people.

The 1871 Currier & Ives lithograph (beat 2) is unchanged. The other worktree keeps the earlier candidate MP4 and its SHA-256 receipt untouched.

## Human review still required

- Listen to the full narration, especially O’Leary and Ahern pronunciation and whether “boasted” is clearly heard.
- Watch the full 1080 × 1920 render on a phone, including image/caption readability and the transition back to the hook.
