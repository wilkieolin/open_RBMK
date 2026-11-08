#!/usr/bin/env python3
"""
Digitise accidont.ru Figs 9 and 10 [ACC]: "Распределение нейтронного потока N по высоте H активной
зоны (показания датчиков ДКЭв)" -- the SKALA axial in-core detector readings at 01:22:30, 26 Apr 1986,
for the 12 height-detector (ДКЭв) cells, 7 sections each, at H = 0.5 ... 6.5 m below the core top.
These are the measured axial data behind INSAG-7 Fig. II-8 (which prints the same 12 shapes, unlabelled
and unscaled).  Each figure has two panels of three labelled curves; the labels are the cells' plant
coordinates YYXX (octal), and all 12 are the ДКЭв cells of sources/derived/unit4_channel_map.csv.

What is read:
  * axes from the drawn grid (found, not assumed): N = 0..250 over x = 28..403 px (left panel) and
    434..809 px (right), 50 per 75 px; H = 0..7 m over y = 10..458 px, 1 m per 64 px.
  * curve <-> cell: labels sit beside their curves in the same left-to-right order as the curves at
    the label's height (checked on 3x zooms of every label).  magenta is always the first label.
  * value: the curve's own pixels (by colour) on the 7 rows above and below each marker row are fitted
    with a line and evaluated at the marker row; where a ring marker is found within 4 units of that,
    the marker centre is used instead (the line under-reads by up to 3.5 at the peaks).
  * every marker found lies within 1.3 of a multiple of 5, so the printout's values are taken as
    multiples of 5 (value = 5 round(N / 5)); the raw reading is kept.
  * five readings are coincident markers that neither the trace nor the ring finder separates; they
    were read from 6x zooms and are flagged 'zoom': 3057 at 1.5 m (250, the marker on the plot edge),
    4047 at 6.5 m (70, shared with 3057), 2027 and 2047 at 4.5 m (100, on a grid line, shared), 2047 at
    0.5 m (150: two touching rings at 140/150 that the finder merges to 146).
Precision: +-5 (one quantum); H exact (the 7 section centres).

    python tools/digitise_accidont_dkev.py sources/accidont/picture09.JPG sources/accidont/picture10.JPG
        -> sources/derived/accidont_fig9_10_dkev_axial.csv
"""
import math, os, sys
import numpy as np
from PIL import Image

LAB = {(0, 'L'): {'magenta': '3017', 'olive': '4027', 'red': '5017'},
       (0, 'R'): {'magenta': '6027', 'red': '6047', 'olive': '5037'},
       (1, 'L'): {'magenta': '5057', 'red': '3057', 'olive': '4047'},
       (1, 'R'): {'magenta': '2027', 'red': '2047', 'olive': '3037'}}
X0 = {'L': 28, 'R': 434}
ZOOM = {('2047', 0.5): 150, ('3057', 1.5): 250, ('4047', 6.5): 70, ('2027', 4.5): 100, ('2047', 4.5): 100}


def masks(im):
    r, g, b = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    return {'red': (r > 160) & (g < 100) & (b < 100),
            'magenta': (r > 160) & (g < 120) & (b > 160),
            'olive': (r > 80) & (r < 175) & (g > 80) & (g < 175) & (b < 80) & (np.abs(r - g) < 45)}


def rings(im, x0, yc):
    """Centres of ring markers (black or grey, radius 4-5 px) on one marker row."""
    S = im.sum(2)
    grey = (np.abs(im[:, :, 0] - im[:, :, 1]) < 20) & (np.abs(im[:, :, 1] - im[:, :, 2]) < 20)
    mark = (S < 300) | (grey & (S > 420) & (S < 620))
    ang = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    best = []
    for y in range(int(yc) - 3, int(yc) + 4):
        for x in range(x0 + 2, x0 + 374):
            sc = max(mark[(y + r * np.sin(ang)).round().astype(int),
                          (x + r * np.cos(ang)).round().astype(int)].mean() for r in (4, 5))
            if sc > 0.6 and S[y - 1:y + 2, x - 1:x + 2].mean() > 600:
                best.append((sc, x))
    best.sort(reverse=True)
    out = []
    for sc, x in best:
        if all(abs(x - p) > 7 for p in out):
            out.append(x)
    return [(x - x0) / 75 * 50 for x in out]


def main(f9, f10, out):
    rows = []
    for fi, path in enumerate((f9, f10)):
        im = np.asarray(Image.open(path).convert('RGB')).astype(int)
        M = masks(im)
        for panel, x0 in X0.items():
            for k in range(7):
                H = 0.5 + k
                yc = 10 + 64 * H
                mk = rings(im, x0, yc)
                for col, cell in LAB[(fi, panel)].items():
                    m = M[col][:, x0 + 1:x0 + 374]
                    pts = [(dy, np.nonzero(m[int(yc) + dy])[0].mean())
                           for dy in list(range(-13, -6)) + list(range(7, 14))
                           if m[int(yc) + dy].any()]
                    raw, how = None, None
                    if len(pts) >= 4:
                        dys, xs = np.array(pts).T
                        a, b = np.polyfit(dys, xs, 1)
                        raw, how = (b + 1) / 75 * 50, 'trace'
                        near = [v for v in mk if abs(v - raw) < 4]
                        if near:
                            raw, how = min(near, key=lambda v: abs(v - raw)), 'marker'
                    if (cell, H) in ZOOM:
                        val, how = ZOOM[(cell, H)], 'zoom'
                    else:
                        val = 5 * round(raw / 5)
                    rows.append((cell, H, val, '' if raw is None else f'{raw:.1f}', how,
                                 f'Fig {9 + fi} {panel}', col))
    rows.sort(key=lambda r: (r[0], r[1]))
    with open(out, 'w') as fh:
        fh.write('# accidont Figs 9-10 [ACC]: SKALA DKEv axial readings at 01:22:30 (tools/digitise_accidont_dkev.py)\n')
        fh.write('# cell = plant coordinate YYXX (octal); H_m = section centre below the core top; N = printout units (multiples of 5)\n')
        fh.write('cell,H_m,N,N_raw,how,figure,colour\n')
        for r in rows:
            fh.write(','.join(str(v) for v in r) + '\n')
    print(f'{len(rows)} readings -> {out}')


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1], sys.argv[2], os.path.join(root, 'sources', 'derived', 'accidont_fig9_10_dkev_axial.csv'))
