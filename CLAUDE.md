# CLAUDE.md — RBMK-1000 / Chernobyl Unit 4

A 3-D coupled neutronics / thermal-hydraulics model of an RBMK-1000, built to reproduce the AZ-5
transient of 26 April 1986 from sourced inputs and, ultimately, to say with uncertainty whether
and where the fuel failed. Scope stops at fuel failure.

- **Tier A** — DRAGON5 lattice + DONJON5 core (Fortran, the `5.1` submodule, patched from
  `patches/`), cross-checked against OpenMC. The DONJON "band" of AZ-5 transients is the
  reference set for Tier B.
- **Tier B** — `tierb/RBMKCore.jl`: a Julia/CUDA engine (RT0 mixed-dual kinetics on the GPU,
  the THM port, a simultaneous-Newton channel solver, a core-wide loop model, post-CHF heat
  transfer). Verified against Tier A (gates B0–B4 passed), then new physics.
- **Tier C** — a real-time mnemonic panel driven by Tier B. Not started.

## Tracking: the kanban board

Work is tracked as cards in `kanban/` with the **kanban-ai** skill (`.claude/skills/kanban-ai/`).
- Open work: `kanban/*.md`; completed milestones: `kanban/archived/*.md` (status `done`).
- View: `bash .claude/skills/kanban-ai/scripts/view_board.sh kanban/` (the scripts read only the
  top level; run them on `kanban/archived/` for done cards).
- New ids: max + 1 over `kanban/` **and** `kanban/archived/`.
- Every result goes into the card's `## Narrative` (dated, append-only; never rewrite old entries),
  with the numbers, the files/stems that produced them, and anything it retracts.
- Tags in use: `tier-a tier-b tier-c neutronics th loop fuel chf sourcing uq numerics infra gpu
  openmc rods xenon burnup`.

`docs/history/PROGRESS.md` is the **frozen** detailed log of sections (1)–(49) (to 2026-10-24).
Code comments cite it as "PROGRESS (n)"; the done cards summarise it and point into it. Do not
append to it. The retired plans (`TIER_A/B_WORKPLAN`, `PROJECT_PLAN`, …) are in `docs/history/`.

## Machine and process rules (hard)

- **DGX Spark GB10, ~110–120 GB unified CPU/GPU memory.** Analyse memory before any non-trivial
  GPU job; exceeding it pages to disk and locks the machine (hard reset). Never form a dense core
  matrix (it would be ~277 GB).
- Every GPU Julia run sets `JULIA_CUDA_HARD_MEMORY_LIMIT=8GiB` (CUDA.jl's pool otherwise grows
  without bound on unified memory).
- **The machine is shared**: other jobs (not ours) can hold 35–66 GB. Before launching, check
  `MemAvailable` and `nvidia-smi`; keep about 4 of our ~10 GB coupled runs at most; guard long
  queues (kill our newest *resumable* run if `MemAvailable` < 8–12 GB). Loop runs checkpoint every
  50 steps (`B4_RESUME=1`, `B4_CKPT_FILE` when the driver source has changed since).
- **Never kill by pattern** (`pkill -f`, `killall`): find PIDs in one command, kill by PID in
  another; Julia may ignore SIGTERM — use `kill -9` and verify.
- Long runs: `setsid nohup … &` with a log in the session scratchpad; wait with background
  until-loops, not foreground sleeps.
- **DONJON (`rdonjon`) runs one at a time.**
- Do not use the old "spark" machine.
- `5.1` is an upstream submodule (shows as modified because `decks/` is linked into it): never
  commit it. Our Fortran changes live in `patches/` (applied by `tools/apply_patches.sh`).
- `atomas.ru` is blocked by DNS policy; do not circumvent it.
- Commit to branch `tier-a/a6` and push. Commit messages end with the session's
  `Co-Authored-By:` / `Claude-Session:` trailer.

## Scientific rules

- **No tuned constants.** Every value is sourced (`sources/`, registered in `sources/README.md`,
  derived numbers in `sources/derived/`) or computed. Unsourced choices are labelled
  ASSUMPTION and bracketed for B5, never fitted.
- **The post-AZ-5 record is a check, not a fit.** Condition only on pre-AZ-5 data (the t = 0
  shapes, the 01:22:30 rod pattern, DREG to 01:23:40).
- **Content-addressed everything.** Deck stems carry digests of their inputs; caches carry the
  digest of what they depend on; a result must postdate its deck.
