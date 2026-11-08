#!/usr/bin/env python3
"""
The model's t = 0 axial shape at the 12 height-detector (ДКЭв) cells, against the SKALA readings
at 01:22:30 (accidont Figs 9-10 [ACC], sources/derived/accidont_fig9_10_dkev_axial.csv).

    python tools/a8_dkev_compare.py <dumpdir with fmap0.asc>

What is compared.  A ДКЭв cell holds detectors, not fuel, so the model value of a section is the
mean BUND-PW of the fuel bundles in the four face-neighbour channels of the cell (those that are
fuel) over the section's 1 m (4 bundles of 25 cm).  Section k (k = 0..6) is H = k..k+1 m below the
core top; the figure plots it at H = k + 0.5.  Two comparisons:
  * shape: each string over its own mean (the axial question, card #33);
  * level: each string's mean over the 12-string mean (a radial check on 12 points).
Lattice: sources/derived/unit4_channel_map.csv (i, j); DONJON ix = i + NPAD + 1, iy = ny - (j +
NPAD) with NPAD 5, ny 58 (gen_rbmk_unit4.py plane()/devices(): the map's j axis is mirrored onto
DONJON's y; FMAP XNAME/YNAME confirm it: ix 23 is plant X 31, iy 53 is plant Y 67).  FMAP channel
order is iy outer, ix inner over fuel cells (test/b4_coupled.jl); BUND-PW is NB blocks of NCH,
block 1 the core bottom (RESPFM.f, tools/a8_axial.py).
"""
import csv, os, sys
from collections import defaultdict
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPAD, NY, NB, PITCH = 5, 58, 28, 25.0


def lcm_record(path, name):
    lines = open(path).read().split('\n')
    for n, l in enumerate(lines):
        if l.strip() == name:
            cnt = int(lines[n - 1].split()[4])
            vals = []
            for l2 in lines[n + 1:]:
                if len(vals) >= cnt:
                    break
                vals += [float(v) for v in l2.split()]
            return np.array(vals[:cnt])
    raise SystemExit(f'{path}: no {name}')


def main(dumpdir):
    cells = list(csv.DictReader(open(os.path.join(ROOT, 'sources/derived/unit4_channel_map.csv'))))
    fuel = sorted(((NY - (int(c['j']) + NPAD), int(c['i']) + NPAD + 1) for c in cells if c['type'] == 'FUEL'))
    ich = {(ix, iy): n for n, (iy, ix) in enumerate(fuel)}
    pw = lcm_record(os.path.join(dumpdir, 'fmap0.asc'), 'BUND-PW')
    nch = len(fuel)
    if len(pw) != nch * NB:
        raise SystemExit(f'BUND-PW {len(pw)} != {nch} x {NB}')
    P = pw.reshape(NB, nch)                                   # P[b, ich], b = 0 bottom
    meas = defaultdict(dict)
    for r in csv.DictReader(l for l in open(os.path.join(ROOT, 'sources/derived/accidont_fig9_10_dkev_axial.csv'))
                            if not l.startswith('#')):
        meas[r['cell']][float(r['H_m'])] = float(r['N'])
    H = [0.5 + k for k in range(7)]
    rows = []
    for c in cells:
        if c['type'] != 'DKEV':
            continue
        cell = c['row'] + c['col']
        i, j = int(c['i']), int(c['j'])
        nb = [ich[(ii + NPAD + 1, NY - (jj + NPAD))] for ii, jj in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1))
              if (ii + NPAD + 1, NY - (jj + NPAD)) in ich]
        mod = []
        for k in range(7):                                   # H in [k, k+1] m below the top
            b_hi = NB - 4 * k                                # 1-based bundle at the section top
            bs = range(b_hi - 4, b_hi)                       # 0-based: 4 bundles
            mod.append(P[np.ix_(list(bs), nb)].mean())
        rows.append((cell, len(nb), np.array([meas[cell][h] for h in H]), np.array(mod)))
    rows.sort()
    m_all = np.array([r[2] for r in rows]); p_all = np.array([r[3] for r in rows])
    print(f'{dumpdir}\n  model = mean BUND-PW of the face-neighbour fuel channels over each 1 m section\n')
    print('cell  nbr  measured shape (H 0.5..6.5 m below top)      model shape                              rms')
    for cell, n, m, p in rows:
        ms, ps = m / m.mean(), p / p.mean()
        print(f'{cell}  {n}   ' + ' '.join(f'{v:4.2f}' for v in ms) + '   ' + ' '.join(f'{v:4.2f}' for v in ps)
              + f'   {np.sqrt(((ms - ps) ** 2).mean()):.3f}')
    ms, ps = m_all.mean(0), p_all.mean(0)
    ms, ps = ms / ms.mean(), ps / ps.mean()
    print('\n12-string mean shape   measured ' + ' '.join(f'{v:4.2f}' for v in ms))
    print('                       model    ' + ' '.join(f'{v:4.2f}' for v in ps))
    print(f'  measured peak at H {H[int(np.argmax(ms))]} m ({ms.max():.2f}); model at H {H[int(np.argmax(ps))]} m ({ps.max():.2f}); '
          f'rms {np.sqrt(((ms - ps) ** 2).mean()):.3f}')
    lm = m_all.mean(1) / m_all.mean(); lp = p_all.mean(1) / p_all.mean()
    print('\nstring level (mean over sections, over the 12-string mean): cell measured model')
    for (cell, *_), a, b in zip(rows, lm, lp):
        print(f'  {cell} {a:5.2f} {b:5.2f}')
    print(f'  correlation r = {np.corrcoef(lm, lp)[0, 1]:.3f}')


if __name__ == '__main__':
    main(sys.argv[1])
