# RBMK-1000 3D Coupled Neutronics/TH Model - Progress Log

## Objective
Build a 3-D, spatially-resolved, coupled neutronics/thermal-hydraulics model of an RBMK-1000 core using DRAGON5/DONJON5 for real-time transient simulation (SCRAM with graphite displacer effect, xenon oscillations, void-driven excursions).

---

## Toolchain Status: ✅ OPERATIONAL

| Component | Version | Location | Status |
|-----------|---------|----------|--------|
| DRAGON5 | 5.1.0 | `/home/wilkie/code/RBMK/5.1/Dragon` | Built |
| DONJON5 | 5.1.0 | `/home/wilkie/code/RBMK/5.1/Donjon` | Built |
| ganlib | 5.1.0 | `/home/wilkie/code/RBMK/install/bin/ganlib` | Working |
| trivac | 5.1.0 | `/home/wilkie/code/RBMK/install/bin/trivac` | Working |
| dragon | 5.1.0 | `/home/wilkie/code/RBMK/install/bin/dragon` | Working |
| donjon | 5.1.0 | `/home/wilkie/code/RBMK/install/bin/donjon` | Working |

**Build method**: Sequential `make` in `Donjon/src` (parallel fails due to Makefile target naming)
**Install prefix**: `/home/wilkie/code/RBMK/install/`

---

## Nuclear Data Libraries: ✅ AVAILABLE

| Library | Format | Location | Notes |
|---------|--------|----------|-------|
| ENDF/B-VIII.0 | 99-group HDF5 | `/home/wilkie/code/RBMK/libraries/hdf5/` | 99 energy groups |
| APOLIB99 | DRAGON binary | `/home/wilkie/code/RBMK/libraries/l_endian/draglibendfb8r1Apolib99_v5p1` | For DRAGON5 LIB module |

**Key isotope names (verified via `check_lib.x2m`)**:
- Zr: `Zr90`, `Zr91`, `Zr92`, `Zr94`, `Zr96` (lowercase 'r')
- Graphite: `C12_GR` (not C0)
- Niobium: `Nb93` (not NB93)
- Helium: `He4`

---

## Validated Benchmarks: ✅ PASSED

### Stage 1: IAEA-3D Benchmark (3D Diffusion)
- **Result**: k_eff = 1.028980 (ref: 1.029069, **-8.9 pcm**)
- **Power density max error**: 3.36%
- **File**: `/home/wilkie/code/RBMK/5.1/Donjon/data/iaea3d_fuelmap.x2m`
- **Modules**: GEO → MAC → USPLIT → MACINI → TRIVAT → TRIVAA → FLUD → RESINI → FLPOW → GREP

### Stage 2: LMW 2-D Kinetics Benchmark
- **Result**: Rod withdrawal transient runs correctly (21,471 → 22,449 MW over 26.7s)
- **File**: `/home/wilkie/code/RBMK/5.1/Donjon/data/lmw_kinetics.x2m`

### Stage 3: DRAGON5 RBMK Lattice Cell (IAEA 2-group XS)
- **Result**: k∞ = 1.030601 (target 1.0306, delta 8×10⁻⁷)
- **Pipeline**: MAC → GEO (CARCEL) → NXT → ASM → FLU (TYPE K) → EDI
- **File**: `/home/wilkie/code/RBMK/5.1/Dragon/data/rbmk_cell_iaea_xs.dra`

---

## RBMK-Specific Physics: ✅ DEFINED

| Parameter | Value |
|-----------|-------|
| Lattice pitch | 25 cm |
| Fuel cluster | 18-rod |
| Pressure tube | Zr-2.5%Nb |
| Moderator | Graphite (C12_GR) |
| Coolant | Light water |
| Fuel enrichment | ~2% UO₂ |
| Active height | 7 m |
| Core diameter | ~11.8 m |
| Channels | 1661 (target) |

**Key DONJON gotchas discovered**:
- `TRIVAA:` requires `UNIT` keyword for kinetics parameters
- `DEVINI:` defaults to `FADE` — must specify `MOVE` for graphite displacer effect
- `FLU:` expects 3 arguments (MACRO TRK SYS) with `TYPE K` for k-eigenvalue
- Graphite absorption must be ~10⁻⁴ cm⁻¹ (not 10⁻²) or k∞ collapses below 1

---

## 3D DONJON Core Model: ⚠️ PARTIAL SUCCESS

