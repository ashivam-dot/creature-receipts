# ep045 Winton portrait upgrade — private draft, 2026-10-03

**Status:** Local visual and packaging candidate only. The channel scheduling hold and all publication reviews remain in force. No upload, hosting, scheduling, or human signoff was performed. The earlier `replacement-review.md` and `independent-audio-screen.json` describe the previous private MP4, not this one.

## Change and source

The previous opening showed Winton's 1938 photograph as a narrow print over a blurred enlargement. The new first and fifth beats show a close, full-frame Winton-only crop, with `WINTON • 1938 PHOTO` burned into both appearances. At 360 × 640 phone size the face, `TRAIN NEVER LEFT` hook, 250-child caption, and date label occupy separate readable areas. [The side-by-side frame](visual-upgrade-contact-sheet.jpg) and refreshed [seven-shot sheet](sheet.jpg) show the rendered result. The title now states the planned 250-child stake: “Winton's Rescue Train for 250 Children Never Left Prague.” The narration and its factual claims were not edited.

The source is the [Wikimedia Commons 1938 Winton photograph](https://commons.wikimedia.org/wiki/File:Nicholas_Winton_(1909-2015)_in_1938_by_the_Associated_Press.jpg), which the Commons API identifies as a 1024 × 844 public-domain image. The local derivative crops source pixels `(580, 0, 1024, 844)` and resizes them with Pillow Lanczos to 666 × 1266 so the renderer uses a vertical cover. This interpolation adds no scene content. The child in the original frame is outside the crop; the picture is not presented as evidence of the cancelled 1939 transport. [The asset receipt](assets/winton-1938-portrait-cover.source.json) records the source and derivative hashes. The renderer now carries declared credit for local derivatives into `work/manifest.json`, rather than reducing them to “local file.”

## Media checks

| Check | Result |
|---|---|
| Private MP4 | `ep045-portrait-upgrade-private.mp4` (ignored by Git), SHA-256 `64a77579dd3163e5d25e9425df10955970be07906518a112fc13492b85c47086` |
| Streams | H.264 1080 × 1920, 30 fps; AAC audio; 29.488 seconds; 10,631,337 bytes |
| Decode | Full FFmpeg video and audio decode completed with no errors |
| Audio | −14.3 LUFS integrated; −1.6 dBFS true peak; automated media warnings `[]` |
| Visual | Opening frames at 0.1 and 1.0 seconds, every second of the 29.49-second MP4, and each shot midpoint inspected at phone size; no blank frame or text collision seen |
| Speech | `small.en` transcribed every beat, with one difference: “planned” heard as “plan” in the opening line. The earlier machine screen also heard “plan”; this is not a native listening clearance. |
| Focused tests | `test_visual_provenance.py`, `test_editorial_hold.py`, `test_history_cards.py`: 7 passed |

The private MP4 is available in this worktree for full-motion playback and native listening. A reviewer still needs to hear the opening distinction between “planned” and “plan,” assess the delivery and music, review the whole video on a phone, and make an independent editorial decision before any release action.
