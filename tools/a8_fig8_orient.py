#!/usr/bin/env python3
"""
Orientation test against the measured radial field: accidont Fig. 8 [ACC] (ДКЭр readings at 01:22:30 on
squares labelled with plant coordinates; sources/derived/accidont_fig8_dker_radial.csv) against
  * INSAG-7 Fig. II-7 as digitised (sources/derived/insag7_fig_II7_lattice.csv, lattice ix/iy), and
  * optionally the model's t = 0 channel powers (BUND-PW summed over bundles) from a dump directory,
each under the 8 symmetries of the square about the fuel centroid.  A square's value is the mean over the
fuel channels within +-2 (decimal) of its label in X and Y; "inner" = squares with N >= 100.

    python tools/a8_fig8_orient.py [dumpdir]
"""
import csv, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a8_dkev_compare import lcm_record, NPAD, NY, NB, ROOT

T = {'identity': [[1, 0], [0, 1]], 'rot90': [[0, -1], [1, 0]], 'rot180': [[-1, 0], [0, -1]],
     'rot270': [[0, 1], [-1, 0]], 'mirrorX': [[-1, 0], [0, 1]], 'mirrorY': [[1, 0], [0, -1]],
     'transpose': [[0, 1], [1, 0]], 'antitranspose': [[0, -1], [-1, 0]]}


def table(name, XY, P, meas):
    c0 = XY.mean(0)
    print(f'\n{name} vs Fig. 8 ({len(meas)} squares)')
    for k, t in T.items():
        xy = (XY - c0) @ np.array(t, float).T + c0
        m = []
        for X, Y, _ in meas:
            s = (np.abs(xy[:, 0] - X) <= 2) & (np.abs(xy[:, 1] - Y) <= 2)
            m.append(P[s].mean() if s.any() else np.nan)
        m = np.array(m); ok = ~np.isnan(m); inn = ok & (meas[:, 2] >= 100)
        print(f'  {k:14s} r {np.corrcoef(meas[ok, 2], m[ok])[0, 1]:.3f}   inner r {np.corrcoef(meas[inn, 2], m[inn])[0, 1]:.3f}')


def main(dumpdir=None):
    cells = list(csv.DictReader(open(os.path.join(ROOT, 'sources/derived/unit4_channel_map.csv'))))
    plant = {(int(c['i']) + NPAD + 1, NY - (int(c['j']) + NPAD)): (int(c['col'], 8), int(c['row'], 8)) for c in cells}
    meas = np.array([(int(r['X'], 8), int(r['Y'], 8), float(r['N'])) for r in csv.DictReader(
        l for l in open(os.path.join(ROOT, 'sources/derived/accidont_fig8_dker_radial.csv')) if not l.startswith('#'))])
    v7 = [(plant[(int(r['ix']), int(r['iy']))], float(r['value'])) for r in csv.DictReader(
        l for l in open(os.path.join(ROOT, 'sources/derived/insag7_fig_II7_lattice.csv')) if not l.startswith('#'))]
    table('INSAG-7 Fig. II-7', np.array([p for p, _ in v7], float), np.array([v for _, v in v7]), meas)
    if dumpdir:
        fuel = sorted((iy, ix) for (ix, iy), c in plant.items()
                      if next(x for x in cells if (int(x['i']) + NPAD + 1, NY - (int(x['j']) + NPAD)) == (ix, iy))['type'] == 'FUEL')
        P = lcm_record(os.path.join(dumpdir, 'fmap0.asc'), 'BUND-PW').reshape(NB, len(fuel)).sum(0)
        table(f'model {os.path.basename(dumpdir.rstrip("/"))}', np.array([plant[(ix, iy)] for iy, ix in fuel], float), P, meas)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