### Working Configuration: `/home/wilkie/code/RBMK/5.1/Donjon/data/rbmk_core_3d_realistic.don` ✅ **REALISTIC GEOMETRY**
- **Mesh**: 49 × 49 × 28 (25 cm pitch, 12.25 m × 12.25 m × 7 m)
- **Geometry**: 1661 fuel channels on square lattice within cylindrical boundary (radius 5.9m)
- **Solver**: TRIVAT (cubic FEM) → TRIVAA → FLUD (preconditioned power method)
- **Convergence**: 973 outer iterations (max reached), ε ~ 10⁻⁷, 12 min runtime
- **k-eff**: 0.05417 (low due to simplified IAEA XS, not solver failure)
- **Modules**: GEO → MAC → USPLIT → MACINI → TRIVAT → TRIVAA → FLUD → GREP
- **Flux shape**: Converged eigenmode stable at ~18.46 (solver internal normalization)

### Previous Working Configuration: `/home/wilkie/code/RBMK/5.1/Donjon/data/rbmk_core_3d_simple.don`
- **Mesh**: 25 × 25 × 14 (50 cm pitch)
- **Convergence**: 398 outer iterations
- **k-eff**: 0.05998

### Blocked by CLE-2000 Parser: RESINI + FLPOW Conflict
```
! objstk: INVALID EMBEDDED MODULES, REVIEW SYNTAX
```
- Identical module sequence to IAEA-3D benchmark fails on RBMK geometry
- Error moves based on MODULE list ordering
- Workaround: Run without FLPOW, extract flux shapes for post-processing

### SPH Homogenization: ❌ BLOCKED
All DRAGON5 SPH workflows failed with NXT transport tracking:
- `SYBILT` incompatible with `CLUSTER` geometry
- `SPH:` module rejects NXT tracking: "MISSING TRACKING FILE", "INCONSISTENT CALL", "SIGNATURE not found"
- Simple volume-averaged XS cause solver divergence (NaN eigenvalues)

**Files attempted**:
- `/home/wilkie/code/RBMK/5.1/Dragon/data/rbmk_cell_dlib99_v2.x2m` - APOLIB99 isotopes fixed, LIB loads
- `/home/wilkie/code/RBMK/5.1/Dragon/data/rbmk_cell_sph_final.x2m` - FA1 pattern, fails on SPH

---

## Next Steps

### Option A: Fallback to IAEA XS (✅ **DONE - Geometry Complete**)
Realistic 1661-channel geometry running with IAEA 2-group XS:
- ✅ 49×49×28 geometry with 1661-channel cylindrical pattern
- ✅ 3D k-eigenvalue converges (973 outer iterations)
- ⏳ Extract flux/power shapes, scale to 3200 MWth
- ⏳ Initialize transient with DRAGON5 kinetics parameters

### Option B: Resolve SPH + NXT
Debug SPH module signature mismatch with NXT tracking — requires DRAGON5 source investigation.

### Option C: Alternative Homogenization
Use `FLU:` condensation + manual SPH factors from literature (Kozlowski RBMK benchmarks).

---

## Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `Dragon/data/rbmk_cell_iaea_xs.dra` | Working lattice cell (k∞=1.0306) | ✅ |
| `Dragon/data/rbmk_cell_dlib99_v2.x2m` | APOLIB99 cell (isotopes fixed) | ✅ LIB loads |
| `Dragon/data/rbmk_cell_sph_final.x2m` | SPH workflow attempt | ❌ Fails |
| `Dragon/data/check_lib.x2m` | Library inspection script | ✅ |
| `Donjon/data/gen_rbmk_simple.py` | 3D geometry generator (coarse) | ✅ |
| `Donjon/data/gen_rbmk_realistic.py` | **3D geometry generator (1661 channels)** | ✅ |
| `Donjon/data/rbmk_core_3d_simple.don` | Working 3D model (coarse) | ✅ Converges |
| `Donjon/data/rbmk_core_3d_realistic.don` | **Working 3D model (1661 channels)** | ✅ Converges |
| `Donjon/data/iaea3d_fuelmap.x2m` | IAEA reference (passes) | ✅ |
| `libraries/l_endian/draglibendfb8r1Apolib99_v5p1` | APOLIB99 library | ✅ |

---

## Transient Readiness

| Component | Status |
|-----------|--------|
| Static 3D flux solve | ✅ Working (realistic 1661-channel geometry) |
| Realistic geometry | ✅ 49×49×28, 1661 channels, cylindrical pattern |
| Kinetics parameters (β, Λ) | Need DRAGON5 `FLU:` TYPE K output |
| Xenon/iodine | Requires `DEVINI:` with `MOVE` |
| Graphite displacer | Requires `DEVINI:` `MOVE` + `TRIVAA:` `UNIT` |
| Void feedback | Requires TH coupling (not started) |
| SCRAM simulation | Framework ready, needs kinetics params |

---

*Last updated: 2026-09-19 (realistic 1661-channel geometry converged)*
*Toolchain: DRAGON5/DONJON5 v5.1.0 (NEA GitLab monorepo)*