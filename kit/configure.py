#!/usr/bin/env python3
"""Give the studio its channel's identity: name, handle, GitHub repository, owner email, launch date,
series, and first hashtag.

It can be run again: kit/channel.json keeps the current values, and each run maps them to the new ones.
Options left out keep their current values.

    python3 kit/configure.py --name "Cosmic Oddities" --handle CosmicOddities \
        --github octocat/cosmic-oddities --email owner@gmail.com --day-zero 2026-10-01 \
        --hashtag space --series "Space Is Weird" "Planets You Won't Believe" "Cosmic Records"

The repository's name becomes the slug for the Modal app and its volumes and secret. Nothing under
kit/, reference/, research/, secrets/, or the channel's content is changed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "kit" / "channel.json"
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".json", ".html", ".css", ".txt", ".plist", ".mdc", ".example"}
TEXT_NAMES = {".gitignore"}
SKIP_TOP = {".git", "kit", "reference", "research", "secrets", "analytics", "reports", "status", ".scratch", "logs"}
SKIP_PARTS = {".venv", ".cache", "__pycache__", "node_modules", ".ruff_cache"}
SKIP_FILES = {"START-HERE.md"}
# Channel content is never touched, except the test specs.
SKIP_PREFIXES = ("content/episodes/", "content/rejected/")
# Documents whose launch-date mentions follow --day-zero.
DATED = ("PLAYBOOK.md", "CHANNEL.md", "OWNER-CHECKLIST.md", "strategy/PLAN-100.md", "strategy/STRATEGY.md")

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 &.-]{1,38}[A-Za-z0-9.]")
HANDLE = re.compile(r"[A-Za-z0-9._-]{3,30}")
USER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{1,38}[a-z0-9]")
EMAIL = re.compile(r"[^@\s\"'<>]+@[^@\s\"'<>]+\.[A-Za-z]{2,}")
HASHTAG = re.compile(r"[a-z0-9]{2,30}")
CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}")
# Until the channel exists (kit/ACCOUNTS.md, step 3).
NO_CHANNEL_ID = "UCxxxxxxxxxxxxxxxxxxxxxx"
SERIES_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ,.'?!&:-]{1,58}[A-Za-z0-9.'?!]")


def fail(message: str) -> None:
    raise SystemExit(f"configure: {message}")


def load_state() -> dict:
    if not STATE.exists():
        fail(f"{STATE.relative_to(ROOT)} is missing; unpack the kit again")
    return json.loads(STATE.read_text(encoding="utf-8"))


def text_files() -> list[Path]:
    found = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if parts[0] in SKIP_TOP or SKIP_PARTS & set(parts) or rel.name in SKIP_FILES:
            continue
        if rel.as_posix().startswith(SKIP_PREFIXES):
            continue
        if path.suffix in TEXT_SUFFIXES or rel.name in TEXT_NAMES:
            found.append(path)
    return found


def identity_pairs(old: dict, new: dict) -> list[tuple[str, str]]:
    """Old and new spellings of each identity field, most specific first."""
    def compact(slug: str) -> str:
        return slug.replace("-", "")

    pairs = [
        (old.get("channel_id", NO_CHANNEL_ID), new.get("channel_id", NO_CHANNEL_ID)),
        (old["repo"], new["repo"]),
        (old["root"], new["root"]),
        (old["email"], new["email"]),
        (old["name"].upper(), new["name"].upper()),
        (old["name"].lower(), new["name"].lower()),
        (old["name"], new["name"]),
        (old["handle"], new["handle"]),
        (old["slug"], new["slug"]),
        (compact(old["slug"]), compact(new["slug"])),
    ]
    return [(a, b) for a, b in pairs if a and a != b]


def replace_identity(text: str, pairs: list[tuple[str, str]]) -> str:
    # Each old spelling is swapped for a placeholder first, so a new value that contains another old one
    # (a name that includes the old slug, say) isn't rewritten twice.
    marks = []
    for number, (old, new) in enumerate(pairs):
        mark = f"\x00{number}\x00"
        if old in text:
            text = text.replace(old, mark)
            marks.append((mark, new))
    for mark, new in marks:
        text = text.replace(mark, new)
    return text


def py_list(items: list[str], opener: str, closer: str) -> str:
    body = "".join(f"    {json.dumps(item, ensure_ascii=False)},\n" for item in items)
    return f"{opener}\n{body}{closer}"


def set_series(text: str, rel: str, series: list[str]) -> str:
    if rel == "pipeline/src/ytc/writer.py":
        text, count = re.subn(r"(?ms)^SERIES = \(\n.*?^\)", lambda _: py_list(series, "SERIES = (", ")"), text, count=1)
        if count != 1:
            fail("couldn't find SERIES in writer.py")
    elif rel == "pipeline/src/ytc/auto.py":
        text, count = re.subn(r"(?ms)^SERIES = \[.*?\]\n", lambda _: py_list(series, "SERIES = [", "]") + "\n", text, count=1)
        if count != 1:
            fail("couldn't find SERIES in auto.py")
    elif rel == "strategy/SCRIPT-RULES.md":
        listed = ", ".join(f"`{s}`" for s in series)
        text = re.sub(r"(?s)(- \*\*Series:\*\* one of ).*?(\. Spell it exactly)", lambda m: m.group(1) + listed + m.group(2), text, count=1)
    elif rel == "strategy/CALENDAR.md":
        text = set_calendar_series(text, series)
    return text


def set_calendar_series(text: str, series: list[str]) -> str:
    """Give the backlog one heading per series, keeping each kept series' topics."""
    lines = text.split("\n")
    try:
        start = lines.index("## Backlog")
    except ValueError:
        fail("strategy/CALENDAR.md has no '## Backlog' section")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    blocks: dict[str, list[str]] = {}
    intro: list[str] = []
    current = None
    for line in lines[start + 1:end]:
        if line.startswith("### "):
            current = line[4:].strip()
            blocks[current] = []
        elif current is None:
            intro.append(line)
        elif line.strip():
            blocks[current].append(line)
    orphans = {name: topics for name, topics in blocks.items() if name not in series and topics}
    if orphans:
        fail("these series have topics in strategy/CALENDAR.md and aren't in --series: " + ", ".join(orphans)
             + ". Move or delete their topics first.")
    section = ["## Backlog"] + (intro if any(l.strip() for l in intro) else [""])
    for name in series:
        section += [f"### {name}", ""] + blocks.get(name, [])
        if blocks.get(name):
            section.append("")
    return "\n".join(lines[:start] + section + lines[end:]).rstrip("\n") + "\n"


