#!/usr/bin/env python3
"""A6.4b -- an explicit rod-cell equivalence, solved against DRAGON's fluxes.

THE PROBLEM.  Gate A6.4 fails.  The homogenisation, the SPH equivalence and the
solver are exact -- A64S, which takes all nine cells of the 3x3 supercell from
the CPS MULTICOMPO, reproduces DRAGON's transport k to about 1 pcm.  But the
core does not have nine CPS cells.  It has one rod cell surrounded by ordinary
fuel, and its fuel data comes from the fuel MULTICOMPO, which is a different
calculation from the supercell's own depleted fuel.  Substituting it costs
7-10 % of the displacer and drained-channel worth.

The cause is specific.  `SPH: ... ASYM 1` normalises the supercell's factors to
1 in fuel cell 1, so the other seven fuel cells carry factors that are close to
1 but not equal to it -- they sit at different distances from the absorber and
see different flux depression.  The core throws all seven away.  The rod cell's
own factor was computed in a context that included them, so once they are gone
it is the wrong factor.

THE FIX.  Re-solve the rod cell's two factors -- one per group -- for the
configuration the core actually has: eight neighbours at exactly 1.0 carrying
fuel-COMPO data.

TARGETS, so that nothing is fitted.  Two unknowns against two conditions: the
rod cell's group-wise volume-integrated flux, as a fraction of the supercell
total.  That is the quantity an SPH equivalence is defined to preserve, it is
normalisation-independent, and it is NOT k.  **k is left free and is the
check** -- which is the right way round, because every worth is a k difference,
so fitting k would make the gate a tautology.

WHERE THE REFERENCE COMES FROM.  Not a new DRAGON run: from A64S, the
all-nine-cells-from-the-CPS-COMPO configuration, which is already validated
against DRAGON's transport solution to ~1 pcm.  Its per-cell fluxes are
DRAGON's per-cell fluxes.  Rule 4 is served separately, by checking the
converged factors against DRAGON's own SPH machinery.

MACHINERY, all confirmed to work inside DONJON before any of it was relied on
(rbmk_cps_a64b_smk.don, 2026-09-30):
  * `SPH: <macrolib> :: MACRO SPRD <nmix> <ngrp> <values>` applies an explicit
    per-mixture, per-group table with no optimiser (SPH.F:325-348), values in
    mixture-major order.  Proved applied, not ignored, by a pair of runs: all
    factors 1.0 reproduces k exactly, and 1.05/0.95 on the centre moves it
    +208 pcm.  All-1.0 alone would prove nothing.
  * `OUT: FLUX TRACK MACRO GEOM :: INTG MIX` integrates the flux over the
    geometry's MIX zones (OUTHOM.f:162) and prints FLUX-INTG per zone per
    group.  Give it no COND, or it condenses to one group.
  * Both live in Dragon/Trivac rather than DONJON's own table (DONDRV.F), but
    DONDRV falls through to KDRDRV and both symbols are in the binary.
"""
import os
import re
import subprocess
import sys

import cps_common as cc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = cc.ROOT
DON = cc.DON
RUN = os.path.join(ROOT, "5.1", "Donjon")

NMIX = 9
ROD = 5                      # centre of the 3 x 3
FUEL_MIX = [m for m in range(1, NMIX + 1) if m != ROD]


def states():
    return [(b, d, t) for b in cc.A64_BUS for t in cc.A64_TFS for d in cc.A64_DCAS]


def _ncr_ref(bu, dca, tf):
    """All nine cells from the CPS COMPO: the A64S configuration, the reference."""
    rows = "".join(
        f"  MIX {m} FROM {m} SET 'burnup' {bu} SET 'DCA' {dca} SET 'TF' {tf} ENDMIX\n"
        for m in range(1, NMIX + 1))
    return (f"MREF := NCR: CCpo :: EDIT 0 MACRO LINEAR NMIX {NMIX}\n"
            f"  COMPO CCpo 'EDICPS'\n{rows}  ;")


