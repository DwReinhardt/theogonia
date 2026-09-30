"""Build the standalone HTML and the artifact fragment from data.json + template.html.

Precomputes: generation tier for every entity (longest-path over parent links, with
anchored and transformation-only entities placed relative to what they attach to),
children lists, and a 'notable' flag used when collective groups are collapsed.
"""
import json, collections, re, subprocess, sys

import os
os.makedirs("dist", exist_ok=True)
subprocess.run([sys.executable, "parse.py"], check=True)
data = json.load(open("data.json"))
E = {e["id"]: e for e in data}

children = collections.defaultdict(list)
for e in data:
    for p in e["parents"]:
        children[p].append(e["id"])

def descendant_depth(a, b):
    """Depth of b below a via parent links, or None."""
    seen, frontier, d = {a}, [a], 0
    while frontier and d < 40:
        d += 1
        nxt = []
        for n in frontier:
            for c in children[n]:
                if c == b: return d
                if c not in seen: seen.add(c); nxt.append(c)
        frontier = nxt
    return None

# constraint edges u -> v with weight w meaning gen[v] >= gen[u] + w
cons = []
for e in data:
    i = e["id"]
    for p in e["parents"]:
        cons.append((p, i, 1))
    for a in e.get("anchor", []):
        t = a["id"]
        dd = descendant_depth(i, t)
        if dd: cons.append((t, i, -dd))          # I'm an ancestor of my anchor: sit above it
        else: cons.append((t, i, 0))             # spouse / associate: same tier
    if not e["parents"] and not e.get("anchor"):
        for t in e.get("trans", []):
            cons.append((t["id"], i, 1))
# "grounded" entities trace back through parent links to a primordial; the rest hang off
# anchor-only roots (e.g. a bride whose father is named but has no recorded lineage).
grounded = {}
def is_grounded(i, stack=()):
    if i in grounded: return grounded[i]
    if i in stack: return False
    e = E[i]
    if e["type"] == "primordial": r = True
    elif e["parents"]: r = any(is_grounded(p, stack + (i,)) for p in e["parents"])
    elif e.get("trans") and not e.get("anchor"): r = any(is_grounded(t["id"], stack + (i,)) for t in e["trans"])
    else: r = False
    grounded[i] = r
    return r
for e in data: is_grounded(e["id"])
for e in data:
    ps = e["parents"]
    for a in ps:
        if not grounded[a]:
            for b in ps:
                if b != a and not descendant_depth(a, b): cons.append((b, a, 0))   # floating parent sits on partner tier
import functools
@functools.lru_cache(maxsize=None)
def longest(a, b):
    """Longest parent-link path length from a down to b (0 if a == b, -1 if unreachable)."""
    if a == b: return 0
    best = -1
    for c in children[a]:
        l = longest(c, b)
        if l >= 0: best = max(best, l + 1)
    return best
for e in data:
    for p in e["parents"]:
        if not grounded[p]: cons.append((e["id"], p, -longest(p, e["id"])))   # ungrounded parent sits just above its child
gen = {e["id"]: 0 for e in data}
for it in range(400):
    changed = False
    for u, v, w in cons:
        if gen[u] + w > gen[v]:
            gen[v] = gen[u] + w; changed = True
    if not changed: break
else:
    sys.exit("generation constraints did not converge")
# normalise so the minimum is 0
m = min(gen.values())
for k in gen: gen[k] -= m

trans_targets = collections.Counter(t["id"] for e in data for t in e.get("trans", []))
anchor_targets = collections.Counter(a["id"] for e in data for a in e.get("anchor", []))
for e in data:
    i = e["id"]
    e["gen"] = gen[i]
    e["kids"] = children[i]
    e["notable"] = bool(e.get("notable") or children[i] or e.get("myth") or e.get("riddles")
                        or e.get("trans") or trans_targets[i] or anchor_targets[i] or e.get("anchor"))
    if e["parents"]:
        e["origin_kind"] = "union" if len(e["parents"]) >= 2 else "single"
    elif e["type"] == "primordial":
        e["origin_kind"] = "primordial"
    elif e.get("trans"):
        e["origin_kind"] = "transform"
    else:
        e["origin_kind"] = "anchor"

print("max generation", max(gen.values()))
for probe in ["chaos", "zeus", "heracles", "achilles", "odysseus", "hecuba", "dymas", "oedipus", "aeneas"]:
    print(f"  {probe}: gen {gen[probe]}")

payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
vis = open("package/standalone/umd/vis-network.min.js", encoding="utf-8").read()
tpl = open("template.html", encoding="utf-8").read()
body = tpl.replace("/*__DATA__*/[]", payload).replace("/*__VIS__*/", vis)

