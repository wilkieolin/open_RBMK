#!/usr/bin/env python3
"""Digitise INSAG-7 Fig. II-9 (pdf p.132, printed p.122): axial neutron flux
at 0 / 4 / 6 / 7 s after EPS-5, against distance from the core top.

Input is the page's native 300 dpi 1-bit scan (pdfimages, no resampling).
Calibration comes from the printed ticks, not the drawn axis lines:
  y: 0.0..3.0 ticks at rows 1320.5..225.5, linear at 365.0 px/unit (the
     seven ticks fit to <1 px);
  x: 200/400/600/800 cm ticks at cols 717.5/1024.5/1332.5/1642.5, a fit
     with residuals <1 px.  Its zero lands at col 408.5, i.e. ~7 cm right of
     the drawn y-axis (col 397.5) -- the figure's own inconsistency, carried
     as a +-7 cm x uncertainty.
Marker centres were placed by eye on zoomed crops, then refined to the ink
centroid in a +-R px window (the curve passing through biases this by a
pixel or two, ~1 cm / ~0.005 units).  A point marked 'fixed' sits where
neighbouring curves crowd the window and drag the centroid; its centre was
read from the marker's hollow interior on a pixel-level zoom instead.

Usage: digitise_fig_II9.py <nat-000.png> <out.csv> [overlay.png]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw

BX, AX = 1.5415, 408.5          # px/cm, col of D=0
Y0, SY = 1320.5, 365.0          # row of flux 0, px per unit

def to_data(c, r):
    return (c - AX) / BX, (Y0 - r) / SY

# by-eye centres, native pixels (col, row)
EYE = {
    0: [(460, 1028), (540, 890), (670, 783), (805, 860), (948, 967),
        (1168, 974), (1375, 1028), (1465, 1172)],
    4: [(478, 1288), (651, 1260), (821, 1189), (923, 1088), (1135.8, 669.2, 'fixed'),
        (1206, 540), (1293, 411), (1361, 488), (1408, 631), (1442, 801)],
    6: [(588, 1298), (688, 1278), (782, 1254), (880, 1194), (959, 1073),
        (1199, 502), (1295, 346), (1373, 424), (1409, 523), (1436, 665)],
    7: [(651, 1300), (766, 1283), (859, 1244), (951, 1124), (1168, 526),
        (1239, 381), (1307, 293), (1386, 390), (1434, 543)],
}
MARK = {0: "star", 4: "circle", 6: "square", 7: "triangle"}

def refine(ink, c, r, R=14, it=3):
    for _ in range(it):
        ci, ri = int(round(c)), int(round(r))
        w = ink[ri - R:ri + R + 1, ci - R:ci + R + 1]
        rr, cc = np.nonzero(w)
        if len(rr) == 0:
            break
        c, r = ci - R + cc.mean(), ri - R + rr.mean()
    return c, r

def main():
    src, out = sys.argv[1], sys.argv[2]
    ink = np.array(Image.open(src).convert("L")) < 128
    rows = []
    for t, pts in EYE.items():
        for c, r, *flag in pts:
            c2, r2 = (c, r) if flag == ["fixed"] else refine(ink, c, r)
            if abs(c2 - c) > 8 or abs(r2 - r) > 8:
                sys.exit(f"t={t} ({c},{r}) refined to ({c2:.1f},{r2:.1f}): "
                         "moved > 8 px, eye placement is wrong")
            D, f = to_data(c2, r2)
            rows.append((t, D, f, c2, r2))
    with open(out, "w") as fh:
        fh.write("# INSAG-7 Fig. II-9 (p.122), digitised by tools/digitise_fig_II9.py\n")
        fh.write("# D_cm = distance below core top; flux in the figure's relative units\n")
        fh.write("t_s,marker,D_cm,flux,px_col,px_row\n")
        for t, D, f, c, r in rows:
            fh.write(f"{t},{MARK[t]},{D:.1f},{f:.3f},{c:.1f},{r:.1f}\n")
    for t in EYE:
        print(f"t={t}s: " + "  ".join(f"({D:.0f},{f:.2f})"
                                       for tt, D, f, *_ in rows if tt == t))
    if len(sys.argv) > 3:
        im = Image.open(src).convert("RGB")
        d = ImageDraw.Draw(im)
        col = {0: (220, 0, 0), 4: (0, 150, 0), 6: (0, 0, 230), 7: (200, 0, 200)}
        for t, D, f, c, r in rows:
            d.ellipse([c - 6, r - 6, c + 6, r + 6], outline=col[t], width=3)
            d.line([c - 10, r, c + 10, r], fill=col[t], width=1)
            d.line([c, r - 10, c, r + 10], fill=col[t], width=1)
        for D in (200, 400, 600, 800):             # calibration ticks back
            d.line([BX * D + AX, Y0 + 4, BX * D + AX, Y0 + 30], fill=(255, 120, 0), width=3)
        for k in range(7):
            d.line([370, Y0 - SY * k / 2, 395, Y0 - SY * k / 2], fill=(255, 120, 0), width=3)
        im.crop((330, 180, 1720, 1420)).save(sys.argv[3])

if __name__ == "__main__":
    main()
