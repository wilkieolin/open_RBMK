"""Analytic volume fractions for the RBMK cell, independent of DRAGON's
MIXTURESVOL.  Compares against the values rbmk_cell_a3.x2m asserts."""
import numpy as np
from rbmk_cell import *

A = lambda r: np.pi * r * r
cell = (2 * HALF_PITCH) ** 2

carr_bore = A(R_CARR_IN)
carr_wall = A(R_CARR_OUT) - A(R_CARR_IN)

n_rods = RING1_N + RING2_N
hole   = n_rods * A(R_HOLE)
pellet = n_rods * (A(R_PELLET) - A(R_HOLE))
gap    = n_rods * (A(R_GAP) - A(R_PELLET))
clad   = n_rods * (A(R_CLAD) - A(R_GAP))

chan_free = A(R_CHANNEL) - A(R_CARR_OUT) - n_rods * A(R_CLAD)
pt        = A(R_PT_OUT) - A(R_CHANNEL)
gasclear  = A(R_GAS_OUT) - A(R_PT_OUT)
rings     = A(R_RINGS_OUT) - A(R_GAS_OUT)
block     = cell - A(R_RINGS_OUT)

v = {
    1: carr_bore + chan_free,   # coolant
    2: pt,                      # pressure tube
    3: hole + gap + gasclear,   # He
    4: rings,
    5: block,
    6: (RING1_N / n_rods) * pellet,
    7: (RING2_N / n_rods) * pellet,
    8: clad,
    9: carr_wall,
}
tot = sum(v.values())

groups = {
    "graphite":  v[4] + v[5],
    "coolant":   v[1],
    "fuel":      v[6] + v[7],
    "zirconium": v[2] + v[8] + v[9],
    "gas":       v[3],
}
expect = {"graphite": 89.6, "coolant": 3.77, "fuel": 2.90,
          "zirconium": 2.73, "gas": 1.00}
# values printed by the DRAGON run (MIXTURESVOL, 2026-09-22)
dragon = {"graphite": 89.594, "coolant": 3.772, "fuel": 2.901,
          "zirconium": 2.729, "gas": 1.004}

print(f"cell area       {tot:12.4f} cm2   (25 x 25 = {cell:.1f})")
print(f"{'':16s}{'analytic %':>12s}{'DRAGON %':>12s}{'deck target':>13s}")
for k in ["graphite", "coolant", "fuel", "zirconium", "gas"]:
    f = 100 * groups[k] / tot
    print(f"  {k:14s}{f:12.4f}{dragon[k]:12.3f}{expect[k]:13.2f}")
print(f"  {'sum':14s}{100*sum(groups.values())/tot:12.4f}")

# geometric clearances -- the rod ring radii are inferred, so check they fit
print("\nclearance checks (cm):")
print(f"  carrier OD to inner ring ID : {RING1_R - R_CARR_OUT - R_CLAD:+.4f}")
print(f"  inner ring rod-to-rod gap   : "
      f"{2*RING1_R*np.sin(np.pi/RING1_N) - 2*R_CLAD:+.4f}")
print(f"  inner to outer ring gap     : {RING2_R - RING1_R - 2*R_CLAD:+.4f}")
print(f"  outer ring rod-to-rod gap   : "
      f"{2*RING2_R*np.sin(np.pi/RING2_N) - 2*R_CLAD:+.4f}")
print(f"  outer ring to tube wall     : {R_CHANNEL - RING2_R - R_CLAD:+.4f}")
