# A6 — CPS channel cells and rod sites

*(Work order for Tier A step A6, written 2026-09-26 after the method-convergence segment closed.
Paths are relative to the repository root.)*

**Audience:** an implementing agent or a reviewer. Steps run in order. Each has a **GATE**; don't start
the next step until it passes. If a gate fails twice, stop and report.

## Why

The core model has no rod sites: every live cell is fuel or graphite. The accident turns on three
things: the rods' reactivity, their water columns, and the **positive scram**, where a falling rod's
graphite displacer first pushes water out of the bottom 1.25 m of its channel. None of that exists
yet. A6 builds the lattice data for the CPS channels and puts them into the core. A7 (steady
coupling) and A8 (the AZ-5 transient) consume it.

## Method basis: A′ (decided 2026-09-26)

Lattice data are generated on the **production settings**: SHEM-361, Zr self-shielded, `RbmkGeo`
mesh, collision probabilities, `decks/common/rbmk.access`. The difference from the converged
method (4× mesh + MOC with P1 scattering) is **measured on every CPS supercell type** and carried
as a documented additive correction, exactly as `openmc/void_bracket.py` does for the fuel void
branches. It is never folded in silently.

Standing rule 4 applies to each new cell type: OpenMC reproduces it before DRAGON's numbers are
trusted.

## Design inputs

**Sourced:**

| Item | Value | Source |
|---|---|---|
| Rods in Unit 4, 1986 | 211 (second-stage RBMK-1000) | INSAG-7 p. 43 (history of the RCPS design), p. 103 |
| Rod types | 24 shortened absorbers (USP), inserted **from below**; 12 automatic (AR), **no displacer**; 24 emergency (AZ, EPS); the rest manual (RR) | INSAG-7 §2.2 (pdf p. 14), p. 103 |
| Axial design | absorber 5 m (USP 3.5 m); 1.25 m water-filled telescope between absorber and displacer; graphite displacer centred in the 7 m core when fully withdrawn, 1.25 m of water at each end, so **4.5 m of graphite** | INSAG-7 §2.2 (pdf p. 14), Fig. 1; p. 43 |
| CPS lattice | 700 mm square pitch, rotated 45° to the fuel lattice | [D] p. 12 |
| CPS channel tube | same Zr alloy as fuel channels, ⌀88 mm, **3 mm wall**, graphite rings outside | [D] p. 12 |
| Absorber link | B₄C bushings 65 × 7.5 mm (r 2.50–3.25 cm), sealed in the annulus between Al-alloy tubes 70 × 2 and 50 × 2; water flows over both faces; 984 mm per link | [D] p. 12 |
| Displacer link | Al-alloy tube 74 × 2.5 mm, sealed, filled with graphite bushings and blocks | [D] p. 12 |
| CPS coolant | separate circuit, water top-down, 40–60 °C (40–80 °C in [TD722]); channel water-filled whatever the rod position | [D] p. 12; [TD722] |
| B₄C temperature | ≈ 350 °C in operation | [TD722] §3.1 item 12 |
| Rod pattern at 01:22:30 | insertion depth of each rod, cm | INSAG-7 Fig. II-6, p. 119 (text layer is OCR-noisy; digitise from the image) |

**Open** (each is carried with a sensitivity, not guessed silently):

| Item | Plan |
|---|---|
| B₄C density, and whether the boron is natural or enriched | Bracket 1.7–2.3 g/cm³ natural B (pressed bushings, 70–90 % of theoretical) and report the rod-worth sensitivity. [TD722]'s "7 kg per section" is the redesigned 1995 rod and implies > 5 g/cm³ on the 1980 geometry, so it doesn't apply. Search: Dollezhal ch. 6, the NIKIET rod design notes, the OECD/NEA Chernobyl benchmarks. |
| Displacer graphite density | Reactor graphite, 1.65 g/cm³ ([D] p. 11, the stack), with 1.73 as the upper case ([D] p. 47). |
| Al alloy | САВ-1 is the Al alloy [D] names for in-core sleeves (p. 59); the CPS tubes are "Al alloy" unspecified. Get its composition and confirm it applies. |
| Gaps: B₄C outer face (r 3.25) to Al tube (r 3.30) | sealed gas, He (as the fuel gaps). |
| Rod-site map (211 positions) | Digitise INSAG-7 Fig. II-6 and cross-check it against the 45°-rotated 700 mm lattice. The digitisation is also A8's initial rod state. |

## Steps

### A6.1 — Sources and inputs
Catalogue INSAG-7 in `sources/README.md` (the Dollezhal CPS data too). Search for the open items
above. Write `openmc/cps_common.py` as the single transcription of the CPS geometry and materials,
generating both the OpenMC models and the DRAGON decks, as `srp94_common.py` does for the SRP cell.

**GATE A6.1:** every sourced value is traceable to a page; every open value has its bracket.

