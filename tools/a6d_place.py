#!/usr/bin/env python3
"""A6d: SOLVE for the burnup placement instead of assuming one.

    python tools/a6d_place.py [iterations]

WHY.  [PAV] Table 1 gives Unit 4's burnup histogram -- eight groups over 1659
assemblies -- but no spatial map, and none has been found.  Measured 2026-10-04
(PROGRESS.md "A6d"), the placement is worth up to ~10 900 pcm on core k, which
makes it the largest single unknown in the model.  Guessing it and quoting a
sensitivity band would be honest but nearly useless, because most of that band
describes cores that cannot exist: the radial orderings put 14-20 MW in a
channel that [D] p.95 operates at 3000-3200 kW.

THE CONSTRAINT IS SOURCED EVEN THOUGH THE MAP IS NOT.  An RBMK is refuelled on
power, a channel or two a day, and the operators place fresh fuel where
reactivity is wanted while holding the channel power distribution flat --
because the channel power limit forces them to.  So the placement is not free:
it is whatever makes the power flat.  That is a physical constraint backed by a
published operating limit, and it collapses most of the band.

THE METHOD is the refuelling rule itself, iterated: run the core, rank the
channels by power, and give the most-burnt fuel to the highest-power channels.
Ranking uses a RUNNING MEAN of the power rather than the last iterate, to damp
rank flipping.

IT DOES NOT CONVERGE, AND THAT IS THE RESULT -- measured 2026-10-04, kept here
rather than deleted because it is evidence.  Peaking goes from 1.83 flat to
13-23 and oscillates; k wanders between 1.088 and 1.167.  The loop gain is
above one.  Putting burnt fuel where the power is high drives the core towards
"most-burnt in the middle", which peaks hard at the EDGE because the fresh fuel
pushed out there is unshielded and the flux piles onto it; the next iteration
swings the other way.  Without control rods or xenon there is no restoring
mechanism for it to settle against, and those are precisely the two other A6d
inputs that are still missing.  So the placement cannot be solved for on its
own: run this again only once rods and xenon are in the core deck.

NOTHING IS INVENTED.  Only the pairing of [PAV]'s groups to channels changes;
the generator re-checks the written file against the histogram as a multiset
and refuses it if it is not a permutation.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "decks", "Donjon", "data", "gen_rbmk_unit4.py")
DON = os.path.join(ROOT, "5.1", "Donjon")
WORK = os.path.join(ROOT, "decks", "Donjon", "data", "a6d_placement.txt")
STEM = "rbmk_unit4_core_out_bfile"
NITER = int(sys.argv[1]) if len(sys.argv) > 1 else 12


def histogram():
    src = open(GEN).read()
    m = re.search(r"PAV_BURNUP = \[(.*?)\]", src, re.S)
    pool = []
    for n, bu in re.findall(r"\((\d+), ([\d.]+)\)", m.group(1)):
        pool += [float(bu) * 1000.0] * int(n)
    return pool


def run(env_extra, stem=None):
    env = dict(os.environ, U4_RODS="out", **env_extra)
    subprocess.run([sys.executable, GEN], check=True, env=env,
                   stdout=subprocess.DEVNULL)
    subprocess.run([os.path.join(ROOT, "tools", "link_decks.sh")],
                   check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    stem = stem or STEM
    res = os.path.join(DON, "Linux_aarch64", f"{stem}.don.result")
    if os.path.exists(res):
        os.remove(res)
    subprocess.run(["./rdonjon", f"{stem}.don"], cwd=DON, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    txt = open(res, "rb").read().decode("latin1")
    lines = txt.splitlines()
    pw = None
    for i, l in enumerate(lines):
        if "CONTENT OF BLOCK 'POWER-CHAN" in l:
            pw = []
            for q in lines[i + 1:]:
                if "CONTENT OF BLOCK" in q or "DRVUTL" in q or "LEAVING" in q:
                    break
                pw += [float(x) for x in q.split()
                       if re.match(r"^[-+]?\d*\.?\d+E[-+]\d+$", x)]
            break
    k = re.findall(r"UNIT4_OUT KEFF\s+([0-9.eE+-]+)", txt)
    peak = re.findall(r"MAXIMUM CHANNEL POWER =\s*([0-9.]+)", txt)
    ff = re.findall(r"CHANNEL-POWER FORM FACTOR.*?MAX/AVG =\s*([0-9.]+)", txt)
    return pw, float(k[-1]), float(peak[-1]), float(ff[-1])


def main():
    # Probe with the flat map first.  It settles the channel count -- the
    # histogram has 1659 assemblies and the sourced map 1661 fuel positions --
    # and it hands the first ranking a real power distribution instead of a
    # random one, so the solver starts from the reactor rather than from noise.
    pw0, k0, peak0, ff0 = run({"U4_BURNMAP": "flat"}, "rbmk_unit4_core_out")
    n = len(pw0)
    raw = histogram()
    pool = raw + [sum(raw) / len(raw)] * (n - len(raw))
    if len(pool) != n:
        sys.exit(f"{len(raw)} assemblies cannot fill {n} channels")
    pool.sort(reverse=True)
    print(f"{n} channels, {len(raw)} sourced assemblies, "
          f"{n - len(raw)} at the core average")
    print(f"{'it':>3} {'k':>10} {'peak kW':>9} {'MAX/AVG':>8} {'moved':>7}")
    print(f"{'flat':>3} {k0:>10.6f} {peak0:>9.1f} {ff0:>8.3f} {'-':>7}")

    avg = pw0
    cur = None
    for it in range(NITER):
        order = sorted(range(n), key=lambda c: -avg[c])
        new = [0.0] * n
        for rank, ch in enumerate(order):
            new[ch] = pool[rank]
        moved = 0 if cur is None else sum(1 for a, b in zip(cur, new) if a != b)
        cur = new
        with open(WORK, "w") as f:
            f.write("\n".join(f"{v:.1f}" for v in cur))
        pw, k, peak, ff = run({"U4_BURNMAP": "file", "U4_BURNFILE": WORK})
        avg = [0.5 * a + 0.5 * p for a, p in zip(avg, pw)]
        print(f"{it:>3} {k:>10.6f} {peak:>9.1f} {ff:>8.3f} {moved:>7}")
        if it and moved == 0:
            print("fixed point reached")
            break
    with open(WORK, "w") as f:
        f.write("\n".join(f"{v:.1f}" for v in cur))
    print(f"\nplacement written to {os.path.relpath(WORK, ROOT)}")


if __name__ == "__main__":
    main()
