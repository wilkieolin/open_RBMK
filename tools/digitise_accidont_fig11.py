#!/usr/bin/env python3
"""
Rod TYPES of Chernobyl-4 at 01:22:30, from accidont Fig. 11 [ACC] ("Положение ОР СУЗ на моменты времени
00:39 и 01:22:30"; cell colour = type, upper number = insertion at 00:39 m, lower = 01:22:30 m; cell
coordinate = plant YYXX, octal), checked against INSAG-7 Fig. II-6 depths and against a third-party
transcription of Karpan's maps [SKSIM].

    python tools/digitise_accidont_fig11.py sources/accidont/picture11.JPG sources/skala_sim_core_data.json
        -> sources/derived/accidont_fig11_cps.csv

Method.
  * registration from the drawn grid (found, not assumed): column k (X = 9 + 2k decimal) centred at
    x = 46.5 + 14.5 (X - 9) px; Y (decimal) centred at y = 30 + 9.45 (54 - Y) px.  It puts the 12 white
    "ДКЭ (в)" cells exactly on the 12 ДКЭв cells of unit4_channel_map.csv.
  * type = the cell's background colour (modal quantised colour of the light pixels in a 22 x 32 px
    box): pink РР, cyan АЗ, green ПК, yellow УСП, lavender АР/ЛАР, white ДКЭ.  It gives 115 / 24 / 24
    / 24 / 24 / 12 = 211 rods + 12 detectors.  АР vs ЛАР (same colour) is split by the printed label;
    the 12 АР cells are those of unit4_channel_map.csv and of [SKSIM], so ЛАР = lavender minus АР.
  * УСП depths at 01:22:30 were read by eye from a 4x montage of the 24 yellow cells (USP_0122 below).
    Every other depth is INSAG-7 Fig. II-6's (the map's depth_cm); [SKSIM]'s 01:22:30 depths agree
    with Fig. II-6 at all 211 sites (to its 7 cm "just off the stop" entries), and with Fig. 11 at the
    24 УСП.  [SKSIM]'s 00:39 depths are carried unverified (column depth0039_cm_sksim).
"""
import collections, csv, json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE = {(240, 192, 192): 'RR', (192, 240, 240): 'AZ', (192, 240, 192): 'PK',
           (240, 240, 144): 'USP', (240, 240, 168): 'USP', (240, 192, 240): 'AR/LAR', (240, 240, 240): 'DKEV'}
# Fig. 11 lower numbers (m) on the 24 yellow cells, read from the 4x montage
USP_0122 = {'6433': 0.8, '6443': 0.2, '5423': 0, '5433': 0, '5443': 0, '5453': 0.1, '4413': 0, '4423': 0,
            '4433': 0, '4443': 0, '4453': 1.2, '4463': 1.9, '3413': 1.8, '3423': 0, '3433': 0, '3443': 0.2,
            '3453': 1.0, '3463': 0, '2423': 0, '2433': 0, '2443': 0, '2453': 0, '1433': 0.1, '1443': 0}


def main(img, sksim):
    im = np.asarray(Image.open(img).convert('RGB')).astype(int)
    cmap = {c['row'] + c['col']: c for c in csv.DictReader(open(os.path.join(ROOT, 'sources/derived/unit4_channel_map.csv')))}
    sk = {r[0].replace('-', ''): r for r in json.load(open(sksim))['cps']}
    out = []
    for cell, r in sk.items():
        Y, X = int(cell[:2], 8), int(cell[2:], 8)
        cx, cy = 46.5 + (X - 9) * 14.5, 30 + (54 - Y) * 9.45
        p = im[int(cy - 16):int(cy + 16), int(cx - 11):int(cx + 11)].reshape(-1, 3)
        p = p[p.sum(1) > 450]
        q = collections.Counter(tuple(int(v) for v in (c // 24) * 24) for c in p).most_common(1)[0][0]
        t = PALETTE[q]
        m = cmap[cell]
        if t == 'AR/LAR':
            t = 'AR' if m['type'] == 'AR' else 'LAR'
        if t == 'DKEV' and m['type'] != 'DKEV':
            raise SystemExit(f'{cell}: white in Fig. 11 but {m["type"]} in the map')
        d_ii6 = m['depth_cm']
        if t == 'USP' and d_ii6 != '' and abs(float(d_ii6) / 100 - USP_0122[cell]) > 0.11:
            raise SystemExit(f'{cell}: USP {USP_0122[cell]} m in Fig. 11, {d_ii6} cm in Fig. II-6')
        out.append(dict(row=cell[:2], col=cell[2:], type_fig11=t, type_map=m['type'],
                        depth0122_cm_figII6=d_ii6, usp0122_m_fig11=USP_0122.get(cell, ''),
                        depth0039_cm_sksim='' if r[5] is None else r[5],
                        entry='bottom' if t == 'USP' else ('' if t == 'DKEV' else 'top')))
    out.sort(key=lambda d: (-int(d['row'], 8), int(d['col'], 8)))
    path = os.path.join(ROOT, 'sources/derived/accidont_fig11_cps.csv')
    with open(path, 'w') as fh:
        fh.write('# accidont Fig. 11 [ACC] rod types at 01:22:30 (tools/digitise_accidont_fig11.py); plant row/col octal\n')
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    c = collections.Counter(d['type_fig11'] for d in out)
    print(path, dict(c))
    x = collections.Counter((d['type_map'], d['type_fig11']) for d in out if d['type_map'] != d['type_fig11'])
    print('map type -> Fig. 11 type, where they differ:', dict(x))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
