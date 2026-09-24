import sys, openmc
from rbmk_cell import make_model
dca = float(sys.argv[1]); parts = int(sys.argv[2]); bat = int(sys.argv[3])
inact = int(sys.argv[4]); cwd = sys.argv[5]
m = make_model(dca=dca, particles=parts, batches=bat, inactive=inact)
sp = m.run(cwd=cwd, threads=20, output=True)
with openmc.StatePoint(sp) as s:
    print(f"RESULT dca={dca} k={s.keff.nominal_value:.6f} +/- {s.keff.std_dev:.6f}")
