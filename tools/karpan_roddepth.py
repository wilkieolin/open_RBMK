#!/usr/bin/env python3
"""
Card #44 depth bracket: Karpan's VK Fig. 3 [KARVK] rod depths at 01:22:30
(sources/derived/karpan_vk_fig3_012230.csv) as a U4_RODDEPTH file for the Fig. 11 map
(sources/derived/unit4_channel_map_fig11.csv): one depth in cm per CPS rod row, in the map's row
order, which is what gen_rbmk_unit4.py's U4_RODDEPTH reads.

    python tools/karpan_roddepth.py  ->  sources/derived/karpan_vk_fig3_roddepth.txt

Karpan's grid has one edge site at 12-25 where Fig. II-6 / Fig. 11 have 64-53; both read 0 cm, so
64-53 is given 0.  Every other rod site must be in Karpan's map, and the differences from the
map's depth_cm (Fig. II-6) are printed: they are the 9-rod conflict of sources/README.md.
"""
import csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'sources', 'derived')
RODS = {'RR', 'AZ', 'PK', 'LAR', 'AR', 'USP'}


def main():
    k = {r['row'] + r['col']: float(r['depth_cm'] or 0) for r in csv.DictReader(
        l for l in open(os.path.join(D, 'karpan_vk_fig3_012230.csv')) if not l.startswith('#'))}
    k.setdefault('6453', 0.0)
    out, tot_k, tot_m = [], 0.0, 0.0
    for r in csv.DictReader(open(os.path.join(D, 'unit4_channel_map_fig11.csv'))):
        if r['type'] not in RODS:
            continue
        cell = r['row'] + r['col']
        if cell not in k:
            raise SystemExit(f'{cell}: not in Karpan Fig. 3')
        dm = float(r['depth_cm'] or 0)
        if k[cell] != dm:
            print(f'  {cell} {r["type"]:4s} II-6 {dm:5.0f}  Karpan {k[cell]:5.0f}')
        out.append(k[cell]); tot_k += k[cell]; tot_m += dm
    if len(out) != 211:
        raise SystemExit(f'{len(out)} rods, expected 211')
    path = os.path.join(D, 'karpan_vk_fig3_roddepth.txt')
    open(path, 'w').write('\n'.join(f'{d:g}' for d in out) + '\n')
    print(f'{path}: 211 rods, total {tot_k / 100:.2f} m (Fig. II-6 {tot_m / 100:.2f} m)')


if __name__ == '__main__':
    main()
