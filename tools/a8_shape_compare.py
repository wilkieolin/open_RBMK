#!/usr/bin/env python3
"""Axial power shapes from an A8 transient against INSAG-7 Fig. II-9.

Reads the POWER-BUND blocks a deck generated with U4_KINSHAPE prints (one
per requested time, each preceded by an 'A8SHAPE istep T t' echo), and the
digitised figure (sources/derived/insag7_fig_II9_axial.csv), and reports,
for every printed shape, its RMS against each measured curve -- so a shape
is compared with the time it was printed at AND with its neighbours.
Optionally draws the overlay.

    a8_shape_compare.py <result> [overlay.png]
"""
import csv
import os
import re
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a8_axial import shape, NB, PITCH                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def measured():
    rows = [r for r in csv.reader(
        l for l in open(os.path.join(ROOT, "sources/derived/insag7_fig_II9_axial.csv"))
        if not l.startswith("#"))][1:]
    out = {}
    for t in "0467":
        p = sorted((float(r[2]), float(r[3])) for r in rows if r[0] == t)
        out[int(t)] = np.array(p)
    return out


def main():
    res = sys.argv[1]
    txt = open(res, "rb").read().decode("latin1")
    times = [float(m.group(2)) for m in
             re.finditer(r"(?m)^>\|A8SHAPE\s+(\d+)\s+T\s+(\S+)", txt)]
    if not times:
        sys.exit(f"{res}: no A8SHAPE echoes -- generate with U4_KINSHAPE")
    Db = 700.0 - (np.arange(NB) + 0.5) * PITCH
    o = np.argsort(Db)
    meas = measured()
    shapes = []
    print("  model t, s   peak (value, D cm)    upper/lower   RMS vs  0 s     4 s     6 s     7 s")
    for i, t in enumerate(times):
        sh = np.array(shape(res, i)[0])
        shapes.append((t, sh))
        f = PchipInterpolator(Db[o], sh[o])
        rms = []
        for tm in (0, 4, 6, 7):
            D, y = meas[tm][:, 0], meas[tm][:, 1]
            m = (D >= Db.min()) & (D <= Db.max())
            rms.append(np.sqrt(np.mean((f(D[m]) - y[m]) ** 2)))
        k = int(np.argmax(sh))
        print(f"  {t:9.3f}     {sh[k]:.2f} at D {Db[k]:3.0f}        "
              f"{max(sh[NB // 2:]) / max(sh[:NB // 2]):6.2f}       "
              + "  ".join(f"{r:6.3f}" for r in rms))
    if len(sys.argv) > 2:
        from PIL import Image, ImageDraw
        W, H, L, R, T, B = 1200, 760, 90, 30, 60, 90
        im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
        X = lambda D: L + (W - L - R) * D / 800; Y = lambda v: H - B - (H - T - B) * v / 3.0
        for D in range(0, 801, 100):
            d.line([X(D), T, X(D), H - B], fill=(225, 225, 225)); d.text((X(D) - 12, H - B + 8), str(D), fill="black")
        for k in range(7):
            d.line([L, Y(k / 2), W - R, Y(k / 2)], fill=(225, 225, 225)); d.text((L - 30, Y(k / 2) - 6), f"{k / 2:.1f}", fill="black")
        d.rectangle([L, T, W - R, H - B], outline="black")
        d.text((L + 300, H - 40), "distance below core top, cm (core bottom at 700)", fill="black")
        d.text((L, 15), f"INSAG-7 Fig. II-9 (circles) vs A8.3 coupled transient (lines): {os.path.basename(res)[:60]}", fill="black")
        col = {0: (200, 0, 0), 4: (0, 140, 0), 6: (0, 70, 220), 7: (170, 0, 170)}
        for tm, p in meas.items():
            for Dm, v in p:
                d.ellipse([X(Dm) - 6, Y(v) - 6, X(Dm) + 6, Y(v) + 6], outline=col[tm], width=3)
        for t, sh in shapes:
            c = col.get(int(round(t)), (90, 90, 90))
            d.line([(X(a), Y(b)) for a, b in sorted(zip(Db, sh))], fill=c, width=3)
        for i, tm in enumerate((0, 4, 6, 7)):
            yy = T + 12 + 20 * i
            d.ellipse([L + 15, yy, L + 27, yy + 12], outline=col[tm], width=3)
            d.text((L + 35, yy), f"{tm} s measured / model at {tm} s", fill="black")
        im.save(sys.argv[2])


if __name__ == "__main__":
    main()
