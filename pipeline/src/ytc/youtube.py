"""YouTube Data and Analytics API access through the owner's own Google Cloud app: analytics and playlists.

Uploads don't go through here: videos uploaded by an unaudited app are locked private, so publishing
uses Buffer instead (see publish.py).
"""

from __future__ import annotations

import json
import os
import re
import webbrowser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .spec import ShortSpec

ROOT = Path(__file__).resolve().parents[3]
SECRETS = ROOT / "secrets"
CLIENT_FILE = SECRETS / "client_secret.json"
TOKEN_FILE = SECRETS / "token.json"
CHANNEL_COPY = ROOT / "brand" / "CHANNEL-COPY.md"
# force-ssl covers playlists now and comment moderation later, so the owner consents once.
MANAGE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
SCOPES = [MANAGE_SCOPE, "https://www.googleapis.com/auth/yt-analytics.readonly"]
LANGUAGE = "en"
RETENTION_POINTS = (0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
CHANNEL_BROWSER = "chrome-profile-1"
VIDEO_METRICS = (
    "views,engagedViews,averageViewDuration,averageViewPercentage,likes,comments,shares,"
    "subscribersGained,subscribersLost"
)


def authorize() -> Path:
    """One-time interactive sign-in in the channel owner's Chrome profile."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    webbrowser.register(
        CHANNEL_BROWSER,
        None,
        webbrowser.GenericBrowser(["open", "-na", "Google Chrome", "--args", "--profile-directory=" + os.environ.get("YTC_CHROME_PROFILE", "Default"), "%s"]),
    )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    creds = flow.run_local_server(port=0, browser=CHANNEL_BROWSER, prompt="consent")
    _save_token(creds)
    return TOKEN_FILE


def _save_token(creds: Credentials) -> None:
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    TOKEN_FILE.chmod(0o600)


def _credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        raise RuntimeError("Not signed in: run `ytc auth` once")
    # Keep the scopes the owner actually granted: asking a refresh for more fails with invalid_scope.
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
    if not creds.valid:
        creds.refresh(Request())
        _save_token(creds)
    return creds


def _query(analytics, **params) -> list[dict]:
    try:
        result = analytics.reports().query(ids="channel==MINE", **params).execute()
    except HttpError as err:
        if "engagedViews" not in params.get("metrics", "") or err.resp.status != 400:
            raise
        params["metrics"] = params["metrics"].replace("engagedViews,", "")
        result = analytics.reports().query(ids="channel==MINE", **params).execute()
    names = [header["name"] for header in result.get("columnHeaders", [])]
    return [dict(zip(names, row)) for row in result.get("rows", [])]


def _retention(analytics, video_id: str, window: dict) -> list[dict]:
    """Share of viewers still watching at points through a Short (above 1 means rewatches), and how that
    compares with videos of similar length (0.5 is typical)."""
    try:
        rows = _query(
            analytics,
            metrics="audienceWatchRatio,relativeRetentionPerformance",
            dimensions="elapsedVideoTimeRatio",
            filters=f"video=={video_id}",
            **window,
        )
    except HttpError:
        return []
    points, seen = [], set()
    for want in RETENTION_POINTS:
        row = min(rows, key=lambda r: abs(r["elapsedVideoTimeRatio"] - want), default=None)
        if row is None or row["elapsedVideoTimeRatio"] in seen:
            continue
        seen.add(row["elapsedVideoTimeRatio"])
        points.append({
            "at": row["elapsedVideoTimeRatio"],
            "watching": round(row["audienceWatchRatio"], 3),
            "vs_similar": round(row["relativeRetentionPerformance"], 3),
        })
    return points


def stats(days: int = 28) -> dict:
    creds = _credentials()
    data = build("youtube", "v3", credentials=creds, cache_discovery=False)
    analytics = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)

    channel = data.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()["items"][0]
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    items = data.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50).execute()["items"]
    video_ids = [item["contentDetails"]["videoId"] for item in items]
    videos = (
        data.videos().list(part="snippet,statistics,contentDetails", id=",".join(video_ids)).execute()["items"]
        if video_ids
        else []
    )

    end = date.today()
    window = {"startDate": (end - timedelta(days=days)).isoformat(), "endDate": end.isoformat()}
    per_video = _query(analytics, metrics=VIDEO_METRICS, dimensions="video", sort="-views", maxResults=200, **window)
    per_day = _query(analytics, metrics="views,engagedViews,subscribersGained,subscribersLost", dimensions="day", **window)
    traffic = _query(analytics, metrics="views", dimensions="insightTrafficSourceType", **window)
    ninety = _query(
        analytics,
        metrics="views,engagedViews",
        startDate=(end - timedelta(days=90)).isoformat(),
        endDate=end.isoformat(),
    )

    by_video = {row["video"]: row for row in per_video}
    for row in by_video.values():
        # Stands in for Studio's "stayed to watch", which the API lacks. Replays count as views but not as
        # engaged views, so it reads a little low for Shorts that loop well.
        if row.get("views") and "engagedViews" in row:
            row["engaged_share"] = round(row["engagedViews"] / row["views"], 3)
    return {
        "date": end.isoformat(),
        # How old each Short was when counted, for growth.breakouts.
        "taken_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "channel": {
            "id": channel["id"],
            "title": channel["snippet"]["title"],
            "subscribers": int(channel["statistics"].get("subscriberCount", 0)),
            "views": int(channel["statistics"].get("viewCount", 0)),
            "videos": int(channel["statistics"].get("videoCount", 0)),
        },
        "last_90_days": ninety[0] if ninety else {},
        "daily": per_day,
        "traffic_sources": traffic,
        "videos": [
            {
                "id": video["id"],
                "title": video["snippet"]["title"],
                "published": video["snippet"]["publishedAt"],
                "duration": video["contentDetails"]["duration"],
                "views": int(video["statistics"].get("viewCount", 0)),
                "likes": int(video["statistics"].get("likeCount", 0)),
                "comments": int(video["statistics"].get("commentCount", 0)),
                "analytics": by_video.get(video["id"], {}),
                "retention": _retention(analytics, video["id"], window) if video["id"] in by_video else [],
            }
            for video in videos
        ],
    }


def short_numbers(video_ids: list[str]) -> dict[str, dict]:
    """Each Short's numbers now: views, likes and comments as of this minute, and what YouTube Analytics has so
    far (it lags a day or two) on watching, retention, and where the views came from."""
    if not video_ids:
        return {}
    creds = _credentials()
    data = build("youtube", "v3", credentials=creds, cache_discovery=False)
    analytics = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    out = {}
    for start in range(0, len(video_ids), 50):
        for video in data.videos().list(part="snippet,statistics", id=",".join(video_ids[start:start + 50])).execute()["items"]:
            published = datetime.fromisoformat(video["snippet"]["publishedAt"].replace("Z", "+00:00"))
            window = {"startDate": published.date().isoformat(), "endDate": date.today().isoformat()}
            try:
                rows = _query(analytics, metrics=VIDEO_METRICS, filters=f"video=={video['id']}", **window)
                sources = _query(analytics, metrics="views", dimensions="insightTrafficSourceType",
                                 filters=f"video=={video['id']}", **window)
            except HttpError:
                rows, sources = [], []
            stats = video["statistics"]
            out[video["id"]] = {
                "published": published.isoformat(),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "analytics": rows[0] if rows else {},
                "sources": {row["insightTrafficSourceType"]: row["views"] for row in sources},
                "retention": _retention(analytics, video["id"], window) if rows else [],
            }
    return out


def _pages(method, **params) -> list[dict]:
    items, token = [], None
    while True:
        page = method(**params, **({"pageToken": token} if token else {})).execute()
        items += page.get("items", [])
        token = page.get("nextPageToken")
        if not token:
            return items


def _series_copy() -> dict[str, str]:
    """Playlist titles and descriptions from the series table in brand/CHANNEL-COPY.md."""
    section = CHANNEL_COPY.read_text(encoding="utf-8").split("## Series and playlists", 1)[1].split("\n## ", 1)[0]
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in section.splitlines() if line.startswith("|")]
    return {name: about for name, about in rows[2:]}


def file_into_playlists(content_dir: Path) -> list[str]:
    """Add every live Short to its series playlist, creating the playlist the first time; returns what changed."""
    creds = _credentials()
    if MANAGE_SCOPE not in (creds.scopes or []):
        raise RuntimeError("the saved sign-in can't edit playlists: run `ytc auth` again")
    data = build("youtube", "v3", credentials=creds, cache_discovery=False)
    about = _series_copy()
    playlists = {p["snippet"]["title"]: p["id"] for p in _pages(data.playlists().list, part="snippet", mine=True, maxResults=50)}
    members: dict[str, set[str]] = {}
    changes = []
    for record_path in sorted(content_dir.glob("*/publish.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        found = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", record.get("youtube_url") or "")
        series = ShortSpec.load(record_path.parent / "short.yaml").series
        if record.get("status") != "sent" or not found or not series:
            continue
        video_id = found.group(1)
        if series not in playlists and series not in about:
            changes.append(f"skipped {record['id']}: series {series!r} isn't in brand/CHANNEL-COPY.md")
            continue
        if series not in playlists:
            body = {"snippet": {"title": series, "description": about.get(series, "")}, "status": {"privacyStatus": "public"}}
            playlists[series] = data.playlists().insert(part="snippet,status", body=body).execute()["id"]
            members[playlists[series]] = set()
            changes.append(f"created playlist {series!r}")
        playlist = playlists[series]
        if playlist not in members:
            items = _pages(data.playlistItems().list, part="contentDetails", playlistId=playlist, maxResults=50)
            members[playlist] = {item["contentDetails"]["videoId"] for item in items}
        if video_id in members[playlist]:
            continue
        body = {"snippet": {"playlistId": playlist, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
        data.playlistItems().insert(part="snippet", body=body).execute()
        members[playlist].add(video_id)
        changes.append(f"added {record['id']} to {series!r}")
    return changes


def fix_languages(content_dir: Path) -> list[str]:
    """Set each live Short's title and audio language to English where YouTube has another: the upload sets none,
    and YouTube guessed French for ep013 (2026-10-01), which points its first test at the wrong viewers."""
    wanted = {}
    for record_path in sorted(content_dir.glob("*/publish.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("status") == "sent" and (found := re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", record.get("youtube_url") or "")):
            wanted[found.group(1)] = record["id"]
    if not wanted:
        return []
    data = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)
    changes = []
    ids = list(wanted)
    for start in range(0, len(ids), 50):
        for item in data.videos().list(part="snippet", id=",".join(ids[start:start + 50])).execute()["items"]:
            snippet = item["snippet"]
            if snippet.get("defaultLanguage") == LANGUAGE and snippet.get("defaultAudioLanguage") == LANGUAGE:
                continue
            body = {key: snippet[key] for key in ("title", "description", "categoryId", "tags") if key in snippet}
            body.update(defaultLanguage=LANGUAGE, defaultAudioLanguage=LANGUAGE)
            data.videos().update(part="snippet", body={"id": item["id"], "snippet": body}).execute()
            changes.append(f"{wanted[item['id']]} language {snippet.get('defaultLanguage')}/{snippet.get('defaultAudioLanguage')} -> {LANGUAGE}")
    return changes


def check_live(content_dir: Path) -> list[dict]:
    """Each Short Buffer sent in the last three days, at least an hour ago, that YouTube hasn't made public:
    {"id", "problem"}, with YouTube's reason when it gives one."""
    now, problems, wanted = datetime.now(timezone.utc), [], {}
    for record_path in sorted(content_dir.glob("*/publish.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("status") != "sent" or not record.get("sent_at"):
            continue
        if not timedelta(hours=1) < now - datetime.fromisoformat(record["sent_at"]) < timedelta(days=3):
            continue
        if found := re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", record.get("youtube_url") or ""):
            wanted[found.group(1)] = record["id"]
        else:
            problems.append({"id": record["id"], "problem": "Buffer sent it but has no YouTube link for it"})
    if not wanted:
        return problems
    data = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)
    found = {item["id"]: item["status"] for item in data.videos().list(part="status", id=",".join(wanted)).execute()["items"]}
    for video_id, short_id in wanted.items():
        status = found.get(video_id)
        if status is None:
            problems.append({"id": short_id, "problem": f"YouTube has no video {video_id}"})
        elif status.get("uploadStatus") != "processed" or status.get("privacyStatus") != "public":
            reason = status.get("rejectionReason") or status.get("failureReason")
            problems.append({"id": short_id, "problem": f"upload {status.get('uploadStatus')}, {status.get('privacyStatus')}"
                                                        + (f" ({reason})" if reason else "")})
    return problems


def save_stats(out_dir: Path) -> Path:
    report = stats()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{report['date']}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
