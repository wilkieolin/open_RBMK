# Fuel failure criteria for the 01:23:40 excursion (PROGRESS (47))

Thresholds in **peak radial-average fuel enthalpy**, as used by `tierb/RBMKCore.jl/test/fuel_diag.jl`.

| cal/g | J/g | what | applies to Unit 4? | source |
|---|---|---|---|---|
| ~120 | ≈500 | dispersal of irradiated fuel after PCMI-type cladding failure | lower bound only: needs > 40 MWd/kgU and PWR/BWR-type cladding; Unit 4 averaged ~10 MWd/kgU with Zr-1%Nb, which does not fail by PCMI in the tests | [NEA10] Ch. 7 |
| ~160 | ~670 | Zr-1%Nb cladding failure by high-temperature ballooning (pressurized rods), fresh and irradiated; pulses to 950 ms, no pulse-width effect | cladding breach WITHOUT significant fuel dispersal ([NEA10] 7.1.2); RBMK rods sit in 7 MPa coolant, so ballooning needs internal overpressure | [HOZ] 2.3 |
| 193–195 | ~810 | Vitanza / KAERI failure correlations at 10 MWd/kgU, 10 µm oxide | as above | [HOZ] eqs 4, 5 |
| 220 | 920 | "fuel elements begin to disintegrate" (T quoted 3300 K; with THM's UO₂ cp 220 cal/g is ~2800 K pellet average) | NSRR fresh fuel; INSAG-7 warns RBMK rods differ | INSAG-7 p. 67 |
| 240–270 | 1005–1130 | rod fragmentation (loss of rod geometry, guillotine cracks, partial dispersal) for fresh rods; IGR VVER: cladding failure and fragmentation together at 1130 | yes (fresh-like fuel, Zr-Nb) | [NEA10] Table 12 |
| 285–325 | 1190–1360 | molten UO₂ expelled into the coolant: violent FCI and pressure pulses | yes | [NEA10] 7.1.2; INSAG-7 285 "rupture", 320 "explode and disperse" |

Cladding temperature limits (design basis, RBMK-1000 Smolensk-3, TECDOC-722 Table 1): 1200 °C,
local oxidation ≤ 18 %, reacted Zr ≤ 1 % per GDH; operational mechanical integrity < 700 °C.

**Reading for the drum record (PROGRESS (46)).** The recorded post-AZ-5 pressure rise needs prompt
fuel-to-coolant heat transfer, i.e. fuel DISPERSED into the coolant. Cladding failure by
ballooning (~160 cal/g) does not provide it; fragmentation does, from ~240–270 cal/g, and violent
FCI from ~285–325. INSAG-7's 220 cal/g is therefore not an over-estimate for the mechanism the
record needs. No RBMK-specific pulse tests were found; the IGR/BIGR VVER data (Zr-1%Nb cladding,
long pulses) are the closest analogue.
