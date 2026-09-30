#!/usr/bin/env python3
"""Generate the A8 kinetics cost probe from the A6.5 solver timing probe.

Phase 0 of the transient plan: we have never advanced a single time step, so
the cost of one is unknown and every later choice (timestep, mesh, whether the
Tier B engine is optional) depends on it.  Do not estimate it -- measure it.

This reads ``rbmk_core_3d_dual.don`` and emits two decks that differ only in
which KINSOL: call form they use:

  rbmk_kin_probe.don   step form,  KINSOL: KINET MACRO TRACK SYST
  rbmk_kin_ramp.don    ramp form,  KINSOL: KINET MACRO TRACK SYST MACRO_0 SYST_0
  rbmk_kin_pert.don    step form, but with the cross sections actually moving

The third deck exists because the first two flatter the solver.  With a frozen
macrolib KINSOL: starts each step from the exact answer and converges at once,
so their cost is a LOWER BOUND, not A8's cost.  rbmk_kin_pert.don rebuilds the
macrolib every step and ramps the absorption of the bottom axial reflector --
crudely, a rod inserting from below, which is the RBMK-relevant direction --
so the flux shape genuinely has to move and the inner iterations are real.

The ramp form keeps a second macrolib and a second factorised system alive, so
the pair answers the plan's question about what that costs in time and RSS.

The geometry, the mesh and the (deliberately wrong) IAEA PWR cross sections are
inherited verbatim from the source deck -- this measures seconds per kinetics
step and max RSS, not reactor physics.  Two things are added:

  * OVERV, the reciprocal neutron speeds.  KINXSD.f:152 aborts with
    '@KINXSD: MISSING OVERV DATA.' without them, and MAC: has no default.
    The values below are textbook two-group speeds, not fitted to anything;
    the real ones reach A8 from the MULTICOMPO, since EDI: writes OVERV
    (Dragon/src/EDIPXS.f) and NCR: propagates it (Donjon/src/NCRMAC.f).
  * UNIT on TRIVAA:, required by TRIVAA.f:174 for anything feeding
    INIKIN:/KINSOL:.  It only adds a unitary weighting matrix, so the same
    system object still serves FLUD:.

THE CHECK THAT MAKES THIS MORE THAN A STOPWATCH: nothing is perturbed.  No rod
moves, no cross section changes, the macrolib is identical at every step.  A
correctly assembled transient starting from a converged flux must therefore
hold power exactly constant.  Drift means the kinetics setup is wrong, and that
is worth finding out now rather than inside A8.

Edit this generator, not the decks it writes.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rbmk_core_3d_dual.don")

# Reciprocal neutron speeds, s/cm, for the 2-group structure of the source
# deck.  v1 = 1.0e7 cm/s (fast group mean), v2 = 2.2e5 cm/s (2200 m/s at
# 0.0253 eV).  Textbook constants for a thermal reactor, carried only so the
# module has something dimensionally right to integrate; see the header.
OVERV = (1.0e-7, 4.545e-6)

NSTEP = int(os.environ.get("KIN_NSTEP", "10"))
DT = 0.001          # s
POWI = 3200.0       # MW, the RBMK-1000 rating; only its constancy is tested

# Six-group delayed data.  These are DONJON's own AFMtest.x2m values
# (AFMtest.x2m:164-165), used unchanged so the probe cannot be accused of
# carrying tuned kinetics.  A8 uses the beta/lambda set A5b MEASURED from the
# draglib with NDEL 6, not these.
BETA = "0.000250 0.001562 0.001505 0.002755 0.000830 0.000317"
LAMBDA = "0.0129 0.0311 0.134 0.331 1.26 3.21"


def read_source():
    with open(SRC) as fh:
        return fh.read().splitlines()


def add_overv(lines):
    """Insert an OVERV entry into every MIX block of the MAC: input.

    Anchored on DIFFX, which every mixture in the source deck has exactly once.
    """
    out, n = [], 0
    for ln in lines:
        out.append(ln)
        m = re.match(r"^(\s*)DIFFX\b", ln)
        if m:
            out.append(f"{m.group(1)}OVERV  {OVERV[0]:.4E}  {OVERV[1]:.4E}")
            n += 1
    if n == 0:
        sys.exit("gen_kin_probe: found no DIFFX lines to anchor OVERV on")
    return out, n


# Absorption ramp for the perturbed deck: the group-2 TOTAL of mixture
# PERT_MIX climbs by DSIG per step.  Not a physical rod -- a deliberate
# perturbation whose only job is to stop KINSOL: starting from the answer,
# so its cost per step is measured with the flux actually moving.
#
# Mix 4 is the INNER bottom axial reflector, directly beneath the fuel, so a
# ramp there is bottom-skewed and shape-changing -- the same geometry as the
# positive scram tip, which is why it is the default.  Override with
# KIN_PERT_MIX / KIN_DSIG.
PERT_MIX = int(os.environ.get("KIN_PERT_MIX", "4"))
DSIG = float(os.environ.get("KIN_DSIG", "1.3e-3"))


def mac_block(lines, templated):
    """Return the MAC: block, optionally with PERT_MIX's thermal TOTAL templated."""
    a = next(i for i, l in enumerate(lines) if l.startswith("MACRO := MAC:"))
    b = next(i for i in range(a, len(lines)) if lines[i].strip() == ";")
    blk = lines[a:b + 1]
    if templated:
        seen, base = False, None
        for i, l in enumerate(blk):
            if re.match(rf"^\s*MIX\s+{PERT_MIX}\s*$", l):
                seen = True
            elif seen and "TOTAL" in l:
                base = re.search(r"TOTAL\s+\S+\s+(\S+)", l).group(1)
                blk[i] = re.sub(r"(TOTAL\s+\S+\s+)\S+", r"\g<1><<sig5>>", l)
                break
        if base is None:
            sys.exit(f"gen_kin_probe: no TOTAL line found under MIX {PERT_MIX}")
        mac_block.base = base
    return blk


