#!/usr/bin/env python3
"""
Digitise INSAG-7 Fig. II-6 (p. 119, pdf page 129): the insertion depth in cm of
every RCPS rod at 01:22:30 on 26 April 1986.  The figure is a typeset plan of
the core: 23 rows of numbers joined by dot leaders.

The PDF's text layer is OCR-noisy, so the two halves of the digitisation come
from different places and are checked against each other:

  positions  measured from the page image (connected components of the digit
             glyphs; 600 dpi render), so no hand-placement is involved;
  values     read by eye from the same image, row by row, top to bottom
             (VALUES below).  Each row's count must equal the number of glyph
             groups found in that row, or the script stops.

Lattice.  Consecutive tokens in a row are one column step apart, and alternate
rows are offset by half a step: a 45-degree rotated square lattice.  With a
step of 2 cells (500 mm) along x and a row spacing of 2 cells, nearest rod
sites are 2*sqrt(2)*250 = 707 mm apart, which is [D] p. 12's "700 mm lattice
rotated 45 degrees".  So a site (h, r) -- h the half-step column, r the row --
is fuel-lattice cell (2h, 2r) up to a constant offset, with h + r even.

Result: 211 rods, which is INSAG-7's count for a second-stage RBMK-1000
(p. 43, p. 103).  The rotated lattice also has 12 empty sites inside the rod
field (wide dot runs in rows 4, 8, 12, 16, 20); they are recorded as EMPTY.
They are consistent with the 12 in-core flux-monitoring channels of [D] p. 12
("12 channels evenly spread in the central part of the core"), but the figure
does not say what they are.

The figure does NOT give rod types (RR / AZ / AR / USP).  See A6_CPS_PLAN.md.

    python tools/digitise_fig_II6.py      # writes sources/derived/insag7_fig_II6_012230.csv
"""
import csv
import glob
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = glob.glob(os.path.join(ROOT, "sources", "INSAG7_*.pdf"))[0]
OUT = os.path.join(ROOT, "sources", "derived", "insag7_fig_II6_012230.csv")
PAGE = 129

# Read by eye, top row first; one entry per rod, left to right.
VALUES = [
    [0, 0, 0, 0],
    [0, 0, 86, 0, 20, 0, 0],
    [0, 0, 240, 0, 0, 0, 0, 0],
    [0, 0, 0, 110, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 30, 0, 140, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 120, 0, 0, 0],
    [0, 70, 160, 0, 0, 160, 30, 0],
    [0, 0, 120, 0, 0, 100, 0, 30, 0, 20, 140, 0],
    [0, 0, 0, 0, 0, 20, 0, 80, 120, 0, 190],
    [0, 0, 0, 0, 20, 0, 0, 0, 140, 0, 0, 180],
    [0, 0, 140, 20, 0, 20, 140, 0, 0],
    [0, 0, 0, 0, 0, 0, 90, 0, 0, 0, 0, 0],
    [180, 0, 0, 0, 0, 20, 20, 0, 100, 170, 0],
    [20, 120, 0, 0, 20, 260, 0, 0, 40, 0, 20, 0],
    [0, 0, 160, 0, 0, 160, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 30, 0, 0],
    [0, 20, 0, 0, 0, 140, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 80, 0, 0],
    [0, 0, 0, 20, 0, 0, 0],
    [0, 0, 0, 0, 0, 30, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]


def glyph_rows():
    """[[x of the right edge of each number, left to right] per row], in page pixels at 600 dpi."""
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-f", str(PAGE), "-l", str(PAGE), "-r", "600", "-png",
                        PDF, os.path.join(d, "p")], check=True)
        im = Image.open(glob.glob(os.path.join(d, "p*.png"))[0]).convert("L")
    s = im.size[0] / 1408                       # figure box measured on a 1408-px-wide view
    x0, y0, x1, y1 = (int(v * s) for v in (290, 925, 1135, 1765))
    ink = np.array(im)[y0:y1, x0:x1] < 128
    lab, _ = nd.label(ink)
    digits = []
    for sl in nd.find_objects(lab):
        if sl[0].stop - sl[0].start > 35:       # digits are ~50 px tall; dots ~10
            digits.append(((sl[0].start + sl[0].stop) / 2, sl[1].start, sl[1].stop))
    digits.sort()
    rows = []
    for dg in digits:
        if rows and abs(dg[0] - rows[-1][-1][0]) < 30:
            rows[-1].append(dg)
        else:
            rows.append([dg])
    out = []
    for r in rows:
        r.sort(key=lambda dg: dg[1])
        toks = []                               # merge the digits of one number
        for dg in r:
            if toks and dg[1] - toks[-1][1] < 25:
                toks[-1][1] = dg[2]
            else:
                toks.append([dg[1], dg[2]])
        out.append([b for a, b in toks])        # numbers are set flush right
    return out


def digitise():
    rows = glyph_rows()
    assert len(rows) == len(VALUES) == 23, len(rows)
    xs = [x for r in rows for x in r]
    # column step: numbers sit on a regular grid; take the half-step from row 0's spacing
    step = np.median(np.diff(rows[4])) / 2      # row 4 is ten zeros: cleanest spacing
    xref = min(xs)
    sites = []
    for ir, (r, vals) in enumerate(zip(rows, VALUES)):
        assert len(r) == len(vals), f"row {ir}: {len(r)} numbers on the page, {len(vals)} read"
        for x, v in zip(r, vals):
            h = (x - xref) / step
            assert abs(h - round(h)) < 0.30, f"row {ir}: x {x:.0f} is off-lattice ({h:.2f})"
            sites.append((ir, int(round(h)), v))
    par = {(ir + h) % 2 for ir, h, _ in sites}
    assert len(par) == 1, "rows are not alternately offset"
    assert len(sites) == 211, len(sites)
    # empty sites: lattice points inside each row's span that carry no number
    empty = []
    for ir in range(23):
        hs = sorted(h for r, h, _ in sites if r == ir)
        for h in range(hs[0], hs[-1] + 1, 2):
            if h not in hs:
                empty.append((ir, h))
    return sites, empty


if __name__ == "__main__":
    sites, empty = digitise()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "h", "kind", "depth_cm"])
        for ir, h, v in sites:
            w.writerow([ir, h, "ROD", v])
        for ir, h in empty:
            w.writerow([ir, h, "EMPTY", ""])
    ins = [v for *_, v in sites if v > 0]
    print(f"{len(sites)} rods, {len(empty)} empty sites -> {os.path.relpath(OUT, ROOT)}")
    print(f"{len(ins)} rods inserted, sum {sum(ins)} cm, "
          f"= {sum(ins) / 700:.1f} fully-inserted-rod equivalents (7 m core, linear)")
