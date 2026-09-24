# RBMK-1000 / Chernobyl Unit 4

A 3-D spatially-resolved coupled neutronics / thermal-hydraulics model of an
RBMK-1000, built to reproduce the AZ-5 transient of 26 April 1986 and to drive a
historically accurate mnemonic display: 1661 channel outlet temperatures, 211 rod
positions, in-core detector readings. Scope stops at fuel failure.

Physics is DRAGON5 (lattice) and DONJON5 (core), cross-checked against OpenMC.
Current status, results and next steps: **[`docs/report.html`](docs/report.html)**,
with the working log in [`PROGRESS.md`](PROGRESS.md) and the roadmap in
[`PROJECT_PLAN.md`](PROJECT_PLAN.md) / [`TIER_A_WORKPLAN.md`](TIER_A_WORKPLAN.md).

## Clean clone

```sh
git clone <url> RBMK
cd RBMK
./tools/bootstrap.sh            # add --no-openmc to skip the 9.7 GB download
```

`bootstrap.sh` is idempotent and does five things:

| # | Step | Cost |
|---|------|------|
| 1 | `git submodule update --init --recursive` | ~6 GB (`libraries`) |
| 2 | `tools/link_decks.sh` — link `decks/` into the `5.1` tree | instant |
| 3 | `tools/tidy_libraries.sh` — keep the `libraries` submodule clean | instant |
| 4 | `./build_monorepo.sh` — compile DRAGON5/DONJON5 | minutes |
| 5 | `tools/fetch_openmc_data.sh` + the pinned venv | 9.7 GB, ~10 min |

Prerequisites: `gfortran`, `gcc`, `g++`, `make`, `libhdf5-dev`, `python3-venv`,
and for the OpenMC build `cmake` and `libpng-dev`.

The two NEA submodules (`5.1`, `libraries`) live on `git.oecd-nea.org` and need
**NEA Data Bank credentials**. Export `NEA_TOKEN` (a GitLab personal access
token) before step 1, or configure a credential helper.

Smoke test:

```sh
cd 5.1/Dragon && ./rdragon -c custom -p 1 rbmk_cell_a3.x2m
grep 'k-infinity' Linux_*/rbmk_cell_a3.result      # 1.308679
```

> **The recorded results predate this number.** Every DRAGON figure in `PROGRESS.md`
> and `docs/report.html` was produced against a decompressed draglib left over from an
> earlier `libraries` revision, which the old `.access` hook silently preferred over the
> one the submodule pins — 1.310172 instead of 1.308679, a systematic −87 pcm. The cache
> is content-addressed now so it cannot recur, but the numbers have not been
> re-baselined. See the 2026-09-24 entry in `PROGRESS.md`.

Nothing in this project touches the GPU. Every run is CPU-only; peak resident
set is ~2 GB for a lattice cell and ~1.6 GB for a depleted OpenMC branch.

## Layout

```
decks/              OUR DRAGON/DONJON input.  Canonical copy.
  Dragon/data/        lattice decks (.x2m) and their .access hooks
  Dragon/data/rbmk_proc/   RbmkLib* composition procedures (.c2m)
  Donjon/data/        core decks (.don), generators (.py), maps (.csv)
  common/             the three shared .access hooks every deck links to
  scripts/            one-off analysis helpers
openmc/             the Monte Carlo cross-check: models, drivers, distilled JSON
tools/              bootstrap and the two sync scripts
docs/               the HTML progress report
quarantine/         superseded decks, kept for provenance.  Do not build on these.
5.1/       (sub)    DRAGON5/DONJON5/TRIVAC5/GANLIB5 5.1.0, upstream, unmodified
libraries/ (sub)    NEA draglibs, upstream, unmodified
armi/      (sub)    TerraPower's dragon-armi-plugin
```

### Why `decks/` is not inside `5.1/`

DRAGON wants its input in `5.1/Dragon/data/`, and that is where these decks were
written. But `5.1` is an upstream submodule: the parent pins a commit on
`git.oecd-nea.org`, which we cannot push to. Decks kept there reach a fresh
clone only if the gitlink points at a local-only commit — and then
`git submodule update --init` fails outright on the other machine.

