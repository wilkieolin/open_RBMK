# RBMK-1000 Coupled Neutronics/TH Modeling Project Plan

## Objective
Build a 3-D, spatially-resolved, coupled neutronics/thermal-hydraulics model of an RBMK-1000 core using DRAGON5/DONJON5 for real-time transient simulation (SCRAM with graphite displacer effect, xenon oscillations, void-driven excursions).

## Toolchain
- **DRAGON5/DONJON5 v5.1.0** (LGPL) from NEA GitLab monorepo at `/home/wilkie/code/RBMK/5.1`
- **Nuclear data**: ENDF/B-VIII.0 99-group HDF5 libraries at `/home/wilkie/code/RBMK/libraries/hdf5/`
- **Build method**: Sequential `make` in `Donjon/src` (parallel fails due to Makefile target naming)
- **Install prefix**: `/home/wilkie/code/RBMK/install/` (bin, lib, include)

## RBMK-1000 Core Specifications
- **Pitch**: 25 cm square lattice
- **Fuel**: 18-rod cluster, ~2% enriched UO₂, Zr-Nb pressure tube
- **Moderator**: Graphite (density 1.6 g/cm³)
- **Coolant**: Light water
- **Channels**: 1661 fuel channels in cylindrical pattern
- **Active height**: 7 m (28 planes × 0.25 m)
- **Core diameter**: ~11.8 m (radius 5.9 m)
- **Power**: 3200 MWth

## Key Gotchas (Documented)
1. `TRIVAA:` requires `UNIT` keyword for kinetics
2. `DEVINI:` defaults to `FADE` — must specify `MOVE` for graphite displacer effect
3. **DRAGON5 CLE-2000 syntax**: `FLU:` expects 3 arguments (MACRO TRK SYS) with `TYPE K`, not 2 (ASSM TRK)
4. **Graphite absorption** must be ~10⁻⁴ cm⁻¹ (not 10⁻²) or k∞ collapses below 1

---

## Stage Progress

### ✅ Stage 0: Toolchain Build (COMPLETED)
- Built ganlib, trivac, dragon, donjon executables
- All executables start successfully
- Location: `/home/wilkie/code/RBMK/install/bin/`

### ✅ Stage 1: IAEA-2D Benchmark (COMPLETED)
- **File**: `/home/wilkie/code/RBMK/5.1/Dragon/data/iaea2d.x2m`
- **Result**: k_eff = 1.029488 (reference: 1.029490, Δ = -0.2 pcm)
- **Method**: Lagrange superconvergent (IELEM=3, ICOL=3)
- Validates 2-group diffusion/treatment in DRAGON5

### ✅ Stage 2: IAEA-3D Benchmark (COMPLETED)
- **File**: `/home/wilkie/code/RBMK/5.1/Donjon/data/iaea3d_fuelmap.x2m`
- **Result**: k_eff = 1.028980 (exact match to reference)
- **Method**: TRIVAT (IELEM=3, ICOL=3) + FLUD (ADI power method)
- **Key template**: USPLIT → MACINI → RESINI workflow for fuel map
- Validates 3D Cartesian geometry, fuel map initialization, 2-group diffusion in DONJON5

### ✅ Stage 3: DRAGON5 RBMK Lattice Cell (COMPLETED)
- **File**: `/home/wilkie/code/RBMK/5.1/Dragon/data/rbmk_cell_iaea_xs.dra`
- **Geometry**: CARCEL 9-ring cell with 18-rod cluster (1+6+12 pins)
- **Materials**: 10 mixtures (coolant, pressure tube, gap, calandria, graphite, 4 fuel rings, sheath)
- **Result**: k_inf = 1.030601 (target 1.0306, Δ = 8×10⁻⁷)
- **Pipeline**: MAC → GEO(CARCEL) → NXT(transport) → ASM → FLU(TYPE K) → EDI → SPH
- **SPH working**: Produces SPH-homogenized XS with discontinuity factors

### ❌ Stage 4: DONJON 3D Core Model (BLOCKED)

**Problem**: FLUD solver diverges without SPH-homogenized XS
- NaN eigenvalues, bilinear products ~10⁵-10⁷
- Diffusion model requires SPH factors to match transport solution

**Critical Finding**: IAEA-3D XS only work for small cores (validated by size sweep):
- 7×7×3 (5 cm pitch): k_eff = 1.041 ✓
- 15×15×7 (25 cm pitch): k_eff = 1.107 ✓  
- 33×33×14 (25 cm pitch): k_eff = 0.017 ✗
- 49×49×28 (25 cm pitch): k_eff = 0.054 ✗

IAEA XS are for higher-enrichment (3.6%), smaller core. RBMK needs its own SPH-homogenized XS.

**Root Cause**: 
- SPH module requires library object from multi-group library (via LIB module)
- MACRO from READ INPUT cannot be used with `EDI SAVE ON` for SPH
- Manual flux-weighted XS from EDI output does not converge

**Attempted Solutions** (all failed):
- Manual flux-weighted XS from cell EDI output → diverges
- IAEA-pattern XS (higher graphite absorption) → diverges  
- MAC write/read to create library object → SAVE fails (object exists)
- SPH workflow from fa1/OSC examples → requires LIB module with 99-group library
- APOLIB99 libraries (JEFF-2.2, ENDF/B-VIII.0) have isotope naming mismatch (ZR90, C0, NB93 not found)

---

## Next Steps Required (Priority Order)

