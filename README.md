# Theogonia: a Greek Mythology Family Tree

An interactive family tree of **1,208 figures of Greek mythology**: primordials, Titans, Olympians, nymphs, monsters, giants, and the royal houses of Argos, Thebes, Troy, Athens, Crete, Sparta, Arcadia and more.

Every figure is traced back to where it came from: two parents, one parent (sea foam, blood, a head-birth), a transformation or curse, or, where the ancient sources name no parents, a link to a spouse or relative. Each entry has a short description, and many have a myth, a riddle, variant parentages from other sources, and citations to the ancient texts (Hesiod, Homer, Apollodorus, Ovid, Pausanias and others).

**Live app:** https://dwreinhardt.github.io/theogonia/ (phone) · https://dwreinhardt.github.io/theogonia/desktop.html (desktop)

## Two versions

| File | Best for | What it does |
|---|---|---|
| `index.html` | Phones | One figure at a time with a pocket family tree, ancestry, descendants, "connect two figures", browse, quiz and sources. Installable and works offline. |
| `desktop.html` | Computers | The whole tree as a zoomable chart by generation, with filters, lineage highlighting, path finding, a sortable table, a citation index and a quiz. |

Both files are self-contained and also work when opened directly from disk.

## Install it on an Android phone

1. Open the site address (see "Publishing" below) in **Chrome** on the phone.
2. Tap the **⋮** menu, then **Install app** (or **Add to Home screen**).
3. It gets its own icon, opens full-screen and keeps working without internet.

Updates published to this repository reach installed copies the next time they're opened online.

## Publishing with GitHub Pages

1. In this repository go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to *Deploy from a branch*, choose branch **main** and folder **/ (root)**, and save.
3. After a minute the app is live at https://dwreinhardt.github.io/theogonia/.

## Legend

- **Solid line:** two recorded parents
- **Amber dotted line:** one recorded parent
- **Red dashed line:** transformed, cursed or created by
- **Grey dashed line:** no recorded parents; linked to a spouse, owner or relative
- **Purple dashed line:** variant parentage from another source (optional)
- **♂ / ♀ / ⚥:** male, female, or both / neither / changed sex / mixed group. Fathers are drawn left of mothers.
- **Colours:** Primordial Void, Olympus & the Heavens, Underworld, Oceans & Rivers, Mortal Earth & Kingdoms, Crete & Troy

"Gen" counts generations down from Chaos along the longest recorded line, so mortal heroes sit many generations below the gods who fathered them.

## Editing the data

Everything is generated from the plain-text files in `source/data/`. The format is documented at the top of `source/parse.py`. A typical entry:

```
medusa | Medusa | Medusa | = | The mortal Gorgon, beheaded by Perseus.
  t: athena | Ovid, Metamorphoses 4.790–803: transformed from a beautiful maiden
  m: In Hesiod, Medusa was always a Gorgon...
  r: A goddess turned my hair to serpents... ;; Medusa
```

To rebuild after editing (requires Python 3 and Node's `npm`):

```
cd source
npm pack vis-network@9.1.9 && tar xzf vis-network-9.1.9.tgz
python3 build.py
```

`build.py` validates the data first: it fails if any figure has no origin link, no citation, an unknown reference, or a family loop. It then writes the finished site to `source/site/`; copy those files to the repository root to publish.

## Notes

- Citations point to the work and, where possible, the book or line numbers. They were compiled without checking each passage against the texts, so verify any you plan to quote formally.
- Ancient genealogies contradict each other. The chart shows the most common version and keeps the others as variant parentages with their sources.
- The desktop chart uses [vis-network](https://github.com/visjs/vis-network) (Apache-2.0 / MIT), bundled inside `desktop.html`. Fonts load from Google Fonts when online; the app falls back to system fonts offline.
