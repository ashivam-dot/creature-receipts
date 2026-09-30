"""Median 60-day English Wikipedia pageviews of flagship articles per candidate niche (demand proxy)."""
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "YouTubeChannel2-research/1.0 (niche research; contact: owner)"
START, END = "20260801", "20260929"

NICHES = {
    "Deep ocean & sea creatures": ["Giant squid", "Anglerfish", "Mariana Trench", "Coelacanth", "Bloop", "Goblin shark", "Colossal squid", "Oarfish", "Challenger Deep", "Megalodon"],
    "Engineering disasters": ["Tacoma Narrows Bridge (1940)", "Hyatt Regency walkway collapse", "St. Francis Dam", "Citigroup Center", "Silver Bridge", "Quebec Bridge", "Johnstown Flood", "Ronan Point", "Sampoong Department Store collapse", "Therac-25"],
    "Aviation incidents": ["Tenerife airport disaster", "Japan Air Lines Flight 123", "Gimli Glider", "Aloha Airlines Flight 243", "De Havilland Comet", "United Airlines Flight 232", "US Airways Flight 1549", "Air France Flight 447", "Malaysia Airlines Flight 370", "British Airways Flight 5390"],
    "Bizarre medical history": ["Phineas Gage", "Radium Girls", "Lobotomy", "Trepanning", "Mary Mallon", "Henrietta Lacks", "Thalidomide", "Bloodletting", "Mummia", "Tuskegee Syphilis Study"],
    "Frauds, scams & heists": ["Charles Ponzi", "Bernie Madoff", "Frank Abagnale", "Victor Lustig", "Antwerp diamond heist", "Isabella Stewart Gardner Museum theft", "Great Train Robbery (1963)", "Enron scandal", "Theranos", "D. B. Cooper"],
    "Money & economic history": ["Rai stones", "1933 double eagle", "Silver Thursday", "Hungarian pengő", "Zimbabwean dollar", "Panic of 1907", "Executive Order 6102", "Knight Capital Group", "Nixon shock", "Black Monday (1987)"],
    "Extreme animals & biology": ["Tardigrade", "Mantis shrimp", "Axolotl", "Honey badger", "Immortal jellyfish", "Pistol shrimp", "Platypus", "Naked mole-rat", "Cordyceps", "Box jellyfish"],
    "Geography & border oddities": ["Baarle-Nassau", "Bir Tawil", "Northwest Angle", "Point Roberts, Washington", "Kaliningrad Oblast", "Pheasant Island", "Kentucky Bend", "Märkisch Buchholz", "Diomede Islands", "Nagorno-Karabakh"],
    "Cold War & military secrets": ["Operation Mockingbird", "Project MKUltra", "Stanislav Petrov", "Vasily Arkhipov", "Operation Northwoods", "1961 Goldsboro B-52 crash", "Project Azorian", "Able Archer 83", "Berlin Tunnel", "Tsar Bomba"],
    "Archaeology & ancient mysteries": ["Antikythera mechanism", "Göbekli Tepe", "Terracotta Army", "Voynich manuscript", "Ötzi", "Nazca Lines", "Baghdad Battery", "Library of Alexandria", "Stonehenge", "Rosetta Stone"],
    "Weather & natural disasters": ["Tri-State tornado", "1900 Galveston hurricane", "Year Without a Summer", "Carrington Event", "1883 eruption of Krakatoa", "Great Blizzard of 1888", "Lake Nyos disaster", "1925 serum run to Nome", "Dust Bowl", "Great Chicago Fire"],
    "Inventions & accidental discoveries": ["Penicillin", "Microwave oven", "Post-it Note", "Teflon", "Vulcanization", "Saccharin", "X-ray", "Velcro", "Super Glue", "Slinky"],
    "Psychology & brain": ["Stanford prison experiment", "Milgram experiment", "Little Albert experiment", "Bystander effect", "Dunning–Kruger effect", "Marshmallow experiment", "Rat Park", "Clever Hans", "H.M. (patient)", "Capgras delusion"],
    "True crime lite": ["Zodiac Killer", "Lizzie Borden", "Black Dahlia", "Jack the Ripper", "Tylenol murders", "Lindbergh kidnapping", "Alcatraz escape (June 1962)", "Somerton Man", "Axeman of New Orleans", "Leopold and Loeb"],
    "Food history": ["Ketchup", "Coca-Cola", "Twinkie", "Garum", "Graham cracker", "Hardtack", "SPAM", "Fortune cookie", "Caesar salad", "Chicken tikka masala"],
    "Shipwrecks & maritime": ["Titanic", "SS Edmund Fitzgerald", "Mary Celeste", "USS Indianapolis (CA-35)", "Endurance (1912 ship)", "SS Eastland", "Sultana (steamboat)", "Andrea Doria", "HMHS Britannic", "SS Central America"],
}


def get_json(url):
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            return None
        except Exception:
            time.sleep(2)
    return None


def resolve(titles):
    """Map each title to its canonical article title (following redirects); None if missing."""
    q = urllib.parse.urlencode({"action": "query", "titles": "|".join(titles), "redirects": 1,
                                "format": "json", "formatversion": 2})
    data = get_json("https://en.wikipedia.org/w/api.php?" + q) or {}
    qd = data.get("query", {})
    norm = {n["from"]: n["to"] for n in qd.get("normalized", [])}
    redir = {r["from"]: r["to"] for r in qd.get("redirects", [])}
    exists = {p["title"] for p in qd.get("pages", []) if not p.get("missing")}
    out = {}
    for t in titles:
        c = norm.get(t, t)
        c = redir.get(c, c)
        out[t] = c if c in exists else None
    return out


def views(title):
    t = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{t}/daily/{START}/{END}"
    time.sleep(0.4)
    data = get_json(url)
    return sum(i["views"] for i in data["items"]) if data else None


if __name__ == "__main__":
    rows = []
    for niche, arts in NICHES.items():
        canon = resolve(arts)
        vs = {a: (views(canon[a]) if canon[a] else None) for a in arts}
        ok = [v for v in vs.values() if v]
        missing = [a for a, v in vs.items() if not v]
        med = statistics.median(ok) if ok else 0
        rows.append((niche, med, sum(ok), missing))
    rows.sort(key=lambda r: -r[1])
    for niche, med, tot, missing in rows:
        print(f"{niche:38s} median60d={int(med):>8,d} total={tot:>10,d} missing={missing}")
