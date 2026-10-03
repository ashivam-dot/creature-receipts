"""Watch the cloud studio. Read-only: it never changes the channel, the repo, or Buffer.

It pulls the studio's status, run history, and latest report from GitHub, checks Buffer's queue, Cloudinary's
usage, and the channel's public feed, then writes monitor/out/dashboard.html and reports each new alert: every
15 minutes on the owner's Mac (launchd, see monitor/install.py) as a macOS notification, and every 3 hours on
GitHub (.github/workflows/watchdog.yml) as a push to the owner's phone through ntfy. The watchdog also sends the
phone a summary of the day each morning.

    /usr/bin/python3 monitor/monitor.py            # refresh, print a summary
    /usr/bin/python3 monitor/monitor.py --open     # refresh and open the dashboard
    /usr/bin/python3 monitor/monitor.py --digest   # refresh and send the phone the day's summary now
"""

from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "monitor" / "out"
REPO = "ashivam-dot/creature-receipts"
WORKFLOW = "studio.yml"
# The channel's YouTube ID: python3 kit/configure.py --channel-id (kit/ACCOUNTS.md, step 3).
CHANNEL_ID = "UC6e6OB3iw3yp8JnnBYxLItA"
IST = ZoneInfo("Asia/Kolkata")
EASTERN = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
# The studio runs every 6 hours on Modal; GitHub's backup takes over when Modal's last run is 8 hours old, and
# its schedule runs late.
QUIET_HOURS = 11
INVENTORY_LOW = 9
MINUTES_LIMIT = 2000
CRON_HOURS_UTC = (5, 11, 17, 23)
CRON_MINUTE = 35
DIGEST_HOUR = 8
# Buffer allows 250 API requests a day for the key, shared with the studio's runs. The Mac reads it at most this
# often and shows the last answer in between; the watchdog on GitHub reads it on each of its checks.
BUFFER_EVERY = dt.timedelta(hours=2)
# The studio sends a post Buffer failed again while its due time is this recent (publish.RESEND_WINDOW).
RESEND_WINDOW = dt.timedelta(hours=1)
# The Studio app opens this link itself. No button for Buffer: its app claims none of Buffer's web links, and its
# bufferapp:// scheme goes nowhere when ntfy opens it.
STUDIO_URL = f"https://studio.youtube.com/channel/{CHANNEL_ID}/analytics/tab-overview/period-default"


def _gh() -> str:
    # launchd's PATH has none of the shell's additions, including AI Suite's tools where gh lives on this Mac.
    for candidate in (shutil.which("gh"), str(Path.home() / ".aisuite" / "bin" / "gh"), "/opt/homebrew/bin/gh", "/usr/local/bin/gh"):
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("the GitHub CLI (gh) isn't installed")


def gh_api(path: str):
    done = subprocess.run([_gh(), "api", path], capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip()[:300] or f"gh api {path} failed")
    return json.loads(done.stdout)


def repo_file(path: str, binary: bool = False):
    data = gh_api(f"repos/{REPO}/contents/{urllib.parse.quote(path)}")
    if isinstance(data, list):
        return data
    raw = base64.b64decode(data["content"]) if data.get("content") else _raw(data["download_url"])
    return raw if binary else raw.decode("utf-8")