def set_hashtag(text: str, rel: str, old: str, new: str) -> str:
    if old == new:
        return text
    if rel == "pipeline/src/ytc/writer.py":
        text = text.replace(f'["{old}"] + [t for t in tags if t and t != "{old}"]',
                            f'["{new}"] + [t for t in tags if t and t != "{new}"]')
        text = re.sub(rf"#{re.escape(old)}\b", f"#{new}", text)
    elif rel == "strategy/SCRIPT-RULES.md":
        text = text.replace(f"`#{old}`", f"`#{new}`")
    return text


def set_day_zero(text: str, rel: str, old: str, new: str) -> str:
    if old == new:
        return text
    old_day, new_day = dt.date.fromisoformat(old), dt.date.fromisoformat(new)
    if rel == "pipeline/src/ytc/auto.py":
        text, count = re.subn(r"^DAY_ZERO = date\(\d+, \d+, \d+\)", f"DAY_ZERO = date({new_day.year}, {new_day.month}, {new_day.day})",
                              text, count=1, flags=re.M)
        if count != 1:
            fail("couldn't find DAY_ZERO in auto.py")
    elif rel in DATED:
        old_100, new_100 = (old_day + dt.timedelta(days=100)).isoformat(), (new_day + dt.timedelta(days=100)).isoformat()
        # Only the phrases that state the plan's dates: a decision logged on launch day keeps its date.
        for before, after in ((f"Day 0 is {old}", f"Day 0 is {new}"), (f"Day 100 is {old_100}", f"Day 100 is {new_100}"),
                              (f"today in IST - {old}", f"today in IST - {new}"), (f"Day 100 ({old_100})", f"Day 100 ({new_100})"),
                              (f"by {old_100}", f"by {new_100}")):
            text = text.replace(before, after)
    return text


