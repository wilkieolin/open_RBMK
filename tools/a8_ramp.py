#!/usr/bin/env python3
"""Static reactivity of the AZ-5 rod ramp, as a function of travel.

For each advance d, every CPS rod is moved d cm from its sourced 01:22:30
position and the core is solved statically.  The reactivity is quoted the way
KINSOL: normalises it -- rho = 1 - k(0)/k(d) -- so it is directly comparable
with the transient's power trace.

This does two jobs at once.  It measures where the net reactivity of the scram
crosses zero, which is the positive-scram window; and because the advances are
NOT multiples of the 25 cm axial mesh, it is the only check that NEWMVF's
sub-node volume-fraction interpolation behaves, the base map having no answer
to compare against off the mesh.  A jagged or stepped curve through the plane
boundaries would say the interpolation is wrong.
"""
import csv
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "decks", "Donjon", "data", "gen_rbmk_unit4.py")
RUNDIR = os.path.join(ROOT, "5.1", "Donjon")
BINDIR = os.path.join(RUNDIR, "Linux_aarch64")
MAP = os.path.join(ROOT, "sources", "derived", "unit4_channel_map.csv")
CPS = {"RR", "AZ", "AZOC", "AR", "USP"}
WORK = "/tmp/a6d_rods"


def depths(adv):
    rows = [r for r in csv.DictReader(open(MAP)) if r["type"] in CPS]
    out = []
    for r in rows:
        q = round(float(r["depth_cm"] or 0) / 25.0) * 25.0
        out.append(min(700.0, q + adv))
    path = os.path.join(WORK, "ramp_%+07.2f.txt" % adv)
    open(path, "w").write("\n".join("%.4f" % x for x in out) + "\n")
    return path


def run(adv):
    env = dict(os.environ, U4_DEV="1", U4_RODS="wat", U4_DEVQ="0",
               U4_RODDEPTH=depths(adv))
    env.pop("U4_KIN", None)
    out = subprocess.run([sys.executable, GEN], env=env, capture_output=True,
                         text=True)
    if out.returncode:
        raise SystemExit("generator failed:\n" + out.stdout + out.stderr)
    name = os.path.basename(re.search(r"wrote (\S+\.don)", out.stdout).group(1))
    subprocess.run([os.path.join(ROOT, "tools", "link_decks.sh")],
                   capture_output=True)
    res = os.path.join(BINDIR, name + ".result")
    if os.path.exists(res):
        os.remove(res)                      # standing rule 5
    subprocess.run(["./rdonjon", name], cwd=RUNDIR, capture_output=True,
                   timeout=1800)
    if not os.path.exists(res):
        raise SystemExit(name + ": no .result")
    txt = open(res, "rb").read().decode("latin1")
    m = re.findall(r"KEFF\s+([0-9.]+e[-+][0-9]+)", txt)
    pk = re.findall(r"MAXIMUM CHANNEL POWER\s*=\s*([0-9.]+)", txt)
    ff = re.findall(r"MAX/AVG\s*=\s*([0-9.]+)\)", txt)
    return float(m[-1]), float(pk[-1]), float(ff[-1])


def main():
    advs = [float(x) for x in sys.argv[1:]] or \
        [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80]
    os.makedirs(WORK, exist_ok=True)
    k0 = None
    print("  adv cm        k        rho pcm    peak kW   MAX/AVG   planes")
    for adv in advs:
        k, pk, ff = run(adv)
        if k0 is None:
            k0 = k
        rho = (1.0 - k0 / k) * 1.0e5
        print("  %7.2f  %.6f  %+9.1f  %9.1f  %8.4f   %5.2f"
              % (adv, k, rho, pk, ff, adv / 25.0))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
