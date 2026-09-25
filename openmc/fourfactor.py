"""Four-factor decomposition of k-inf and of the void effect, both codes.

For an infinite lattice, with a thermal cut at 0.625 eV,

    k = nuF / A = eps * p * f * eta
      eps = nuF / nuF_th            fast-fission factor
      p   = A_th / A                fraction of absorptions that happen thermal
                                    (the resonance-escape analogue)
      f   = A_fuel,th / A_th        thermal utilisation
      eta = nuF_th / A_fuel,th      thermal reproduction factor

This is an exact identity on the reaction rates, so the void effect splits as

    d ln k = d ln eps + d ln p + d ln f + d ln eta      (x 1e5 -> pcm)

Whichever factor carries the DRAGON/OpenMC difference names the mechanism:
p -> resonance self-shielding, f -> spatial thermal flux / moderator
absorption, eta -> the U-235 thermal-epithermal spectrum, eps -> fast fission.

DRAGON: parse_dragon.py output on rbmk_rates.result (dca 0.72 then 0.02).
OpenMC: rates.py statepoints in <dir>_d0.72 and <dir>_d0.02.

Run:  python fourfactor.py <dragon_rates.txt> <openmc_prefix>
"""
import glob
import math
import os
import re
import sys

FUEL = ("U235", "U238")


def factors(A, A_th, Af_th, F, F_th):
    return dict(eps=F / F_th, p=A_th / A, f=Af_th / A_th, eta=F_th / Af_th, k=F / A)


def dragon(path):
    """{dca: factors, plus thermal-absorption shares by nuclide}"""
    out, cur = {}, None
    for line in open(path):
        if not line.startswith("@@"):
            continue
        t = line.split()
        if t[1] == "dca":
            cur = float(t[2]); out[cur] = dict(abs={}, nuf={})
        elif t[1] in ("abs", "nuf"):
            out[cur][t[1]].setdefault(t[2], {})[t[3]] = float(t[4])
    res = {}
    for dca, d in out.items():
        A_th = sum(v.get("thermal", 0) for v in d["abs"].values())
        A = A_th + sum(v.get("fast_epi", 0) for v in d["abs"].values())
        Af_th = sum(d["abs"].get(n, {}).get("thermal", 0) for n in FUEL)
        F_th = sum(v.get("thermal", 0) for v in d["nuf"].values())
        F = F_th + sum(v.get("fast_epi", 0) for v in d["nuf"].values())
        shares = {n: v.get("thermal", 0) / A_th for n, v in d["abs"].items()}
        res[dca] = (factors(A, A_th, Af_th, F, F_th), shares)
    return res


def openmc_rates(prefix):
    import openmc
    res = {}
    for d in sorted(glob.glob(f"{prefix}_d*")):
        if not os.path.isdir(d):
            continue
        dca = float(re.search(r"_d([\d.]+)$", d).group(1))
        sp = sorted(glob.glob(os.path.join(d, "statepoint.*.h5")))[-1]
        with openmc.StatePoint(sp) as s:
            n = s.get_tally(name="by nuclide").get_pandas_dataframe()
            t = s.get_tally(name="totals").get_pandas_dataframe()
        lo = n.columns[0]                       # energy low [eV] column
        th = lambda df: df[df[lo] == 0.0]
        A = t[t.score == "absorption"]["mean"].sum()
        A_th = th(t)[th(t).score == "absorption"]["mean"].sum()
        F = t[t.score == "nu-fission"]["mean"].sum()
        F_th = th(t)[th(t).score == "nu-fission"]["mean"].sum()
        nt = th(n)[th(n).score == "absorption"]
        Af_th = nt[nt.nuclide.isin(FUEL)]["mean"].sum()
        shares = {r.nuclide: r["mean"] / A_th for _, r in nt.iterrows()}
        res[dca] = (factors(A, A_th, Af_th, F, F_th), shares)
    return res


def show(name, res):
    print(f"\n{name}")
    print(f"  {'dca':>5} {'k':>9} {'eps':>9} {'p':>9} {'f':>9} {'eta':>9}")
    for dca in sorted(res, reverse=True):
        f = res[dca][0]
        print(f"  {dca:>5} {f['k']:>9.5f} {f['eps']:>9.5f} {f['p']:>9.5f}"
              f" {f['f']:>9.5f} {f['eta']:>9.5f}")
    if 0.72 in res and 0.02 in res:
        a, b = res[0.72][0], res[0.02][0]
        dl = {x: 1e5 * math.log(b[x] / a[x]) for x in ("eps", "p", "f", "eta", "k")}
        print("  void 0.72 -> 0.02, d ln (pcm): " + "  ".join(
            f"{x} {dl[x]:+.0f}" for x in ("eps", "p", "f", "eta", "k")))
        return dl


def shares(name, res):
    print(f"\n{name}: where thermal absorptions go (% of A_th)")
    keys = ["U235", "U238", "H1", "H1_H2O", "C12", "C12_GR", "Zr91", "Nb93"]
    for dca in sorted(res, reverse=True):
        s = res[dca][1]
        print(f"  {dca:>5} " + "  ".join(f"{k} {100*s[k]:.2f}" for k in keys if k in s))


if __name__ == "__main__":
    D = dragon(sys.argv[1])
    O = openmc_rates(sys.argv[2])
    dd = show("DRAGON", D)
    do = show("OpenMC", O)
    if dd and do:
        print("\nOpenMC - DRAGON, void d ln (pcm): " + "  ".join(
            f"{x} {do[x]-dd[x]:+.0f}" for x in ("eps", "p", "f", "eta", "k")))
    shares("DRAGON", D)
    shares("OpenMC", O)
