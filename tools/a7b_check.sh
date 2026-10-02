#!/usr/bin/env bash
#
# A7b: the coupled core.  Flux -> power -> thermal-hydraulics -> coolant
# density and fuel temperature back into the cross-section interpolation.
#
# HISTORY, because it is the point of the run.  On the 840-point MULTICOMPO
# this did not finish: the axes had been built around a lattice-cell nominal
# state and a real core left the box at both ends -- DCA topped out at 0.72
# where the subcooled inlet is 0.778, TF floored at 600 K where the end of a
# low-power channel sits at 586.  Neither was a modelling error, and NCR: has
# no clamp, so the table had to cover the state.  The 2026-10-01 rebuild
# widened both (0.80 and 530 K) and the loop now closes.
#
# So this runs it BOTH ways and the pair separates the two feedbacks:
#   U4_VOIDFB=0  coolant density pinned at 0.72   -> Doppler alone
#   U4_VOIDFB=1  density from the map             -> Doppler + void
# and each flow case is run under both, because with the density pinned the
# flow cannot reach k at all and the two flow cases must agree -- which is the
# check that the pin is really a pin.  No number here is typed by hand.
#
# WHAT CONVERGES, AND WHAT DOES NOT (measured 2026-10-02).  The eigenvalue
# converges to single-precision roundoff.  The temperature and density fields
# do not: they settle into a limit cycle of a few K and a few hundredths of a
# g/cc, localised at the boiling-onset node, because K0 -- the integer index
# of that node -- is set by a threshold test (THMH2O.f:383) that lives inside
# the Picard loop.  A node on the threshold flips the two-phase branch on and
# off forever.  Under-relaxation lowers the plateau -- about 7, 2 and 0.6 K at
# RELAX 1.0, 0.5, 0.2 -- but never to zero, while keff comes out bit-identical
# at all three, so the loop tests dk and reports the field residuals beside it
# rather than pretending they will reach zero.
#
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

GEN="$RBMK_ROOT/decks/Donjon/data/gen_rbmk_unit4.py"
DON="$RBMK_ROOT/5.1/Donjon"
OUT="${1:-$RBMK_ROOT/decks/Donjon/data/a7b_check.txt}"

run () {            # run <flow> <voidfb> -> stem
    local stem
    stem=$(U4_THM=1 U4_RODS=out U4_FLOW="$1" U4_VOIDFB="$2" python3 "$GEN" \
           | head -1 | sed 's|.*/||; s|\.don$||')
    "$RBMK_ROOT/tools/link_decks.sh" >/dev/null 2>&1
    # A7B_REUSE=1 keeps an existing .result when the deck that produced it is
    # byte-identical to the one just generated, so the prose and the tables can
    # be iterated without re-solving the core four times.  Timestamps cannot be
    # used for this: run() regenerates the deck first, so the deck is always
    # newer than the result.  The hash is written beside the result, and a
    # result without "normal end of execution" is never reused.
    local deck="$RBMK_ROOT/decks/Donjon/data/$stem.don"
    local res="$DON/Linux_aarch64/$stem.don.result"
    local sum; sum=$(md5sum < "$deck" | cut -d" " -f1)
    if [ -n "${A7B_REUSE:-}" ] && [ -f "$res" ] \
       && [ "$(cat "$res.deckmd5" 2>/dev/null)" = "$sum" ] \
       && grep -aq "normal end of execution" "$res"; then
        echo "$stem"; return
    fi
    rm -f "$DON/Linux_aarch64/$stem.don.result"
    ( cd "$DON" && ./rdonjon "$stem.don" ) >/dev/null 2>&1 || true
    printf "%s" "$sum" > "$res.deckmd5"
    echo "$stem"
}

