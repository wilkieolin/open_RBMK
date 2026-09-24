# Stage 0 Complete: DRAGON5/DONJON5 Toolchain Built

*(Paths in this document are relative to the repository root.)*

## Build Summary
- **Source**: `5.1` (monorepo v5.1.0)
- **Install prefix**: `install`
- **Build method**: Native Makefiles (sequential build required due to Makefile target naming)

## Built Components
| Component | Executable | Library | Status |
|-----------|-----------|---------|--------|
| GANLIB5 | `ganlib` | `libGanlib.a` | ✅ Built, 3/4 tests pass |
| UTILIB5 | (library only) | `libUtilib.a` | ✅ Built |
| TRIVAC5 | `trivac` | `libTrivac.a` | ✅ Built |
| DRAGON5 | `dragon` | `libDragon.a` | ✅ Built, executable starts |
| DONJON5 | `donjon` | `libDonjon.a` | ✅ Built, executable starts |

## Nuclear Data Libraries (Pre-installed)
Location: `libraries/`
- `hdf5/gal_xs_99g.h5` - 99-group cross sections (~318 MB)
- `hdf5/gal_ss_99g.h5` - Self-shielding library (~60 MB)
- `hdf5/gal_bateman_99g.h5` - Bateman depletion (~0.3 MB)
- `ascii/SECLIB_XSM_NEW` - ASCII format library

## Known Issues
1. **Ganlib testgan4 (HDF5)**: Fails with "INVALID IPARAM (8)" - likely HDF5 version/test data mismatch
2. **Parallel build**: Fails due to Makefile target naming (`$(lib_module)/` vs `$(lib_module)`)
3. **Dragon/Donjon test data**: Non-regression test inputs not included in monorepo
4. **ARMI plugin**: Requires Terrapower's internal `armi` package (not on PyPI)

## Verification Commands
```bash
# Test executables start
echo "END" | install/bin/dragon
echo "END" | install/bin/donjon

# Run Ganlib tests
cd 5.1/Ganlib
./rganlib -c custom -p 1 -q testgan1.x2m  # ✅ PASS
./rganlib -c custom -p 1 -q testgan2.x2m  # ✅ PASS
./rganlib -c custom -p 1 -q testgan3.x2m  # ✅ PASS
```

## Next Steps (Stage 1: IAEA-3D Benchmark)
1. Create IAEA-3D benchmark input for DONJON5
2. Run static 3-D diffusion calculation
3. Verify k_eff and power distribution match published values

## Environment Setup for Stage 1+
```bash
export PATH="$PWD/install/bin:$PATH"
export LD_LIBRARY_PATH="$PWD/install/lib:$LD_LIBRARY_PATH"
export DRAGON_LIBRARY_PATH="$PWD/libraries/hdf5"
```
