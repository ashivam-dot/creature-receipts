"""Research from fetched pages. Keep a claim only with two independently matched source quotes."""

from __future__ import annotations

import logging
import re
import unicodedata
import urllib.parse
from dataclasses import dataclass

import requests
import trafilatura

from . import llm
from .visuals import _user_agent

log = logging.getLogger(__name__)
logging.getLogger("trafilatura").setLevel(logging.ERROR)

WIKI_API = "https://en.wikipedia.org/w/api.php"
# Some news and museum sites refuse requests that don't look like a browser.
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
# Reputable sites per the script rules, read first. Other sites are read after these.
TRUSTED = (
    "britannica.com", "smithsonianmag.com", "si.edu", "history.com", "nationalgeographic.com", "bbc.co.uk",
    "bbc.com", "loc.gov", "archives.gov", "nps.gov", "nationalarchives.gov.uk", "npr.org", "pbs.org",
    "nytimes.com", "theguardian.com", "washingtonpost.com", "time.com", "historyextra.com", "atlasobscura.com",
    "livescience.com", "newyorker.com", "theatlantic.com", "telegraph.co.uk", "independent.co.uk", "latimes.com",
    "rmg.co.uk", "britishmuseum.org", "metmuseum.org", "historic-uk.com", "history.state.gov",
    "thecanadianencyclopedia.ca", "historylink.org", "encyclopedia.com", "worldhistory.org", "historynet.com",
    "pompeiisites.org", "encyclopedia-titanica.org", "usgs.gov", "volcano.si.edu", "noaa.gov",
    "archaeology.org", "nature.com", "science.org", "scientificamerican.com", "abc.net.au",
    "museum", ".edu", ".gov", ".ac.uk",
)
SKIP = (
    "wikipedia.org", "wikimedia.org", "wikidata.org", "wikisource.org", "books.google", "google.com", "doi.org",
    "jstor.org", "worldcat.org", "archive.org/details", "amazon.", "youtube.com", "twitter.com", "x.com/",
    "facebook.com", "instagram.com", "reddit.com", "pinterest.", "tiktok.com", "imdb.com", "goodreads.com",
    "findagrave.com", "ancestry.", "ebay.", "geohack", "openlibrary.org", "hathitrust.org", "gutenberg.org",
    "viaf.org", "id.loc.gov", "d-nb.info", "catalogue.bnf.fr", "orcid.org", "semanticscholar", "pubmed",
    "bing.com", "duckduckgo.com",
)
WIKI_CHARS = 45_000
SOURCE_CHARS = 16_000
MAX_SOURCES = 7
MIN_WORDS = 250


@dataclass
class Source:
    label: str
    url: str
    title: str
    text: str
    full_text: str | None = None  # When the prompt contains focused excerpts, verify quotes against the full page.

    @property
    def site(self) -> str:
        return site(self.url)


def site(url: str) -> str:
    """The site a URL belongs to, looking through web.archive.org copies to the original."""
    if match := re.match(r"https?://web\.archive\.org/web/[^/]+/(.+)", url):
        url = match.group(1)
    host = urllib.parse.urlparse(url if "://" in url else "https://" + url).netloc.lower()
    host = host.removeprefix("www.").removeprefix("m.")
    parts = host.split(".")
    keep = 3 if len(parts) > 2 and parts[-2] in ("co", "ac", "gov", "org", "com") and len(parts[-1]) == 2 else 2
    return ".".join(parts[-keep:])


def _wiki(params: dict) -> dict:
    response = requests.get(WIKI_API, params={"format": "json", "formatversion": 2, **params},
                            headers={"User-Agent": _user_agent()}, timeout=30)
    response.raise_for_status()
    return response.json()


def _existing(titles: list[str]) -> list[str]:
    """The titles that are real English Wikipedia articles, after redirects, in the given order."""
    if not titles:
        return []
    found = _wiki({"action": "query", "titles": "|".join(titles[:10]), "redirects": 1})["query"]
    renamed = {r["from"]: r["to"] for r in found.get("normalized", []) + found.get("redirects", [])}
    real = {p["title"] for p in found.get("pages", []) if not p.get("missing") and not p.get("invalid")}
    out = []
    for title in titles:
        for _ in range(3):  # normalized, then redirected
            title = renamed.get(title, title)
        if title in real and title not in out:
            out.append(title)
    return out