def _ncr_trial(bu, dca, tf):
    """What the core has: eight fuel cells from the FUEL COMPO, centre from CPS."""
    rows = "".join(
        f"  MIX {m} FROM 1 SET 'burnup' {bu} SET 'DCA' {dca} SET 'TF' {tf}"
        f" SET 'TG' 750.0 ENDMIX\n" for m in FUEL_MIX)
    return (f"MTRI := NCR: FCpo CCpo :: EDIT 0 MACRO LINEAR NMIX {NMIX}\n"
            f"  COMPO FCpo 'EDIRBMK'\n{rows}"
            f"  COMPO CCpo 'EDICPS'\n"
            f"  MIX {ROD} FROM {ROD} SET 'burnup' {bu} SET 'DCA' {dca}"
            f" SET 'TF' {tf} ENDMIX ;")


def _sprd(f1, f2):
    """SPRD table: 1.0 on every fuel mixture, (f1,f2) on the rod cell."""
    v = []
    for m in range(1, NMIX + 1):
        v.append(f"{f1:.8f} {f2:.8f}" if m == ROD else "1.0 1.0")
    return f"  MACRO SPRD {NMIX} 2\n  " + "\n  ".join(v) + " ;"


def _solve(tag, extra=""):
    """TRIVAA -> FLUD -> k -> OUT: INTG MIX, on whatever macrolib MCUR holds."""
    return f"""SYSTEM := TRIVAA: MCUR TRACK :: EDIT 0 ;
FLUX := FLUD: SYSTEM TRACK :: EDIT 0 EXTE 1.0E-7 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>kk<< ;
ECHO "A64B {tag}{extra}" kk ;
OUTM := OUT: FLUX TRACK MCUR GEOM :: EDIT 2 INTG MIX ;
OUTM SYSTEM FLUX := DELETE: OUTM SYSTEM FLUX ;"""


def deck(stype, trials_by_state):
    """trials_by_state: one list of (f1, f2) per state, aligned with states().

    One deck per solver iteration.  Every state's reference and every trial are
    evaluated in a single DONJON process, because the process launch costs more
    than the solves do -- 18 states x 3 trials is a few seconds.
    """
    ntr = {len(t) for t in trials_by_state}
    if len(ntr) != 1:
        sys.exit("a64b: every state needs the same number of trials")
    trials = next(iter(ntr))
    tag = stype
    L = [f"""*----
*  A6.4b -- rod-cell equivalence, centre {stype}.
*  GENERATED by openmc/a64b.py.  Edit the generator, not this file.
*
*  Per state: the REF configuration (all nine cells from the CPS COMPO, which
*  A64S validates against DRAGON to ~1 pcm) followed by {trials} trial
*  SPH factor pairs applied to the rod cell of the TRIAL configuration (eight
*  fuel cells from the fuel COMPO -- what the core actually has).
*
*  Output, in execution order:
*    A64B REF   <bu> <dca> <tf> <k>   + an OUT: INTG MIX block
*    A64B TRI t<i> <bu> <dca> <tf> <k> + an OUT: INTG MIX block, one per trial
*----
LINKED_LIST FCpo CCpo MREF MTRI MCUR OUTM GEOM TRACK SYSTEM FLUX ;
SEQ_ASCII   _ACompo :: FILE './_ACompo' ;
SEQ_ASCII   _CCompo :: FILE './_CCompo{tag}' ;
MODULE      NCR: GEO: TRIVAT: TRIVAA: FLUD: OUT: SPH: GREP: DELETE: END: ;
REAL kk ;
FCpo := _ACompo ;
CCpo := _CCompo ;
GEOM := GEO: :: CAR2D 3 3
  X- REFL X+ REFL Y- REFL Y+ REFL
  MESHX 0.0 25.0 50.0 75.0 MESHY 0.0 25.0 50.0 75.0
  MIX 1 2 3  4 5 6  7 8 9 ;
TRACK := TRIVAT: GEOM :: EDIT 0 MAXR 20 DUAL 1 1 ;"""]

    for (bu, dca, tf), tr in zip(states(), trials_by_state):
        st = f"{bu} {dca} {tf}"
        L.append(f"\n{_ncr_ref(bu, dca, tf)}\nMCUR := MREF ;\n"
                 f"{_solve('REF', f' {st}')}\nMREF MCUR := DELETE: MREF MCUR ;")
        L.append(f"{_ncr_trial(bu, dca, tf)}")
        for i, (f1, f2) in enumerate(tr):
            L.append(f"MCUR := SPH: MTRI :: EDIT 0\n{_sprd(f1, f2)}\n"
                     f"{_solve(f'TRI t{i}', f' {st}')}\nMCUR := DELETE: MCUR ;")
        L.append("MTRI := DELETE: MTRI ;")

    L.append(f'\nECHO "rbmk_cps_a64b_{tag} completed" ;\nEND: ;\nQUIT .\n')
    text = "\n".join(L)
    over = [i + 1 for i, l in enumerate(text.splitlines()) if len(l) > 120]
    if over:
        sys.exit(f"a64b: lines over 120 columns: {over[:5]}")
    return text


