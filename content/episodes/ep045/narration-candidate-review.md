# ep045 controlled narration candidate — private local review

**Status:** Isolated candidate based on History commit `aa40f4a`. No upload, hosting, scheduling, publication, hold clearance, or human review was performed. The [private Modal backup](private-modal-backup.json) remains bound to the earlier MP4 with SHA-256 `64a77579dd3163e5d25e9425df10955970be07906518a112fc13492b85c47086`; it was not replaced.

## Editorial change

Beat 1 now says: “A train meant to rescue 250 children never left Prague.” This replaces “A rescue train planned for 250 children never left Prague,” whose final consonant in “planned” was ambiguous to machine listeners. The new sentence keeps `script.json` beat 1 bound to claim 1 in `research.json`: the Nicholas Winton family exhibition and BBC retrospective support an organized transport for 250 children, scheduled for 1 September 1939 and cancelled after Germany invaded Poland. It does not say the children boarded or assign any survival count. The title, description, 1938 Winton portrait, source credits, date labels, other five beat texts, and channel editorial hold remain unchanged.

## Final media candidate

| Check | Result |
|---|---|
| Private local MP4 | `ep045-narration-candidate-private.mp4` (ignored by Git); SHA-256 `f96d9c2165120e668a97a0dbdacda64c1bb7a808f073aeb5b39190f688968161`; 10,231,331 bytes |
| Spec and manifest | `short.yaml` SHA-256 `30793c9182ef3de39e825437f70643818d202c04cc8fd8e1d77e120fda3a0d10`; `work/manifest.json` SHA-256 `50c1fcbc31938f83f0bc0b17052ec05498234edd8e76986f16f65b43c538bb84`, with matching MP4 hash |
| Streams and decode | H.264 1080 × 1920 at 30 fps, AAC; 29.457 seconds; full FFmpeg video and audio decode completed without errors |
| Audio | 73 spoken words; −14.3 LUFS integrated; −1.9 dBFS true peak; automated warnings `[]`; narration WAV SHA-256 `f13a6064700b5ee4dbb9c2f0c293ac71d90fddb9cd42cd5e487a7075e2ee6c67` |
| Narration WAV ASR | `small.en` heard the new first line exactly. It heard “that proc” for “Prague” in the final memorial line, leaving one `speech.differences` item in `work/speech.json`. |
| Finished MP4 ASR | The same `small.en` settings heard every scripted word, including “Prague station”; zero differences. This does not substitute for native listening. |
| Visual review | [Phone-size opening comparison](narration-candidate-opening.jpg) at 0.1, 1.5, 2.2, and 3.5 seconds, all seven shot midpoints in the refreshed [sheet](sheet.jpg), and one frame per second through the full MP4 inspected. The date label, hook, and captions remain readable without collisions or blank frames. The 250 count is visible by 1.5 seconds. |
| Focused tests | `test_visual_provenance.py`, `test_history_cards.py`, `test_short_reviews.py`: 10 passed |

The target opening ambiguity is resolved in both machine transcripts. The WAV-only final-word difference still needs a native ear check, along with full-motion phone playback, music/delivery review, and independent editorial signoff before this candidate could replace the held draft.
