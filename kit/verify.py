#!/usr/bin/env python3
"""Check the studio at each setup gate. Each stage includes the ones before it.

    python3 kit/verify.py --stage kit          # the kit is complete and its code compiles
    python3 kit/verify.py --stage configured   # the channel's identity is set everywhere (kit/configure.py)
    python3 kit/verify.py --stage adapted      # the niche is written in: no NICHE: markers, calendar seeded
    python3 kit/verify.py --stage predeploy    # after `git add -A`: keys set, and nothing secret is staged

Prints each problem with where to fix it and exits 1 if there are any. Never prints a secret's value.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import configure  # noqa: E402

STAGES = ("kit", "configured", "adapted", "predeploy")
REQUIRED_FILES = (
    "START-HERE.md", "PLAYBOOK.md", "CHANNEL.md", "OWNER-CHECKLIST.md", ".gitignore", "kit/channel.json",
    "pipeline/pyproject.toml", "pipeline/uv.lock", "pipeline/.python-version", "pipeline/.env.example",
    "pipeline/modal_secret.py", "pipeline/src/ytc/auto.py", "pipeline/src/ytc/cloud.py", "pipeline/src/ytc/writer.py",
    "pipeline/assets/fonts/Anton-Regular.ttf", ".github/workflows/studio.yml", ".github/workflows/watchdog.yml",
    ".github/backup_gate.py", "monitor/monitor.py", "strategy/CALENDAR.md", "strategy/LEARNINGS.md",
    "strategy/SCRIPT-RULES.md", "strategy/STRATEGY.md", "strategy/PLAN-100.md",
)
PLACEHOLDERS = ("Kit Channel", "KIT CHANNEL", "kit channel", "KitChannel", "kit-channel", "kitchannel", "kit-owner",
                "owner@example.com", "/Users/you/youtube-studio")
# Wording from the channel the kit came from that would make the new one write about history.
RESIDUE = ("strange-but-true history", "Days of Odd", "DaysOfOdd", "days-of-odd", "history Short")
RESIDUE_IN = ("pipeline/src/", "strategy/SCRIPT-RULES.md", "site/", "brand/make_brand.py")
LEARNINGS_HEADINGS = ("## What to beat", "## Rules we've proven", "## Hypotheses to test", "## Scoreboard", "## Log")
MEASURES = ("Engaged share", "Average percentage viewed", "Still watching at 10%", "Subscribers per 1,000 views",
            "Likes per 100 views")
RULES_SECTIONS = ("## Script rules", "## Metadata rules", "## Visual rules", "## Sound rules", "## Spec schema")
STATUS_MARK = re.compile(r"\s+—\s+(making|done|dropped|parked)\s+\((ep\d{3})\)\s*$")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MIN_TOPICS, MIN_PER_SERIES = 40, 3
REQUIRED_ENV = ("YTC_CONTACT", "BUFFER_API_KEY", "BUFFER_YOUTUBE_CHANNEL_ID", "CLOUDINARY_URL", "MODAL_TOKEN_ID",
                "MODAL_TOKEN_SECRET", "YTC_GEMINI_API_KEY")
NOT_SECRET = {"YTC_CONTACT", "BUFFER_YOUTUBE_CHANNEL_ID", "BUFFER_TIKTOK_CHANNEL_ID", "BUFFER_INSTAGRAM_CHANNEL_ID",
              "YTC_MODAL_CREDIT", "YTC_LLM_FIRST", "YTC_CURSOR_MODEL",
              "YTC_DESCRIPTION_LINKS", "YTC_IMAGE_PROVIDER", "BUFFER_ORG_ID", "YTC_CHROME_PROFILE"}
# The fields of the Google sign-in files that are secret (the project id and URLs aren't).
SECRET_FIELDS = {"client_secret", "refresh_token", "token", "access_token", "id_token", "private_key"}


class Report:
    def __init__(self) -> None:
        self.problems: list[str] = []
        self.warnings: list[str] = []

    def problem(self, text: str) -> None:
        self.problems.append(text)

    def warn(self, text: str) -> None:
        self.warnings.append(text)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def assigned(rel: str, name: str):
    for node in ast.parse(read(rel)).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
    return None


def calendar(text: str) -> tuple[list[str], dict[str, list[str]], list[str]]:
    """The backlog's series headings, each series' open topics, and the anniversary dates."""
    headings, topics, dates = [], {}, []
    section = series = None
    for line in text.splitlines():
        if line.startswith("## "):
            section, series = line[3:].strip(), None
        elif line.startswith("### ") and section == "Backlog":
            series = line[4:].strip()
            headings.append(series)
            topics[series] = []
        elif section == "Backlog" and series and line.startswith("- ") and not STATUS_MARK.search(line):
            topics[series].append(line[2:].strip())
        elif section and section.startswith("Anniversaries") and line.startswith("| ") and not line.startswith(("| Date", "|---")):
            dates.append(line.strip().strip("|").split("|")[0].strip())
    return headings, topics, dates


def check_kit(report: Report) -> dict:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            report.problem(f"{rel} is missing: unpack the kit again")
    # The pipeline is written for Python 3.12 (pipeline/.python-version); older interpreters can't parse all of it.
    modern = sys.version_info >= (3, 12)
    if not modern:
        report.warn(f"Python {sys.version_info.major}.{sys.version_info.minor} skips the pipeline's syntax check; "
                    "`uv run --no-sync python ../kit/verify.py` in pipeline/ runs it")
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if configure.SKIP_PARTS & set(rel.parts) or rel.parts[0] in (".git", "reference", "research"):
            continue
        if not modern and rel.parts[:2] == ("pipeline", "src"):
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(rel), "exec")
        except SyntaxError as err:
            report.problem(f"{rel}:{err.lineno}: syntax error: {err.msg}")
    for name in ("instagram.py", "reels.py"):
        if (ROOT / "pipeline/src/ytc" / name).exists():
            report.warn(f"pipeline/src/ytc/{name} isn't part of the kit")
    return configure.load_state()


def check_configured(report: Report, state: dict) -> None:
    if not state.get("configured"):
        report.problem("kit/configure.py hasn't been run yet")
    for path in configure.text_files():
        rel = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            found = [p for p in PLACEHOLDERS if p in line]
            if found:
                report.problem(f"{rel}:{number}: placeholder {found[0]!r} left; run kit/configure.py with every option")
    series = state["series"]
    for rel in ("pipeline/src/ytc/writer.py", "pipeline/src/ytc/auto.py"):
        node = assigned(rel, "SERIES")
        values = list(ast.literal_eval(node)) if node is not None else None
        if values != series:
            report.problem(f"{rel}: SERIES doesn't match kit/channel.json; run kit/configure.py --series ...")
    headings, _, _ = calendar(read("strategy/CALENDAR.md"))
    if headings != series:
        report.problem("strategy/CALENDAR.md: the Backlog's ### headings must be the series, in order "
                       f"(found {headings}); run kit/configure.py --series ...")
    rules = read("strategy/SCRIPT-RULES.md")
    missing = [s for s in series if f"`{s}`" not in rules]
    if missing:
        report.problem(f"strategy/SCRIPT-RULES.md: the Series rule doesn't list {missing}")
    tag = state["hashtag"]
    writer = read("pipeline/src/ytc/writer.py")
    if f'["{tag}"]' not in writer or f"#{tag}" not in writer:
        report.problem(f"pipeline/src/ytc/writer.py doesn't enforce #{tag} as the first hashtag; run kit/configure.py --hashtag {tag}")
    day = state["day_zero"].split("-")
    if not re.search(rf"^DAY_ZERO = date\({int(day[0])}, {int(day[1])}, {int(day[2])}\)", read("pipeline/src/ytc/auto.py"), re.M):
        report.problem("pipeline/src/ytc/auto.py: DAY_ZERO doesn't match kit/channel.json")


def check_adapted(report: Report, state: dict) -> None:
    if state.get("channel_id", configure.NO_CHANNEL_ID) == configure.NO_CHANNEL_ID:
        report.problem("no channel ID yet: `python3 kit/configure.py --channel-id UC...` (kit/ACCOUNTS.md, step 3)")
    # "history Short" is normal wording for this channel, but residue in a copied kit.
    residue = tuple(r for r in RESIDUE if r != "history Short" or state.get("hashtag") != "history")
    for path in configure.text_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if "NICHE:" in line:
                report.problem(f"{rel}:{number}: NICHE marker; rewrite this for the niche, then delete the marker "
                               "(kit/NICHE-ADAPTATION.md)")
            if rel.startswith(RESIDUE_IN) and (hit := next((r for r in residue if r in line), None)):
                report.problem(f"{rel}:{number}: still says {hit!r} (the channel this kit came from)")
    headings, topics, dates = calendar(read("strategy/CALENDAR.md"))
    total = sum(len(t) for t in topics.values())
    if total < MIN_TOPICS:
        report.problem(f"strategy/CALENDAR.md: {total} open topics; seed at least {MIN_TOPICS}")
    for series, items in topics.items():
        if len(items) < MIN_PER_SERIES:
            report.problem(f"strategy/CALENDAR.md: series {series!r} has {len(items)} topics; give it {MIN_PER_SERIES} or more")
    for label in dates:
        if not re.match(rf"({'|'.join(MONTHS)}) \d{{1,2}}\b", label):
            report.problem(f"strategy/CALENDAR.md: anniversary date {label!r} should look like 'Oct 7'")
    if not dates:
        report.warn("strategy/CALENDAR.md has no anniversaries; dated stories get a boost on their day")
    learnings = read("strategy/LEARNINGS.md")
    for heading in LEARNINGS_HEADINGS:
        if heading not in learnings:
            report.problem(f"strategy/LEARNINGS.md lost {heading!r}; the daily routine needs it")
    what = learnings.split("## What to beat")[-1].split("\n## ")[0]
    for label in MEASURES:
        if f"| {label}" not in what:
            report.problem(f"strategy/LEARNINGS.md: the 'What to beat' table needs its {label!r} row")
    rules = read("strategy/SCRIPT-RULES.md")
    for heading in RULES_SECTIONS:
        if heading not in rules:
            report.problem(f"strategy/SCRIPT-RULES.md lost {heading!r}; writer.py reads the rules by these headings")
    for rel, size in (("strategy/STRATEGY.md", 3000), ("strategy/PLAN-100.md", 1500), ("CHANNEL.md", 3000)):
        if len(read(rel)) < size:
            report.warn(f"{rel} looks short; is it written for the new channel?")
    for rel in ("brand/out/avatar-800.png", "brand/out/banner-2560x1440.jpg", "brand/CREDITS.md", "brand/CHANNEL-COPY.md"):
        if not (ROOT / rel).exists():
            report.warn(f"{rel} is missing (brand: kit/NICHE-ADAPTATION.md)")


def env_values() -> dict[str, str]:
    path = ROOT / "pipeline" / ".env"
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines() if path.exists() else []:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


def secret_values() -> dict[str, str]:
    """Secret strings to look for in staged files, by where they came from. Never printed."""
    found = {k: v for k, v in env_values().items() if k not in NOT_SECRET and len(v) >= 8}

    def strings(value, prefix):
        if isinstance(value, dict):
            for key, item in value.items():
                yield from strings(item, f"{prefix}.{key}")
        elif isinstance(value, list):
            for item in value:
                yield from strings(item, prefix)
        elif isinstance(value, str) and len(value) >= 16 and prefix.rsplit(".", 1)[-1] in SECRET_FIELDS:
            yield prefix, value

    for name in ("client_secret.json", "token.json"):
        path = ROOT / "secrets" / name
        if path.exists():
            try:
                for key, value in strings(json.loads(path.read_text(encoding="utf-8")), f"secrets/{name}"):
                    found[key] = value
            except json.JSONDecodeError:
                pass
    key = ROOT / "secrets" / "modal_deploy_key"
    if key.exists():
        for number, line in enumerate(key.read_text(encoding="utf-8").splitlines()):
            if len(line) >= 40 and "PRIVATE KEY" not in line:
                found[f"secrets/modal_deploy_key line {number}"] = line
    return found


def check_predeploy(report: Report, state: dict) -> None:
    if not (ROOT / ".git").exists():
        report.problem("no git repository yet: run `git init -b main` and `git add -A` in the studio folder")
        return
    staged = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    staged = [s for s in staged if s]
    if not staged:
        report.problem("nothing is staged: run `git add -A` first")
    for rel in staged:
        parts = rel.split("/")
        if rel == "pipeline/.env" or parts[0] == "secrets" or rel.endswith((".pem", ".key")) or "modal_deploy_key" in rel:
            report.problem(f"{rel} is staged but must never be committed: `git rm --cached {rel}` and check .gitignore")
        if configure.SKIP_PARTS & set(parts):
            report.problem(f"{rel} is staged (a cache or environment folder); check .gitignore")
    wanted = secret_values()
    for rel in staged:
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, value in wanted.items():
            if value in text:
                report.problem(f"{rel} contains the value of {name}; take it out before committing")
    values = env_values()
    for name in REQUIRED_ENV:
        if not values.get(name):
            report.problem(f"{name} isn't set in pipeline/.env (kit/ACCOUNTS.md)")
    for name, how in (("client_secret.json", "kit/ACCOUNTS.md, step 3"), ("token.json", "`uv run --no-sync ytc auth` in pipeline/")):
        if not (ROOT / "secrets" / name).exists():
            report.problem(f"secrets/{name} is missing ({how})")
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True)
    if remote.returncode == 0 and state["repo"].lower() not in remote.stdout.lower():
        report.problem(f"the git remote ({remote.stdout.strip()}) isn't {state['repo']}; fix it or re-run kit/configure.py --github")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--stage", choices=STAGES, default="kit")
    args = parser.parse_args()
    report = Report()
    state = check_kit(report)
    upto = STAGES.index(args.stage)
    if upto >= 1:
        check_configured(report, state)
    if upto >= 2:
        check_adapted(report, state)
    if upto >= 3:
        check_predeploy(report, state)
    for text in report.warnings:
        print(f"warning: {text}")
    for number, text in enumerate(report.problems, start=1):
        print(f"{number}. {text}")
    print(f"{args.stage}: " + (f"FAIL, {len(report.problems)} to fix" if report.problems else "PASS"))
    return 1 if report.problems else 0


if __name__ == "__main__":
    sys.exit(main())
