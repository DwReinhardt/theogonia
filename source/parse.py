"""Parse the mythology DSL files in data/ into data.json and validate integrity.

DSL
---
Directives (apply to following entities until changed; "-" clears):
  @type <type>   @region <region>   @house <house>   @grp <group-id>
  @src <default citation>
Entity line:
  id | Name | Roman | parents | description
    parents: "a+b", "a", "-" (primordial / none), "=" (same as the current @grp collective)
Detail lines (indented, "key: value"):
  m: myth summary            r: riddle clue ;; answer (answer defaults to Name)
  a: p1+p2 | source          alternate parentage (repeatable)
  t: id | note               transformed / cursed / reshaped by (repeatable)
  x: id | note               anchor link when parentage is unrecorded (spouse, owner, slayer)
  o: origin note             e.g. "born from the sea foam"
  s: source (replaces default)   S: source (added to default)
  w: Wikipedia title         T/R/H: override type/region/house    n: 1 = always show group member
"""
import json, re, sys, glob, collections

TYPES = {"primordial", "titan", "olympian", "deity", "spirit", "nymph", "monster",
         "giant", "creature", "demigod", "mortal"}
REGIONS = {"void", "olympus", "under", "sea", "earth", "cretetroy"}

def parse(files):
    ents, order = {}, []
    errors = []
    for fn in files:
        st = {"type": None, "region": None, "house": None, "grp": None, "src": None}
        cur = None
        for ln, raw in enumerate(open(fn, encoding="utf-8"), 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            where = f"{fn.split('/')[-1]}:{ln}"
            if line.startswith("@"):
                k, _, v = line[1:].partition(" ")
                v = v.strip()
                st[k] = None if v in ("-", "") else v
                if k not in st:
                    errors.append(f"{where} unknown directive {k}")
                continue
            if line[0] in " \t":
                if cur is None:
                    errors.append(f"{where} detail with no entity"); continue
                k, _, v = line.strip().partition(":")
                v = v.strip(); k = k.strip()
                if k == "m": cur["myth"] = (cur.get("myth", "") + " " + v).strip()
                elif k == "r":
                    q, _, a = v.partition(";;")
                    cur.setdefault("riddles", []).append({"q": q.strip(), "a": a.strip() or cur["name"]})
                elif k == "a":
                    p, _, s = v.partition("|")
                    cur.setdefault("alt", []).append({"parents": [x.strip() for x in p.split("+") if x.strip()], "src": s.strip()})
                elif k in ("t", "x"):
                    i, _, note = v.partition("|")
                    cur.setdefault("trans" if k == "t" else "anchor", []).append({"id": i.strip(), "note": note.strip()})
                elif k == "o": cur["origin"] = v
                elif k == "s": cur["src"] = v
                elif k == "S": cur["src"] = (cur.get("src") + "; " if cur.get("src") else "") + v
                elif k == "w": cur["wiki"] = v
                elif k == "T": cur["type"] = v
                elif k == "R": cur["region"] = v
                elif k == "H": cur["house"] = v
                elif k == "n": cur["notable"] = True
                else: errors.append(f"{where} unknown key {k}")
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 5:
                errors.append(f"{where} expected 5 fields, got {len(parts)}: {line[:60]}"); cur = None; continue
            i, name, roman, par, desc = parts
            if i in ents:
                errors.append(f"{where} duplicate id {i}")
            e = {"id": i, "name": name, "desc": desc, "type": st["type"], "region": st["region"],
                 "where": where}
            if roman: e["roman"] = roman
            if st["house"]: e["house"] = st["house"]
            if st["src"]: e["src"] = st["src"]
            if st["grp"] and i != st["grp"]:
                e["grp"] = st["grp"]
            if par == "=":
                e["parents"] = "="
            elif par == "-":
                e["parents"] = []
            else:
                e["parents"] = [p.strip() for p in par.split("+") if p.strip()]
            ents[i] = e; order.append(i); cur = e
    # resolve group "=" parents
    for i in order:
        e = ents[i]
        if e["parents"] == "=":
            g = ents.get(e.get("grp"))
            if not g:
                errors.append(f"{e['where']} '=' parents but no group"); e["parents"] = []
            else:
                e["parents"] = list(g["parents"])
                if "src" not in e and g.get("src"): e["src"] = g["src"]
    return ents, order, errors

def validate(ents, order):
    errors, warns = [], []
    for i in order:
        e = ents[i]
        if e["type"] not in TYPES: errors.append(f"{e['where']} {i}: bad type {e['type']}")
        if e["region"] not in REGIONS: errors.append(f"{e['where']} {i}: bad region {e['region']}")
        for a in e.get("alt", []):
            known = [p for p in a["parents"] if p in ents]
            unk = [p for p in a["parents"] if p not in ents]
            if unk:
                warns.append(f"{i}: alt parent(s) shown as text only: {unk}")
                a["names"] = [u.replace("_", " ").title() for u in unk]
            a["parents"] = known
        refs = list(e["parents"]) + \
               [t["id"] for t in e.get("trans", [])] + [t["id"] for t in e.get("anchor", [])]
        if e.get("grp"): refs.append(e["grp"])
        for r in refs:
            if r not in ents: errors.append(f"{e['where']} {i}: unknown ref '{r}'")
        if i in e["parents"]: errors.append(f"{i}: self-parent")
        if not e.get("src"): errors.append(f"{e['where']} {i}: no citation")
        mapped = e["parents"] or e.get("trans") or e.get("anchor") or e["type"] == "primordial"
        if not mapped: errors.append(f"{e['where']} {i}: UNMAPPED (no parents, transformer, or anchor)")
    # cycle check on primary parent graph
    state = {}
    def visit(n, stack):
        if state.get(n) == 1: errors.append("cycle: " + " -> ".join(stack + [n])); return
        if state.get(n) == 2: return
        state[n] = 1
        for p in ents[n]["parents"]:
            if p in ents: visit(p, stack + [n])
        state[n] = 2
    for i in order: visit(i, [])
    return errors, warns

if __name__ == "__main__":
    files = sorted(glob.glob("data/*.txt"))
    ents, order, errs = parse(files)
    # sex of each entity (data/sex.tsv), and father-left ordering of parents
    sx = {}
    for ln in open("data/sex.tsv", encoding="utf-8"):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            k, v = ln.split(); sx[k] = v
    rank = {"m": 0, "x": 1, "f": 2}
    for i in order:
        e = ents[i]
        if i not in sx: errs.append(f"{i}: no sex recorded in data/sex.tsv")
        elif sx[i] not in rank: errs.append(f"{i}: bad sex '{sx[i]}'")
        e["sex"] = sx.get(i, "x")
    for i in order:
        e = ents[i]
        key = lambda p: rank.get(sx.get(p, "x"), 1)
        if isinstance(e["parents"], list): e["parents"].sort(key=key)
        for a in e.get("alt", []): a["parents"].sort(key=key)
    for k in sx:
        if k not in ents: errs.append(f"sex.tsv: unknown id {k}")
    verrs, warns = validate(ents, order)
    errs += verrs
    for e in errs: print("ERROR", e)
    for w in warns: print("WARN", w)
    c = collections.Counter(ents[i]["type"] for i in order)
    r = collections.Counter(ents[i]["region"] for i in order)
    print(len(order), "entities |", dict(c), "|", dict(r))
    for e in ents.values(): e.pop("where", None)
    json.dump([ents[i] for i in order], open("data.json", "w"), ensure_ascii=False, separators=(",", ":"))
    sys.exit(1 if errs else 0)