ACCESS = """#!/bin/sh
# Generated by openmc/a64b.py: stage the fuel and CPS MULTICOMPOs.
src="$1"/../Dragon/compo
cp "$src"/_ACompo . || exit 1
cp "$src"/_CCompo{t} . || exit 1
"""

MARK = re.compile(r">\|A64B (REF|TRI t\d+) +([\d.eE+-]+) +([\d.eE+-]+) +"
                  r"([\d.eE+-]+) +([\d.eE+-]+)")
GRP = re.compile(r"^ G R O U P   :\s+(\d+)")
ROW = re.compile(r"^\s+(\d+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)")


def parse(path):
    """Walk the .result once, attributing each INTG block to the marker before it.

    Order is the only association available -- OUT: prints no label -- so the
    deck emits an ECHO immediately before every OUT: call and this reads them
    strictly in sequence.  Any mismatch in count is an error, not a warning.
    """
    out, cur, grp = [], None, None
    for ln in open(path, errors="replace"):
        m = MARK.search(ln)
        if m:
            what, bu, dca, tf, k = m.groups()
            cur = dict(what=what, state=(float(bu), float(dca), float(tf)),
                       k=float(k), flux={}, ntot={}, sigw={})
            out.append(cur)
            continue
        g = GRP.match(ln)
        if g:
            grp = int(g.group(1))
            continue
        r = ROW.match(ln)
        if r and cur is not None and grp is not None:
            col = ln.split()
            ihom = int(col[0])
            # VOLUME FLUX-INTG NTOT0 SIGW00 ... (OUTAUX.f:374)
            cur["flux"][(ihom, grp)] = float(col[2])
            cur["ntot"][(ihom, grp)] = float(col[3])
            cur["sigw"][(ihom, grp)] = float(col[4])
    return out


# Which quantity the equivalence is solved against.  SPH equivalence is defined
# by preserving REACTION RATES, not fluxes -- see the 2026-09-30 entry in
# PROGRESS.md for the measurement that settles this.  "flux" is kept only
# because it is the target the plan originally recorded and the run that
# disproved it has to stay reproducible.
TARGET = os.environ.get("A64B_TARGET", "removal")


def _zone(rec, m, g, what=None):
    what = what or TARGET
    phi = rec["flux"][(m, g)]
    if what == "flux":
        return phi
    if what == "collision":
        return rec["ntot"][(m, g)] * phi
    if what == "removal":
        # (total - within-group scatter) x flux: the rate at which this cell
        # takes neutrons OUT of group g, by absorption or by scattering them
        # to another group.  For the rod cell, which does not fission, that IS
        # its whole effect on the core.
        return (rec["ntot"][(m, g)] - rec["sigw"][(m, g)]) * phi
    sys.exit(f"a64b: unknown target {what!r}")