def _raw(url: str) -> bytes:
    token = subprocess.run([_gh(), "auth", "token"], capture_output=True, text=True).stdout.strip()
    request = urllib.request.Request(url, headers={"Authorization": f"token {token}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _env() -> dict:
    """Keys from pipeline/.env on the Mac; the cloud watchdog gets them as environment variables instead."""
    values = {}
    path = ROOT / "pipeline" / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    values |= {k: v for k, v in os.environ.items() if k.startswith(("BUFFER_", "CLOUDINARY_")) and v}
    return values


def _parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def online() -> bool:
    try:
        urllib.request.urlopen("https://api.github.com/zen", timeout=10).read()
    except urllib.error.HTTPError:
        # Any answer means the network is up; this endpoint's anonymous limit is shared by everyone on a VPN.
        pass
    except Exception:
        return False
    return True


# --- sources ---------------------------------------------------------------------------------------------


def job_times(runs: list[dict], month: str) -> None:
    """Add when each run's job really started and finished: a run that waited for the one before it was created
    (and, to GitHub, started) hours earlier, and only the job's time is billed."""
    cache_path = OUT / "job_times.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    for run in runs:
        key = str(run["id"])
        if key not in cache and (run["status"] != "completed" or run["created_at"].startswith(month)):
            jobs = gh_api(f"repos/{REPO}/actions/runs/{run['id']}/jobs").get("jobs") or [{}]
            times = {"started": jobs[0].get("started_at"), "completed": jobs[0].get("completed_at")}
            if run["status"] == "completed":
                cache[key] = times
        else:
            times = cache.get(key, {})
        run["job_started_at"], run["job_completed_at"] = times.get("started"), times.get("completed")
    cache_path.write_text(json.dumps(cache))


def github() -> dict:
    runs = gh_api(f"repos/{REPO}/actions/workflows/{WORKFLOW}/runs?per_page=40")["workflow_runs"]
    workflow = gh_api(f"repos/{REPO}/actions/workflows/{WORKFLOW}")
    try:
        status = json.loads(repo_file("status/status.json"))
        history = [json.loads(line) for line in repo_file("status/history.jsonl").splitlines() if line.strip()]
    except RuntimeError as err:
        if "404" not in str(err) and "Not Found" not in str(err):
            raise
        # No studio run has finished yet.
        status, history = {}, []
    report_name = f"reports/day-{status.get('day', 0):03d}.md"
    try:
        report = repo_file(report_name)
    except RuntimeError:
        report = ""
    try:
        names = sorted(f["name"] for f in repo_file("analytics") if f["name"].endswith(".json"))
        analytics = json.loads(repo_file(f"analytics/{names[-1]}")) if names else {}
    except (RuntimeError, ValueError):
        analytics = {}
    try:
        scheduling_hold = json.loads(repo_file("status/scheduling_hold.json"))
    except (RuntimeError, ValueError):
        scheduling_hold = None
    try:
        private_videos = json.loads(repo_file("status/private_videos.json"))
    except (RuntimeError, ValueError):
        private_videos = {}
    month = dt.datetime.now(UTC).strftime("%Y-%m")
    job_times(runs, month)
    minutes = 0
    for run in runs:
        started, ended = _parse_time(run.get("job_started_at")), _parse_time(run.get("job_completed_at"))
        if run["created_at"].startswith(month) and started and ended and run["status"] == "completed":
            minutes += int((ended - started).total_seconds() // 60) + 1
    return {"runs": runs, "workflow_state": workflow.get("state"), "status": status, "history": history,
            "report": report, "report_name": report_name, "minutes": minutes,
            "youtube_channel": analytics.get("channel") or {}, "analytics_date": analytics.get("date"),
            "scheduling_hold": scheduling_hold, "private_videos": private_videos}


def buffer(env: dict) -> dict:
    """Buffer's queue as of its last read: at most every BUFFER_EVERY, and after Buffer refuses a read, not again
    until its limit resets."""
    key = env.get("BUFFER_API_KEY")
    if not key:
        return {"error": "no BUFFER_API_KEY in pipeline/.env"}
    path, now = OUT / "buffer.json", dt.datetime.now(UTC)
    kept = json.loads(path.read_text()) if path.exists() else {}
    if kept.get("next_read") and now < dt.datetime.fromisoformat(kept["next_read"]):
        return kept
    try:
        found = _read_buffer(key, env, kept.get("org")) | {"checked_at": now.isoformat(),
                                                             "next_read": (now + BUFFER_EVERY).isoformat()}
    except urllib.error.HTTPError as err:
        if err.code != 429:
            raise
        retry = err.headers.get("Retry-After", "")
        found = (kept if "scheduled" in kept else {"error": "Buffer's API limit (250 requests a day) is used up for now"}) \
            | {"next_read": (now + dt.timedelta(seconds=int(retry) if retry.isdigit() else 900)).isoformat()}
    path.write_text(json.dumps(found))
    return found


def _read_buffer(key: str, env: dict, org: str | None) -> dict:
    query = """query Posts($input: PostsInput!, $after: String) {
      posts(input: $input, first: 50, after: $after) {
        edges { node { id status dueAt sentAt externalLink text error { message }
                       metadata { ... on YoutubePostMetadata { title } } } }
        pageInfo { hasNextPage endCursor } } }"""
    org = org or _buffer(key, "query { account { organizations { id } } }")["account"]["organizations"][0]["id"]
    channels = _buffer(key, """query Channels($input: ChannelsInput!) {
      channels(input: $input) { id service isDisconnected isLocked isQueuePaused } }""",
                       {"input": {"organizationId": org}})["channels"]
    youtube = next((c for c in channels if c["id"] == env.get("BUFFER_YOUTUBE_CHANNEL_ID")), None) \
        or next((c for c in channels if c["service"] == "youtube"), None)
    now = dt.datetime.now(UTC)
    filters = {"startDate": (now - dt.timedelta(days=3)).isoformat(), "endDate": (now + dt.timedelta(days=365)).isoformat()}
    if channel := env.get("BUFFER_YOUTUBE_CHANNEL_ID"):
        filters["channelIds"] = [channel]
    variables = {"input": {"organizationId": org, "filter": filters}, "after": None}
    posts = []
    while True:
        page = _buffer(key, query, variables)["posts"]
        posts += [edge["node"] for edge in page["edges"]]
        if not page["pageInfo"]["hasNextPage"]:
            break
        variables["after"] = page["pageInfo"]["endCursor"]
    scheduled = sorted((p for p in posts if p["status"] not in ("sent", "error", "draft")), key=lambda p: p.get("dueAt") or "")
    return {"scheduled": scheduled, "errors": [p for p in posts if p["status"] == "error"],
            "sent": [p for p in posts if p["status"] == "sent"], "channel": youtube, "org": org}


def _buffer(key: str, query: str, variables: dict | None = None) -> dict:
    request = urllib.request.Request(
        "https://api.buffer.com", data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read())
    if body.get("errors"):
        raise RuntimeError(body["errors"][0].get("message", "Buffer error"))
    return body["data"]


def cloudinary(env: dict) -> dict:
    url = env.get("CLOUDINARY_URL")
    if not url:
        return {"error": "no CLOUDINARY_URL in pipeline/.env"}
    parsed = urllib.parse.urlparse(url)
    auth = base64.b64encode(f"{urllib.parse.unquote(parsed.username)}:{urllib.parse.unquote(parsed.password)}".encode()).decode()
    request = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{parsed.hostname}/usage", headers={"Authorization": f"Basic {auth}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        usage = json.loads(response.read())
    credits = usage.get("credits", {})
    return {"credits_used": credits.get("usage"), "credits_limit": credits.get("limit"), "percent": credits.get("used_percent"),
            "storage_mb": round((usage.get("storage", {}).get("usage") or 0) / 1e6), "plan": usage.get("plan")}


def youtube_feed() -> list[dict]:
    """The channel's public upload feed: proof that Shorts actually went live, independent of Buffer. YouTube
    answers the feed with a 404 or 500 about half the time, whatever the client, so it's asked up to six times."""
    for attempt in range(6):
        try:
            with urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}", timeout=30) as response:
                root = ET.fromstring(response.read())
            break
        except urllib.error.HTTPError:
            if attempt == 5:
                raise
            time.sleep(2)
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
    videos = []
    for entry in root.findall("a:entry", ns):
        stats = entry.find("media:group/media:community/media:statistics", ns)
        videos.append({"id": entry.findtext("yt:videoId", namespaces=ns), "title": entry.findtext("a:title", namespaces=ns),
                       "published": entry.findtext("a:published", namespaces=ns),
                       "views": int(stats.get("views", 0)) if stats is not None else None})
    return videos


# --- health ----------------------------------------------------------------------------------------------


def next_cron(now: dt.datetime) -> dt.datetime:
    now = now.astimezone(UTC)
    for day in range(2):
        for hour in CRON_HOURS_UTC:
            when = dt.datetime(now.year, now.month, now.day, hour, CRON_MINUTE, tzinfo=UTC) + dt.timedelta(days=day)
            if when > now:
                return when
    return now


def assess(data: dict) -> list[tuple[str, str]]:
    """(level, message) pairs; level is 'alert' or 'warn'."""
    problems: list[tuple[str, str]] = []
    now = dt.datetime.now(UTC)
    gh = data.get("github")
    if not gh:
        problems.append(("alert", f"Can't read the studio's status from GitHub: {data.get('github_error')}"))
        return problems
    status, runs = gh["status"], gh["runs"]
    scheduling_hold = gh.get("scheduling_hold")
    private_records = (gh.get("private_videos") or {}).get("videos") or []
    private_ids = {v["youtube_video_id"] for v in private_records
                   if v.get("privacy_status") == "private" and v.get("youtube_video_id")}
    private_episodes = {v["episode_id"] for v in private_records
                        if v.get("privacy_status") == "private" and v.get("episode_id")}
    if gh["workflow_state"] != "active":
        problems.append(("warn", f"The studio's backup workflow on GitHub is {gh['workflow_state']}, so nothing takes over if "
                                 f"Modal's runs stop (gh workflow enable {WORKFLOW} --repo {REPO})."))
    finished = [r for r in runs if r["status"] == "completed"]
    # Runs on Modal and on GitHub both write the history; a scheduled GitHub run that found Modal's fresh doesn't.
    history = gh.get("history") or []
    ended = [_parse_time(h["started_at_utc"]) + dt.timedelta(seconds=h.get("seconds", 0))
             for h in history if h.get("result") in ("ok", "degraded") and h.get("started_at_utc")]
    last_good = max(ended, default=None)
    if not last_good or now - last_good > dt.timedelta(hours=QUIET_HOURS):
        since = f"since {last_good.astimezone(IST):%a %H:%M} IST" if last_good else "yet"
        problems.append(("alert", f"No successful studio run {since}; runs are due every 6 hours."))
    run = status.get("run") or {}
    if run.get("host") == "github-actions" and run.get("trigger") == "schedule" and any(h.get("host") == "modal" for h in history):
        problems.append(("warn", "GitHub's backup made the last studio run, so Modal's scheduled runs stopped or failed "
                                 "(modal.com > creature-receipts > studio_run)."))
    if finished and finished[0]["conclusion"] not in ("success", "cancelled"):
        problems.append(("alert", f"The last studio run (#{finished[0]['run_number']}) ended {finished[0]['conclusion']}: {finished[0]['html_url']}"))
    running = [r for r in runs if r["status"] == "in_progress" and r.get("job_started_at")]
    if running and now - _parse_time(running[0]["job_started_at"]) > dt.timedelta(hours=5):
        problems.append(("alert", f"Studio run #{running[0]['run_number']} has been going for over 5 hours."))
    if status.get("result") == "degraded":
        problems.append(("warn", "The last run finished with problems: " + "; ".join(status.get("errors", []))[:400]))
    # With INVENTORY_LOW Shorts or more ready, Shorts wait for Gemini's reset by design; below it, Cursor takes over.
    stalled = [m["id"] for m in status.get("made", []) if m.get("quota")] \
        if status.get("inventory", {}).get("total", 0) < INVENTORY_LOW else []
    if stalled or any(note.startswith("holding production") for note in status.get("notes", [])):
        problems.append(("warn", "Gemini's free quota ran out and Cursor didn't take over, so Shorts waited ("
                                 + (", ".join(stalled) or "production held")
                                 + "); check the YTC_CURSOR_API_KEY secret (OWNER-CHECKLIST.md)."))
    for action in status.get("owner_action", []):
        problems.append(("alert", f"Owner action needed: {action}"))
    for stage in status.get("stages", []):
        if not stage.get("ok") and stage["name"].startswith("preflight "):
            problems.append(("alert", f"{stage['name'].removeprefix('preflight ')} may not go out: {stage.get('error')}"))
    inv = status.get("inventory", {})
    room = status.get("capacity") or {}
    why = (" The studio is making what its free budgets allow: Modal's monthly credit is used up and the runner is "
           "on its share of the Actions minutes. A card on Modal (OWNER-CHECKLIST.md) lifts this."
           if room and not room.get("cloud") and status.get("modal_credit", 1) < 10 else "")
    total = inv.get("total", 0)
    if scheduling_hold:
        problems.append(("warn", "New scheduling is paused for editorial review: "
                         + scheduling_hold.get("reason", "release checks are pending")))
    elif total < 3:
        ready, left = ("1 Short is", "in 1 day") if total == 1 else (f"{total} Shorts are", f"in {total} days" if total else "today")
        problems.append(("alert", f"Only {ready} ready; at one a day the channel runs dry {left}.{why}"))
    elif total < INVENTORY_LOW:
        # Matches auto.per_day.
        problems.append(("warn", f"Only {total} Shorts are ready (target {inv.get('target', 21)}), so the studio "
                                 f"posts {max(1, total // 3)} a day instead of 3.{why}"))
    for post in status.get("failed_posts", []):
        problems.append(("alert", f"Buffer failed to publish {post['id']}: {post.get('error')}"))
    for short in status.get("not_live", []):
        if short.get("id") in private_episodes:
            continue
        problems.append(("alert", f"{short['id']} went out through Buffer but isn't public on YouTube: {short['problem']}"))
    for job in status.get("in_cloud", []):
        started = _parse_time(job.get("spawned_at"))
        if started and now - started > dt.timedelta(hours=9):
            problems.append(("warn", f"{job['id']} ({job.get('topic')}) has been in the cloud since {started.astimezone(IST):%a %H:%M} IST; "
                                     "the next run stops and retries it."))
    rejected = [m for m in status.get("made", []) if m.get("outcome") == "rejected"]
    if len(rejected) >= 3:
        problems.append(("warn", f"{len(rejected)} Shorts failed the quality gate in the last run: "
                                 + "; ".join(f"{m['id']}: {m.get('reason')}" for m in rejected)[:300]))
    minutes = max(gh["minutes"], status.get("minutes_this_month", 0))
    # Making Shorts on the runner is paced to reach about 1,800 by the month's end.
    metered = status.get("minutes_budget", MINUTES_LIMIT) is not None
    if metered and minutes > MINUTES_LIMIT * 0.95:
        problems.append(("warn", f"GitHub Actions minutes this month: about {minutes:.0f} of {MINUTES_LIMIT}."))
    buf = data.get("buffer") or {}
    if buf.get("error"):
        problems.append(("warn", f"Can't read Buffer: {buf['error']}"))
    elif "scheduled" in buf:
        channel = buf.get("channel") or {}
        wrong = [name for flag, name in (("isDisconnected", "disconnected"), ("isLocked", "locked"),
                                          ("isQueuePaused", "paused")) if channel.get(flag)]
        if "channel" in buf and (not channel or wrong):
            problems.append(("alert", f"Buffer's YouTube channel is {' and '.join(wrong) or 'missing'}, so no Short goes out "
                                      "until it's fixed: publish.buffer.com > Settings > Channels, as aksha.shivam18@gmail.com."))
        read = _parse_time(buf.get("checked_at")) or now
        for post in buf.get("errors", []):
            due, why = _parse_time(post.get("dueAt")), (post.get("error") or {}).get("message")
            if due and dt.timedelta(0) <= read - due <= RESEND_WINDOW:
                problems.append(("warn", f"Buffer failed the post due {_when(post.get('dueAt'))} IST, and the studio is "
                                         f"sending it again: {why}"))
            else:
                problems.append(("alert", f"Buffer couldn't publish a post due {_when(post.get('dueAt'))} IST: {why}"))
        due = sorted(_parse_time(p["dueAt"]) for p in buf["scheduled"] if p.get("dueAt"))
        if not due:
            if not scheduling_hold:
                problems.append(("alert", "Buffer has nothing scheduled: no Shorts will go out."))
        # The longest gap between slots at the pace the stock allows (auto.per_day): 16 h at 3 a day, 18 at 2, 24 at 1.
        elif due[0] - now > dt.timedelta(hours={3: 16, 2: 18, 1: 24}[max(1, min(3, total // 3))] + 1):
            problems.append(("warn", f"Nothing publishes until {due[0].astimezone(IST):%a %H:%M} IST."))
    feed = data.get("feed")
    if isinstance(feed, list) and feed:
        newest = max(_parse_time(v["published"]) for v in feed)
        if now - newest > dt.timedelta(hours=26):
            level = "warn" if scheduling_hold else "alert"
            problems.append((level, f"No new Short on YouTube since {newest.astimezone(IST):%a %b %d %H:%M} IST."))
        public = {v["id"] for v in feed}
        for post in buf.get("sent", []):
            sent, link = _parse_time(post.get("sentAt")), post.get("externalLink") or ""
            video = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", link)
            if video and video.group(1) in private_ids:
                continue
            if sent and now - sent > dt.timedelta(hours=3) and not (video and video.group(1) in public):
                title = (post.get("metadata") or {}).get("title") or (post.get("text") or "")[:50]
                problems.append(("alert", f'"{title}" went to YouTube {sent.astimezone(IST):%a %H:%M} IST but isn\'t on '
                                          f"the channel's public feed: {link or 'Buffer has no YouTube link for it'}"))
    cld = data.get("cloudinary") or {}
    if cld.get("percent") and cld["percent"] > 80:
        problems.append(("warn", f"Cloudinary has used {cld['percent']:.0f}% of this month's free credits."))
    modal_cost = status.get("modal_cost") or {}
    credit = status.get("modal_credit", 1)
    if modal_cost.get("billed", 0) > 0:
        problems.append(("alert", f"Modal billed ${modal_cost['billed']:.2f} this month beyond its free credit: "
                                  "set the usage limit back to the credit in Modal's settings."))
    elif credit >= 10 and modal_cost.get("metered", 0) > credit * 0.8:
        # Without a card the $1 is meant to be used up every month; with one, running low is news.
        problems.append(("warn", f"Modal has used ${modal_cost['metered']:.2f} of its ${credit:g} monthly free credit."))
    if (status.get("open_topics") or 99) < 21:
        problems.append(("warn", f"Only {status['open_topics']} topics left in the calendar; the daily routine's "
                                 "'new topics' stage isn't keeping up."))
    return problems


# --- output ----------------------------------------------------------------------------------------------


def _when(value: str | None, zone=IST) -> str:
    t = _parse_time(value)
    return f"{t.astimezone(zone):%a %b %d %H:%M}" if t else "–"


def _ago(value: str | None) -> str:
    t = _parse_time(value)
    if not t:
        return "–"
    minutes = int((dt.datetime.now(UTC) - t).total_seconds() // 60)
    return f"{minutes} min ago" if minutes < 90 else f"{minutes // 60} h ago" if minutes < 48 * 60 else f"{minutes // 1440} days ago"


def _table(headers: list[str], rows: list[list]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body or '<tr><td colspan=9>none</td></tr>'}</tbody></table>"


def dashboard(data: dict, problems: list[tuple[str, str]]) -> str:
    gh = data.get("github") or {}
    status = gh.get("status") or {}
    level = "alert" if any(p[0] == "alert" for p in problems) else "warn" if problems else "ok"
    headline = {"ok": "All good", "warn": "Working, with warnings", "alert": "Needs attention"}[level]
    e = html.escape
    parts = [f"""<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="300">
<title>History's Last Hours monitor</title><style>
body{{font:14px -apple-system,system-ui,sans-serif;background:#0f1216;color:#e6e6e6;margin:24px;max-width:1200px}}
h1{{margin:0 0 4px}} h2{{margin:28px 0 8px;font-size:16px;color:#9fb3c8;text-transform:uppercase;letter-spacing:.05em}}
.badge{{display:inline-block;padding:6px 12px;border-radius:14px;font-weight:600}}
.ok{{background:#12391f;color:#7ee2a0}} .warn{{background:#3d3212;color:#f3d36b}} .alert{{background:#451616;color:#ff9b9b}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid #232a33;vertical-align:top}}
th{{color:#8a9bb0;font-weight:500}} a{{color:#7cc4ff}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.card{{background:#161b22;border:1px solid #232a33;border-radius:10px;padding:12px}} .big{{font-size:26px;font-weight:700}}
.muted{{color:#8a9bb0}} pre{{white-space:pre-wrap;background:#161b22;padding:12px;border-radius:10px;border:1px solid #232a33}}
.sheet img{{max-width:100%;border-radius:6px}} .sheets{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
</style></head><body>
<h1>History's Last Hours monitor</h1>
<div class="muted">Checked {dt.datetime.now(IST):%a %b %d %H:%M} IST · Day {status.get('day', '–')} of 100 ·
next studio run about {next_cron(dt.datetime.now(UTC)).astimezone(IST):%H:%M} IST · refreshes every 15 min</div>
<p><span class="badge {level}">{headline}</span></p>"""]
    if problems:
        parts.append("<ul>" + "".join(f'<li><span class="badge {l}">{l}</span> {e(m)}</li>' for l, m in problems) + "</ul>")
    inv = status.get("inventory", {})
    buf = data.get("buffer") or {}
    feed = data.get("feed") if isinstance(data.get("feed"), list) else []
    cld = data.get("cloudinary") or {}
    llm = status.get("llm", {})
    parts.append(f"""<h2>At a glance</h2><div class="grid">
<div class="card"><div class="muted">Shorts ready</div><div class="big">{inv.get('total', '–')} / {inv.get('target', 21)}</div>
<div class="muted">{inv.get('in_buffer', '–')} in Buffer · {inv.get('waiting', '–')} waiting · {len(inv.get('remote', []))} being made in the cloud · {len(inv.get('making', []))} half-made</div></div>
<div class="card"><div class="muted">Live on YouTube</div><div class="big">{status.get('live', '–')}</div>
<div class="muted">latest: {e(feed[0]['title'][:40]) if feed else '–'} ({_ago(feed[0]['published']) if feed else '–'})</div></div>
<div class="card"><div class="muted">Last studio run</div><div class="big">{e(status.get('result', '–'))}</div>
<div class="muted">{_ago(status.get('updated_at'))} · {round((status.get('run') or {}).get('seconds', 0) / 60)} min · {e(str((status.get('run') or {}).get('trigger')))}</div></div>
<div class="card"><div class="muted">Free-tier budgets</div><div>Actions: ~{max(gh.get('minutes', 0), status.get('minutes_this_month', 0)):.0f} / {MINUTES_LIMIT} min</div>
<div>Cloudinary: {cld.get('credits_used', '–')} / {cld.get('credits_limit', '–')} credits</div>
<div>Modal: ${(status.get('modal_cost') or {}).get('metered', '–')} / ${status.get('modal_credit', 1):g} credit</div>
<div>Room last run: {(status.get('capacity') or {}).get('cloud', '–')} on Modal, {(status.get('capacity') or {}).get('runner', '–')} on the runner</div>
<div>Models last run: {llm.get('calls', 0)} calls{' (' + e(', '.join(f'{m} {n}' for m, n in sorted((llm.get('by_model') or {}).items(), key=lambda kv: -kv[1]))) + ')' if llm.get('by_model') else ''}{', Gemini out: ' + ', '.join(llm.get('out_of_quota', [])) if llm.get('out_of_quota') else ''}</div>
<div>Renders: Modal {status.get('renders', {}).get('modal', 0)}, runner {status.get('renders', {}).get('runner', 0)}</div></div></div>""")

    parts.append("<h2>Last run, stage by stage</h2>")
    parts.append(_table(["Stage", "Result", "Seconds", "Detail"], [
        [e(s["name"]), "✅" if s["ok"] else "❌", s.get("seconds", ""), e(s.get("error") or s.get("detail") or "")[:300]]
        for s in status.get("stages", [])]))
    if status.get("notes"):
        parts.append("<p class='muted'>" + e("; ".join(status["notes"])) + "</p>")

    scheduled = buf.get("scheduled") if "scheduled" in buf else None
    queue = status.get("queue", [])
    titles = {q["id"]: q["title"] for q in queue}
    parts.append(f"<h2>Publishing queue (Buffer, read {_ago(buf.get('checked_at'))})</h2>")
    if scheduled is not None:
        parts.append(_table(["Publishes (IST)", "Publishes (ET)", "Short"], [
            [_when(p["dueAt"]), _when(p["dueAt"], EASTERN), e((p.get("text") or "").split("\n")[0][:90])] for p in scheduled]))
    else:
        parts.append(_table(["Id", "Publishes (IST)", "Title"], [[q["id"], _when(q["due_at"]), e(q["title"] or "")] for q in queue]))
    if status.get("waiting"):
        parts.append("<p>Waiting for a Buffer slot: " + ", ".join(f"{w['id']} ({e(w['title'] or '')})" for w in status["waiting"]) + "</p>")
    if status.get("in_cloud"):
        parts.append("<p>Being made on Modal: " + ", ".join(f"{j['id']} ({e(j.get('topic') or '')}, started {_ago(j.get('spawned_at'))})"
                                                           for j in status["in_cloud"]) + "</p>")

    parts.append("<h2>Made in recent runs</h2>")
    made = [m for h in gh.get("history", [])[-12:] for m in h.get("made", [])]
    parts.append(_table(["Run", "Result", "Made", "Started on Modal", "Scheduled", "Inventory", "Minutes", "Errors"], [
        [_when(h["started_at_utc"]), e(h["result"]), e(", ".join(h.get("made", [])) or "–"), e(", ".join(h.get("spawned", [])) or "–"),
         e(", ".join(h.get("published", [])) or "–"),
         h.get("inventory", "–"), round(h.get("seconds", 0) / 60), e("; ".join(h.get("errors", []))[:200])]
        for h in reversed(gh.get("history", [])[-15:])]))
    sheets = data.get("sheets", [])
    if sheets:
        parts.append('<div class="sheets">' + "".join(
            f'<div class="card sheet"><b>{e(s["id"])}</b> {e(s["title"])}<br><span class="muted">{e(s["scores"])}</span>'
            f'<img src="{s["file"]}"></div>' for s in sheets) + "</div>")

    parts.append("<h2>On YouTube (public feed)</h2>")
    parts.append(_table(["Published (IST)", "Title", "Views"], [
        [_when(v["published"]), f'<a href="https://www.youtube.com/shorts/{v["id"]}">{e(v["title"])}</a>', v.get("views", "–")] for v in feed[:12]]))

    parts.append("<h2>Studio runs on GitHub</h2>")
    parts.append(_table(["#", "Started (IST)", "Trigger", "Status", "Minutes"], [
        [f'<a href="{r["html_url"]}">{r["run_number"]}</a>', _when(r.get("job_started_at") or r["created_at"]), e(r["event"]),
         e(r["conclusion"] or r["status"]),
         round((_parse_time(r["job_completed_at"]) - _parse_time(r["job_started_at"])).total_seconds() / 60)
         if r.get("job_started_at") and r.get("job_completed_at") else "–"]
        for r in gh.get("runs", [])[:15]]))
    if gh.get("report"):
        parts.append(f"<h2>{e(gh['report_name'])}</h2><pre>{e(gh['report'])}</pre>")
    parts.append("</body></html>")
    return "\n".join(parts)


def recent_sheets(status: dict) -> list[dict]:
    """Contact sheets of the Shorts made in the last few runs, cached locally."""
    ids = [m["id"] for m in status.get("made", []) if m.get("outcome") == "ready"]
    ids += [w["id"] for w in status.get("waiting", [])]
    out, sheets_dir = [], OUT / "sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    for episode in list(dict.fromkeys(ids))[:6]:
        target = sheets_dir / f"{episode}.jpg"
        try:
            if not target.exists():
                target.write_bytes(repo_file(f"content/episodes/{episode}/sheet.jpg", binary=True))
            hold = json.loads(repo_file(f"content/episodes/{episode}/hold.json"))
            scores = ", ".join(f"{k} {v}" for k, v in (hold.get("scores") or {}).items())
            out.append({"id": episode, "title": hold.get("title", ""), "scores": scores, "file": f"sheets/{episode}.jpg"})
        except Exception:
            continue
    return out


def notify(problems: list[tuple[str, str]]) -> None:
    """A notification for each alert that wasn't there on the last check: on the Mac's screen, and on the owner's
    phone through ntfy when YTC_NTFY_TOPIC is set (only the cloud watchdog sets it, so the phone gets each alert once)."""
    seen_path = OUT / "seen.json"
    seen = set(json.loads(seen_path.read_text())) if seen_path.exists() else set()
    current = {re.sub(r"\d+", "#", m) for _, m in problems}
    topic = os.environ.get("YTC_NTFY_TOPIC")
    for level, message in problems:
        if re.sub(r"\d+", "#", message) not in seen and level == "alert":
            if sys.platform == "darwin":
                text = message.replace('"', "'")[:230]
                subprocess.run(["osascript", "-e", f'display notification "{text}" with title "History\'s Last Hours" subtitle "Needs attention" sound name "Basso"'],
                               capture_output=True)
            if topic:
                push(topic, message)
    seen_path.write_text(json.dumps(sorted(current)))


def push(topic: str, message: str, title: str = "History's Last Hours needs attention", priority: int = 4,
         tags: tuple[str, ...] = ("warning",), actions: list[dict] | None = None) -> bool:
    # JSON, so a title needn't be Latin-1 as a header must.
    body = {"topic": topic, "title": title, "message": message, "priority": priority, "tags": list(tags)}
    if actions:
        body["actions"] = actions
    request = urllib.request.Request("https://ntfy.sh/", data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            urllib.request.urlopen(request, timeout=30).read()
            return True
        except Exception as err:
            if attempt == 2:
                print(f"ntfy push failed: {err}", file=sys.stderr)
                return False
            time.sleep(5)
    return False


def _plural(n: int, word: str) -> str:
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def _clip(text: str, limit: int = 48) -> str:
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _slot(value: str | None) -> str:
    t = _parse_time(value)
    return f"{t.astimezone(IST):%a %H:%M}" if t else "–"


def digest(data: dict, problems: list[tuple[str, str]]) -> tuple[str, str]:
    """The day's summary for the phone: the channel, what's scheduled, the stock, the studio, and the budgets."""
    gh = data.get("github") or {}
    status = gh.get("status") or {}
    alerts = [m for level, m in problems if level == "alert"]
    warns = [m for level, m in problems if level == "warn"]
    state = (f"needs attention ({_plural(len(alerts), 'alert')})" if alerts
             else _plural(len(warns), "warning") if warns else "all good")
    # Android shows about eight lines of a notification, so what needs the owner comes first.
    shown = alerts or warns
    lines = [("Needs you: " if alerts else "Warning: ") + " | ".join(_clip(m, 160) for m in shown[:2])
             + (f" (and {len(shown) - 2} more)" if len(shown) > 2 else "")] if shown else []
    feed = data.get("feed") if isinstance(data.get("feed"), list) else []
    channel = gh.get("youtube_channel") or {}
    live = status.get("live")
    about = [_plural(live, "Short") + " live"] if live is not None else []
    if feed:
        # The feed's counts are live; the channel's total in the analytics lags by a day or more.
        views = sum(v.get("views") or 0 for v in feed)
        about.append(_plural(views, "view") + (f" on the latest {len(feed)}" if live and live > len(feed) else ""))
    if channel:
        day = gh.get("analytics_date") or ""
        when = "" if day == dt.datetime.now(IST).date().isoformat() else f" ({dt.date.fromisoformat(day):%b %d})" if day else ""
        about.append(_plural(channel.get("subscribers", 0), "subscriber") + when)
    if about:
        lines.append("Channel: " + ", ".join(about))
    if feed:
        newest = max(feed, key=lambda v: v["published"])
        lines.append(f"Newest: {_clip(newest['title'])} ({_ago(newest['published'])}, {_plural(newest.get('views') or 0, 'view')})")
        best = max(feed, key=lambda v: v.get("views") or 0)
        if best["id"] != newest["id"]:
            lines.append(f"Most viewed lately: {_clip(best['title'])} ({_plural(best.get('views') or 0, 'view')})")
    buf = data.get("buffer") or {}
    due = ([p["dueAt"] for p in buf["scheduled"] if p.get("dueAt")] if "scheduled" in buf
           else [q["due_at"] for q in status.get("queue", []) if q.get("due_at")])
    lines.append(f"Posting next: {', '.join(_slot(d) for d in due[:3])} IST ({len(due)} in Buffer)" if due
                 else "Posting next: nothing is scheduled in Buffer")
    inv = status.get("inventory") or {}
    if inv:
        making = len(inv.get("remote", [])) + len(inv.get("making", []))
        lines.append(f"Stock: {inv.get('total', 0)} Shorts ready of {inv.get('target', 42)}" + (f", {making} being made" if making else ""))
    if status:
        run = status.get("run") or {}
        host = {"modal": "Modal", "github-actions": "GitHub"}.get(run.get("host"), run.get("host") or "?")
        studio = (f"Studio: last run {status.get('result', '–')} {_ago(status.get('updated_at'))} on {host}, "
                  f"next about {next_cron(dt.datetime.now(UTC)).astimezone(IST):%H:%M} IST")
        if (status.get("llm") or {}).get("out_of_quota") or any(n.startswith("holding production") for n in status.get("notes", [])):
            studio += ", waiting for Gemini's daily reset"
        lines.append(studio)
    cost, cld = status.get("modal_cost") or {}, data.get("cloudinary") or {}
    budgets = [f"Modal ${cost.get('metered', 0):.2f} of ${status.get('modal_credit', 0):g}"] if cost else []
    if cld.get("credits_limit"):
        budgets.append(f"Cloudinary {cld.get('credits_used') or 0:g} of {cld['credits_limit']:g} credits")
    if budgets:
        lines.append("This month: " + ", ".join(budgets))
    return f"Day {status.get('day', '–')} of 100: {state}", "\n".join(lines)


def send_digest(data: dict, problems: list[tuple[str, str]], force: bool = False) -> None:
    """The day's summary goes to the phone on the watchdog's first check after DIGEST_HOUR IST, at normal priority
    (alerts come high). It comes every day, so a morning without one means the watchdog itself stopped. force sends
    it now, from the Mac too (--digest, with the topic from pipeline/.env)."""
    topic = os.environ.get("YTC_NTFY_TOPIC") or (_env().get("YTC_NTFY_TOPIC") if force else None)
    path = OUT / "digest.json"
    today = dt.datetime.now(IST).date().isoformat()
    sent = json.loads(path.read_text()).get("date") if path.exists() else None
    if not topic or not (force or (sent != today and dt.datetime.now(IST).hour >= DIGEST_HOUR)):
        return
    title, message = digest(data, problems)
    actions = [{"action": "view", "label": "YouTube Studio", "url": STUDIO_URL}]
    if push(topic, message, title=title, priority=3, tags=("bar_chart",), actions=actions):
        path.write_text(json.dumps({"date": today}))


def collect() -> dict:
    data: dict = {"checked_at": dt.datetime.now(UTC).isoformat()}
    env = _env()
    try:
        data["github"] = github()
    except Exception as err:
        data["github_error"] = str(err)
    for name, fn in (("buffer", lambda: buffer(env)), ("cloudinary", lambda: cloudinary(env)), ("feed", youtube_feed)):
        try:
            data[name] = fn()
        except Exception as err:
            data[name] = {"error": f"{type(err).__name__}: {err}"[:200]}
    # The watchdog on GitHub only sends alerts; nobody opens its dashboard.
    if data.get("github") and not os.environ.get("GITHUB_ACTIONS"):
        data["sheets"] = recent_sheets(data["github"]["status"])
    return data


def summary(data: dict, problems: list[tuple[str, str]]) -> str:
    status = (data.get("github") or {}).get("status") or {}
    inv = status.get("inventory", {})
    lines = [f"History's Last Hours, {dt.datetime.now(IST):%a %b %d %H:%M} IST, day {status.get('day', '–')}",
             f"  last studio run: {status.get('result', '–')} ({_ago(status.get('updated_at'))}), "
             f"made {', '.join(m['id'] + ' ' + m['outcome'] for m in status.get('made', [])) or 'nothing'}",
             f"  ready: {inv.get('total', '–')}/{inv.get('target', 21)} ({inv.get('in_buffer', '–')} in Buffer, {inv.get('waiting', '–')} waiting, "
             f"{len(inv.get('remote', []))} being made on Modal)",
             f"  live Shorts: {status.get('live', '–')}"]
    runs = (data.get("github") or {}).get("runs", [])
    running = [r for r in runs if r["status"] == "in_progress" and r.get("job_started_at")]
    waiting = [r for r in runs if r["status"] in ("queued", "pending", "waiting", "requested")
               or (r["status"] == "in_progress" and not r.get("job_started_at"))]
    if waiting:
        lines.insert(2, f"  waiting: run #{waiting[-1]['run_number']}, queued {_ago(waiting[-1]['created_at'])}")
    if running:
        lines.insert(2, f"  running now: run #{running[0]['run_number']}, started {_ago(running[0]['job_started_at'])}")
    lines += [f"  {level.upper()}: {message}" for level, message in problems] or ["  no problems"]
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not online():
        (OUT / "last.txt").write_text(f"{dt.datetime.now(IST):%a %H:%M} IST: offline, nothing checked\n")
        print("offline: nothing checked")
        return
    data = collect()
    problems = assess(data)
    (OUT / "dashboard.html").write_text(dashboard(data, problems), encoding="utf-8")
    (OUT / "last.json").write_text(json.dumps({"problems": problems, "checked_at": data["checked_at"]}, indent=2))
    text = summary(data, problems)
    (OUT / "last.txt").write_text(text + "\n")
    notify(problems)
    send_digest(data, problems, force="--digest" in sys.argv or os.environ.get("YTC_DIGEST_NOW") == "true")
    print(text)
    print(f"dashboard: {OUT / 'dashboard.html'}")
    if "--open" in sys.argv:
        subprocess.run(["open", "-na", "Google Chrome", "--args", "--profile-directory=Default", (OUT / "dashboard.html").as_uri()])


if __name__ == "__main__":
    main()
