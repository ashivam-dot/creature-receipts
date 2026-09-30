"""One-off research: channel, publish date and views for video IDs, plus that channel's public stats."""
import json
import re
import sys
import urllib.request

from yt_stats import stats

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                                               "Cookie": "CONSENT=YES+1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def video(vid):
    html = fetch(f"https://www.youtube.com/watch?v={vid}")
    g = lambda p: (re.search(p, html).group(1) if re.search(p, html) else None)
    return {
        "id": vid,
        "channel": g(r'"ownerChannelName":"([^"]+)"'),
        "owner": g(r'"ownerProfileUrl":"http://www.youtube.com/@([^"]+)"'),
        "published": g(r'"publishDate":"([^"]+)"'),
        "views": g(r'"viewCount":"(\d+)"'),
        "title": (g(r'<meta name="title" content="([^"]+)"') or "")[:80],
    }


if __name__ == "__main__":
    seen = {}
    for vid in sys.argv[1:]:
        try:
            v = video(vid)
        except Exception as e:
            print(json.dumps({"id": vid, "error": str(e)}))
            continue
        h = v.get("owner")
        if h and h not in seen:
            s = stats(h)
            seen[h] = {k: s.get(k) for k in ("subs", "videos", "views", "joined", "country")}
        v["channel_stats"] = seen.get(h)
        print(json.dumps(v))