def rod_fraction(rec, what=None):
    """The rod cell's share of the supercell total, per group.

    A share rather than an absolute value, because an eigenvalue flux carries
    an arbitrary normalisation.
    """
    return tuple(_zone(rec, ROD, g, what)
                 / sum(_zone(rec, m, g, what) for m in range(1, NMIX + 1))
                 for g in (1, 2))


def run(stype, trials_by_state):
    name = f"rbmk_cps_a64b_{stype}"
    p = os.path.join(DON, name + ".don")
    open(p, "w").write(deck(stype, trials_by_state))
    a = p + ".access"
    open(a, "w").write(ACCESS.replace("{t}", stype))
    os.chmod(a, 0o755)
    subprocess.run([os.path.join(ROOT, "tools", "link_decks.sh")],
                   check=True, capture_output=True)
    res = os.path.join(RUN, "Linux_aarch64", name + ".don.result")
    if os.path.exists(res):
        os.remove(res)                      # rule 5: never read a stale result
    subprocess.run(["./rdonjon", name + ".don"], cwd=RUN,
                   check=True, capture_output=True)
    recs = parse(res)
    want = len(states()) * (1 + len(trials_by_state[0]))
    if len(recs) != want:
        sys.exit(f"a64b: parsed {len(recs)} records, expected {want} -- see {res}")
    for r in recs:
        if len(r["flux"]) != NMIX * 2:
            sys.exit(f"a64b: {r['what']} {r['state']} has {len(r['flux'])} flux "
                     f"entries, expected {NMIX * 2}")
    return recs


# ---------------------------------------------------------------------------
# The solve
# ---------------------------------------------------------------------------

DELTA = 0.01          # finite-difference step on an SPH factor
TOL = 1.0e-6          # absolute, on a rod flux fraction of order 0.07-0.10
MAXIT = 20


def solve(stype, verbose=True):
    """Newton on two unknowns per state, all states advanced together.

    One DONJON run per iteration evaluates, for every state, the base point and
    the two finite-difference perturbations.  The Jacobian is 2x2 and inverted
    in closed form; a damped step keeps the factors positive.  Returns
    {state: (f1, f2, residual, k_at_solution, k_reference)}.
    """
    sts = states()
    f = {s: [1.0, 1.0] for s in sts}
    done, hist = {}, []

    for it in range(MAXIT):
        live = [s for s in sts if s not in done]
        if not live:
            break
        trials = []
        for s in sts:
            f1, f2 = f[s]
            trials.append([(f1, f2), (f1 + DELTA, f2), (f1, f2 + DELTA)])
        recs = run(stype, trials)

        byst = {}
        for r in recs:
            byst.setdefault(r["state"], []).append(r)

        worst = 0.0
        for s in live:
            ref, t0, t1, t2 = byst[s]
            assert ref["what"] == "REF", ref["what"]
            tgt = rod_fraction(ref)
            r0 = [rod_fraction(t0)[g] - tgt[g] for g in (0, 1)]
            worst = max(worst, max(abs(x) for x in r0))
            if max(abs(x) for x in r0) < TOL:
                done[s] = (f[s][0], f[s][1], r0, t0["k"], ref["k"])
                continue
            # 2 x 2 Jacobian by forward difference
            j = [[(rod_fraction(t1)[g] - rod_fraction(t0)[g]) / DELTA,
                  (rod_fraction(t2)[g] - rod_fraction(t0)[g]) / DELTA]
                 for g in (0, 1)]
            det = j[0][0] * j[1][1] - j[0][1] * j[1][0]
            if abs(det) < 1e-14:
                sys.exit(f"a64b: singular Jacobian at {s}: {j}")
            d1 = -(r0[0] * j[1][1] - r0[1] * j[0][1]) / det
            d2 = -(j[0][0] * r0[1] - j[1][0] * r0[0]) / det
            # damp so a factor can never go non-positive or jump wildly
            scale = min(1.0, 0.5 / max(abs(d1), abs(d2), 1e-30))
            f[s] = [max(1e-3, f[s][0] + scale * d1),
                    max(1e-3, f[s][1] + scale * d2)]
        hist.append((it, len(done), worst))
        if verbose:
            print(f"  iter {it}: converged {len(done)}/{len(sts)}, "
                  f"worst residual {worst:.2e}")

    if len(done) != len(sts):
        sys.exit(f"a64b: {len(sts) - len(done)} states did not converge in {MAXIT}")
    return done, hist


