"""OpenMC side of the DRAGON/OpenMC method-gap study (PROGRESS.md, "Method gap").

Each variant changes ONE input of the fresh-fuel cell relative to the control
and is run at the same seed and statistics, so statistical noise is largely
common to the pair and cancels in the difference.

  control     c_Graphite (crystal), reflective sides   -- = run81_d* in rebaseline.sh
  g10p        c_Graphite_10p: DRAGON's own graphite TSL      (H1: identical data)
  g30p        c_Graphite_30p: closest to RBMK porosity       (H1: sensitivity)
  g10p_white  10p + white side boundaries, as DRAGON's TISO  (H2)

Run:  python method_study.py <variant> <dca> [<dca> ...]
Appends one record per run to method_study.json.
"""
import json
import os
import sys

import openmc

from rbmk_cell import make_model

VARIANTS = {
    "control":    dict(graphite_tsl="c_Graphite",     boundary="reflective"),
    "g10p":       dict(graphite_tsl="c_Graphite_10p", boundary="reflective"),
    "g30p":       dict(graphite_tsl="c_Graphite_30p", boundary="reflective"),
    "g10p_white": dict(graphite_tsl="c_Graphite_10p", boundary="white"),
}
# Same statistics and seed as the rebaseline fresh sweep (run_one.py 50000 300 50),
# so "control" is directly comparable with run81_d*/log.txt.
PARTICLES, BATCHES, INACTIVE, SEED = 50_000, 300, 50, 1
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "method_study.json")


def run(variant, dca):
    d = f"meth_{variant}_d{dca}"
    os.makedirs(d, exist_ok=True)
    model = make_model(dca=dca, particles=PARTICLES, batches=BATCHES,
                       inactive=INACTIVE, seed=SEED, **VARIANTS[variant])
    sp = model.run(cwd=d, output=False,
                   threads=int(os.environ.get("RBMK_THREADS", os.cpu_count())))
    with openmc.StatePoint(sp) as s:
        k, sd = s.keff.nominal_value, s.keff.std_dev
    rec = dict(variant=variant, dca=dca, k=k, sd=sd, seed=SEED,
               particles=PARTICLES, batches=BATCHES, inactive=INACTIVE,
               **VARIANTS[variant])
    recs = json.load(open(OUT)) if os.path.exists(OUT) else []
    recs = [r for r in recs if not (r["variant"] == variant and r["dca"] == dca)]
    json.dump(recs + [rec], open(OUT, "w"), indent=1)
    print(f"METHOD {variant:11s} dca={dca:<5} k={k:.6f} +/- {sd:.6f}", flush=True)


if __name__ == "__main__":
    variant = sys.argv[1]
    for dca in (float(x) for x in sys.argv[2:]):
        run(variant, dca)
