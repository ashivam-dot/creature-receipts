"""Bounded, read-only source and art preflight for two checked accident leads.

This records evidence for editorial review. It never writes the producer calendar,
creates an episode, or approves a script, image, or release.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "HistoryAccidentIntake/1.0 (https://github.com/ashivam-dot/creature-receipts)"
MAX_SOURCE_BYTES = 3_000_000
MAX_IMAGE_BYTES = 12_000_000
EXPECTED_IDS = {"oppau-1921", "mann-gulch-1949"}
ISSUE_TITLE = "[supply] Checked History accident lane needs independent source and art approval"


class IntakeError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise IntakeError(reason)


def words(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join("".join(char if char.isalnum() else " " for char in value).split())


def plain(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def clean_url(value: str) -> str:
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def fetch(url: str, limit: int, *, allowed_hosts: set[str] | None = None) -> tuple[bytes, str]:
    parsed = urlsplit(url)
    require(parsed.scheme == "https" and parsed.hostname and not parsed.username and
            not parsed.password and not parsed.fragment, "intake URL is not a plain HTTPS URL")
    if allowed_hosts is not None:
        require(parsed.hostname in allowed_hosts, "intake URL left its pinned host")
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT,
                                                "Accept": "text/html,text/plain,image/jpeg,application/json"}),
                         timeout=35) as response:
                actual = urlsplit(response.geturl())
                require(actual.scheme == "https" and not actual.username and not actual.password,
                        "intake fetch redirected away from HTTPS")
                if allowed_hosts is not None:
                    require(actual.hostname in allowed_hosts, "intake fetch redirected off pinned host")
                else:
                    source_host = parsed.hostname.removeprefix("www.")
                    actual_host = actual.hostname.removeprefix("www.")
                    require(actual_host == source_host or
                            (source_host == "archive.org" and actual_host.endswith(".archive.org")),
                            "source fetch redirected to another host")
                data = response.read(limit + 1)
                require(len(data) <= limit, "intake response exceeded its byte limit")
                return data, response.headers.get("Content-Type", "").lower()
        except HTTPError as exc:
            if exc.code not in (429, 503) or attempt == 2:
                raise IntakeError(f"intake HTTP {exc.code} from {parsed.hostname}") from exc
            time.sleep(2 ** attempt)
        except (URLError, TimeoutError, OSError) as exc:
            raise IntakeError(f"intake fetch failed from {parsed.hostname}: {type(exc).__name__}") from exc
    raise IntakeError("intake retry limit reached")


def read_json(url: str, *, allowed_hosts: set[str]) -> dict:
    body, content_type = fetch(url, MAX_SOURCE_BYTES, allowed_hosts=allowed_hosts)
    require("json" in content_type, "intake API did not return JSON")
    try:
        value = json.loads(body)
    except ValueError as exc:
        raise IntakeError("intake API JSON is malformed") from exc
    require(isinstance(value, dict), "intake API JSON is not an object")
    return value


def source_check(source: dict, canaries: list[str]) -> dict:
    require(source.get("role") in ("primary", "independent") and
            isinstance(source.get("url"), str) and
            isinstance(canaries, list) and 2 <= len(canaries) <= 4,
            "source preflight metadata is malformed")
    body, mime = fetch(source["url"], MAX_SOURCE_BYTES)
    require(mime.startswith("text/html") or mime.startswith("text/plain"),
            "source did not return readable HTML or text")
    text = body.decode("utf-8", "replace")
    if mime.startswith("text/html"):
        text = plain(re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", text))
    normalized = words(text)
    require(len(normalized) >= 1500, "source page has too little readable event text")
    for phrase in canaries:
        require(isinstance(phrase, str) and len(words(phrase)) >= 8 and
                words(phrase) in normalized,
                f"{source['role']} source lost a pinned event phrase")
    return {"role": source["role"], "url": source["url"],
            "text_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
            "matched_phrases": len(canaries)}


def art_check(item: dict) -> dict:
    title = item.get("title")
    require(isinstance(title, str) and title.startswith("File:") and
            isinstance(item.get("sha256"), str) and
            re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) and
            isinstance(item.get("scene"), str) and len(item["scene"]) >= 35,
            "art preflight metadata is malformed")
    params = urlencode({"action": "query", "format": "json", "titles": title,
                        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
                        "iiurlwidth": 1280})
    data = read_json(COMMONS_API + "?" + params, allowed_hosts={"commons.wikimedia.org"})
    pages = data.get("query", {}).get("pages", {})
    require(isinstance(pages, dict) and len(pages) == 1, "Commons art lookup is incomplete")
    page = next(iter(pages.values()))
    require(page.get("title") == title and not page.get("missing"), "Commons art title changed")
    image = (page.get("imageinfo") or [None])[0]
    require(isinstance(image, dict) and image.get("mime") == "image/jpeg" and
            image.get("width", 0) >= 600 and image.get("height", 0) >= 450,
            "Commons art dimensions or format are unsuitable")
    meta = image.get("extmetadata") or {}
    value = lambda name: plain(meta.get(name, {}).get("value", ""))
    require(value("LicenseShortName").casefold() == "public domain" and
            value("UsageTerms").casefold() == "public domain" and
            value("Copyrighted").casefold() == "false" and
            value("AttributionRequired").casefold() == "false" and
            bool(value("Credit")), "Commons art rights metadata changed or is incomplete")
    require(image.get("descriptionurl") == item.get("description_url") and
            words(item.get("description_canary", "")) in words(value("ImageDescription")),
            "Commons description no longer supports the bounded scene")
    download = item.get("download_url")
    require(isinstance(download, str) and download == clean_url(download) and
            download in {clean_url(image.get("url", "")), clean_url(image.get("thumburl", ""))},
            "Commons download URL differs from the pinned original or thumbnail")
    body, mime = fetch(download, MAX_IMAGE_BYTES,
                       allowed_hosts={"upload.wikimedia.org", "thumb.wikimedia.org"})
    require(mime.startswith("image/jpeg") and body.startswith(b"\xff\xd8\xff") and
            hashlib.sha256(body).hexdigest() == item["sha256"],
            "Commons image bytes differ from the visually inspected pin")
    return {"title": title, "page": item["description_url"],
            "sha256": item["sha256"], "rights": "Commons public-domain assertion",
            "scene": item["scene"], "bytes": len(body)}


def build_payload(root: Path = ROOT) -> dict:
    pool = json.loads((root / "strategy/ACCIDENT-CANDIDATES.json").read_text())
    spec = json.loads((root / "strategy/ACCIDENT-INTAKE.json").read_text())
    require(spec.get("version") == 1 and spec.get("max_candidates_per_run") == 2 and
            {row.get("id") for row in spec.get("candidates", [])} == EXPECTED_IDS,
            "bounded intake manifest changed scope")
    by_id = {row["id"]: row for row in pool if isinstance(row, dict) and "id" in row}
    require(EXPECTED_IDS <= by_id.keys(), "checked source pool is missing an intake lead")
    stories = json.loads((root / "status/stories.json").read_text())
    used = {record["candidate_id"] for record in stories.get("topics", {}).values()
            if isinstance(record, dict) and record.get("candidate_id")}
    titles = set(stories.get("topics", {}))
    for folder in ("content/episodes", "content/rejected", "content/shelved"):
        for path in (root / folder).glob("ep*/topic.json"):
            meta = json.loads(path.read_text())
            if meta.get("candidate_id"):
                used.add(meta["candidate_id"])
            if meta.get("topic"):
                titles.add(meta["topic"])
    for line in (root / "strategy/CALENDAR.md").read_text().splitlines():
        if line.startswith("- "):
            titles.add(line[2:])
    return {"pool": [by_id[key] for key in sorted(EXPECTED_IDS)],
            "intake": spec["candidates"], "used_ids": sorted(used),
            "known_titles": sorted(titles)}


def audit(payload: dict) -> dict:
    """At most two live leads, four source pages, and four exact images."""
    intake = payload["intake"]
    pool = {row["id"]: row for row in payload["pool"]}
    require(len(intake) == 2 and {row["id"] for row in intake} == EXPECTED_IDS,
            "intake exceeded its two-lead bound")
    used = set(payload["used_ids"])
    known = [words(title) for title in payload["known_titles"]]
    results = []
    for entry in intake:
        candidate = pool[entry["id"]]
        aliases = [words(alias) for alias in candidate["aliases"]]
        duplicate = entry["id"] in used or any(
            f" {alias} " in f" {title} " for alias in aliases for title in known)
        if duplicate:
            results.append({"id": entry["id"], "state": "used_or_duplicate",
                            "eligible_for_selection": False})
            continue
        result = {"id": entry["id"], "state": "preflight_failed",
                  "eligible_for_selection": False, "sources": [], "art": []}
        try:
            source_plan = candidate["sources"]
            require(len(source_plan) == 2 and
                    {item.get("role") for item in source_plan} == {"primary", "independent"},
                    "candidate no longer has one original and one independent source")
            for source in source_plan:
                result["sources"].append(source_check(
                    source, entry["source_canaries"][source["role"]]))
            require(len({urlsplit(item["url"]).hostname for item in result["sources"]}) == 2,
                    "source pair is no longer from distinct hosts")
            require(len(entry["art"]) == 2 and
                    len({item["title"] for item in entry["art"]}) == 2,
                    "art preflight must pin two distinct scenes")
            for item in entry["art"]:
                result["art"].append(art_check(item))
            result["state"] = "technical_preflight_pass"
            if entry["primary_kind"] != "contemporaneous_board_report":
                result["state"] = "original_report_missing"
                result["source_limit"] = "Primary is a retrospective technical study, not a contemporary inquiry."
            result["selection_hold"] = (
                "Two checked images are not a finished visual plan; independent source, "
                "scene, script, and exact-media review are still required.")
        except (IntakeError, KeyError, TypeError, ValueError) as exc:
            result["failure"] = str(exc)[:300]
        results.append(result)
    return {"version": 1, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "bounded_leads": len(intake), "unused_leads": sum(
                item["state"] != "used_or_duplicate" for item in results),
            "technical_passes": sum(item["state"] == "technical_preflight_pass" for item in results),
            "eligible_for_selection": 0, "release_enabled": False, "candidates": results}


def issue_body(report: dict) -> str:
    lines = [f"Daily bounded source/art preflight: {report['checked_at_utc']}.", "",
             f"Unused checked leads: **{report['unused_leads']} of {report['bounded_leads']}**. "
             f"Technical passes: **{report['technical_passes']}**. "
             "Candidates cleared for producer selection: **0**.", "",
             "| Lead | Intake state | Hold or failure |", "|---|---|---|"]
    for item in report["candidates"]:
        reason = item.get("failure") or item.get("source_limit") or item.get("selection_hold") or "Already used or duplicated."
        lines.append(f"| `{item['id']}` | {item['state']} | {reason.replace('|', '/')} |")
    lines += ["", "Each run refetches the pinned primary and independent pages and the exact Commons images, "
              "checks event phrases, public-domain metadata, scene descriptions, and SHA-256 bytes. "
              "A technical pass is an editorial lead only. Two leads cannot sustain a 100-day schedule.",
              "Keep producer selection and recurring release closed until source claims, image rights/scene fit, "
              "script, and exact media pass independent review; prove ep065 public delivery and costs separately.",
              "The full per-run JSON is retained as an Actions artifact for 14 days."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--issue-body", type=Path, required=True)
    args = parser.parse_args()
    report = audit(build_payload())
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.issue_body.write_text(issue_body(report))
    print(json.dumps({"unused_leads": report["unused_leads"],
                      "technical_passes": report["technical_passes"],
                      "eligible_for_selection": 0,
                      "states": {item["id"]: item["state"] for item in report["candidates"]}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