So `decks/` in this repo is the one true copy and `tools/link_decks.sh`
symlinks it into the submodule. `rdragon` copies each deck into a scratch
directory before running it, and `cp` follows symlinks, so a linked deck behaves
exactly like a real one. There is never a second copy to edit by mistake — which
is standing rule 6 in `PROGRESS.md`: *a fix that lives in a copy of the file is
not a fix.*

The script also writes the submodule's `.git/info/exclude`, so `5.1` reports
clean despite the 117 links sitting in its tree. Run it again after adding a
deck.

### The `.access` hooks

`rdragon` runs `data/<deck>.access` before the deck and discards the scratch
directory afterwards, so the hook is the only place to stage a library. There
used to be 36 near-identical copies of the upstream boilerplate; there are now
three real scripts in `decks/common/`, and every deck's `.access` is a symlink
to one of them:

- **`dlib99.access`** — the default. Stages `DLIB_99` (ENDF/B-VIII.1 in the
  172-group XMAS/APOLIB-99 structure) and the `RbmkLib` procedures.
- **`shem361.access`** — the same evaluation in SHEM-361, for resolution studies.
- **`compo.access`** — DONJON side; brings in the exported MULTICOMPO.

`dlib99.access` differs from upstream in one way that matters here: upstream
gunzips the draglib **in place**, inside the `libraries` submodule, so a clean
clone dirties itself on its first run and `git submodule update` then fights the
working tree. Ours decompresses into `.cache/draglib/` (gitignored) and never
writes inside a submodule. `tools/tidy_libraries.sh` migrates a tree that the
old behaviour already dirtied.

## Nuclear data

| What | Where | How |
|---|---|---|
| DRAGON draglibs | `libraries/` submodule | `git submodule update --init` |
| OpenMC ENDF/B-VIII.1 HDF5 (43 GB) | `$NUCDATA_DIR` | `tools/fetch_openmc_data.sh viii.1` |
| OpenMC ENDF/B-VIII.0 HDF5 (13 GB) | `$NUCDATA_DIR` | `tools/fetch_openmc_data.sh viii.0` |
| VIII.0 depletion chain | `$NUCDATA_DIR` | fetched with either of the above |

`NUCDATA_DIR` defaults to `$HOME/nucdata`; the OpenMC data is 56 GB unpacked, so
it deliberately lives outside the repo. The fetch script pins each download by
exact byte count and refuses a mismatch, because the upstream links are opaque
Box URLs that could be republished under the same address.

VIII.1 is the evaluation DRAGON's `DLIB_99` is built from, so a DRAGON/OpenMC
comparison on VIII.1 isolates *method* from *data*. VIII.0 is kept only so the
first sweep stays reproducible.

## What a clean clone does **not** get

Two derived artifacts are too large to track and are rebuilt, not downloaded:

- **`5.1/Dragon/compo/_ACompo`** (114 MB) — the 630-point MULTICOMPO. Rebuild
  with `cd 5.1/Dragon && ./rdragon -c custom -p 1 rbmk_a5b_compo.x2m`, about 81
  minutes. Every DONJON deck that reads a COMPO needs it;
  `decks/common/compo.access` falls back to the smoke-test database with a loud
  warning rather than failing silently.
- **OpenMC statepoints and depletion results** under `openmc/run*`, `openmc/depl*`,
  `openmc/branch*`. The distilled numbers are committed as
  `openmc/branch_results81.json`, `openmc/dragon_a5b_void.json` and the `.txt`
  rate tables, and those are what the report and `void_bracket.py` read.

## Environment overrides

Everything resolves from the repo location; nothing is hardcoded to one machine.
`tools/env.sh` and `openmc/env.sh` honour:

| Variable | Default |
|---|---|
| `RBMK_ROOT` | the repo root |
| `NUCDATA_DIR` | `$HOME/nucdata` |
| `ENDF_RELEASE` | `viii.1` |
| `DRAGLIB_CACHE` | `$RBMK_ROOT/.cache/draglib` |
| `DRAGON_ARCH` | `$(uname -s)_$(uname -m)` |
| `PY` | `$RBMK_ROOT/.venv-openmc/bin/python` |

## Stage-0 scripts

`fetch_source.sh`, `build_all.sh`, `test_all.sh`, `fetch_nuclear_data.sh`,
`setup_armi.sh` and `stage0_build.sh` predate the submodule layout: they fetch
and build the five DRAGON packages separately. They still work, but
**`build_monorepo.sh` is the live build** and is what `bootstrap.sh` calls.
