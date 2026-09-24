import numpy as np

# Region volumes from EDI output (cm^3)
volumes = np.array([
    5.77959E+01,  # 1: coolant
    2.31849E+01,  # 2: pressure tube
    5.63181E+00,  # 3: gap gas
    2.05887E+02,  # 4: calandria tube
    2.82783E+02,  # 5: graphite moderator
    1.17666E+00,  # 6: central fuel
    7.05999E+00,  # 7: inner ring fuel
    1.41200E+01,  # 8: middle ring fuel
    2.11800E+01,  # 9: outer ring fuel
    6.18066E+00,  # 10: sheath/cladding
])

# EDI reaction rates for 3 condensed groups (10 regions x 3 groups)
flux_g1 = np.array([3.52843E-07, 2.60987E-07, 2.50224E-07, 2.08116E-07, 1.59449E-07,
    4.71323E-07, 4.70250E-07, 4.63057E-07, 4.28624E-07, 4.23588E-07])
coll_g1 = np.array([1.33600E-06, 9.22509E-08, 2.88918E-11, 6.37972E-07, 5.22527E-06,
    1.19407E-07, 7.14809E-07, 1.40775E-06, 1.95460E-06, 3.89804E-08])
abs_g1 = np.array([1.50791E-07, -3.24656E-08, 6.41848E-17, -2.24091E-07, 3.84875E-07,
    -1.63894E-10, -9.81174E-10, -1.93234E-09, -2.68301E-09, -1.36921E-08])
nusigf_g1 = np.array([0.0, 0.0, 0.0, 0.0, 0.0,
    8.64564E-08, 5.17558E-07, 1.01928E-06, 1.41523E-06, 0.0])
scat_ww_g1 = np.array([4.05449E-07, 4.85603E-08, 6.76843E-12, 3.22784E-07, 2.13805E-06,
    6.31603E-08, 3.78100E-07, 7.44633E-07, 1.03389E-06, 1.97223E-08])
scat_og_g1 = np.array([7.79756E-07, 7.61562E-08, 2.21233E-11, 5.39279E-07, 2.70234E-06,
    5.64101E-08, 3.37690E-07, 6.65050E-07, 9.23393E-07, 3.29502E-08])

flux_g2 = np.array([1.74247E-06, 1.30112E-06, 1.25107E-06, 1.05422E-06, 8.26928E-07,
    2.31926E-06, 2.31404E-06, 2.27944E-06, 2.11235E-06, 2.08672E-06])
coll_g2 = np.array([6.90385E-06, 4.91768E-07, 1.66850E-10, 3.45685E-06, 2.70056E-05,
    5.74288E-07, 3.43796E-06, 6.77313E-06, 9.41496E-06, 2.05409E-07])
abs_g2 = np.array([8.01714E-07, -1.44972E-07, 1.37390E-15, -1.01467E-06, 1.21558E-06,
    3.58921E-09, 2.14866E-08, 4.23306E-08, 5.88416E-08, -6.02924E-08])
nusigf_g2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0,
    3.87110E-07, 2.31742E-06, 4.56556E-06, 6.34634E-06, 0.0])
scat_ww_g2 = np.array([1.75741E-06, 2.78423E-07, 4.32521E-11, 1.89338E-06, 1.15784E-05,
    2.84885E-07, 1.70546E-06, 3.35992E-06, 4.67044E-06, 1.12506E-07])
scat_og_g2 = np.array([4.34473E-06, 3.58317E-07, 1.23596E-10, 2.57813E-06, 1.42116E-05,
    2.85814E-07, 1.71102E-06, 3.37088E-06, 4.68568E-06, 1.53195E-07])

flux_g3 = np.array([3.07365E-01, 3.24980E-01, 3.25688E-01, 3.26254E-01, 3.27668E-01,
    2.84834E-01, 2.87134E-01, 2.93227E-01, 3.03123E-01, 2.97852E-01])
coll_g3 = np.array([1.57097E+01, 2.49434E-01, 6.65556E-05, 2.18644E+00, 3.18802E+01,
    1.60973E-01, 9.81689E-01, 2.04585E+00, 3.33603E+00, 5.92180E-02])