# Artifact version: no doctype/html/head/body (the host wraps it)
open("dist/artifact.html", "w", encoding="utf-8").write(body)
# Standalone file: full document
m = re.match(r"(?s)\s*(<title>.*?</title>)(.*)", body)
full = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        + m.group(1) + "\n</head>\n<body>\n" + m.group(2) + "\n</body>\n</html>\n")
open("dist/greek_mythology_tree.html", "w", encoding="utf-8").write(full)
print("wrote dist/ (", len(full) // 1024, "KB )")

# ---------- mobile edition ----------
tplm = open("template_mobile.html", encoding="utf-8").read()
bodym = tplm.replace("/*__DATA__*/[]", payload)
open("dist/artifact_mobile.html", "w", encoding="utf-8").write(bodym)
mm = re.match(r"(?s)\s*(<title>.*?</title>)(.*)", bodym)
fullm = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
         "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
         "<meta name=\"theme-color\" content=\"#F8F8F4\" media=\"(prefers-color-scheme: light)\">\n"
         "<meta name=\"theme-color\" content=\"#151C28\" media=\"(prefers-color-scheme: dark)\">\n"
         "<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n"
         + mm.group(1) + "\n<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>\n</head>\n<body>\n"
         + mm.group(2) + "\n</body>\n</html>\n")
open("dist/greek_mythology_tree_mobile.html", "w", encoding="utf-8").write(fullm)
print("wrote mobile edition (", len(fullm) // 1024, "KB )")

# ---------- GitHub Pages site (installable web app) ----------
import hashlib, shutil, os
site = "site"
if os.path.isdir(site): shutil.rmtree(site)
os.makedirs(site + "/icons")
for f in os.listdir("site_assets"):
    shutil.copy("site_assets/" + f, site + "/icons/" + f)
ver = hashlib.sha1((fullm + full).encode()).hexdigest()[:10]
pwa_head = ('<link rel="manifest" href="manifest.webmanifest">\n'
            '<link rel="icon" type="image/png" href="icons/favicon.png">\n'
            '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n')
sw_reg = ('<script>if("serviceWorker" in navigator){addEventListener("load",()=>'
          'navigator.serviceWorker.register("sw.js").catch(()=>{}))}</script>\n')
idx = fullm.replace("<title>Greek Mythology Family Tree Mobile</title>",
                    "<title>Theogonia · Greek Mythology Family Tree</title>\n" + pwa_head).replace("</body>", sw_reg + "</body>")
open(site + "/index.html", "w", encoding="utf-8").write(idx)
desk = full.replace("</title>", "</title>\n" + '<link rel="icon" type="image/png" href="icons/favicon.png">\n').replace("</body>", sw_reg + "</body>")
open(site + "/desktop.html", "w", encoding="utf-8").write(desk)
manifest = {
  "name": "Theogonia: Greek Mythology Family Tree", "short_name": "Theogonia",
  "description": "Family tree of 1,208 figures of Greek mythology, with myths, riddles, sources and a quiz. Works offline.",
  "start_url": "./index.html", "scope": "./", "display": "standalone", "orientation": "portrait",
  "background_color": "#151C28", "theme_color": "#151C28",
  "icons": [
    {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
json.dump(manifest, open(site + "/manifest.webmanifest", "w"), indent=2)
sw = """// Theogonia service worker: keeps the app usable offline and picks up new versions.
const CACHE = "theogonia-%s";
const CORE = ["./", "index.html", "desktop.html", "manifest.webmanifest",
  "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "icons/apple-touch-icon.png", "icons/favicon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k.startsWith("theogonia-")).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    if (req.mode === "navigate") {   // pages: try the network first so updates arrive, fall back offline
      e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(k => k.put(req, c)); return r; })
        .catch(() => caches.match(req, {ignoreSearch: true}).then(r => r || caches.match("index.html"))));
    } else {
      e.respondWith(caches.match(req).then(r => r || fetch(req).then(n => { const c = n.clone(); caches.open(CACHE).then(k => k.put(req, c)); return n; })));
    }
  } else if (/fonts\\.(googleapis|gstatic)\\.com$/.test(url.hostname)) {   // fonts: serve cached, refresh in background
    e.respondWith(caches.open(CACHE + "-fonts").then(c => c.match(req).then(hit => {
      const net = fetch(req).then(r => { c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net; })));
  }
});
""" % ver
open(site + "/sw.js", "w").write(sw)
print("wrote site/ (version", ver, ")")