def baseline(st):
    """The unit-factor picture: how far off the core configuration starts."""
    recs = run(st, [[(1.0, 1.0)]] * len(states()))
    print(f"{'bu':>8} {'dca':>5} {'tf':>6}  {'k REF':>9} {'k TRI':>9} "
          f"{'dk/pcm':>8}  {'rodfrac REF g1/g2':>19} {'TRI g1/g2':>17}")
    for i in range(0, len(recs), 2):
        ref, tri = recs[i], recs[i + 1]
        assert ref["what"] == "REF" and ref["state"] == tri["state"], (ref, tri)
        bu, dca, tf = ref["state"]
        rr, rt = rod_fraction(ref), rod_fraction(tri)
        dk = (1 / ref["k"] - 1 / tri["k"]) * 1e5
        print(f"{bu:8.0f} {dca:5.2f} {tf:6.0f}  {ref['k']:9.6f} {tri['k']:9.6f} "
              f"{dk:8.0f}  {rr[0]:9.6f} {rr[1]:9.6f} {rt[0]:8.6f} {rt[1]:8.6f}")


def worths(types=("WAT", "ABS", "DSP", "VOID"), f=None):
    """The quantity the A6.4 gate is actually about: a k DIFFERENCE.

    k itself can be wrong by a lot and the worth still right, if the neighbour
    error is common to the rodded and unrodded configurations.  This measures
    how much of it cancels.  `f` is an optional {state: (f1,f2)} applied to the
    rod cell of the TRIAL configuration of every type.
    """
    sts = states()
    out = {}
    for t in types:
        tr = [[(1.0, 1.0)] if f is None else [tuple(f[t][s])] for s in sts]
        recs = run(t, tr)
        for i in range(0, len(recs), 2):
            ref, tri = recs[i], recs[i + 1]
            out[(t, ref["state"])] = (ref["k"], tri["k"])
    print(f"{'bu':>7} {'dca':>5} {'tf':>6} {'type':>5}"
          f"  {'worth REF':>10} {'worth TRI':>10} {'err':>8} {'err %':>7}")
    err = {}
    for s in sts:
        for t in types:
            if t == "WAT":
                continue
            kr0, kt0 = out[("WAT", s)]
            kr1, kt1 = out[(t, s)]
            wr = (1 / kr0 - 1 / kr1) * 1e5
            wt = (1 / kt0 - 1 / kt1) * 1e5
            pc = 100.0 * (wt - wr) / wr if wr else float("nan")
            err.setdefault(t, []).append(pc)
            print(f"{s[0]:7.0f} {s[1]:5.2f} {s[2]:6.0f} {t:>5}"
                  f"  {wr:10.0f} {wt:10.0f} {wt-wr:8.0f} {pc:7.2f}")
    print("\n  worth error range, %")
    for t, v in err.items():
        print(f"    {t:>5}  {min(v):+7.2f} to {max(v):+7.2f}")
    return out