def _articles(topic: str, results: list[str]) -> list[str]:
    """The one or two Wikipedia articles that tell this story best: from web results, else Gemini's guess."""
    from_results = [
        urllib.parse.unquote(u.split("/wiki/", 1)[1]).replace("_", " ").split("#")[0]
        for u in results if re.match(r"https://en\.(m\.)?wikipedia\.org/wiki/[^:]+$", u)
    ]
    if titles := _existing(from_results)[:2]:
        return titles
    guess = llm.generate(
        f"A history Short will tell this story: {topic}\n\nName the one or two English Wikipedia articles that "
        "tell this specific story in the most detail, best first, with their exact titles.",
        schema={"type": "object", "properties": {"titles": {"type": "array", "items": {"type": "string"}}}, "required": ["titles"]},
        models=llm.LIGHT, purpose="name Wikipedia articles",
    )
    if titles := _existing(guess.get("titles", []))[:2]:
        return titles
    hits = _wiki({"action": "query", "list": "search", "srsearch": re.sub(r"[():\"“”]", " ", topic.split(":")[0]),
                  "srlimit": 1})["query"]["search"]
    return [h["title"] for h in hits]


def _article(title: str) -> tuple[Source, list[str]]:
    page = _wiki({"action": "query", "prop": "extracts|info", "explaintext": 1, "inprop": "url",
                  "titles": title, "redirects": 1})["query"]["pages"][0]
    text = re.sub(r"\n==+ (See also|References|Notes|Further reading|External links|Bibliography|Sources|Citations|Footnotes) ==+\n.*",
                  "", page.get("extract", ""), flags=re.S)
    links = _wiki({"action": "parse", "page": page["title"], "prop": "externallinks", "redirects": 1})
    urls = links.get("parse", {}).get("externallinks", [])
    return Source("", page["fullurl"], page["title"], text[:WIKI_CHARS]), urls


def _search(query: str, count: int = 15) -> list[str]:
    """Web result links through the ddgs metasearch library; empty if every engine refuses."""
    from ddgs import DDGS

    try:
        return [r["href"] for r in DDGS().text(query, max_results=count) if r.get("href", "").startswith("http")]
    except Exception as err:  # ddgs raises its own errors for blocked or empty engines
        log.info("web search unavailable: %s", err)
        return []


def _rank(urls: list[str]) -> list[str]:
    def score(url: str) -> int:
        domain = site(url)
        for i, trusted in enumerate(TRUSTED):
            if trusted.startswith(".") and domain.endswith(trusted) or trusted in domain:
                return i
        return len(TRUSTED)

    usable = [u for u in dict.fromkeys(urls) if u.startswith("http") and not any(s in u.lower() for s in SKIP)
              and not u.lower().split("?")[0].endswith((".pdf", ".jpg", ".png", ".djvu"))]
    return sorted(usable, key=score)


def _read(url: str) -> tuple[str, str] | None:
    try:
        response = requests.get(url, headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"},
                                timeout=25, stream=True)
        kind = response.headers.get("content-type", "").lower()
        if response.status_code != 200 or not ("html" in kind or ("text/plain" in kind and url.endswith(".txt"))):
            return None
        body = response.raw.read(3_000_000, decode_content=True).decode(response.encoding or "utf-8", errors="replace")
    except (requests.RequestException, OSError, ValueError):
        return None
    if "text/plain" in kind:
        return url.rsplit("/", 1)[-1], body
    html = body
    text = trafilatura.extract(html, url=url, include_comments=False, include_tables=False, favor_recall=True)
    if not text:
        return None
    title = trafilatura.extract_metadata(html).title if trafilatura.extract_metadata(html) else None
    return (title or url), text


def _key_terms(titles: list[str], topic: str) -> list[str]:
    words = re.findall(r"[A-Z][a-z]{3,}|\d{4}", " ".join(titles) + " " + topic)
    return list(dict.fromkeys(w.lower() for w in words))[:8]


