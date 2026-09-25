"""Regenerate dragon_a5b_void.json from the A5b COMPO run.

rbmk_a5b_compo.x2m prints one line per branch point,

    A5BTAB  <burnup MWd/t>  <dca g/cm3>  <TF K>  <TG K>  <k-inf>

and void_bracket.py needs the DCA sweep at the nominal temperatures
(TF 900 K, TG 750 K).  This file used to be assembled by hand.  It is now
derived, so it cannot drift from the .result it claims to come from.

Also writes dragon_a5b_all.json with every branch point, keyed
"bu|dca|tf|tg", for anything that wants the temperature axes.
"""
import json
import os
import platform
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = os.environ.get("DRAGON_ARCH", f"Linux_{platform.machine()}")
RESULT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "5.1", "Dragon", ARCH, "rbmk_a5b_compo.result")
TF_NOM, TG_NOM = 900.0, 750.0

NUM = r"([-+]?\d+\.\d+[eE][-+]\d+)"
ROW = re.compile(r"A5BTAB\s+" + r"\s+".join([NUM] * 5))

rows = []
with open(RESULT, errors="ignore") as f:
    for line in f:
        m = ROW.search(line)
        if m:
            rows.append(tuple(float(x) for x in m.groups()))

# each ECHO appears once in the output; guard against the listing echoing it
rows = sorted(set(rows))
print(f"{RESULT}: {len(rows)} A5BTAB rows")
if len(rows) != 630:
    sys.exit(f"ERROR: expected 630 branch points, found {len(rows)}")

nominal = {}
for bu, dca, tf, tg, k in rows:
    if abs(tf - TF_NOM) < 1e-6 and abs(tg - TG_NOM) < 1e-6:
        nominal.setdefault(str(int(round(bu))), {})[f"{dca:g}"] = round(k, 6)

with open(os.path.join(HERE, "dragon_a5b_void.json"), "w") as f:
    json.dump(nominal, f, indent=1, sort_keys=True)
with open(os.path.join(HERE, "dragon_a5b_all.json"), "w") as f:
    json.dump({f"{int(round(bu))}|{dca:g}|{tf:g}|{tg:g}": round(k, 6)
               for bu, dca, tf, tg, k in rows}, f, indent=1, sort_keys=True)
print("wrote dragon_a5b_void.json "
      f"({len(nominal)} burnups x {len(next(iter(nominal.values())))} densities)"
      " and dragon_a5b_all.json")
