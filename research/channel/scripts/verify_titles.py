"""Verify exact English Wikipedia titles exist (no redirect) via the MediaWiki API, one curl call per title."""
import json
import subprocess
import sys
import time
import urllib.parse

TITLES = [
    "De Havilland Comet",
    "Hyatt Regency walkway collapse",
    "Citicorp Center engineering crisis",
    "Citigroup Center",
    "Gimli Glider",
    "British Airways Flight 5390",
    "Aloha Airlines Flight 243",
    "Tacoma Narrows Bridge (1940)",
    "Silver Bridge",
    "Quebec Bridge",
    "Iron Ring",
    "Cocoanut Grove fire",
    "SS Eastland",
    "St. Francis Dam",
    "Therac-25",
    "Tenerife airport disaster",
    "Grover Shoe Factory disaster",
    "Air Canada Flight 797",
    "Iroquois Theatre fire",
    "SS Schenectady (1942)",
    "Ronan Point",
    "United Airlines Flight 232",
    "1961 Goldsboro B-52 crash",
    "Texas City disaster",
    "Sultana (steamboat)",
    "SS Edmund Fitzgerald",
    "Johnstown Flood",
    "Kemper Arena",
    "Hartford Civic Center",
    "Point Pleasant, West Virginia",
    "British Airways Flight 9",
    "Air Transat Flight 236",
]


def check(title):
    url = "https://en.wikipedia.org/w/api.php?action=query&titles=" + urllib.parse.quote(title) + "&format=json&prop=info"
    for attempt in range(6):
        out = subprocess.run(["curl", "-s", "-A", "YouTubeChannel2-research/1.0 (niche research)", url],
                             capture_output=True, text=True).stdout
        try:
            data = json.loads(out)
            break
        except json.JSONDecodeError:
            time.sleep(5 * (attempt + 1))
    else:
        return "ERROR (rate limited)"
    pages = data["query"]["pages"]
    pid, page = next(iter(pages.items()))
    if pid == "-1" or "missing" in page:
        return "MISSING"
    norm = data["query"].get("normalized")
    flag = " REDIRECT" if "redirect" in page else ""
    return f"OK{flag} pageid={pid} title={page['title']!r}" + (f" (normalized from {norm[0]['from']!r})" if norm else "")


if __name__ == "__main__":
    titles = sys.argv[1:] or TITLES
    for t in titles:
        print(f"{t!r}: {check(t)}")
        time.sleep(1.0)
