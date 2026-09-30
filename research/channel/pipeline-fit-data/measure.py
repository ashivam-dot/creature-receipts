"""Measure Commons picture depth and Wikipedia depth for candidate niche topics."""
import json, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "NicheAudit/0.1 (https://github.com/ashivam; ashivam@example.com) python-urllib"
OK = re.compile(r"^(public domain|pd\b|pd-|cc0|cc by \d(\.\d)?( [a-z]{2})?$|cc-by-\d(\.\d)?(-[a-z]{2})?$)", re.I)

NICHES = {
    "Deep ocean / sea creatures": ["Giant squid", "Challenger Deep", "Anglerfish"],
    "Engineering disasters": ["Tacoma Narrows Bridge (1940)", "Hyatt Regency walkway collapse", "St. Francis Dam"],
    "Aviation mysteries / incidents": ["Flight 19", "Hindenburg disaster", "Northwest Orient Airlines Flight 305"],
    "Bizarre medical history": ["Trepanning", "Radium Girls", "Phineas Gage"],
    "Frauds / scams / heists": ["Victor Lustig", "Isabella Stewart Gardner Museum theft", "Great Train Robbery (1963)"],
    "Money / economic oddities": ["Tulip mania", "Rai stones", "Hyperinflation in the Weimar Republic"],
    "Extreme animals / biology": ["Tardigrade", "Axolotl", "Mantis shrimp"],
    "Geography / border oddities": ["Baarle-Hertog", "Bir Tawil", "Northwest Angle"],
    "Cold War / military secrets": ["Project Azorian", "Duga radar", "1961 Goldsboro B-52 crash"],
    "Archaeology / ancient mysteries": ["Antikythera mechanism", "Terracotta Army", "Göbekli Tepe"],
    "Natural disasters / extreme weather": ["1900 Galveston hurricane", "1980 eruption of Mount St. Helens", "Dust Bowl"],
    "Accidental inventions / discoveries": ["Mauveine", "Microwave oven", "Post-it Note"],
}


def get(url, params):
    full = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 * (attempt + 1))
            err = e
    raise err


def wiki(title):
    q = get("https://en.wikipedia.org/w/api.php", {"action": "query", "format": "json", "titles": title, "redirects": 1,
                                                     "prop": "info|pageprops|pageimages", "ppprop": "wikibase_item",
                                                     "pilicense": "free", "piprop": "name"})
    page = next(iter(q["query"]["pages"].values()))
    if "missing" in page:
        return None
    wt = get("https://en.wikipedia.org/w/api.php", {"action": "parse", "format": "json", "page": page["title"],
                                                      "prop": "wikitext|images", "formatversion": 2})["parse"]
    text = wt["wikitext"]
    refs = len(re.findall(r"<ref[\s>]", text, re.I))
    words = len(re.sub(r"\{\{[^{}]*\}\}|<ref[^>]*/>|<ref.*?</ref>", " ", text, flags=re.S).split())
    try:
        end = time.strftime("%Y%m%d", time.gmtime(time.time() - 86400))
        start = time.strftime("%Y%m%d", time.gmtime(time.time() - 86400 * 91))
        t = urllib.parse.quote(page["title"].replace(" ", "_"), safe="")
        pv = get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{t}/daily/{start}/{end}", {})
        views = sum(i["views"] for i in pv["items"]) // 90
    except Exception:
        views = None
    return {"title": page["title"], "bytes": page.get("length"), "refs": refs, "words_approx": words,
            "qid": page.get("pageprops", {}).get("wikibase_item"), "article_images": len(wt.get("images", [])),
            "daily_views": views}


def commons_cat(qid):
    if not qid:
        return None
    e = get("https://www.wikidata.org/w/api.php", {"action": "wbgetentities", "format": "json", "ids": qid, "props": "claims"})
    claims = e["entities"][qid].get("claims", {})
    p373 = claims.get("P373")
    if p373:
        return p373[0]["mainsnak"]["datavalue"]["value"]
    return None


