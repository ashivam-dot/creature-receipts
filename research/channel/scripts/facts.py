"""Print sentences from English Wikipedia plain-text extracts that contain given keywords (fact spot-checks)."""
import json
import re
import subprocess
import time
import urllib.parse

CHECKS = {
    "De Havilland Comet": ["ADF", "square", "fatigue"],
    "Hyatt Regency walkway collapse": ["rod", "double", "114"],
    "Citicorp Center engineering crisis": ["Hartley", "quartering", "night", "1995"],
    "Gimli Glider": ["pounds", "kilogram", "drag", "race"],
    "British Airways Flight 5390": ["bolts", "Lancaster", "diameter"],
    "Aloha Airlines Flight 243": ["Lansing", "aging", "cycles"],
    "Tacoma Narrows Bridge (1940)": ["Tubby", "dog"],
    "Silver Bridge": ["eyebar", "inch", "National Bridge Inspection"],
    "Quebec Bridge": ["1916", "collapsed", "Iron Ring"],
    "Cocoanut Grove fire": ["revolving", "outward", "492"],
    "SS Eastland": ["lifeboats", "844", "Seamen"],
    "St. Francis Dam": ["Mulholland", "inspect", "hours"],
    "Therac-25": ["race condition", "quickly", "operator"],
    "Tenerife airport disaster": ["bomb", "Gran Canaria", "takeoff", "phraseology"],
    "Grover Shoe Factory disaster": ["boiler", "ASME", "code"],
}


def extract(title):
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "titles": title,
                                "format": "json", "formatversion": 2})
    for attempt in range(6):
        out = subprocess.run(["curl", "-s", "-A", "YouTubeChannel2-research/1.0 (niche research)",
                              "https://en.wikipedia.org/w/api.php?" + q], capture_output=True, text=True).stdout
        try:
            return json.loads(out)["query"]["pages"][0].get("extract", "")
        except Exception:
            time.sleep(5 * (attempt + 1))
    return ""


if __name__ == "__main__":
    for title, kws in CHECKS.items():
        text = extract(title)
        sents = re.split(r"(?<=[.!?])\s+", text)
        print(f"## {title}")
        for kw in kws:
            hits = [s.strip() for s in sents if kw.lower() in s.lower()][:2]
            for h in hits:
                print(f"  [{kw}] {h[:260]}")
        time.sleep(1)