> **Status 2026-09-26: PASSED**, with the rod types carried forward as open.
> - `openmc/cps_common.py` is the single transcription. It writes `RbmkCpsLib.c2m` (MIX 10–15
>   added to the fuel cell's library), `RbmkSc{FUEL,WAT,ABS,DSP,VOID}.c2m` (the supercells) and the
>   `rbmk_cps_*` decks, and builds the OpenMC supercells. The CPS tube's Zr-2.5Nb is read from
>   RbmkLib MIX 2, not copied.
> - Al alloy: САВ-1, closed ([SF], [OST]). Additional absorbers in Unit 4: one, closed
>   (INSAG-7 pp. 67, 107).
> - B₄C density: no source found. Carried as 2.0 g/cm³ (1.7–2.3). Displacer graphite: 1.65 g/cm³
>   (1.50–1.73) at the CPS water temperature (773 K upper case).
> - Rod-site map: `tools/digitise_fig_II6.py` → `sources/derived/insag7_fig_II6_012230.csv`. It has
>   211 rods, 12 empty lattice sites and the depth of every rod at 01:22:30, and it is checked
>   against the page glyph by glyph. Rod **types** are not in the figure and are still open (see
>   sources/README.md). They are needed from A6.5 on.
> - The real CPS lattice is 45°-rotated with 7 fuel cells per CPS cell. The 3 × 3 supercell has 8.
>   OpenMC measures the difference with a 4 × 4 periodic "r45" cell; it is reported and not applied.

### A6.2 — Supercells
A CPS cell cannot be homogenised alone: it has no fuel. Model a **3 × 3 supercell** of 25 cm cells,
the CPS channel at the centre and 8 fuel channels around it, with reflective boundaries. At a 700 mm
rotated pitch, each CPS channel's nearest neighbours are fuel. The central-cell section types:

| Type | Radial content |
|---|---|
| `ABS` | absorber: water / Al 50×2 / B₄C 65×7.5 / gas / Al 70×2 / water / Zr 88×3 |
| `DSP` | displacer: graphite / Al 74×2.5 / water / Zr 88×3 |
| `WAT` | water column: channel full of CPS water |
| `VOID` | CPS channel drained (loss of CPS cooling; bounding case) |

Supercell axes, i.e. the state of the surrounding fuel: burnup (0, 10.9 ≈ Unit 4 average, 15),
fuel-channel coolant density (0.72, 0.35, 0.02), and fuel temperature (nominal plus one hot
branch).

**GATE A6.2:**
- guardrail: the supercell's volume fractions equal the analytic ones (standing rule 2);
- `WAT` with the centre replaced by a fuel cell reproduces the single fuel cell's k∞ to < 10 pcm.

### A6.3 — Verify each section type (rule 4) and measure the A′ correction
For each type at fresh fuel and at 10.9 MWd/kg:
- OpenMC reference;
- DRAGON production;
- DRAGON converged (4× mesh + MOC P1; MOC is expected to matter more next to B₄C).

The quantities are the **section worths**: Δρ(ABS−WAT), Δρ(DSP−WAT), Δρ(VOID−WAT), and their change
when the surrounding fuel voids.

**GATE A6.3:** converged DRAGON within 5 % of OpenMC on each worth, or the residual attributed. The
production-minus-converged difference is tabulated as the A′ correction for CPS sections.

### A6.4 — Homogenisation and COMPO
Two-group homogenisation of the central cell with **SPH** equivalence. Diffusion theory is not
adequate next to B₄C, and this is the place A4's SPH work was always meant for. Write a CPS
MULTICOMPO with the A6.2 axes. The round-trip and off-grid gates are as in A5b (≤ 10 / ≤ 30 pcm on
the supercell).

**GATE A6.4:** DONJON on the homogenised supercell reproduces DRAGON's supercell k∞ and the section
worths within 1 % (the SPH test).

### A6.5 — Rod sites in the core
Add the 211 CPS sites to the core generator (`decks/Donjon/data/gen_rbmk_realistic.py`) from the digitised
map. Each rod is an axial stack (absorber / telescope water / displacer / water) that moves as one:
- RR and AZ: 5 m absorber + 1.25 m water + 4.5 m displacer;
- AR: absorber only;
- USP: 3.5 m absorber, from below.

> **Found 2026-09-26, blocks this step until A6d's channel map exists.** The generator's core is
> the 1661 cells nearest the centre of a 590 cm circle, which holds only 1749 cells. Unit 4 needs
> 1884 channel positions: 1661 fuel, 211 rods and the 12 empty lattice sites of Fig. II-6. That
> is 117.8 m², an equivalent diameter of 12.2 m. The rods are also interspersed with the fuel, not
> set outside it. Placing the digitised lattice on the current grid puts 209–221 sites inside the
> circle, whatever the offset. So the channel map is rebuilt from a sourced cartogram in A6d, with
> Fig. II-6's lattice as its skeleton. It is not patched here.
> The counts close exactly: 1661 fuel + 211 rods + 12 empty sites = 1884 = 1661 + the 223
> digitised sites. A centred circle can't reproduce that, because circle cell counts step by 8.
> The nearest is R² ≤ 596 cells², giving 1885 cells with all 223 sites inside and 1662 fuel,
> one too many. So A6d traces the real outline from a cartogram ([LEG] Fig. 6.7's staircase
> boundary is legible). The circle is the fallback, and it is one channel off.

Drive positions with `DSET:` and a computed level. `MOVDEV:` is broken for multi-part rods, and a
parked displacer must be a base-map mixture (TIER_A_WORKPLAN "Known traps").

**GATE A6.5 (TIER_A_WORKPLAN A6 gate):**
- **inserting only the displacer from below gives positive reactivity**, with a bottom-skewed axial
  flux;
- all-rods-in gives the expected large negative worth, reported and not tuned.

## After A6
A6b (Xe axis + fuel COMPO rebuild), A6c (Smolensk-3 start-up benchmark: the first use of these
rods in a measured core), A6d (Unit 4 initial state at 01:22:30, including the full digitisation
of Fig. II-6). See PROJECT_PLAN.md, roadmap.

## Not in A6
- The 01:22:30 rod pattern, beyond digitising it: that's A8's initial state.
- Additional absorbers (ДП) in fuel channels at start-up: none are listed for Unit 4 in 1986;
  confirm in A6.1.
- Xenon in the surrounding fuel: the fuel COMPO has no Xe axis yet (A5b deferral).