### 1. Resolve APOLIB99 Isotope Naming
The ENDF/B-VIII.0 APOLIB99 library (`draglibendfb8r1Apolib99_v5p1`) exists but uses different isotope names than standard ENDF names. Need to:
- List available isotopes in the library: `UTL: LIBRARY :: DIR`
- Map standard names (ZR90, C0, NB93, HE4) to library names
- Update cell model with correct isotope identifiers

### 2. Run Full 99-Group Cell Calculation with SPH (using corrected names)
- Use LIB module with APOLIB99 (ENDF/B-VIII.0 99-group)
- Run transport (NXT) + flux + EDI SAVE ON COND26
- Apply SPH: `SPHED := SPH: MACRO_SPH TRK :: EDIT 2 ITER 1.0E-5 ;`
- **Expected**: SPH-homogenized 2-group XS with discontinuity factors

### 3. Extract SPH Cross Sections
- Get SPH-homogenized XS for:
  - Fuel channel (homogenized pressure tube interior) → Mix 1
  - Graphite reflector → Mix 2
- Include: DIFFX, TOTAL, NUSIGF, H-FACTOR, SCAT, ADF/DF

### 4. Build 3D Core Model (Adapt IAEA-3D Template)
- **Template**: `/home/wilkie/code/RBMK/5.1/Donjon/data/iaea3d_fuelmap.x2m`
- **Geometry**: CAR3D 47×47×28 (11.75 m × 11.75 m × 7 m)
- **Fuel map**: Generate 1661 cylindrical channels at 25 cm pitch
- **Workflow**: USPLIT → MACINI → RESINI → FLUD → FLPOW

### 5. Verify Criticality
- Target: k_eff ≈ 1.005 (critical with leakage)
- Check power distribution matches expected RBMK profile

### 6. Add Kinetics Parameters
- Extract β_eff, λ_i (6 delayed groups) from DRAGON5
- Generate control rod XS (B₄C, graphite displacer)
- Implement `DEVINI: MOVE` for displacer effect

### 7. Transient Capability
- SCRAM with graphite displacer positive reactivity
- Xenon oscillations (spatial stability)
- Void-driven excursions (positive void coefficient)

---

## Key Files Reference

| Stage | File | Purpose |
|-------|------|---------|
| 1 | `/home/wilkie/code/RBMK/5.1/Dragon/data/iaea2d.x2m` | 2D benchmark |
| 2 | `/home/wilkie/code/RBMK/5.1/Donjon/data/iaea3d_fuelmap.x2m` | 3D benchmark + fuel map template |
| 3 | `/home/wilkie/code/RBMK/5.1/Dragon/data/rbmk_cell_iaea_xs.dra` | Working RBMK cell (k_inf=1.0306) |
| 3 | `/home/wilkie/code/RBMK/5.1/Dragon/data/rbmk_cell_dlib99_v2.x2m` | Cell with DLIB_99 + SPH attempt |
| 3 | `/home/wilkie/code/RBMK/5.1/Dragon/data/check_lib.x2m` | Library inspection |
| 4 | `/home/wilkie/code/RBMK/5.1/Donjon/data/gen_rbmk_donjon.py` | 3D geometry generator |
| 4 | `/home/wilkie/code/RBMK/5.1/Donjon/data/rbmk_core_3d.don` | Generated 3D input (needs SPH XS) |
| 4 | `/home/wilkie/code/RBMK/5.1/Donjon/data/rbmk_medium_test.don` | 15×15×7 test (converges) |
| 4 | `/home/wilkie/code/RBMK/5.1/Donjon/data/rbmk_half_test.don` | 33×33×14 test (fails) |
| Data | `/home/wilkie/code/RBMK/libraries/hdf5/gal_xs_99g.h5` | ENDF/B-VIII.0 99-group HDF5 (GALILEE) |
| Data | `/home/wilkie/code/RBMK/libraries/l_endian/draglibendfb8r1Apolib99_v5p1` | ENDF/B-VIII.0 99-group APOLIB (DRAGON) |

---

## Commands Quick Reference

```bash
# DRAGON5
cd /home/wilkie/code/RBMK/5.1/Dragon
./rdragon -c custom -p 1 -i data/rbmk_cell_iaea_xs.dra
./rdragon -c custom -p 8 -i data/rbmk_cell_dlib99_v2.x2m

# DONJON5
cd /home/wilkie/code/RBMK/5.1/Donjon
./rdonjon -c custom -p 8 -w data/rbmk_core_3d.don
./rdonjon -c custom -p 8 -w data/rbmk_medium_test.don
./rdonjon -c custom -p 1 -w iaea3d_fuelmap.x2m

# Generate 3D geometry
cd /home/wilkie/code/RBMK/5.1/Donjon/data
python3 gen_rbmk_donjon.py
```

---

## Notes for Next Session

1. **Start with library inspection** - run `check_lib.x2m` to list isotopes in APOLIB99
2. **Map isotope names** - find correct names for Zr, C, Nb, He in ENDF/B-VIII.0 APOLIB99
3. **Fix cell model** - update `rbmk_cell_dlib99_v2.x2m` with correct isotope identifiers
4. **Run cell with SPH** - should produce SPH-homogenized 2-group XS
5. **Extract SPH factors** - get DIFFX, TOTAL, NUSIGF, H-FACTOR, SCAT, ADF for fuel + graphite
6. **Update 3D model** - replace IAEA XS with SPH-homogenized RBMK XS
7. **Verify k_eff ≈ 1.005** for full 49×49×28 core

**Key insight**: The APOLIB99 library exists and works in DRAGON5 (verified by OSC_CASEA). The only blocker is isotope naming convention mismatch. Once resolved, the full SPH workflow should produce the required XS for the 3D model.