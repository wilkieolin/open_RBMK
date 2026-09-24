"""Pull the 2-group per-isotope absorption balance out of the DRAGON edition
and put it in the same form as the OpenMC tallies in rates_d*.txt."""
import os, platform, re, sys

# The DRAGON result lands in the arch-named output dir of the 5.1 submodule.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.environ.get("DRAGON_ARCH", f"Linux_{platform.machine()}")
R = os.environ.get("DRAGON_RESULT",
                   os.path.join(ROOT, "5.1", "Dragon", ARCH, "rbmk_rates.result"))
txt = open(R, errors="ignore").read()

# the two cases appear in order: dca = 0.72 then dca = 0.02
hom = re.findall(
    r"F L U X E S   A N D   H O M O G E N I Z E D   X - S.*?"
    r"G R O U P   :   1.*?\n\s+1\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+).*?"
    r"G R O U P   :   2.*?\n\s+1\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)",
    txt, re.S)

def iso_blocks(txt):
    """{case_index: {isotope: {'N':x, 'NWT0':[g1,g2], 'NG':[..], ...}}}"""
    out = []
    for m in re.finditer(r"CROSS SECTION OF MERGED/CONDENSED ISOTOPE '(\S+)\s*\d*'"
                         r"(.*?)(?=CROSS SECTION OF MERGED/CONDENSED ISOTOPE|\Z)",
                         txt, re.S):
        name, body = m.group(1), m.group(2)
        nd = re.search(r"NUMBER DENSITY =\s+([\d.E+-]+)", body)
        rec = {"N": float(nd.group(1)) if nd else 0.0}
        for rm in re.finditer(r"REACTION '\s*(\S+)\s*':\s*\n\s*([\d.E+-]+)\s+([\d.E+-]+)",
                              body):
            rec[rm.group(1)] = [float(rm.group(2)), float(rm.group(3))]
        out.append((name, rec))
    return out

# split the isotope blocks between the two cases at the second homogenized table
split_at = [m.start() for m in re.finditer(
    r"F L U X E S   A N D   H O M O G E N I Z E D   X - S", txt)]
cases = []
for i, s in enumerate(split_at):
    e = split_at[i+1] if i+1 < len(split_at) else len(txt)
    cases.append(iso_blocks(txt[s:e]))

DCA = [0.72, 0.02]
for ci, (blocks, h) in enumerate(zip(cases, hom)):
    f1, _, sa1, nf1 = map(float, h[:4])
    f2, _, sa2, nf2 = map(float, h[4:])
    tot_abs = sa1 * f1 + sa2 * f2
    tot_nuf = nf1 * f1 + nf2 * f2
    print(f"@@ dca {DCA[ci]}")
    print(f"@@ kinf {tot_nuf/tot_abs:.6f}")
    print(f"@@ totabs {tot_abs:.8e}")
    print(f"@@ flux {f1:.6e} {f2:.6e}")
    seen = {}
    for name, rec in blocks:
        if "NWT0" not in rec:
            continue
        ng = rec.get("NG", [0, 0]); nf = rec.get("NFTOT", [0, 0])
        nsf = rec.get("NUSIGF", [0, 0])
        n = rec["N"]; w = rec["NWT0"]
        a1 = n * (ng[0] + nf[0]) * w[0]
        a2 = n * (ng[1] + nf[1]) * w[1]
        p1 = n * nsf[0] * w[0]
        p2 = n * nsf[1] * w[1]
        if name in seen:
            seen[name][0] += a1; seen[name][1] += a2
            seen[name][2] += p1; seen[name][3] += p2
        else:
            seen[name] = [a1, a2, p1, p2]
    print(f"@@ totnuf {tot_nuf:.8e}")
    for name, (a1, a2, p1, p2) in sorted(seen.items(),
                                         key=lambda x: -(x[1][0]+x[1][1])):
        if a1 + a2 <= 0:
            continue
        print(f"@@ abs {name} fast_epi {a1:.8e} {100*a1/tot_abs:.4f}")
        print(f"@@ abs {name} thermal  {a2:.8e} {100*a2/tot_abs:.4f}")
        if p1 + p2 > 0:
            print(f"@@ nuf {name} fast_epi {p1:.8e} {100*p1/tot_nuf:.4f}")
            print(f"@@ nuf {name} thermal  {p2:.8e} {100*p2/tot_nuf:.4f}")
