"""Print public subscriber and video counts for YouTube handles (reads the public channel page)."""
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


def stats(handle):
    try:
        html = fetch(f"https://www.youtube.com/@{handle}/about")
    except Exception as e:
        return {"handle": handle, "error": str(e)}
    out = {"handle": handle}
    m = re.search(r'"title":"([^"]+)","description"', html)
    t = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    out["title"] = t.group(1) if t else (m.group(1) if m else None)
    for key, pat in [
        ("subs", r'"subscriberCountText":"([^"]+)"'),
        ("videos", r'"videoCountText":"([^"]+)"'),
        ("views", r'"viewCountText":"([\d,]+ views)"'),
        ("joined", r'"joinedDateText":\{"content":"Joined ([^"]+)"'),
        ("country", r'"country":"([^"]+)"'),
    ]:
        mm = re.search(pat, html)
        if mm:
            out[key] = mm.group(1)
    return out


if __name__ == "__main__":
    for h in sys.argv[1:]:
        print(json.dumps(stats(h)))