def transform(lines, ramp, pert=False):
    lines, nmix = add_overv(lines)
    macro_tpl = mac_block(lines, True)
    out = []
    for ln in lines:
        if ln.startswith("LINKED_LIST"):
            ln = ln.rstrip(" ;") + " KINET SYSTEM0 MACRO0 ;"
        elif ln.startswith("MODULE "):
            ln = ln.rstrip(" ;") + " INIKIN: KINSOL: DELETE: ;"
        elif ln.strip() == "REAL Keff ;":
            ln = ("REAL Keff powf ;\n"
                  f"REAL DT := {DT} ;\n"
                  f"REAL powi := {POWI} ;\n"
                  f"REAL sig5 := {mac_block.base} ;\n"
                  "INTEGER istep := 0 ;")
        out.append(ln)

    text = "\n".join(out)

    # TRIVAA: must build the unitary weighting matrix -- TRIVAA.f:174.
    old_trivaa = "SYSTEM := TRIVAA: MACRO2 TRACK ::\n      EDIT 1 ;"
    if old_trivaa not in text:
        sys.exit("gen_kin_probe: the TRIVAA: call is not where it was")
    text = text.replace(old_trivaa,
                        "SYSTEM := TRIVAA: MACRO2 TRACK ::\n      EDIT 1 UNIT ;")

    # Replace the source deck's closing ECHO/END: with the kinetics probe.
    tail_at = text.index('ECHO "rbmk_core_3d_dual completed" ;')
    text = text[:tail_at] + kinetics_block(ramp, pert, macro_tpl)
    return text, nmix