def validate(new: dict) -> None:
    checks = [("name", NAME, "letters, digits, spaces, '&', '.', or '-', 3 to 40 characters"),
              ("handle", HANDLE, "3 to 30 letters, digits, '.', '_', or '-' (no @)"),
              ("slug", SLUG, "lowercase letters, digits, and dashes"),
              ("email", EMAIL, "an email address"),
              ("hashtag", HASHTAG, "lowercase letters and digits, without the #")]
    for field, pattern, rule in checks:
        if not pattern.fullmatch(new[field]):
            fail(f"--{field if field != 'slug' else 'github'} {new[field]!r} isn't valid: {rule}")
    if not CHANNEL_ID.fullmatch(new.get("channel_id", NO_CHANNEL_ID)):
        fail(f"--channel-id {new['channel_id']!r} isn't a channel ID: UC and 22 more letters, digits, '-', or '_'")
    user = new["repo"].split("/")[0]
    if not USER.fullmatch(user):
        fail(f"--github user {user!r} isn't a valid GitHub username")
    series = new["series"]
    if not 3 <= len(series) <= 8:
        fail("give 3 to 8 series")
    if len(set(s.lower() for s in series)) != len(series):
        fail("series names must differ")
    for name in series:
        if not SERIES_NAME.fullmatch(name) or " — " in name or "|" in name:
            fail(f"series {name!r} isn't valid: 3 to 60 characters of letters, digits, spaces, and , . ' ? ! & : -")
    dt.date.fromisoformat(new["day_zero"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--name", help="the channel's name, as on YouTube")
    parser.add_argument("--handle", help="the channel's handle, without the @")
    parser.add_argument("--github", help="owner/repository for the channel's private GitHub repository")
    parser.add_argument("--email", help="the owner's personal email")
    parser.add_argument("--day-zero", help="launch date, YYYY-MM-DD (day numbers and the 100-day plan count from it)")
    parser.add_argument("--hashtag", help="the hashtag every Short starts with, without the #")
    parser.add_argument("--series", nargs="+", help="the channel's series, in order")
    parser.add_argument("--channel-id", help="the YouTube channel's ID (UC...), once the channel exists")
    parser.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    args = parser.parse_args()

    old = load_state()
    new = dict(old)
    if args.name:
        new["name"] = " ".join(args.name.split())
    if args.handle:
        new["handle"] = args.handle.lstrip("@")
    if args.github:
        if args.github.count("/") != 1:
            fail("--github takes owner/repository")
        new["repo"] = args.github
        new["slug"] = args.github.split("/")[1].lower()
    if args.email:
        new["email"] = args.email
    if args.day_zero:
        new["day_zero"] = args.day_zero
    if args.hashtag:
        new["hashtag"] = args.hashtag.lstrip("#").lower()
    if args.series:
        new["series"] = [" ".join(s.split()) for s in args.series]
    if args.channel_id:
        new["channel_id"] = args.channel_id.strip()
    new["root"] = str(ROOT)
    validate(new)

    pairs = identity_pairs(old, new)
    # Every change is worked out before any file is written, so a refused change leaves nothing half done.
    updates = {}
    for path in text_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        updated = replace_identity(text, pairs)
        if new["series"] != old["series"]:
            updated = set_series(updated, rel, new["series"])
        updated = set_hashtag(updated, rel, old["hashtag"], new["hashtag"])
        updated = set_day_zero(updated, rel, old["day_zero"], new["day_zero"])
        if updated != text:
            updates[path] = updated
    changed = [path.relative_to(ROOT).as_posix() for path in updates]
    if not args.dry_run:
        for path, updated in updates.items():
            path.write_text(updated, encoding="utf-8")

    old_plist = ROOT / "monitor" / f"com.{old['slug'].replace('-', '')}.monitor.plist"
    new_plist = ROOT / "monitor" / f"com.{new['slug'].replace('-', '')}.monitor.plist"
    if old_plist != new_plist and old_plist.exists():
        changed.append(f"{old_plist.relative_to(ROOT)} -> {new_plist.name}")
        if not args.dry_run:
            old_plist.rename(new_plist)

    new["configured"] = True
    if not args.dry_run:
        STATE.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(("would change" if args.dry_run else "changed") + f" {len(changed)} files:")
    for rel in changed:
        print(f"  {rel}")
    channel_id = new.get("channel_id", NO_CHANNEL_ID)
    print(f"channel: {new['name']} (@{new['handle']}), repository {new['repo']}, Modal app {new['slug']}, "
          f"day 0 {new['day_zero']}, #{new['hashtag']}, {len(new['series'])} series, "
          + (f"channel ID {channel_id}" if channel_id != NO_CHANNEL_ID else "no channel ID yet (kit/ACCOUNTS.md, step 3)"))
    if not args.dry_run:
        print("next: python3 kit/verify.py --stage configured")


if __name__ == "__main__":
    sys.exit(main())