abs_g3 = np.array([4.29828E-02, 2.62988E-03, 2.66454E-12, 2.01208E-02, 5.99004E-03,
    1.88051E-02, 1.19136E-01, 2.70555E-01, 5.19341E-01, 4.38368E-04])
nusigf_g3 = np.array([0.0, 0.0, 0.0, 0.0, 0.0,
    2.08776E-02, 1.33245E-01, 3.08663E-01, 5.87966E-01, 0.0])
scat_ww_g3 = np.array([1.56667E+01, 2.46804E-01, 6.65556E-05, 2.16632E+00, 3.18742E+01,
    1.42168E-01, 8.62553E-01, 1.77529E+00, 2.81669E+00, 5.87796E-02])
scat_og_g3 = np.zeros(10)

# Combine groups 1+2 into fast group (flux-weighted)
flux_fast = flux_g1 + flux_g2
coll_fast = coll_g1 + coll_g2
abs_fast = abs_g1 + abs_g2
nusigf_fast = nusigf_g1 + nusigf_g2
scat_fast_fast = scat_ww_g1 + scat_ww_g2 + scat_og_g1  # within fast + g1->g2
scat_fast_therm = scat_og_g2  # g2->g3

# Thermal group = group 3
flux_therm = flux_g3
coll_therm = coll_g3
abs_therm = abs_g3
nusigf_therm = nusigf_g3
scat_therm_therm = scat_ww_g3
scat_therm_fast = scat_og_g3

# Compute per-region cross sections (rate / flux)
def safe_div(num, den):
    return np.where(den > 1e-30, num / den, 0.0)

total_fast = safe_div(coll_fast, flux_fast)
abs_fast_xs = safe_div(abs_fast, flux_fast)
abs_fast_xs = np.maximum(abs_fast_xs, 0.0)  # clamp negative to zero
nusigf_fast_xs = safe_div(nusigf_fast, flux_fast)
scat_ff = safe_div(scat_fast_fast, flux_fast)
scat_ft = safe_div(scat_fast_therm, flux_fast)

total_therm = safe_div(coll_therm, flux_therm)
abs_therm_xs = safe_div(abs_therm, flux_therm)
abs_therm_xs = np.maximum(abs_therm_xs, 0.0)
nusigf_therm_xs = safe_div(nusigf_therm, flux_therm)
scat_tt = safe_div(scat_therm_therm, flux_therm)
scat_tf = safe_div(scat_therm_fast, flux_therm)

# Mixture definitions
# Mixture 1 (FUEL CHANNEL): regions 1,2,3,6,7,8,9,10 (inside pressure tube)
# Mixture 2 (MODERATOR): regions 4,5 (calandria tube + graphite)
fuel_regions = [0, 1, 2, 5, 6, 7, 8, 9]  # 0-indexed
mod_regions = [3, 4]

def volume_weight(xs, region_indices):
    vol = volumes[region_indices]
    return np.sum(xs[region_indices] * vol) / np.sum(vol)

# Volume-weight cross sections (not diffusion coefficients!)
# Fuel mixture
total_fast_fuel = volume_weight(total_fast, fuel_regions)
abs_fast_fuel = volume_weight(abs_fast_xs, fuel_regions)
nusigf_fast_fuel = volume_weight(nusigf_fast_xs, fuel_regions)
scat_ff_fuel = volume_weight(scat_ff, fuel_regions)
scat_ft_fuel = volume_weight(scat_ft, fuel_regions)

total_therm_fuel = volume_weight(total_therm, fuel_regions)
abs_therm_fuel = volume_weight(abs_therm_xs, fuel_regions)
nusigf_therm_fuel = volume_weight(nusigf_therm_xs, fuel_regions)
scat_tt_fuel = volume_weight(scat_tt, fuel_regions)
scat_tf_fuel = volume_weight(scat_tf, fuel_regions)

# Moderator mixture
total_fast_mod = volume_weight(total_fast, mod_regions)
abs_fast_mod = volume_weight(abs_fast_xs, mod_regions)
nusigf_fast_mod = volume_weight(nusigf_fast_xs, mod_regions)
scat_ff_mod = volume_weight(scat_ff, mod_regions)
scat_ft_mod = volume_weight(scat_ft, mod_regions)

