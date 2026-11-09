#!/usr/bin/env python3
"""
Card #44: the Unit 4 channel map with Unit 4's OWN rod types at 01:22:30, from accidont Fig. 11 [ACC]
(sources/derived/accidont_fig11_cps.csv), in place of Leningrad-2's (Dollezhal Fig. 2.3) plus the
assumed types on the 32 extra sites that unit4_channel_map.csv carries.

    python tools/retype_unit4_map.py  ->  sources/derived/unit4_channel_map_fig11.csv

Same rows, same order, same i/j and depth_cm; only `type` changes on the 211 rod sites (the 12 ДКЭв
must already agree and the 4 KD are not in Fig. 11, so they are kept).  `type_dollezhal` keeps the old
type and `type_source` says where the new one came from.  Types: RR, AZ, PK (the 24-rod
over-compensation group of RR-construction rods: NUREG-1250 Tab. 2.5 139 РР = 115 + 24; INSAG-7 RU
"ПК-АЗ"), LAR, AR, USP.  How each is BUILT (displacer or not) is the generator's business
(gen_rbmk_unit4.py, ROD_DSP/ROD_ABS/ROD_BOT, U4_LARDSP), not this file's.

Cross-checked against Karpan's VK Fig. 3 (sources/derived/karpan_vk_fig3_012230.csv), which marks
УСП, АР and ДКЭв: every one of those must sit on the same sites here.
"""
import collections, csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'sources', 'derived')


def rows(path):
    return list(csv.DictReader(l for l in open(path) if not l.startswith('#')))


def main():
    m = rows(os.path.join(D, 'unit4_channel_map.csv'))
    f = {r['row'] + r['col']: r for r in rows(os.path.join(D, 'accidont_fig11_cps.csv'))}
    k = {r['row'] + r['col']: r for r in rows(os.path.join(D, 'karpan_vk_fig3_012230.csv'))}
    if len(f) != 223:
        raise SystemExit(f'Fig. 11: {len(f)} sites, expected 211 rods + 12 ДКЭв')
    seen = set()
    out = []
    for r in m:
        cell = r['row'] + r['col']
        r = dict(r, type_dollezhal=r['type'])
        if cell in f:
            t = f[cell]['type_fig11']
            if t == 'DKEV' and r['type'] != 'DKEV':
                raise SystemExit(f'{cell}: ДКЭв in Fig. 11, {r["type"]} in the map')
            if r['type'] in ('FUEL', 'KD'):
                raise SystemExit(f'{cell}: a Fig. 11 site is {r["type"]} in the map')
            r['type'] = t
            r['type_source'] = 'accidont Fig. 11'
            seen.add(cell)
        elif r['type'] not in ('FUEL', 'KD'):
            raise SystemExit(f'{cell}: CPS type {r["type"]} in the map but no Fig. 11 site')
        out.append(r)
    if seen != set(f):
        raise SystemExit(f'Fig. 11 sites missing from the map: {sorted(set(f) - seen)}')
    # Karpan's marks: УСП / АР / ДКЭв must be the same sites
    for mark, t in (('USP', 'USP'), ('AR', 'AR'), ('DKEV', 'DKEV')):
        a = {c for c, r in k.items() if r['mark'] == mark}
        b = {r['row'] + r['col'] for r in out if r['type'] == t}
        if a != b:
            raise SystemExit(f'{t}: Karpan {sorted(a ^ b)} differ')
    path = os.path.join(D, 'unit4_channel_map_fig11.csv')
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator='\n')
        w.writeheader(); w.writerows(out)
    print(path, dict(collections.Counter(r['type'] for r in out)))
    print('old -> new where they differ:',
          dict(collections.Counter((r['type_dollezhal'], r['type']) for r in out if r['type_dollezhal'] != r['type'])))


if __name__ == '__main__':
    main()