report () {         # report <label> <stem>
    python3 - "$1" "$DON/Linux_aarch64/$2.don.result" <<'PYEOF'
import re, sys
label, path = sys.argv[1], sys.argv[2]
t = open(path, "rb").read().decode("latin1")
# The loop echoes ERRD beside ERRT since 2026-10-02: the fuel-temperature
# residual alone cannot tell a converging solve from a limit cycle at the
# boiling-onset node, and the coolant-density residual can.
it = [(int(a), float(b), float(c), float(d)) for a, b, c, d in re.findall(
      r"ITER\s+(\d+) KEFF\s+([0-9.eE+-]+) DK\s+[0-9.eE+-]+ "
      r"ERRT\s+([0-9.eE+-]+) ERRD\s+([0-9.eE+-]+)", t)]
print(f"   {label}")
print(f"   {'pass':>6} {'k-eff':>14} {'dk pcm':>9} {'fuel-T err K':>14} "
      f"{'D-cool err g/cc':>16}")
for n, (i, k, e, ed) in enumerate(it):
    dk = "" if n == 0 else f"{1e5*(k-it[n-1][1]):+9.1f}"
    print(f"   {i:>6} {k:>14.6f} {dk:>9} {e:>14.1f} {ed:>16.4f}")
# No extrapolation here any more.  It belonged to the era when the loop ran
# out of iterations: it fitted the geometric phase and added the tail to the
# last pass, which is wrong once the last pass IS the limit.  The contraction
# ratio is still worth printing -- it says the coupling is well conditioned --
# but the converged eigenvalues come from finals() below, measured not fitted.
if len(it) >= 5:
    d = [it[n][1] - it[n-1][1] for n in range(1, 5)]
    r = [d[n] / d[n-1] for n in range(1, len(d)) if d[n-1] != 0.0]
    if r:
        print(f"   first passes contract at r = {sum(r)/len(r):.3f}"
              f"  (converged in {it[-1][0]} passes, last dk "
              f"{abs(1e5*(it[-1][1]-it[-2][1])):.1f} pcm)")
hit = re.search(r"NCRRGR: REAL PARAMETER (\S+)\s+WITH VALUE\s+([0-9.eE+-]+) "
                r"IS OUTSIDE THE DOMAIN", t)
dom = re.search(r"Domain:\s+([0-9.eE+-]+)\s+<->\s+([0-9.eE+-]+)", t)
if hit:
    print(f"   STOPPED: {hit.group(1).strip()} reached {float(hit.group(2)):.4g}, "
          f"axis covers {float(dom.group(1)):.4g} to {float(dom.group(2)):.4g}")
PYEOF
}

finals () {        # finals <stem> <stem> <stem> <stem>
    python3 - "$DON" "$@" <<'PYFIN'
import re, sys
don, stems = sys.argv[1], sys.argv[2:]
labels = ["Doppler only, flow valved to power", "Doppler only, uniform flow",
          "full coupling, flow valved to power", "full coupling, uniform flow"]
k = {}
for st, lab in zip(stems, labels):
    t = open(f"{don}/Linux_aarch64/{st}.don.result", "rb").read().decode("latin1")
    m = re.findall(r"FINAL keff\s+([0-9.eE+-]+)", t)
    c = re.findall(r"CONVERGED keff\s+([0-9.eE+-]+) after\s+(\d+)", t)
    f = re.findall(r"ITER\s+1 KEFF\s+([0-9.eE+-]+)", t)
    k[lab] = (float(m[-1]) if m else None, float(c[-1][0]) if c else None,
              int(c[-1][1]) if c else None, float(f[0]) if f else None)
print(f"   {'case':<38}{'cold k':>10}{'converged':>11}{'passes':>8}{'feedback pcm':>14}")
for lab, (fin, con, it, cold) in k.items():
    if con is None or cold is None:
        print(f"   {lab:<38}{'--':>10}{'did not finish':>11}")
        continue
    # reactivity of the converged state minus the cold one: 1/k_cold - 1/k_conv.
    # Positive means the feedback ADDED reactivity, which is what the coolant
    # density does in an RBMK and is the whole reason the reactor is here.
    fb = 1e5 * (1 / cold - 1 / con)
    print(f"   {lab:<38}{cold:>10.6f}{con:>11.6f}{it:>8}{fb:>+14.0f}")
pin = [v[1] for lab, v in k.items() if "Doppler only" in lab and v[1]]
if len(pin) == 2:
    print(f"\n   the two PINNED cases differ by {abs(1e5*(1/pin[0]-1/pin[1])):.1f} pcm.")
    print("   With the density pinned the only path from flow to k is cut, so")
    print("   they must agree, and that is the measurement that the pin holds.")
live = [v[1] for lab, v in k.items() if "full coupling" in lab and v[1]]
if len(live) == 2:
    print(f"   the two LIVE cases differ by {abs(1e5*(1/live[0]-1/live[1])):.1f} pcm.")
    print("   Here the flow DOES reach k, through the coolant density, so this")
    print("   spread is the width of the flow assumption on the eigenvalue --")
    print("   no total core flow is sourced, and the real reactor is between.")
PYFIN
}

