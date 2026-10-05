#!/usr/bin/env python3
"""Look each day for free things that could make the studio better, and tell the owner about each one once.

    python3 monitor/scout.py

Checks OpenRouter's free models, the Gemini models the channel's key can use, new open-source projects that
are taking off on GitHub in the studio's fields (voices, video, motion, depth), and the models trending on the
Hugging Face Hub for speech, image-to-video and pictures whose licence allows a monetized channel. What it finds
goes to the job's summary and, when YTC_NTFY_TOPIC is set, to the owner's phone in one message. It only reports: trying a find and
switching to it stays a reviewed change. Pexels isn't checked here because its site refuses scripted requests.

The first run only records what already exists, so the phone hears about new things rather than the whole list.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
STATE = OUT / "scout.json"
# GitHub topics for the studio's parts: the narrator, the footage and motion, and the depth effect on stills.
TOPICS = ("text-to-speech", "tts", "voice-cloning", "video-generation", "image-to-video", "video-editing",
          "motion-graphics", "depth-estimation", "stock-footage")
NEW_REPO_DAYS = 45
NEW_REPO_STARS = 300
# Too little context for a research prompt with its sources (llm.BACKUPS takes 250,000).
MIN_CONTEXT = 100_000
# Hugging Face Hub tasks for the narrator, the motion and the pictures, and how many trending models to read in each.
HF_TASKS = ("text-to-speech", "image-to-video", "text-to-image")
HF_PER_TASK = 20
# A licence label with one of these can't be used on a monetized channel (cc-by-nc-*, *-non-commercial-*,
# *-research-*, Coqui's CPML); NONCOMMERCIAL_NAMES are whole labels. A model with no licence, or only "other"
# without naming it, is skipped too: there is nothing to check its terms against.
NONCOMMERCIAL = ("-nc", "noncommercial", "non-commercial", "non_commercial", "research", "coqui-public-model")
NONCOMMERCIAL_NAMES = ("mrl", "cpml")


def _get(url: str, headers: dict | None = None) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "creature-receipts-scout", **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def openrouter_free() -> dict[str, str]:
    found = {}
    for model in _get("https://openrouter.ai/api/v1/models")["data"]:
        pricing = model.get("pricing") or {}
        if str(pricing.get("prompt")) != "0" or str(pricing.get("completion")) != "0":
            continue
        if (model.get("context_length") or 0) < MIN_CONTEXT:
            continue
        inputs = (model.get("architecture") or {}).get("input_modalities") or []
        sees = " and reads pictures" if "image" in inputs else ""
        found[f"openrouter:{model['id']}"] = f"OpenRouter free model {model['id']}: {model['context_length']:,} tokens{sees}"
    return found


def gemini_models() -> dict[str, str] | None:
    key = os.environ.get("YTC_GEMINI_API_KEY")
    if not key:
        return None
    found, token = {}, ""
    while True:
        query = urllib.parse.urlencode({"pageSize": 1000, **({"pageToken": token} if token else {})})
        page = _get(f"https://generativelanguage.googleapis.com/v1beta/models?{query}", {"x-goog-api-key": key})
        for model in page.get("models", []):
            if "generateContent" in model.get("supportedGenerationMethods", []):
                name = model["name"].removeprefix("models/")
                found[f"gemini:{name}"] = f"Gemini model {name} ({model.get('displayName', name)}) answers on the channel's key"
        if not (token := page.get("nextPageToken")):
            return found


def rising_repos() -> dict[str, str]:
    since = (datetime.now(timezone.utc) - timedelta(days=NEW_REPO_DAYS)).date().isoformat()
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    found = {}
    for number, topic in enumerate(TOPICS):
        # Search allows 30 requests a minute with a token and 10 without.
        time.sleep(2.5 if number and headers.get("Authorization") else 7 if number else 0)
        query = urllib.parse.urlencode({"q": f"topic:{topic} created:>{since} stars:>{NEW_REPO_STARS}",
                                        "sort": "stars", "per_page": 10})
        for repo in _get(f"https://api.github.com/search/repositories?{query}", headers).get("items", []):
            about = (repo.get("description") or "").strip()[:140]
            found[f"repo:{repo['full_name']}"] = (f"New on GitHub ({topic}): {repo['full_name']}, "
                                                  f"{repo['stargazers_count']:,} stars. {about} {repo['html_url']}")
    return found


def hf_licences(model: dict) -> list[str]:
    """Every licence label a Hub model carries: its license: tags and its card's license and license_name."""
    card = model.get("cardData") or {}
    labels = [tag.removeprefix("license:") for tag in model.get("tags") or [] if tag.startswith("license:")]
    for field in ("license", "license_name"):
        value = card.get(field)
        labels += value if isinstance(value, list) else [value] if value else []
    return list(dict.fromkeys(str(label).strip().lower() for label in labels if str(label).strip()))


def commercial(labels: list[str]) -> bool:
    return set(labels) - {"other", "unknown"} != set() and not any(
        label in NONCOMMERCIAL_NAMES or any(marker in label for marker in NONCOMMERCIAL) for label in labels)


def hf_trending() -> dict[str, str]:
    found = {}
    for task in HF_TASKS:
        query = urllib.parse.urlencode([("pipeline_tag", task), ("sort", "trendingScore"), ("limit", HF_PER_TASK),
                                        *(("expand[]", field) for field in ("cardData", "tags", "likes", "trendingScore"))])
        for model in _get(f"https://huggingface.co/api/models?{query}"):
            labels = hf_licences(model)
            # A quantized re-upload trends alongside the model it copies, which is reported in its own right.
            if not commercial(labels) or (model.get("cardData") or {}).get("base_model_relation") == "quantized":
                continue
            found[f"hf:{model['id']}"] = (f"Trending on Hugging Face ({task}): {model['id']}, "
                                          f"{model.get('likes', 0):,} likes, licence {' / '.join(labels)}. "
                                          f"https://huggingface.co/{model['id']}")
    return found


CHECKS = {"openrouter": openrouter_free, "gemini": gemini_models, "repos": rising_repos, "huggingface": hf_trending}


def push(topic: str, message: str) -> None:
    body = {"topic": topic, "title": "History's Last Hours scout: new free tools", "message": message[:3900],
            "priority": 3, "tags": ["mag"]}
    request = urllib.request.Request("https://ntfy.sh/", data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json"})
    urllib.request.urlopen(request, timeout=30).read()


def main() -> int:
    OUT.mkdir(exist_ok=True)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    new, failed = [], []
    for name, check in CHECKS.items():
        try:
            found = check()
        except Exception as err:
            failed.append(f"{name}: {type(err).__name__}")
            continue
        if found is None:
            continue
        if name in state:
            new += [found[k] for k in sorted(found) if k not in state[name]]
        # Kept seen even when a model leaves, so one that comes and goes isn't reported each time.
        state[name] = sorted(set(state.get(name, [])) | set(found))
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")

    lines = [f"- {line}" for line in new] or ["- Nothing new today."]
    if failed:
        lines.append(f"- Couldn't check: {', '.join(failed)}")
    report = "## Scout\n\n" + "\n".join(lines) + "\n"
    print(report)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(report)
    if new and (topic := os.environ.get("YTC_NTFY_TOPIC")):
        push(topic, "\n".join(f"• {line}" for line in new))
    return 0


if __name__ == "__main__":
    sys.exit(main())
