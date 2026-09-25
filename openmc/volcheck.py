"""Analytic volume fractions for the RBMK cell, independent of DRAGON's
MIXTURESVOL.  Compares against the values rbmk_cell_a3.x2m asserts."""
import numpy as np
from rbmk_cell import *

A = lambda r: np.pi * r * r
cell = (2 * HALF_PITCH) ** 2

carr_water = A(R_CTUBE_IN) - A(R_CARR_ROD)              # 0.25 mm annulus
carr_zr    = A(R_CARR_ROD) + A(R_CTUBE_OUT) - A(R_CTUBE_IN)

n_rods = RING1_N + RING2_N
hole   = n_rods * A(R_HOLE)
pellet = n_rods * (A(R_PELLET) - A(R_HOLE))
gap    = n_rods * (A(R_GAP) - A(R_PELLET))
clad   = n_rods * (A(R_CLAD) - A(R_GAP))

chan_free = A(R_CHANNEL) - A(R_CTUBE_OUT) - n_rods * A(R_CLAD)
pt        = A(R_PT_OUT) - A(R_CHANNEL)
gasclear  = A(R_GAS_OUT) - A(R_PT_OUT)
rings     = A(R_RINGS_OUT) - A(R_GAS_OUT)
block     = cell - A(R_RINGS_OUT)

v = {
    1: carr_water + chan_free,  # coolant
    2: pt,                      # pressure tube
    3: hole + gap + gasclear,   # He
    4: rings,
    5: block,
    6: (RING1_N / n_rods) * pellet,
    7: (RING2_N / n_rods) * pellet,
    8: clad,
    9: carr_zr,
}
tot = sum(v.values())

groups = {
    "graphite":  v[4] + v[5],
    "coolant":   v[1],
    "fuel":      v[6] + v[7],
    "zirconium": v[2] + v[8] + v[9],
    "gas":       v[3],
}
# Deck targets, recomputed 2026-09-24 (3) for clad OD 13.58.
expect = {"graphite": 89.59, "coolant": 3.60, "fuel": 2.90,
          "zirconium": 3.03, "gas": 0.87}
# Values printed by the DRAGON run (MIXTURESVOL) of rbmk_cell_a3.x2m.  Update
# these by hand from the .result whenever the geometry changes.
# 2026-09-24 (3): clad OD 13.58, pinned draglib cb1395ffbb65, k-inf 1.304123.
dragon = {"graphite": 89.594, "coolant": 3.604, "fuel": 2.901,
          "zirconium": 3.031, "gas": 0.870}

print(f"cell area       {tot:12.4f} cm2   (25 x 25 = {cell:.1f})")
print(f"{'':16s}{'analytic %':>12s}{'DRAGON %':>12s}{'deck target':>13s}")
for k in ["graphite", "coolant", "fuel", "zirconium", "gas"]:
    f = 100 * groups[k] / tot
    print(f"  {k:14s}{f:12.4f}{dragon[k]:12.3f}{expect[k]:13.2f}")
print(f"  {'sum':14s}{100*sum(groups.values())/tot:12.4f}")

# geometric clearances.  The clad-to-channel-wall gap is published, 2.2 mm
# [TD722 p.107], and checks the outer ring radius and clad OD together.
# [RU-B] quotes a 1.7 mm "minimum gap between rods"; the tightest gap here is
# tube-to-inner-rod, so that match is loose -- see sources/README.md.
def nearest(r1, a1, n1, r2, a2, n2):
    """Closest centre-to-centre distance between two rod rings."""
    p1 = [r1 * np.exp(1j * (a1 + 2 * np.pi * k / n1)) for k in range(n1)]
    p2 = [r2 * np.exp(1j * (a2 + 2 * np.pi * k / n2)) for k in range(n2)]
    return min(abs(a - b) for a in p1 for b in p2)

print("\nclearance checks (cm):")
print(f"  central tube OD to inner ring: {RING1_R - R_CTUBE_OUT - R_CLAD:+.4f}"
      "   ([RU-B] min gap 0.17, loosely)")
print(f"  inner ring rod-to-rod gap   : "
      f"{2*RING1_R*np.sin(np.pi/RING1_N) - 2*R_CLAD:+.4f}")
d12 = nearest(RING1_R, RING1_A, RING1_N, RING2_R, RING2_A, RING2_N)
print(f"  inner to outer ring gap     : {d12 - 2*R_CLAD:+.4f}"
      "   (at the pi/12 stagger)")
print(f"  outer ring rod-to-rod gap   : "
      f"{2*RING2_R*np.sin(np.pi/RING2_N) - 2*R_CLAD:+.4f}")
print(f"  outer ring to tube wall     : {R_CHANNEL - RING2_R - R_CLAD:+.4f}"
      "   (published 0.22)")