S1=$(run prop 0)
S2=$(run unif 0)
S3=$(run prop 1)
S4=$(run unif 1)
{
  echo "A7b -- the coupled core, converged, and the two feedbacks separated"
  echo "generated by tools/a7b_check.sh on $(date -u +%Y-%m-%dT%H:%MZ)"
  echo "58 x 58 x 32, DUAL 1 1, rods withdrawn, uniform 10900 MWd/t, 3200 MWth"
  echo
  echo "The axis ends that stopped this on 2026-10-01 are gone: the rebuilt"
  echo "MULTICOMPO reaches DCA 0.80 and TF 530 K, so all four cases now run to"
  echo "convergence.  Pinning the density (U4_VOIDFB=0) is no longer a way to"
  echo "get the loop to finish -- it is the decomposition, isolating Doppler."
  echo
  echo "1. DOPPLER ONLY, FLOW VALVED TO POWER"
  echo "   (U4_FLOW=prop on [D] p.95's 30 t/h at 3100 kW; density pinned)"
  echo
  report "" "$S1"
  echo
  echo "2. DOPPLER ONLY, UNIFORM FLOW  (the core average of the same scaling)"
  echo
  report "" "$S2"
  echo
  echo "3. FULL COUPLING, FLOW VALVED TO POWER  (density from the map)"
  echo
  report "" "$S3"
  echo
  echo "4. FULL COUPLING, UNIFORM FLOW"
  echo
  report "" "$S4"
  echo
  echo "READING IT."
  echo
  echo "THE FOUR EIGENVALUES, AND WHAT EACH PAIR MEASURES."
  echo
  finals "$S1" "$S2" "$S3" "$S4"
  echo
  echo "The loop converges, and the coupling machinery is right: NCR: reads"
  echo "the thermal-hydraulic state back out of the fuel map, MACINI: and"
  echo "TRIVAA: rebuild on it, and FLPOW: feeds THM: in turn.  The first four"
  echo "passes contract geometrically and the eigenvalue follows them down to"
  echo "single-precision roundoff -- dk reaches exactly zero between passes."
  echo
  echo "THE TEMPERATURE FIELD DOES NOT CONVERGE, AND IT IS NOT GOING TO."
  echo "   The fuel-temperature and coolant-density residuals fall for about"
  echo "   fifteen passes and then plateau, while the field EXTREMA freeze to"
  echo "   the thousandth and keff goes bit-stable.  Bit-stable keff means"
  echo "   bit-stable power, so a converged field would give a residual of"
  echo "   exactly zero; a plateau means a limit cycle.  The mechanism is in"
  echo "   the source rather than inferred: K0, the index of the axial node"
  echo "   where boiling starts, is an INTEGER set by the Saha-Zuber test"
  echo "   IF(TCALO.GE.TSAT-DTSUB) K0=K (THMH2O.f:383) and reset to 0 at :276,"
  echo "   and it gates the entire two-phase block at :147.  A node within"
  echo "   rounding of that threshold switches the branch on and off, moving"
  echo "   its density by a finite step each pass; DTSUB depends on the heat"
  echo "   flux, so the switch sits inside the Picard loop.  Relaxation scales"
  echo "   the plateau -- about 7, 2 and 0.6 K at RELAX 1.0, 0.5, 0.2 -- without"
  echo "   ever reaching zero, and the eigenvalue is BIT-IDENTICAL at all"
  echo "   three.  So the loop tests dk and reports the field residuals beside"
  echo "   it, and the residual plateau is a property of the void correlation"
  echo "   that A8 will march through, not an unconverged steady state."
  echo
  echo "AND THE POWER SHAPE IS NEW.  Until 2026-10-02 the block that computes"
  echo "   it never ran: the loop deletes FLUX at the end of every pass, so"
  echo "   the deck died with kernel error 666 immediately after printing the"
  echo "   loop results.  Everything reported before was from inside the loop"
  echo "   and is unaffected, but no converged power distribution existed."
  echo "   The fix re-solves once on the converged field, which is also the"
  echo "   right order: inside the loop the power is computed BEFORE that"
  echo "   pass's THM: update, so it belongs to the previous temperature."
} > "$OUT"
cat "$OUT"