def _focused_text(text: str, terms: list[str]) -> str:
    """Keep exact OCR passages around checked terms within one source's prompt budget."""
    if not terms:
        return text[:SOURCE_CHARS]
    spans = [(0, min(1_500, len(text)))]
    found = False
    for term in terms:
        if match := re.search(re.escape(term), text, re.I):
            found = True
            spans.append((max(0, match.start() - 2_000), min(len(text), match.end() + 4_000)))
    if not found:
        return text[:SOURCE_CHARS]
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return "\n[...]\n".join(text[start:end] for start, end in merged)[:SOURCE_CHARS]


def gather(topic: str, source_plan: list[dict] | None = None) -> list[Source]:
    """Read checked pages only for a curated lead; otherwise search as before."""
    if source_plan:
        sources = []
        subject_terms = [word.casefold() for word in re.findall(r"[A-Za-z]{4,}", topic.split(":", 1)[0])
                         if word.casefold() not in {"collapse", "explosion", "disaster", "fire"}]
        for item in source_plan:
            url = item["url"]
            read = _read(url)
            if not read:
                log.warning("checked accident source could not be read: %s", url)
                continue
            title, text = read
            if len(text.split()) < MIN_WORDS or (subject_terms and not all(term in text.casefold() for term in subject_terms)):
                log.warning("checked accident source lacks readable event text: %s", url)
                continue
            sources.append(Source(f"S{len(sources) + 1}", url, title,
                                  _focused_text(text, item.get("focus", [])), full_text=text))
        return sources
    sources: list[Source] = []
    results = _search(re.sub(r"[():\"“”]", " ", topic))
    titles = _articles(topic, results)
    candidates = list(results)
    for title in titles:
        article, cited = _article(title)
        sources.append(article)
        candidates += cited
    terms = _key_terms(titles, topic)
    per_site: dict[str, int] = {}
    for url in _rank(candidates):
        if len(sources) >= MAX_SOURCES:
            break
        if per_site.get(site(url), 0) >= 1:
            continue
        read = _read(url)
        if not read:
            continue
        title, text = read
        mentions = sum(1 for t in terms if t in text.lower())
        if len(text.split()) < MIN_WORDS or mentions < min(2, len(terms)):
            continue
        per_site[site(url)] = 1
        sources.append(Source("", url, title, text[:SOURCE_CHARS]))
    for number, source in enumerate(sources, start=1):
        source.label = f"S{number}"
    log.info("read %d sources: %s", len(sources), ", ".join(s.site for s in sources))
    return sources


RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "viable": {"type": "boolean"},
        "reason": {"type": "string"},
        "story": {"type": "string"},
        "angle": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "array", "items": {"type": "object", "properties": {
                        "source": {"type": "string"}, "quote": {"type": "string"}},
                        "required": ["source", "quote"]}},
                    "confidence": {"type": "string", "enum": ["high", "medium"]},
                },
                "required": ["claim", "sources", "evidence", "confidence"],
            },
        },
        "disputed": {"type": "array", "items": {"type": "string"}},
        "visuals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"subject": {"type": "string"}, "queries": {"type": "array", "items": {"type": "string"}}},
                "required": ["subject", "queries"],
            },
        },
    },
    "required": ["viable", "reason", "story", "angle", "claims", "disputed", "visuals"],
}

