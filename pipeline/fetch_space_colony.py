"""Download NASA Ames 1970s space colony / planetary paintings (Rick Guidice,
Don Davis) from images.nasa.gov as LoRA training candidates.

Usage:
    python pipeline/fetch_space_colony.py

Writes data/space_colony/raw/<nasa_id>.<ext> (original resolution) and
data/space_colony/raw/metadata.json. All NASA imagery is public domain.
"""

import json
import os
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "space_colony", "raw")
API = "https://images-api.nasa.gov"

QUERIES = ["space colony", "space colonization", "space settlement",
           "bernal sphere", "torus", "Rick Guidice", "Don Davis"]
# Text overlays, someone else's copyright, or not a painting.
SKIP = {"ARC-1976-AC76-1713", "ARC-1977-AC77-0359"}


def get(url):
    with urllib.request.urlopen(url, timeout=120) as resp:
        return json.load(resp)


def is_painting(meta):
    text = f"{meta.get('title', '')} {meta.get('description', '')}".lower()
    year = meta.get("date_created", "")[:4]
    return ("1974" <= year <= "1978"
            and ("guidice" in text or "guidace" in text or "don davis" in text
                 or ("colon" in text and ("art" in text or "artist" in text))))


found = {}
for query in QUERIES:
    params = urllib.parse.urlencode({"q": query, "media_type": "image",
                                     "center": "ARC", "page_size": 100})
    for item in get(f"{API}/search?{params}")["collection"]["items"]:
        meta = item["data"][0]
        if meta["nasa_id"] not in SKIP and is_painting(meta):
            found[meta["nasa_id"]] = meta

os.makedirs(OUT, exist_ok=True)
for nasa_id, meta in sorted(found.items()):
    assets = [a["href"] for a in get(f"{API}/asset/{urllib.parse.quote(nasa_id)}")["collection"]["items"]]
    orig = next((h for h in assets if "~orig." in h), assets[0])
    ext = orig.rsplit(".", 1)[-1].lower()
    path = os.path.join(OUT, f"{nasa_id}.{ext}")
    if not os.path.exists(path):
        urllib.request.urlretrieve(orig.replace("http://", "https://"), path)
    meta["file"] = os.path.basename(path)
    print(nasa_id, "|", (meta.get("description") or meta["title"])[:90].replace("\n", " "))

with open(os.path.join(OUT, "metadata.json"), "w") as f:
    json.dump(found, f, indent=1)
print(len(found), "paintings in", os.path.relpath(OUT, ROOT))
