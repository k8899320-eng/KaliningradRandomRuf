import json, math, re, time, urllib.parse, urllib.request
from collections import Counter
VER = 2
d = json.load(open("buildings.json"))
if d.get("v", 0) >= VER:
    print("доп. объекты уже есть"); raise SystemExit(0)
AREAS = {
    "Калининград":  "54.640,20.340,54.790,20.640",
    "Светлогорск":  "54.920,20.110,54.960,20.200",
    "Зеленоградск": "54.940,20.430,54.980,20.520",
    "Советск":      "55.050,21.820,55.110,21.940",
    "Балтийск":     "54.620,19.860,54.675,19.950",
}
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
           "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
def ask(q):
    for rnd in range(5):
        for url in MIRRORS:
            try:
                req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "roof-randomizer-kaliningrad"})
                with urllib.request.urlopen(req, timeout=150) as r: return json.load(r)["elements"]
            except Exception as e: print("FAIL", url, e)
        time.sleep(20)
    raise SystemExit("Overpass не ответил")
EXCL = re.compile(r"ги(а|га)нт|giant", re.I)
MALLNAME = r"(ТЦ|ТРЦ|ТРК|ТК |[Тт]оргов|[Mm]all|[Пп]лаза|[Пп]ассаж)"
have = {b["id"] for b in d["buildings"]}
def lv_of(t):
    try: return int(str(t.get("building:levels", "")).split(".")[0])
    except ValueError: pass
    try:
        h = float(re.sub(r"[^0-9.]", "", t.get("height", "")) or 0)
        return max(1, round(h / 3.2)) if h else 0
    except ValueError: return 0
out = []
for city, bb in AREAS.items():
    res = "" if city == "Калининград" else (
        f'way["building"]["building:levels"~"^([5-9]|[1-9][0-9])$"]["addr:housenumber"]({bb});'
        f'relation["building"]["building:levels"~"^([5-9]|[1-9][0-9])$"]["addr:housenumber"]({bb});')
    q = ("[out:json][timeout:120];("
         f'nwr["shop"="mall"]({bb});'
         f'way["building"~"^(retail|commercial)$"]["name"~"{MALLNAME}"]({bb});'
         f'nwr["tourism"="hotel"]({bb});'
         f'nwr["man_made"~"^(water_tower|lighthouse)$"]({bb});'
         f'nwr["man_made"="tower"]["tower:type"~"observation|defensive|watchtower|clock"]({bb});'
         f'way["building"="tower"]({bb});'
         f'nwr["historic"="tower"]({bb});' + res + ");out center tags;")
    els = ask(q); print(city, "объектов:", len(els))
    for e in els:
        t = e.get("tags", {}); c = e.get("center") or ({"lat": e["lat"], "lon": e["lon"]} if "lat" in e else None)
        if not c: continue
        iid = f'{e["type"]}/{e["id"]}'
        if iid in have: continue
        name = t.get("name") or t.get("building:name") or ""
        if EXCL.search(name) or EXCL.search(t.get("brand", "")): continue
        if t.get("building") in ("church", "chapel", "cathedral") or t.get("amenity") == "place_of_worship": continue
        if t.get("tourism") == "hotel": cat = "hotel"
        elif t.get("shop") == "mall" or t.get("building") in ("retail", "commercial"): cat = "mall"
        elif t.get("man_made") or t.get("building") == "tower" or t.get("historic") == "tower": cat = "tower"
        else: cat = "res"
        if cat == "res" and t.get("building") not in ("apartments", "residential", "yes", "dormitory"): continue
        street = t.get("addr:street") or t.get("addr:place") or ""
        if cat == "tower" and not name: name = {"water_tower": "Водонапорная башня", "lighthouse": "Маяк"}.get(t.get("man_made"), "Башня")
        if cat != "res" and not name: continue
        out.append({"id": iid, "lv": lv_of(t), "street": street, "num": t.get("addr:housenumber", ""),
            "name": name, "type": t.get("building", ""), "cat": cat, "city": city,
            "lat": round(c["lat"], 6), "lon": round(c["lon"], 6),
            "year": t.get("building:start_date") or t.get("start_date") or "", "h": t.get("height", "")})
        have.add(iid)
    time.sleep(5)
def near(a, b): return math.hypot((a["lat"]-b["lat"])*111000, (a["lon"]-b["lon"])*64000) < 80
uniq = []
for x in sorted(out, key=lambda x: (x["id"].startswith("node"), -x["lv"])):
    if any(y["cat"] == x["cat"] and near(x, y) and ((x["name"] and x["name"].lower() == y["name"].lower()) or (x["street"] and x["street"] == y["street"] and x["num"] == y["num"])) for y in uniq): continue
    uniq.append(x)
for b in d["buildings"]: b.setdefault("cat", "res"); b.setdefault("city", "Калининград")
for x in uniq:
    if x["city"] != "Калининград": x["d"] = ""
d["buildings"] += uniq; d["v"] = VER
print("добавлено:", len(uniq)); print(Counter((x["city"], x["cat"]) for x in uniq))
json.dump(d, open("buildings.json", "w"), ensure_ascii=False, separators=(",", ":"))