PROMPT = """You research stories for History's Last Hours, a YouTube Shorts channel of true, sourced stories of
history's tragedies (lost cities, doomed voyages and expeditions, fallen empires, ignored warnings, and the few
who survived) for a US audience. Each Short tells the human story of one real disaster: who was there, what they
saw and decided, what they could not know, and the detail most people have never heard.

Topic: {topic}
Series: {series}
Source-audit cautions (keep their uncertainty; do not add them as claims without quotes):
{cautions}

The sources below are the only ones you may use. Do not add anything you know from elsewhere. A claim
counts only if at least two sources from different sites state it. For each claim, include `sources` and
`evidence`: at least two source labels with a short, exact quote copied verbatim from each labelled source
text. Quotes are checked against the fetched page text; paraphrases and invented quotes are rejected.
If a claim has no matching quotes from two different sites, omit it. Wikipedia is one site.

Return:
- viable: false if these sources can't support a surprising 45-second story with at least 10 claims that
  each have two sites; give the reason. Otherwise true, with a one-line reason.
- story: the true story in about 150 plain words.
- angle: the single most surprising true fact, the one a viewer would stop scrolling for.
- claims: 12 to 24 short, atomic facts a script could use (who, what, when, where, numbers, outcomes, the
  twist), each with its source labels, evidence quotes, and confidence (high when the sources agree plainly,
  medium when their wording differs). Leave out anything only one site states, and legends presented as fact.
- disputed: details the sources disagree on or treat as legend, and how a script should handle each
  (leave out, or attribute: "according to one account").
- visuals: 8 to 14 things a viewer could see (period photographs, paintings, engravings, and newspaper
  front pages of the event; the people involved; the ship, building, or city before and after; ruins and
  artifacts as they are today; maps), never corpses, wounds, or remains shown as gore, each with 2 or 3
  Wikimedia Commons search queries naming the exact subject ("RMS Titanic departing Southampton",
  "Karl Bryullov Last Day of Pompeii", "Lisbon earthquake 1755 engraving"), not generic words.

Sources:
{sources}
"""


def _quote_key(text: str) -> str:
    """Keep words and numbers while tolerating page whitespace and typographic punctuation."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join("".join(char if char.isalnum() else " " for char in normalized).split())


def _matched_evidence(claim: dict, by_label: dict[str, Source]) -> list[dict]:
    """Reject source labels that the model listed without quoting the fetched text."""
    cited = set(re.findall(r"S\d+", " ".join(claim.get("sources", [])).upper()))
    verified = []
    for item in claim.get("evidence", []):
        label = re.search(r"S\d+", str(item.get("source", "")).upper())
        label = label.group() if label else None
        source = by_label.get(label)
        quote = str(item.get("quote", "")).strip()
        key = _quote_key(quote)
        if label not in cited or not source or len(key) < 20 or len(key.split()) < 4:
            continue
        if key not in _quote_key(source.full_text or source.text) or any(e["source"] == label for e in verified):
            continue
        verified.append({"source": label, "quote": quote})
    return verified


def research(topic: str, series: str, source_plan: list[dict] | None = None, cautions: list[str] | None = None) -> dict:
    """The claims table with exact evidence from at least two distinct fetched sites."""
    sources = gather(topic, source_plan) if source_plan else gather(topic)
    if source_plan and len(sources) != len(source_plan):
        raise RuntimeError("a checked accident source is unavailable; research cannot substitute another page")
    if len(sources) < 2:
        return {"viable": False, "reason": "fewer than two readable sources", "claims": [], "sources": []}
    listing = "\n\n".join(f"[{s.label}] {s.title} ({s.url})\n{s.text}" for s in sources)
    caution_text = "\n".join(f"- {item}" for item in cautions) if cautions else "None supplied."
    found = llm.generate(PROMPT.format(topic=topic, series=series, cautions=caution_text, sources=listing),
                         schema=RESEARCH_SCHEMA, models=llm.BROAD, purpose="research")
    by_label = {s.label: s for s in sources}
    kept = []
    for claim in found.get("claims", []):
        evidence = _matched_evidence(claim, by_label)
        labels = [item["source"] for item in evidence]
        if len({by_label[label].site for label in labels}) >= 2:
            kept.append({**claim, "sources": labels, "evidence": evidence})
    dropped = len(found.get("claims", [])) - len(kept)
    if dropped:
        log.info("dropped %d claims without matched quotes from two different sites", dropped)
    if not kept and len(found.get("claims", [])) >= 8:
        # Every claim lost its citations: the answer is malformed, not the topic weak. A later run asks again.
        raise RuntimeError(f"research answer supplied no usable two-site quotes ({llm.answered_by()}); asking again next run")
    found["claims"] = kept
    if found.get("viable") and len(kept) < 8:
        found["viable"] = False
        found["reason"] = f"only {len(kept)} claims have verified quotes from two different sites"
    found["sources"] = [{"label": s.label, "url": s.url, "title": s.title, "site": s.site} for s in sources]
    found["topic"], found["series"] = topic, series
    return found
