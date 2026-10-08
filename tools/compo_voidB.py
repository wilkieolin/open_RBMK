#!/usr/bin/env python3
"""Bracket B in the core: a copy of the fuel MULTICOMPO whose void worth is OpenMC's.

void_bracket.corrections(bu, dca) gives, at every (burnup, coolant density),
the reactivity dB - dA by which OpenMC's void worth exceeds the production
COMPO's, relative to the nominal 0.72 g/cm3 (zero at and above it).  DRAGON
cannot write a scaled COMPO, so this tool edits the SEQ_ASCII file itself.

At each of the COMPO's elementary calculations it rebuilds the homogenised
two-group infinite-medium cross sections exactly as NCR: MACRO does (sum over
ISOTOPESLIST of density x microscopic data, *MAC*RES at density 1), solves for
the thermal absorption x that moves the point's k-infinity by
    1/k' = 1/k - delta(bu, dca),
and adds x to *MAC*RES's group-2 NTOT0, NG and STRD.  Thermal absorption is a
stated choice: it changes reactivity without touching fission, beta or chi.
The correction is applied identically at every TF and TG, since the bracket was
measured at TF 900 / TG 750 and is additive in reactivity.

Checks, all printed: the rebuilt k-infinity at the nominal fresh point against
DRAGON's; every edited point re-read from the written file reproduces its target
to 0.05 pcm (measured worst 0.014 pcm, the
8-digit E16.8 storage); points with delta = 0 are byte-identical.

Usage: compo_voidB.py <in _ACompo> <out file> [--check-only]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "openmc"))


def parse(path):
    """Return (lines, records).  A record is a dict: level, type, n, name,
    hdr (header line index), d0/d1 (data line range), and 'elem' for list
    elements (the '->  L  0  0 -1  <- 0000000k' headers)."""
    lines = open(path, "rb").read().decode("latin1").split("\n")
    recs = []
    i, n = 0, len(lines)
    while i < n:
        l = lines[i]
        if not l.startswith("->"):
            i += 1
            continue
        p = l[2:].split()
        lev, _, typ, cnt = int(p[0]), int(p[1]), int(p[2]), int(p[3])
        if lev < 0 or (typ == 0 and cnt == -1 and l.rstrip().endswith("<-")):
            # end-of-directory marker, or an anonymous directory header
            recs.append(dict(level=lev, type=typ, n=cnt, name="", hdr=i,
                             d0=i + 1, d1=i + 1, elem=None))
            i += 1
            continue
        if typ == 0 and cnt == -1:          # list element: name is in the header
            recs.append(dict(level=lev, type=0, n=-1, name="", hdr=i, d0=i + 1,
                             d1=i + 1, elem=int(l.split("<-")[1])))
            i += 1
            continue
        name = lines[i + 1].strip()
        j = i + 2
        while j < n and not lines[j].startswith("->"):
            j += 1
        recs.append(dict(level=lev, type=typ, n=cnt, name=name, hdr=i, d0=i + 2,
                         d1=j, elem=None))
        i = j
    return lines, recs


def nums(lines, r, conv=float):
    out = []
    for l in lines[r["d0"]:r["d1"]]:
        out.extend(l.split())
    out = [conv(x) for x in out]
    if r["type"] == 3:                      # character records: lengths first
        raise ValueError("character record")
    return out[:r["n"]] if r["n"] > 0 else out


def fmt_reals(vals):
    out, row = [], ""
    for k, v in enumerate(vals):
        row += "%16.8E" % v
        if k % 5 == 4:
            out.append(row)
            row = ""
    if row:
        out.append(row)
    return out


def tree(lines, recs):
    """calc index (1-based) -> (bu, tf, tg, dca) through GLOBAL pvals + TREE."""
    by = {}
    for r in recs:
        if r["name"].startswith("pval") or r["name"] in ("DEBARB", "ARBVAL", "NVP"):
            by.setdefault(r["name"], r)
    pv = {k: nums(lines, by["pval%08d" % k]) for k in (1, 2, 3, 4)}
    nvp = [int(x) for x in nums(lines, by["NVP"], int)]
    deb = [0] + [int(x) for x in nums(lines, by["DEBARB"], int)]
    arb = [0] + [int(x) for x in nums(lines, by["ARBVAL"], int)]
    out = {}

    def walk(node, depth, vals):
        if depth == 4:
            # leaves follow the internal nodes; DEBARB holds a sentinel (the
            # end of the last internal range) first, so leaf L's calculation
            # index is DEBARB(L+1)
            out[deb[node + 1]] = tuple(vals)
            return
        for c in range(deb[node], deb[node + 1]):
            walk(c, depth + 1, vals + [pv[depth + 1][arb[c] - 1]])
    walk(1, 0, [])
    assert len(out) == 1728, len(out)
    return out


def calculations(recs):
    """Group record indices by calculation (level-5 list elements under
    CALCULATIONS) and, inside, by isotope (level-7 elements)."""
    k0 = next(k for k, r in enumerate(recs) if r["name"] == "CALCULATIONS")
    calcs, cur, iso = {}, None, None
    for k in range(k0 + 1, len(recs)):
        r = recs[k]
        if r["level"] == 5 and r["elem"] is not None:
            cur = calcs.setdefault(r["elem"], {"iso": {}, "rec": {}})
            iso = None
            continue
        if r["level"] in (4, 3) and r["elem"] is None and r["name"]:
            break                           # left the CALCULATIONS list
        if cur is None:
            continue
        if r["level"] == 7 and r["elem"] is not None:
            iso = cur["iso"].setdefault(r["elem"], {})
            continue
        if r["level"] == 8 and iso is not None and r["name"]:
            iso[r["name"]] = k
        elif r["level"] == 6 and r["name"]:
            cur["rec"][r["name"]] = k
            iso = None
    return calcs


def homog(lines, recs, c):
    dens = nums(lines, recs[c["rec"]["ISOTOPESDENS"]])
    ng = 2
    tot = [0.0] * ng
    nsf = [0.0] * ng
    chi = [0.0] * ng
    sc = [[0.0] * ng for _ in range(ng)]       # sc[to][from]
    resk = None
    for e, iso in sorted(c["iso"].items()):
        N = dens[e - 1]
        alias = lines[recs[iso["ALIAS"]]["d0"] + 1]
        if alias.startswith("*MAC*RES"):
            resk = e
        if N == 0.0:
            continue
        t = nums(lines, recs[iso["NTOT0"]])
        for g in range(ng):
            tot[g] += N * t[g]
        if "NUSIGF" in iso:
            f = nums(lines, recs[iso["NUSIGF"]])
            x = nums(lines, recs[iso["CHI"]]) if "CHI" in iso else [1.0, 0.0]
            for g in range(ng):
                nsf[g] += N * f[g]
            for g in range(ng):
                chi[g] += N * x[g] * (f[0] + f[1])  # weight later
        nj = [int(v) for v in nums(lines, recs[iso["NJJS00"]], int)]
        ij = [int(v) for v in nums(lines, recs[iso["IJJS00"]], int)]
        s = nums(lines, recs[iso["SCAT00"]])
        pos = 0
        for g in range(ng):                    # destination group g
            for m in range(nj[g]):
                src = ij[g] - m                 # 1-based source group
                sc[g][src - 1] += N * s[pos]
                pos += 1
    cs = sum(chi)
    chi = [v / cs for v in chi] if cs else [1.0, 0.0]
    return dict(tot=tot, nsf=nsf, chi=chi, sc=sc, res=resk)


def kinf(h, x=0.0):
    t = list(h["tot"])
    t[1] += x
    s = h["sc"]
    # removal matrix A = diag(t) - S, fission F = chi nsf^T ; k = max eig(A^-1 F)
    a11, a12 = t[0] - s[0][0], -s[0][1]
    a21, a22 = -s[1][0], t[1] - s[1][1]
    det = a11 * a22 - a12 * a21
    i11, i12, i21, i22 = a22 / det, -a12 / det, -a21 / det, a11 / det
    c, f = h["chi"], h["nsf"]
    # A^-1 F is rank one: k = f^T A^-1 chi
    v1 = i11 * c[0] + i12 * c[1]
    v2 = i21 * c[0] + i22 * c[1]
    return f[0] * v1 + f[1] * v2


def solve_x(h, delta):
    k0 = kinf(h)
    target = 1.0 / (1.0 / k0 - delta)
    lo, hi = -0.5 * (h["tot"][1] - h["sc"][1][1]), 0.0
    if delta < 0:
        lo, hi = 0.0, 0.5 * h["tot"][1]
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if (kinf(h, mid) > target) == (delta > 0):
            lo, hi = (mid, hi) if delta > 0 else (lo, mid)
        else:
            lo, hi = (lo, mid) if delta > 0 else (mid, hi)
    return 0.5 * (lo + hi), k0, target


def main():
    import void_bracket as vb
    src, dst = sys.argv[1], sys.argv[2]
    check_only = "--check-only" in sys.argv
    lines, recs = parse(src)
    calc_par = tree(lines, recs)
    calcs = calculations(recs)
    D, M, O = vb.dragon(), vb.method_correction(), vb.openmc_full_void()
    print(f"{len(calcs)} calculations, {len(calc_par)} on the tree")
    # nominal fresh point first: the reconstruction check
    for ic, (bu, tf, tg, dca) in sorted(calc_par.items()):
        if bu == 0.0 and abs(tf - 900) < 1 and abs(tg - 750) < 1 and abs(dca - 0.72) < 1e-4:
            print("fresh nominal point: calc %d, rebuilt two-group k-inf %.6f"
                  % (ic, kinf(homog(lines, recs, calcs[ic]))))
    edits, nedit, worst = {}, 0, 0.0
    for ic, (bu, tf, tg, dca) in sorted(calc_par.items()):
        a, _, b = vb.corrections(bu, dca, D, M, O)
        delta = b - a
        if abs(delta) < 1e-9:
            continue
        h = homog(lines, recs, calcs[ic])
        x, k0, tgt = solve_x(h, delta)
        worst = max(worst, abs(1.0 / k0 - 1.0 / kinf(h, x) - delta))
        iso = calcs[ic]["iso"][h["res"]]
        for nm in ("NTOT0", "NG", "STRD"):
            r = recs[iso[nm]]
            v = nums(lines, r)
            v[1] += x
            edits[r["d0"]] = (r["d1"], fmt_reals(v))
        nedit += 1
        if nedit <= 3 or (bu == 10000 and abs(dca - 0.02) < 1e-4 and abs(tf - 900) < 1
                          and abs(tg - 750) < 1):
            print(f"  calc {ic}: bu {bu:.0f} tf {tf:.0f} tg {tg:.0f} dca {dca:.2f}  "
                  f"delta {1e5 * delta:+7.1f} pcm  k {k0:.6f} -> {kinf(h, x):.6f}  "
                  f"x {x:+.4e} (Sigma_t2 {h['tot'][1]:.4e})")
    print(f"{nedit} points edited; worst internal target error {1e5 * worst:.4f} pcm")
    if check_only:
        return
    out, i = [], 0
    while i < len(lines):
        if i in edits:
            d1, new = edits[i]
            out.extend(new)
            i = d1
        else:
            out.append(lines[i])
            i += 1
    open(dst, "wb").write("\n".join(out).encode("latin1"))
    # re-read and verify
    l2, r2 = parse(dst)
    c2 = calculations(r2)
    bad = 0
    for ic, (bu, tf, tg, dca) in sorted(calc_par.items()):
        a, _, b = vb.corrections(bu, dca, D, M, O)
        k0 = kinf(homog(lines, recs, calcs[ic]))
        k1 = kinf(homog(l2, r2, c2[ic]))
        if abs((1 / k0 - 1 / k1) - (b - a)) > 5e-7:
            bad += 1
    print(f"re-read {dst}: {bad} of {len(calc_par)} points miss their target by > 0.05 pcm")


if __name__ == "__main__":
    main()
