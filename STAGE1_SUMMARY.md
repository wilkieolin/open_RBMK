# Stages 1-2 Complete: Benchmark Validation

## Stage 1: IAEA-3D Benchmark (Static 3-D Diffusion)
**File**: `/home/wilkie/code/RBMK/5.1/Trivac/data/iaea3d.x2m`

| Metric | Computed | Reference | Error |
|--------|----------|-----------|-------|
| k-effective | 1.028980 | 1.029069 | **-8.9 pcm** |
| Power density max error | — | — | 3.36% |
| Power density avg error | — | — | 0.90% |

**Status**: ✅ PASSED - Excellent agreement with published values

## Stage 2: LMW 2-D Kinetics Benchmark (Space-Time Kinetics)
**File**: `/home/wilkie/code/RBMK/5.1/Trivac/data/Ktests.x2m` (includes LMW 2D test)

| Metric | Result |
|--------|--------|
| Transient type | Rod withdrawal over 26.7s |
| Initial power | ~21,471 MW |
| Final power | ~22,449 MW |
| Time step | 0.1s |
| KINSOL scheme | CRANK/CRANK |
| Test result | **PASSED** ("TEST SUCCESSFUL") |

**Status**: ✅ PASSED - Kinetics engine (`KINSOL:`) working correctly

## Verification Commands
```bash
# IAEA-3D
cd /home/wilkie/code/RBMK/5.1/Trivac
./rtrivac -c custom -p 1 -q iaea3d.x2m

# LMW 2D Kinetics (part of Ktests)
./rtrivac -c custom -p 1 -q Ktests.x2m
```

## Next: Stage 3 - DRAGON5 RBMK Cell Model
- Build RBMK lattice cell (25 cm pitch, 18-rod cluster, Zr-Nb pressure tube)
- Target: k_inf ~1.02-1.05 (fresh fuel)
- Use ENDF/B-VIII.0 99-group library from `/home/wilkie/code/RBMK/libraries/hdf5/`
