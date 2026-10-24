#!/usr/bin/env python3
"""
Digitise INSAG-7 Fig. II-7 (p. 120, pdf page 130): "radial distribution of the initial neutron
field in the core" -- a contour plan, Ref. [28]'s reconstruction for 01:22:30 (INSAG-7 p. 119).

What is read from the figure:
  * contour lines every 10 (labels every 20: 20 ... 160).  Counting the lines from the outline in
    to the innermost loop (labelled 160) gives 15-17 along every direction, which an interval of
    20 (8 lines) cannot give.
  * the levels are % of the core mean: with the interval 10, the digitised field averages 104 over
    the 1661 fuel channels.
Method (no hand placement):
  * 400 dpi render, threshold 140; the outside of the outline is the background component of the
    lines dilated by 3 px (the outline has gaps);
  * registration: the outline's extent away from its four bulges, x 60-1200 px, y 75-1200 px,
    onto the fuel lattice's ix, iy 6-53 (cell edges 5.5-53.5): 23.6 px per 25 cm cell, centre
    (630, 637) px = (ix, iy) (29.5, 29.5).  ORIENTATION ASSUMED: as printed, Fig. II-6's (the same
    reconstruction, the same section; the model's lattice is registered to Fig. II-6 exactly:
    ix to the right, iy up the page);
  * at each fuel cell: the number k of line crossings from the cell to the outside, median over
    72 rays (a ray over the hill crosses a closed contour twice and one through a label gap misses
    a line; the median sits between); value = 10 (k - 1) + 5, the midpoint of the band, k = 1
    being between the outline and the 10 line.
Precision: one band (10 %) and about one cell.

    python tools/digitise_fig_II7.py <fuel cells file: "ix iy" per line>
        -> sources/derived/insag7_fig_II7_lattice.csv
"""
import glob, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = glob.glob(os.path.join(ROOT, "sources", "INSAG7_*.pdf"))[0]
OUT = os.path.join(ROOT, "sources", "derived", "insag7_fig_II7_lattice.csv")
PAGE = 130
CROP = (640 + 35, 1740 + 30, 640 + 1330, 1740 + 1315)     # inside the figure frame, 400 dpi
PX, XC, YC = 23.6, 630.0, 637.0


def render():
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-f", str(PAGE), "-l", str(PAGE), "-r", "400", "-png", PDF,
                        os.path.join(td, "p")], check=True)
        f = glob.glob(os.path.join(td, "p*.png"))[0]
        return np.array(Image.open(f).convert("L").crop(CROP))


def main(cellfile):
    a = render()
    dark = a < 140
    h, w = dark.shape
    lab, _ = nd.label(~nd.binary_dilation(dark, iterations=3))
    ins = lab != lab[0, 0]

    def count(px, py, th):
        dx, dy = np.cos(th), np.sin(th)
        runs, prev, gap, t = 0, False, 99, 0.0
        while True:
            x, y = int(round(px + dx * t)), int(round(py + dy * t))
            if x < 0 or y < 0 or x >= w or y >= h:
                return runs
            d = dark[y, x]
            if d and not prev and gap >= 3:
                runs += 1
            gap = 0 if d else gap + 1
            prev = d
            t += 0.5

    rows = []
    for line in open(cellfile):
        ix, iy = map(int, line.split())
        x0, y0 = int(round(XC + (ix - 29.5) * PX)), int(round(YC - (iy - 29.5) * PX))
        if dark[y0, x0]:                       # on a line or label: the nearest white pixel
            cand = [(abs(dx) + abs(dy), x0 + dx, y0 + dy) for dx in range(-15, 16) for dy in range(-15, 16)
                    if not dark[y0 + dy, x0 + dx]]
            _, x0, y0 = min(cand)
        if not ins[y0, x0]:
            rows.append((ix, iy, 0, float("nan")))
            continue
        k = float(np.median([count(x0, y0, th) for th in np.linspace(0, 2 * np.pi, 72, endpoint=False)]))
        rows.append((ix, iy, k, 10.0 * (k - 1) + 5.0))
    with open(OUT, "w") as f:
        f.write("# INSAG-7 Fig. II-7 on the model's fuel lattice (tools/digitise_fig_II7.py); value = % of the core mean, band midpoint\n")
        f.write("ix,iy,k,value\n")
        for r in rows:
            f.write("%d,%d,%g,%g\n" % r)
    v = np.array([r[3] for r in rows if r[2] > 0])
    print(f"{len(rows)} cells, {len(v)} inside the outline; mean {v.mean():.1f}, max {v.max():.0f} -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