- Standing rules (from the log):
  1. Every asserted value comes from a calculation, never from a constant chosen to make it pass.
  2. Every deck verifies what it actually built, not what it was meant to build.
  3. A DRAGON error message is a statement about the input until proven otherwise.
  4. No physics number is validated until a second, independent method reproduces it.
  5. A `.result` is not evidence unless it postdates the deck (delete before re-running;
     `cd X && cmd &` runs the `cd` in the background subshell).
  6. A fix that lives in a copy of the file is not a fix.
  7. A cache without a key is a silent substitution.
- A new option must leave every existing result unchanged when off (check byte-identical
  outputs, e.g. a 30-step `b4_coupled.jl` trace, or `cmp` a regenerated deck).
- Report retractions in the card that made the claim and in the card that finds the error.

## Where things are

| path | what |
|---|---|
| `decks/Donjon/data/gen_rbmk_unit4.py` | the Unit 4 core-deck generator (env `U4_*`; the stem encodes them) |
| `decks/` | canonical DRAGON/DONJON input, symlinked into `5.1/` by `tools/link_decks.sh` |
| `patches/` | DONJON/THM/Ganlib patches 0001–0015 |
| `sources/`, `sources/README.md`, `sources/derived/` | source PDFs (gitignored), the register, digitised/derived data |
| `tools/` | bootstrap, exports (`tierb_export_xs.py`, `tierb_kinref.py`), digitisers, analysis |
| `tierb/RBMKCore.jl/src/` | `XS`, `CoreModel` (Core.jl), `Mixed`/`DualKinetics`/`GPUDual` (kinetics), `Channel` (THM port + post-CHF), `Column` (Newton channel), `Loop` (drums, pumps, legs), `IF97` |
| `tierb/RBMKCore.jl/test/` | gate tests and drivers: `b4_coupled.jl`, `loop_setup.jl`, `fuel_diag.jl`, `shape_diag.jl`, `chf_single.jl`, `drum_energy_bound.jl` |
| `tierb/xs/<stem>_tbd0/` | per-deck t = 0 dumps (`fmap0.asc`) and every B4 output for that deck |
| `openmc/` | Monte Carlo cross-check; distilled numbers in `openmc/*.json` |
| `kanban/`, `docs/history/` | tracking; retired plans and the frozen log |

## How to run (Tier B)

The band-B AZ-5 deck stem:
`rbmk_unit4_a7_acco668_pc99b7f3_dev_axf527ca_kin700v40g12shvdfr025fi60cc01dt001_vB65c86e_cB4af83e`.

- Regenerate a deck: set the generator environment (see the stem's suffixes; `U4_AXBURN` must be
  the **absolute** path for the `axf527ca` digest) and run the generator; check a known deck
  regenerates byte-identical before changing an input.
- t = 0 dump for a new deck: `python3 tools/tierb_kinref.py <stem> --dual --t0only` (DONJON,
  ~5 min) → `tierb/xs/<stem>_tbd0/fmap0.asc`.
- Coupled AZ-5 transient (from `tierb/RBMKCore.jl`):
  `JULIA_CUDA_HARD_MEMORY_LIMIT=8GiB B4_TH=<thmtrs|newton|loop> julia --project=. -t 5 test/b4_coupled.jl <stem> tierb/xs/<stem>_tbd0 700 0.01`
  - loop: `DRUM_TAU` (s; two-region drum), `B4_VST` (m³), `B4_QG` (MW), `B4_HSH`, `B4_FREEZE`,
    `LOOP_WREC=1` (recorded pre-AZ-5 flow), `LOOP_PSD_GAUGE=1`; pre-runs are cached by content.
  - `B4_CHF=1` (post-CHF), `B4_CHFMUL`, `B4_ZRSEC=1`, `B4_CLAMP=1` (T-FUEL held at 2000 K: an
    upper estimate after it).
  - outputs per run: `b4_trace_*`, `b4_fuel_*` (failure criteria, dry nodes), `b4_shape_*`
    (Kv/Kr/Kz, adiabatic energy), `b4_pw_*.bin`, `b4_loop_*`.
  - Costs: newton ~2 h, loop ~4–6 h (≈10 GB each).
- Single-channel CHF check: `julia --project=. test/chf_single.jl <stem> <dumpdir> <channel> [chfmul]`.