def kinetics_block(ramp, pert, macro_tpl):
    name = "rbmk_kin_pert" if pert else ("rbmk_kin_ramp" if ramp else "rbmk_kin_probe")
    if pert:
        form = (f"step form; mix {PERT_MIX} thermal TOTAL ramped "
                f"{mac_block.base} + {DSIG:g}/step")
    elif ramp:
        form = "ramp (6-entry: MACRO_0 and SYST_0 retained)"
    else:
        form = "step (4-entry: cross sections constant across the step)"

    if pert:
        mac = "\n".join("  " + l for l in macro_tpl)
        keep = (
            f"  EVALUATE sig5 := sig5 {DSIG:.4E} + ;\n"
            "  MACRO MACRO2 SYSTEM := DELETE: MACRO MACRO2 SYSTEM ;\n"
            f"{mac}\n"
            "  MACRO2 MATEX := MACINI: MATEX MACRO :: EDIT 0 ;\n"
            "  SYSTEM := TRIVAA: MACRO2 TRACK :: EDIT 1 UNIT ;\n"
            "  KINET := KINSOL: KINET MACRO2 TRACK SYSTEM ::\n"
            "    EDIT 1 DELTA <<DT>> SCHEME FLUX THETA 0.8 PREC THETA 0.8 ;\n"
        )
    elif ramp:
        keep = (
            "  MACRO0 := MACRO2 ;\n"
            "  SYSTEM0 := SYSTEM ;\n"
            "  SYSTEM := DELETE: SYSTEM ;\n"
            "  SYSTEM := TRIVAA: MACRO2 TRACK :: EDIT 1 UNIT ;\n"
            "  KINET := KINSOL: KINET MACRO2 TRACK SYSTEM MACRO0 SYSTEM0 ::\n"
            "    EDIT 1 DELTA <<DT>> SCHEME FLUX THETA 0.8 PREC THETA 0.8 ;\n"
            "  MACRO0 SYSTEM0 := DELETE: MACRO0 SYSTEM0 ;\n"
        )
    else:
        keep = (
            "  SYSTEM := DELETE: SYSTEM ;\n"
            "  SYSTEM := TRIVAA: MACRO2 TRACK :: EDIT 1 UNIT ;\n"
            "  KINET := KINSOL: KINET MACRO2 TRACK SYSTEM ::\n"
            "    EDIT 1 DELTA <<DT>> SCHEME FLUX THETA 0.8 PREC THETA 0.8 ;\n"
        )

    return f'''*==============================================================
* KINETICS COST PROBE -- {form}
*
* TRIVAA: is rebuilt inside the loop on purpose.  In A8 the cross sections
* change every step, so the system matrix must be re-assembled and re-factored
* every step; skipping it here would measure a cost A8 does not get to pay.
*==============================================================
KINET := INIKIN: MACRO2 TRACK SYSTEM FLUX ::
  EDIT 1
  NDEL 6
  BETA {BETA}
  LAMBDA {LAMBDA}
  CHID 1.0 1.0 1.0 1.0 1.0 1.0
       0.0 0.0 0.0 0.0 0.0 0.0
  NORM POWER-INI <<powi>>
;

REPEAT
  EVALUATE istep := istep 1 + ;
{keep}  GREP: KINET :: GETVAL E-POW 1 >>powf<< ;
  ECHO "KINSTEP" istep "power=" powf ;
UNTIL istep {NSTEP} >= ;

*--- THE CHECK (step/ramp decks): nothing was perturbed, so power must not
* have moved.  In the perturbed deck power MUST move -- downward, since the
* ramp only ever adds absorption -- and a rise would mean the sign is wrong.
* Reported, not asserted: the tolerance a drift would have to beat is itself
* something this run is measuring.  A visibly changing power means the
* kinetics assembly is wrong, not that the reactor did something.
ECHO "{'PERTURBED' if pert else 'UNPERTURBED'} TRANSIENT: power-ini=" powi "power-final=" powf ;
ECHO "{name} completed" ;
END: ;
QUIT .
'''


def main():
    src = read_source()
    for ramp, pert, name in ((False, False, "rbmk_kin_probe"),
                             (True, False, "rbmk_kin_ramp"),
                             (False, True, "rbmk_kin_pert")):
        text, nmix = transform(list(src), ramp, pert)
        header = f'''*----
*  A8 KINETICS COST PROBE ({"perturbed" if pert else "ramp" if ramp else "step"} form)
*  GENERATED by decks/Donjon/data/gen_kin_probe.py -- edit the generator.
*
*  Phase 0 of the transient plan.  Measures seconds per KINSOL: step and max
*  RSS on the full DUAL 1 1 core, so A8's timestep and the urgency of the
*  Tier B engine are decided on a measurement rather than a guess.
*
*  Cross sections are the wrong-on-purpose IAEA PWR constants inherited from
*  rbmk_core_3d_dual.don.  OVERV added to {nmix} mixtures (KINXSD.f:152).
*  {f"Mix {PERT_MIX} thermal absorption ramps {DSIG:g}/step: power MUST fall."
     if pert else
     "Nothing is perturbed: constant power is the correctness check."}
*  Step count {NSTEP}; regenerate with KIN_NSTEP=<n> to change it.
*----
'''
        # Drop the source deck's own header block, keep everything from the
        # first real statement on.
        body = text[text.index("* DONJON5 RBMK-1000"):]
        path = os.path.join(HERE, name + ".don")
        with open(path, "w") as fh:
            fh.write(header + body)

        over = [i + 1 for i, l in enumerate((header + body).splitlines())
                if len(l) > 120]
        if over:
            sys.exit(f"gen_kin_probe: {name}.don lines over 120 columns: {over[:5]}")
        print(f"wrote {path}  ({len((header+body).splitlines())} lines, "
              f"OVERV on {nmix} mixtures, {NSTEP} steps)")


if __name__ == "__main__":
    main()
