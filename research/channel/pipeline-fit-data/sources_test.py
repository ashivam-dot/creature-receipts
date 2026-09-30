"""Probe candidate open image APIs with niche queries; print counts, licenses, and sample URLs."""
import json, urllib.parse, urllib.request

UA = "NicheAudit/0.1 (https://github.com/ashivam; ashivam@example.com) python-urllib"


def get(url, params=None, headers=None):
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(full, headers={"User-Agent": UA, "Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return str(e)[:80], None


def show(name, status, n, samples):
    print(f"\n== {name}: HTTP {status}, total={n}")
    for s in samples[:3]:
        print("   ", s)


# iNaturalist: research-grade observations with CC0 / CC BY photos, no key
for taxon in ("Ambystoma mexicanum", "Architeuthis dux", "Odontodactylus scyllarus"):
    st, d = get("https://api.inaturalist.org/v1/observations", {"taxon_name": taxon, "photo_license": "cc0,cc-by",
                                                                "quality_grade": "research", "per_page": 5, "order_by": "votes"})
    if d:
        show(f"iNaturalist {taxon}", st, d["total_results"],
             [(o["photos"][0]["license_code"], o["photos"][0]["attribution"][:50], o["photos"][0]["url"].replace("square", "original"))
              for o in d["results"] if o.get("photos")])
    else:
        show(f"iNaturalist {taxon}", st, None, [])

# Europeana: public demo key, reusability=open (PD, CC0, CC BY, CC BY-SA)
for q in ("Tacoma Narrows bridge", "tulip mania", "Hindenburg Lakehurst"):
    st, d = get("https://api.europeana.eu/record/v2/search.json", {"wskey": "api2demo", "query": q, "reusability": "open",
                                                                    "media": "true", "qf": "TYPE:IMAGE", "rows": 5,
                                                                    "profile": "minimal"})
    if d:
        show(f"Europeana '{q}'", st, d.get("totalResults"),
             [((r.get("rights") or [""])[0], (r.get("title") or [""])[0][:50], (r.get("edmIsShownBy") or [""])[0][:90]) for r in d.get("items", [])])
    else:
        show(f"Europeana '{q}'", st, None, [])

# Cleveland Museum of Art: CC0 open access, no key
for q in ("trepanning", "tulip", "ship wreck"):
    st, d = get("https://openaccess-api.clevelandart.org/api/artworks/", {"q": q, "cc0": 1, "has_image": 1, "limit": 5})
    if d:
        show(f"Cleveland CC0 '{q}'", st, d["info"]["total"],
             [(r["share_license_status"], r["title"][:50], (r.get("images") or {}).get("web", {}).get("url")) for r in d["data"]])

# Smithsonian Open Access: CC0 filter, DEMO_KEY (api.data.gov free key recommended)
for q in ("Hindenburg", "Wright Flyer", "deep sea anglerfish"):
    st, d = get("https://api.si.edu/openaccess/api/v1.0/search",
                {"q": f'{q} AND online_media_type:"Images" AND media_usage:"CC0"', "rows": 5, "api_key": "DEMO_KEY"})
    if d:
        rows = d["response"]["rows"]

        def media(x):
            m = ((x["content"].get("descriptiveNonRepeating") or {}).get("online_media") or {}).get("media") or [{}]
            return m[0].get("content", "")[:90]
        show(f"Smithsonian CC0 '{q}'", st, d["response"]["rowCount"],
             [(x["content"]["descriptiveNonRepeating"].get("metadata_usage", {}).get("access"), x["title"][:50],
               x["content"]["descriptiveNonRepeating"].get("unit_code"), media(x)) for x in rows])
    else:
        show(f"Smithsonian '{q}'", st, None, [])

# Rijksmuseum new open search API (Linked Art), no key
st, d = get("https://data.rijksmuseum.nl/search/collection", {"title": "tulp"})
show("Rijksmuseum search title=tulp", st, (d or {}).get("partOf", {}).get("totalItems") if d else None,
     [i.get("id") for i in (d or {}).get("orderedItems", [])[:3]])

# Openverse, current pipeline source, for comparison
for q in ("axolotl", "Tacoma Narrows Bridge collapse"):
    st, d = get("https://api.openverse.org/v1/images/", {"q": q, "license": "cc0,pdm,by", "page_size": 20})
    if d:
        show(f"Openverse '{q}'", st, d["result_count"], [(r["license"], r["source"], r["title"][:40]) for r in d["results"]])

# Wikimedia Commons: a US-gov archive category sizes (shallow)
for cat in ("NOAA Photo Library", "Images from the USGS", "Images from the National Archives and Records Administration",
            "Images from the Library of Congress", "Photographs by the United States Navy", "Images from NIH"):
    st, d = get("https://commons.wikimedia.org/w/api.php", {"action": "query", "prop": "categoryinfo", "titles": "Category:" + cat, "format": "json"})
    info = next(iter(d["query"]["pages"].values())).get("categoryinfo") if d else None
    print(f"\n== Commons Category:{cat}: {info}")
