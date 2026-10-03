# History's Last Hours: editorial and growth strategy

Updated 2026-10-03 after the live-channel audit. This is the current plan for `@HistorysLastHours`; older animal-channel assumptions in the first launch plan no longer apply. Episode writing rules remain in `strategy/SCRIPT-RULES.md`.

## Current evidence

The owned YouTube API showed one public Short, eight channel views and zero subscribers at the latest authenticated read. Five prior uploads are private; three were withdrawn after factual or image-source errors. The channel has no useful Shorts-feed sample or retention curve. We cannot infer audience preference, posting time, or reach suppression from these numbers. The public Winton Short has a description clarification while a replacement is being rebuilt. New scheduling is held in `status/scheduling_hold.json`.

## Editorial promise

Tell one documented turning point in the last hours of a disaster, rescue, siege, or expedition. Open with a specific person, choice, warning, or event; explain what happened next; end with the consequence or a well-supported correction to a famous myth. Use American English, a calm human tone, and no gore. The event must be at least 75 years old. The visual record is evidence: period photographs, documents, prints and maps take priority. A later reconstruction must say that it is a reconstruction.

The best repeatable angle is **what people knew at the time and what they did with it**. It fits the existing channel name, supports the Warnings Ignored and Sole Survivors series, and is more distinctive than another list of tragedies. Do not force a villain or a neat single cause where historians disagree. The first four corrected pilots should test a rescue, a survivor, a disputed legend and a warning; the data, once there is enough of it, will decide which angle grows.

## Release contract

A candidate is ready to host and schedule only when all of these are true:

1. Every spoken and on-screen factual claim has a claim-level citation to a directly inspected institutional, primary, scholarly or reputable history source. Record disputes and estimates explicitly. A source list alone is insufficient.
2. The chosen visual's actual subject, date and license match the line it illustrates. Label reenactments, later art and reconstructions. Check the first frame and each beat at phone size. Do not reuse unrelated archival material for atmosphere.
3. The exact final MP4 has a hash receipt, complete decode, acceptable loudness and peak, speech/caption alignment, and a full-video and narration review. Automated scores and a contact sheet alone do not establish factual or listening quality.
4. A reviewer independent of the producing process signs the candidate or records the remaining holds. The hosted asset must be bound to the reviewed bytes. A superseded hosted draft can never enter Buffer.
5. The owned YouTube and Buffer state is read back after any scheduling or privacy change. The cloud watchdog checks that the scheduled media, due time and channel still match the receipt.

The channel-wide hold stays until there is a complete, reviewed release batch and the old hosted assets cannot be selected by the scheduler. Individual episode holds stay until their own repairs pass. An automated run may make drafts while either hold is active; it cannot treat a successful render as release approval.

## Format to test

- **Length:** target 22–35 seconds when the story fits; give a complicated account more time rather than cut a qualification that changes its meaning.
- **First two seconds:** the named subject and the stakes, with an event-specific image or an animated map. Avoid an unexplained black card or a long date card.
- **Visual grammar:** archival image or artifact; deliberate crop/close-up; a restrained map, timeline or mechanism where motion explains a fact; a final evidence or consequence card. Every movement should reveal information. Avoid repeated zooms over the same still and generic disaster footage.
- **Narration:** understandable names, natural pacing and emphasis, with silence where a fact needs to land. Keep captions legible within Shorts safe areas. A synthetic voice must be disclosed in the description.
- **Packaging:** a truthful, specific title and first-frame text that the video pays off. The description carries source and image credits. No emoji or question is needed if a direct statement is stronger.

## Publishing and learning

Release the first four corrected pilots over at least one week, at most one per day, after the release contract passes. Do not select times from the channel's eight views. Start with the US Eastern evening slot already configured, then compare only videos with similar age and actual Shorts-feed traffic. At 24 and 72 hours record engaged views, viewed versus swiped away, average viewed percentage, subscribers per 1,000 engaged views, traffic source and the first retention drop when the API supplies it. Record missing metrics as missing.

After at least ten eligible Shorts have comparable traffic, compare the three story angles and the two opening treatments. Make follow-ups to a breakout only after verifying that the follow-up's claims and art are as strong. Raise output toward two per day only when the source, visual and independent release gates can sustain it and the prior batch's engagement is not falling. Volume is a capacity decision, not a promise of distribution.

The 100,000-subscriber target in 100 days is a stretch target. At an illustrative conversion of one to two subscribers per 1,000 engaged views, it would require roughly 50–100 million engaged views. The present data cannot forecast that. We will change hooks, format and story selection from measured feed behavior, while keeping the accuracy gate intact. Check current YPP eligibility inside YouTube Studio; no earnings date is guaranteed.

## Automation state

Modal runs production in the cloud and GitHub Actions is a backup; GitHub's watchdog checks the service. This reduces dependence on the Mac, but it does not solve source judgment, independent QA, provider outages or Buffer quota limits. The scheduling hold and superseded-media check are required safeguards until those gaps are closed. `strategy/PLAN-100.md` tracks milestones and decision points.