total_therm_mod = volume_weight(total_therm, mod_regions)
abs_therm_mod = volume_weight(abs_therm_xs, mod_regions)
nusigf_therm_mod = volume_weight(nusigf_therm_xs, mod_regions)
scat_tt_mod = volume_weight(scat_tt, mod_regions)
scat_tf_mod = volume_weight(scat_tf, mod_regions)

# Compute diffusion coefficients from volume-weighted XS
sigtr_fast_fuel = total_fast_fuel - 0.5 * scat_ff_fuel
sigtr_therm_fuel = total_therm_fuel - 0.5 * scat_tt_fuel
diff_fast_fuel = 1.0 / (3.0 * sigtr_fast_fuel)
diff_therm_fuel = 1.0 / (3.0 * sigtr_therm_fuel)

sigtr_fast_mod = total_fast_mod - 0.5 * scat_ff_mod
sigtr_therm_mod = total_therm_mod - 0.5 * scat_tt_mod
diff_fast_mod = 1.0 / (3.0 * sigtr_fast_mod)
diff_therm_mod = 1.0 / (3.0 * sigtr_therm_mod)

print("=== Volume-weighted 2-mixture cross sections (CORRECTED) ===")
print("\nMixture 1 (FUEL CHANNEL):")
print(f"  FAST:  TOTAL={total_fast_fuel:.6e} ABS={abs_fast_fuel:.6e} NUSIGF={nusigf_fast_fuel:.6e}")
print(f"         SCAT_F->F={scat_ff_fuel:.6e} SCAT_F->T={scat_ft_fuel:.6e} DIFF={diff_fast_fuel:.6e}")
print(f"  THERM: TOTAL={total_therm_fuel:.6e} ABS={abs_therm_fuel:.6e} NUSIGF={nusigf_therm_fuel:.6e}")
print(f"         SCAT_T->T={scat_tt_fuel:.6e} SCAT_T->F={scat_tf_fuel:.6e} DIFF={diff_therm_fuel:.6e}")

print("\nMixture 2 (MODERATOR):")
print(f"  FAST:  TOTAL={total_fast_mod:.6e} ABS={abs_fast_mod:.6e} NUSIGF={nusigf_fast_mod:.6e}")
print(f"         SCAT_F->F={scat_ff_mod:.6e} SCAT_F->T={scat_ft_mod:.6e} DIFF={diff_fast_mod:.6e}")
print(f"  THERM: TOTAL={total_therm_mod:.6e} ABS={abs_therm_mod:.6e} NUSIGF={nusigf_therm_mod:.6e}")
print(f"         SCAT_T->T={scat_tt_mod:.6e} SCAT_T->F={scat_tf_mod:.6e} DIFF={diff_therm_mod:.6e}")

# Donjon MAC: READ INPUT format
print("\n=== Donjon MAC: READ INPUT format ===")
print("MACRO := MAC: READ INPUT ::")
print("  NMIX 2")
print("  NGROUP 2")
print("  MIX 1")
print(f"  DIFF {diff_fast_fuel:.6e} {diff_therm_fuel:.6e}")
print(f"  TOTAL {total_fast_fuel:.6e} {total_therm_fuel:.6e}")
print(f"  ABS {abs_fast_fuel:.6e} {abs_therm_fuel:.6e}")
print(f"  NUSIGF {nusigf_fast_fuel:.6e} {nusigf_therm_fuel:.6e}")
print(f"  SCAT 2 2  {scat_ft_fuel:.6e} {scat_ff_fuel:.6e}  2 2  {scat_tt_fuel:.6e} {scat_tf_fuel:.6e}")
print("  MIX 2")
print(f"  DIFF {diff_fast_mod:.6e} {diff_therm_mod:.6e}")
print(f"  TOTAL {total_fast_mod:.6e} {total_therm_mod:.6e}")
print(f"  ABS {abs_fast_mod:.6e} {abs_therm_mod:.6e}")
print(f"  NUSIGF {nusigf_fast_mod:.6e} {nusigf_therm_mod:.6e}")
print(f"  SCAT 2 2  {scat_ft_mod:.6e} {scat_ff_mod:.6e}  2 2  {scat_tt_mod:.6e} {scat_tf_mod:.6e}")
print("  ;")

