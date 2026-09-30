"""One-off research: list channels behind top YouTube search results for a query (public page)."""
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                                               "Cookie": "CONSENT=YES+1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def walk(o, found):
    if isinstance(o, dict):
        if "videoRenderer" in o:
            v = o["videoRenderer"]
            title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
            ch = v.get("ownerText", {}).get("runs", [{}])[0]
            url = ch.get("navigationEndpoint", {}).get("browseEndpoint", {}).get("canonicalBaseUrl", "")
            found.append({
                "kind": "video",
                "channel": ch.get("text"),
                "handle": url,
                "title": title[:90],
                "views": v.get("viewCountText", {}).get("simpleText"),
                "age": v.get("publishedTimeText", {}).get("simpleText"),
            })
        if "shortsLockupViewModel" in o:
            s = o["shortsLockupViewModel"]
            found.append({
                "kind": "short",
                "title": s.get("overlayMetadata", {}).get("primaryText", {}).get("content", "")[:90],
                "views": s.get("overlayMetadata", {}).get("secondaryText", {}).get("content"),
                "id": s.get("onTap", {}).get("innertubeCommand", {}).get("reelWatchEndpoint", {}).get("videoId"),
            })
        for val in o.values():
            walk(val, found)
    elif isinstance(o, list):
        for val in o:
            walk(val, found)


def search(q, sp=""):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q) + (f"&sp={sp}" if sp else "")
    html = fetch(url)
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html)
    if not m:
        return []
    found = []
    walk(json.loads(m.group(1)), found)
    return found


if __name__ == "__main__":
    sp = ""
    args = sys.argv[1:]
    if args and args[0].startswith("--sp="):
        sp = args[0][5:]
        args = args[1:]
    for q in args:
        print(f"## {q}")
        for r in search(q, sp)[:25]:
            print(json.dumps(r))
