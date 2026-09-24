"""The void coefficient as a production/absorption balance, in both codes.

DRAGON numbers come from parse_dragon.py (2-group edition of rbmk_rates.x2m);
OpenMC numbers from rates_d0.72.txt / rates_d0.02.txt.  Both are ENDF/B-VIII.1
with bound hydrogen, so data and composition are matched and only the
transport method differs.
"""

D = dict(
    n_abs=1.59999625e-03, v_abs=1.60000243e-03,
    n_nuf=2.09627576e-03, v_nuf=2.10239825e-03,
    n_u5=1.15947108e-04 + 1.91530465e-03, v_u5=1.67112131e-04 + 1.85993740e-03,
    n_u8=6.49643850e-05 + 3.20015993e-09, v_u8=7.53231551e-05 + 3.15666119e-09,
)
O = dict(
    n_abs=1.00047732, v_abs=1.00073735,
    n_nuf=1.31989736, v_nuf=1.33570954,
    n_u5=1.27947953, v_u5=1.28932463,
    n_u8=0.04041783, v_u8=0.04638491,
)

pc = lambda a, b: 100 * (b - a) / a
rho = lambda k: 1 - 1 / k

print("Change on going from dca=0.72 to dca=0.02 (97.2% void)\n")
print(f"{'':<26}{'DRAGON 172g':>14}{'OpenMC CE':>13}")
for lbl, kn, kv in (("total absorption", "n_abs", "v_abs"),
                    ("total nu-fission", "n_nuf", "v_nuf"),
                    ("  from U-235", "n_u5", "v_u5"),
                    ("  from U-238", "n_u8", "v_u8")):
    print(f"{lbl:<26}{pc(D[kn], D[kv]):>+13.3f}%{pc(O[kn], O[kv]):>+12.3f}%")

kD_n, kD_v = D["n_nuf"] / D["n_abs"], D["v_nuf"] / D["v_abs"]
kO_n, kO_v = O["n_nuf"] / O["n_abs"], O["v_nuf"] / O["v_abs"]
print(f"\n{'k-inf nominal':<26}{kD_n:>14.5f}{kO_n:>13.5f}")
print(f"{'k-inf voided':<26}{kD_v:>14.5f}{kO_v:>13.5f}")
rD = 1e5 * (rho(kD_v) - rho(kD_n))
rO = 1e5 * (rho(kO_v) - rho(kO_n))
print(f"{'void reactivity, pcm':<26}{rD:>+14.0f}{rO:>+13.0f}")

print("\nAttribution of the gap:")
dU8abs = 3.822 - 3.419          # percentage points of total absorption
k2 = kO_v * (1 - dU8abs / 100)
print("  DRAGON grows U-238 epithermal capture by +3.822 pp of total absorption")
print("  OpenMC grows it by                       +3.419 pp  (DRAGON +12% relative)")
print(f"  imposing that extra {dU8abs:.3f} pp on OpenMC's voided k: "
      f"{kO_v:.5f} -> {k2:.5f}")
r2 = 1e5 * (rho(k2) - rho(kO_n))
print(f"    void reactivity would fall to {r2:+.0f} pcm (from {rO:+.0f})")
gap, closed = rO - rD, rO - r2
print(f"    that closes {closed:.0f} of the {gap:.0f} pcm gap "
      f"({100 * closed / gap:.0f}%)")

print("\n" + "=" * 62)
print("EXACT DECOMPOSITION.  k = nu-fission / absorption, so")
print("  k_void/k_nom = (nuf ratio) / (abs ratio)")
rat = lambda t, a, b: t[b] / t[a]
kD = rat(D, "n_nuf", "v_nuf") / rat(D, "n_abs", "v_abs")
kO = rat(O, "n_nuf", "v_nuf") / rat(O, "n_abs", "v_abs")
print(f"\n{'':<34}{'DRAGON':>10}{'OpenMC':>10}{'diff pp':>10}")
print(f"{'k ratio on voiding':<34}{kD:>10.5f}{kO:>10.5f}"
      f"{100*(kO-kD):>+10.3f}")
pn = 100 * (rat(O, "n_nuf", "v_nuf") - rat(D, "n_nuf", "v_nuf"))
an = -100 * (rat(O, "n_abs", "v_abs") - rat(D, "n_abs", "v_abs"))
print(f"{'  contribution: nu-fission':<34}{'':>20}{pn:>+10.3f}")
print(f"{'  contribution: absorption':<34}{'':>20}{an:>+10.3f}")

print("\nand splitting the nu-fission term by nuclide "
      "(weighted by each nuclide's share):")
for nuc, kn, kv in (("U-235", "n_u5", "v_u5"), ("U-238", "n_u8", "v_u8")):
    shareD = D[kn] / D["n_nuf"]; shareO = O[kn] / O["n_nuf"]
    cD = 100 * (D[kv] - D[kn]) / D["n_nuf"]
    cO = 100 * (O[kv] - O[kn]) / O["n_nuf"]
    print(f"  {nuc}  share {shareO:.3f}   DRAGON {cD:+.3f} pp"
          f"   OpenMC {cO:+.3f} pp   diff {cO-cD:+.3f} pp")
print("\n=> the disagreement is a U-235 fission-production effect.")
print("   U-238 resonance capture differs too, but in the OPPOSITE direction")
print("   and at a tenth the size.")
