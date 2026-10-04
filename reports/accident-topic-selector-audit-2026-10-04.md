# Accident topic selector audit — 2026-10-04

## Existing path

`auto.daily()` fills the calendar through three paths: Wikipedia disaster-list harvesting and model scoring (`add_stories`), an open-ended model prompt (`add_topics`), and trending/news prompts (`add_timely`). `choose_topics` takes current timely and near-anniversary entries first, then generally ranks backlog topics by a model story score multiplied by a function of Wikipedia readership. The harvest reads 60 days of page views; the separate backlog demand cache reads 30 days. None of these discovery paths requires a checked inquiry or independent account before adding a topic. Research later checks exact quotes from two fetched sites, but discovery can still write an unsupported hook and can miss low-readership events entirely. This audit corrected the `add_stories` activity message that had called its 60-day count “readers a year.”

The saved harvest has zero recorded readers for Oppau, Texas City and Mann Gulch, and no Quebec Bridge candidate. Since `stories.score()` skips entries without a positive reader count, those three saved entries cannot reach its scoring prompt. A zero here may reflect an API gap, so it is evidence about this selector's coverage, not a claim that nobody read about the events.

The owned 2026-10-03 analytics snapshot does not provide a useful Shorts-feed sample, so neither an accident preference nor a “hidden accidents” audience can be claimed. The editorial test remains two independently reviewed accident pilots after the corrected release batch, under the existing scheduling hold.

## Checked candidate lane

`strategy/ACCIDENT-CANDIDATES.json` holds four specific research leads. On 2026-10-04, the exact URLs below returned event-specific text to the pipeline's fetcher:

| Lead | Original report or study | Separately published account | Editorial limit |
|---|---|---|---|
| Quebec Bridge, 1907 | [Royal Commission OCR](https://archive.org/download/reportandplansa01schngoog/reportandplansa01schngoog_djvu.txt), including the measured lower-chord deflections and defective-design finding | [STRUCTURE Magazine](https://www.structuremag.org/article/quebec-bridge-the-first-failure-1907/), structural engineer Frank Griggs Jr. | The commission says the collapse could not have been prevented after August 27; distinguish this from avoiding loss of life. |
| Oppau, 1921 | [Norwegian Defence Research Establishment original technical reassessment](https://www.ffi.no/en/publications-archive/a-factual-clarification-and-chemical-technical-reassessment-of-the-1921-oppau-explosion-disaster-the-unforeseen-explosivity-of-porous-ammonium-sulfate-nitrate-fertilizer) | [French Ministry of Environment ARIA accident record](https://www.aria.developpement-durable.gouv.fr/fiche_detaillee/14373/) | The technical study says the precise cause was never completely understood. Its original research is retrospective; ARIA is an official later summary, not the 1925 inquiry. |
| Texas City, 1947 | [Texas Fire Prevention and Engineering Bureau / National Board of Fire Underwriters report](https://www.local1259iaff.org/report.htm), published in 1947 and hosted by the local firefighters' site | [Texas State Historical Association](https://www.tshaonline.org/handbook/entries/texas-city-disaster) | Keep the *Grandcamp* and *High Flyer* explosions distinct; the report's photographs need separate rights checks. |
| Mann Gulch, 1949 | [U.S. Forest Service Board of Review OCR](https://archive.org/download/nfsl_2_43087/p17053coll2_43087_djvu.txt) | [Forest History Society history](https://foresthistory.org/research-explore/us-forest-service-history/policy-and-law/fire-u-s-forest-service/famous-fires/mann-gulch-fire-1949/) | The Board found the escape fire did not impede the crew and could not determine how many men understood Dodge's directions; a relative argued otherwise. |

The Texas City report returned HTTP 406 to a generic user agent but HTTP 200 to the pipeline's browser user agent; its extracted text contained the named ships and both explosion times. Both Texas City pages were still readable by that fetcher on a second check. Other slate entries remain editorial leads outside this small first pool. A [claim-level overlap check](accident-source-overlap-2026-10-04.md) found 9, 9, 10, and 10 distinct claims, respectively, with short matched quotations from both pages in each pair. No third source is needed for the requested eight-claim floor. Texas City is first in selector priority for the bounded cloud trial because its pair clears the research prompt's ten-claim target; the other leads remain in the pool. These are candidates for research and visual review, not approved narration.

The new daily step adds at most one candidate and waits until the current lead is done or dropped. It checks stable IDs and event aliases against the calendar, status history, and episode folders, including rejected episodes. A checked candidate gets a bounded editorial priority so zero Wikipedia page views do not bury it. When an episode starts, `topic.json` carries the exact source plan and cautions into `research()`. Research reads only those pages, stops if one cannot be read, and retains the existing exact-quote/two-site claim filter. OCR passages around the report's findings and event chronology are included without rewriting them; each quote is verified against the full fetched text, so it cannot join words from two distant excerpts. Cached research from a different source plan cannot be resumed.

The source-pair gate checks distinct origins and direct fetched text. It does not prove two publications reached every conclusion independently. It does not license images, approve a script, satisfy an independent review, or change any release setting. The other general topic-discovery paths are unchanged.

## Production during the channel hold

When `status/scheduling_hold.json` exists and `release.policy()` is inactive or invalid, the daily run still performs its nonproduction work but starts no automatic drafts, including if a scheduled trigger supplies a count. An explicit manual `--produce=N` remains available for a bounded editorial pilot. The pause lifts only after the existing autonomous release policy is active; this branch does not enable or alter that policy or the scheduling hold. The dormant release step's status note now describes the pause accurately.

## Verification

- The pipeline fetcher read all eight source URLs directly on 2026-10-04; each returned the named event, and both OCR passages used for the Quebec and Mann Gulch leads contained the checked focus terms.
- Offline tests cover bad source metadata, repeat selection, episode source binding, missing/cached-source failures, plain-text OCR ingestion, preservation of the quote gate, and the automatic-production pause. The full pipeline suite passed (159 tests).
- The overlap sheet's 38 quotations from each side passed the research quote matcher against the fetched prompt text on 2026-10-04. This does not guarantee the separate research prompt's ten-claim viability threshold or future page availability.
- No daily run, production job, upload, schedule action, or release-policy configuration change was performed for this branch.
