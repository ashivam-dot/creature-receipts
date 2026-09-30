"""One-off research: count long-form vs Shorts on a channel's public Videos and Shorts tabs (first page)."""
import json
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                                               "Cookie": "CONSENT=YES+1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def items(handle, tab):
    try:
        html = fetch(f"https://www.youtube.com/@{handle}/{tab}")
    except Exception:
        return []
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html)
    if not m:
        return []
    out = []

    def walk(o):
        if isinstance(o, dict):
            if "videoRenderer" in o:
                v = o["videoRenderer"]
                out.append(("long", "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))[:60],
                            v.get("viewCountText", {}).get("simpleText"), v.get("publishedTimeText", {}).get("simpleText")))
            if "shortsLockupViewModel" in o:
                s = o["shortsLockupViewModel"]["overlayMetadata"]
                out.append(("short", s.get("primaryText", {}).get("content", "")[:60],
                            s.get("secondaryText", {}).get("content"), None))
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(json.loads(m.group(1)))
    return out


if __name__ == "__main__":
    for h in sys.argv[1:]:
        v = items(h, "videos")
        s = items(h, "shorts")
        print(f"## @{h}: long-form on first page={len(v)}, shorts on first page={len(s)}")
        for row in (v[:6] + s[:8]):
            print("  ", row)