def files_in(cat, depth=1, cap=600):
    files, cats, seen = [], [cat], set()
    for level in range(depth + 1):
        nxt = []
        for c in cats:
            if c in seen or len(files) >= cap:
                continue
            seen.add(c)
            cont = {}
            while len(files) < cap:
                r = get("https://commons.wikimedia.org/w/api.php", {"action": "query", "format": "json", "list": "categorymembers",
                                                                     "cmtitle": "Category:" + c, "cmtype": "file|subcat",
                                                                     "cmlimit": 500, **cont})
                for m in r["query"]["categorymembers"]:
                    if m["ns"] == 6:
                        files.append(m["title"])
                    elif m["ns"] == 14:
                        nxt.append(m["title"].removeprefix("Category:"))
                if "continue" not in r:
                    break
                cont = r["continue"]
        cats = nxt[:40]
    return list(dict.fromkeys(files))[:cap], len(seen)


def license_scan(titles):
    usable = full = pd_us = bysa = 0
    for i in range(0, len(titles), 20):
        batch = titles[i:i + 20]
        r = get("https://commons.wikimedia.org/w/api.php", {"action": "query", "format": "json", "titles": "|".join(batch),
                                                             "prop": "imageinfo", "iiprop": "size|mime|extmetadata",
                                                             "iiextmetadatafilter": "LicenseShortName|Categories"})
        for p in r.get("query", {}).get("pages", {}).values():
            info = (p.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            lic = (meta.get("LicenseShortName") or {}).get("value", "")
            cats = (meta.get("Categories") or {}).get("value", "")
            if info.get("mime") not in ("image/jpeg", "image/png", "image/tiff", "image/webp"):
                continue
            w, h = info.get("width", 0), info.get("height", 0)
            if max(w, h) >= 600 and re.match(r"(cc by-sa|cc-by-sa)", lic.strip(), re.I):
                bysa += 1
            if max(w, h) < 600 or min(w, h) < 300 or not OK.match(lic.strip()):
                continue
            usable += 1
            if max(w, h) >= 1200:
                full += 1
            if re.search(r"PD[ -]US(Gov|[ -]government)|PD US|United States government|NOAA|USGS|NARA|US Navy|USAF|Library of Congress", cats, re.I):
                pd_us += 1
    return usable, full, pd_us, bysa


def depicts(qid):
    if not qid:
        return 0
    r = get("https://commons.wikimedia.org/w/api.php", {"action": "query", "format": "json", "list": "search",
                                                         "srsearch": f"haswbstatement:P180={qid} filetype:bitmap", "srnamespace": 6,
                                                         "srlimit": 1, "srinfo": "totalhits"})
    return r["query"]["searchinfo"]["totalhits"]


def measure(niche, topic):
    w = wiki(topic)
    if not w:
        return {"niche": niche, "topic": topic, "missing": True}
    cat = commons_cat(w["qid"])
    files, ncats = files_in(cat) if cat else ([], 0)
    direct = files_in(cat, depth=0)[0] if cat else []
    usable, full, pd_us, bysa = license_scan(files) if files else (0, 0, 0, 0)
    return {"niche": niche, "topic": topic, **w, "category": cat, "cat_files_direct": len(direct),
            "cat_files_depth1": len(files), "subcats_scanned": ncats, "usable": usable, "usable_1200": full,
            "us_gov_pd": pd_us, "bysa_excluded": bysa, "depicts_hits": depicts(w["qid"])}


EXTRA = {
    "Cold War / military secrets": ["Duga radar", "Operation Ivy Bells", "Castle Bravo"],
    "Frauds / scams / heists": ["Charles Ponzi", "Piltdown Man", "Cardiff Giant"],
    "Aviation mysteries / incidents": ["Amelia Earhart", "Lady Be Good (aircraft)", "1945 Empire State Building B-25 crash"],
    "Deep ocean / sea creatures": ["Trieste (bathyscaphe)", "Hydrothermal vent", "Coelacanth"],
    "Engineering disasters": ["Boston molasses disaster", "Quebec Bridge", "Johnstown Flood"],
    "Geography / border oddities": ["Point Roberts, Washington", "Kaliningrad Oblast", "Four Corners Monument"],
}
if len(sys.argv) > 2:
    NICHES = EXTRA

if __name__ == "__main__":
    jobs = [(n, t) for n, ts in NICHES.items() for t in ts]
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(lambda a: _safe(*a), jobs)) if False else None
    out = []
    with ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(measure, n, t) for n, t in jobs]
        for (n, t), f in zip(jobs, futs):
            try:
                out.append(f.result())
            except Exception as e:
                out.append({"niche": n, "topic": t, "error": str(e)})
            print(json.dumps(out[-1]), flush=True)
    with open(sys.argv[1], "w") as fh:
        json.dump(out, fh, indent=1)