def gate(types=("WAT", "ABS", "DSP", "VOID")):
    """The A6.4b gate end to end.

    Solve the two rod-cell factors per type per state against the rod flux
    fraction, then measure the worths with those factors in place.  k and the
    worths are both left free during the solve, so this is a test, not a fit.
    """
    import json
    print(f"target = {TARGET}\n")
    f = {}
    for t in types:
        print(f"--- solving {t}")
        sol, _ = solve(t)
        f[t] = {s: (v[0], v[1]) for s, v in sol.items()}
        v1 = [v[0] for v in f[t].values()]
        v2 = [v[1] for v in f[t].values()]
        print(f"    f1 {min(v1):.6f}..{max(v1):.6f}   f2 {min(v2):.6f}..{max(v2):.6f}")
    out = os.path.join(HERE, f"a64b_factors_{TARGET}.json")
    json.dump({t: {repr(s): list(v) for s, v in d.items()} for t, d in f.items()},
              open(out, "w"), indent=1)
    print(f"\nwrote {out}\n")
    print("=== worths WITH the solved rod-cell factors ===")
    worths(types, f=f)


def scan(stype="VOID", lo=0.80, hi=1.20, n=5):
    """How much authority does a rod-cell SPH factor actually have?

    The removal-rate solve stalls, which is a physical statement rather than a
    numerical one: raising a black absorber's cross section depresses its flux
    almost proportionally, so its reaction rate -- and with it its effect on
    the core -- barely moves.  If that is right, NO rod-only equivalence can
    close the A6.4 gate, and this scan is what shows it.

    Holds the WAT reference cell at 1.0 and sweeps the <stype> rod cell.
    """
    grid = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    tr = [[(a, b) for a in grid for b in grid]] * len(states())
    rw = run("WAT", [[(1.0, 1.0)]] * len(states()))
    kw = {r["state"]: r["k"] for r in rw if r["what"] == "TRI t0"}
    kwr = {r["state"]: r["k"] for r in rw if r["what"] == "REF"}
    rv = run(stype, tr)
    ref = {r["state"]: r["k"] for r in rv if r["what"] == "REF"}
    print(f"\nWorth of {stype} vs WAT, sweeping the {stype} rod cell's SPH "
          f"factors over [{lo}, {hi}]\n(WAT cell held at 1.0; err % against "
          f"the REF worth, which A64S validates to ~1 pcm)\n")
    for s in states()[:3] + states()[6:7]:
        wr = (1 / kwr[s] - 1 / ref[s]) * 1e5
        row = [r for r in rv if r["state"] == s and r["what"] != "REF"]
        errs = [100.0 * ((1 / kw[s] - 1 / r["k"]) * 1e5 - wr) / wr for r in row]
        print(f"  bu {s[0]:6.0f} dca {s[1]:4.2f} tf {s[2]:5.0f}: "
              f"REF worth {wr:7.0f} pcm, err over the whole grid "
              f"{min(errs):+7.2f} to {max(errs):+7.2f} %")
    print("\n  If that range does not straddle 0, a rod-only equivalence "
          "cannot close the gate.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "solve"
    st = sys.argv[2] if len(sys.argv) > 2 else "ABS"
    if cmd == "baseline":
        baseline(st)
    elif cmd == "worths":
        worths()
    elif cmd == "gate":
        gate()
    elif cmd == "scan":
        scan(st if len(sys.argv) > 2 else "VOID")
    else:
        print(f"A6.4b rod-cell equivalence, centre {st}")
        sol, _ = solve(st)
        print(f"\n{'bu':>8} {'dca':>5} {'tf':>6}  {'f1':>9} {'f2':>9}"
              f"  {'k solved':>9} {'k ref':>9} {'dk/pcm':>7}")
        for s in states():
            f1, f2, _r, ks, kr = sol[s]
            print(f"{s[0]:8.0f} {s[1]:5.2f} {s[2]:6.0f}  {f1:9.6f} {f2:9.6f}"
                  f"  {ks:9.6f} {kr:9.6f} {(1/kr - 1/ks)*1e5:7.0f}")
