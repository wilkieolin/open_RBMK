"""
The void-coefficient bracket, as a table.

DRAGON and OpenMC agree that the RBMK void coefficient is positive and rises
steeply with burnup.  They disagree on its magnitude.  Rather than pick one,
the project carries both and lets the AZ-5 transient decide whether the
difference is load-bearing (PROGRESS.md, "A5b"; the plan of 2026-09-23).

This module turns that disagreement into a single number per state:

    r(BU, v) = dRho_OpenMC(BU, v) / dRho_DRAGON(BU, v)

where v = 1 - dca/0.72 is the void fraction and dRho is measured relative to
the nominal density 0.72 g/cm3 AT THE SAME BURNUP.  It is deliberately a ratio
of BRANCH reactivities, not of absolute k: the two codes' depletion
trajectories diverge (OpenMC is +268 pcm above DRAGON at 5 MWd/kg and -2084
below at 20), so correcting absolute k would fold a depletion difference into
a void correction.

Variant A of the transient uses r = 1 (DRAGON as computed).  Variant B
multiplies the void-induced reactivity by r.  The two therefore differ only in
how the DCA axis of the COMPO is used, which was the intent of the "two
COMPOs" in the plan.

WHY THIS IS A TABLE AND NOT A SECOND COMPO FILE
-----------------------------------------------
The plan called for a second MULTICOMPO on disk with the void branches
rescaled.  DRAGON cannot produce one: there is no cross-section scaling
facility anywhere in the write path -- not in LIB: (see the keyword list in
LIBINP.f), not in EDI:, not in COMPO:.  The alternatives were to patch the
DRAGON source (5.1/ is an upstream submodule) or to hand-edit the 114 MB LCM
ASCII file, which would reverse-engineer an undocumented format to produce an
opaque derived artifact that has to be regenerated whenever an OpenMC branch
point is added -- and two were added on 2026-09-23 alone.

Carrying the correction as data keeps it inspectable and keeps the single
source of truth for the physics in _ACompo.  The application point moves to
the consumer (A7/A8), where it is one visible multiplier rather than a second
binary.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NOMINAL = 0.72

rho = lambda k: 1 - 1 / k


def _dragon():
    """DRAGON branch reactivities from the A5b COMPO run, at TF=900 K, TG=750 K.

    Source: the A5BTAB rows of
    5.1/Dragon/Linux_aarch64/rbmk_a5b_compo.result (630 points).
    """
    path = os.path.join(HERE, "dragon_a5b_void.json")
    with open(path) as f:
        raw = json.load(f)
    out = {}
    for bu, row in raw.items():
        kn = row[str(NOMINAL)]
        out[int(bu)] = {float(d): rho(k) - rho(kn) for d, k in row.items()}
    return out


def _openmc():
    """OpenMC branch reactivities and their 1-sigma statistical error.

    Returns {bu: {dca: (dRho, sigma)}}.  The two k values are independent runs,
    so the errors add in quadrature; d(rho)/dk = 1/k^2.
    """
    by = {}
    for fn in ("branch_results81.json", "branch_results81_mid.json"):
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        for r in json.load(open(p)):
            by[(int(round(r["bu"] * 1000)), r["dca"])] = (r["k"], r["sd"])
    out = {}
    for (bu, d), (k, sd) in by.items():
        nom = by.get((bu, NOMINAL))
        if nom is None:
            continue
        kn, sn = nom
        sig = ((sd / k ** 2) ** 2 + (sn / kn ** 2) ** 2) ** 0.5
        out.setdefault(bu, {})[d] = (rho(k) - rho(kn), sig)
    return out


def ratio_table():
    """r(BU, void fraction) at the densities where OpenMC has a branch point.

    DRAGON is interpolated linearly in void fraction onto OpenMC's densities.
    The nominal point is excluded: both dRho are zero there by construction and
    the ratio is 0/0.
    """
    D, O = _dragon(), _openmc()
    tab = {}
    for bu in sorted(O):
        if bu not in D:
            continue
        dd = sorted(D[bu].items())            # (dca, dRho), ascending dca
        xs = [1 - d / NOMINAL for d, _ in dd]  # void fraction, descending
        ys = [v for _, v in dd]
        xs, ys = xs[::-1], ys[::-1]            # ascending void fraction
        row = {}
        for d, (o, sig) in sorted(O[bu].items()):
            v = 1 - d / NOMINAL
            if v <= 0:
                continue
            # linear interpolation of the DRAGON curve at this void fraction
            for i in range(len(xs) - 1):
                if xs[i] <= v <= xs[i + 1]:
                    f = (v - xs[i]) / (xs[i + 1] - xs[i])
                    dr = ys[i] + f * (ys[i + 1] - ys[i])
                    break
            else:
                dr = ys[-1]
            # DRAGON is deterministic, so all the error is OpenMC's
            row[round(v, 4)] = (None if abs(dr) < 1e-6
                                else (o / dr, abs(sig / dr)))
        tab[bu] = row
    return tab


def bracket_multiplier(bu, void_fraction):
    """r for one state, by linear interpolation of ratio_table() in both axes.

    Returns 1.0 where there is no OpenMC evidence (zero void), so variant B
    degrades gracefully to variant A rather than extrapolating.
    """
    if void_fraction <= 0:
        return 1.0
    tab = ratio_table()
    bus = sorted(tab)
    bu = min(max(bu, bus[0]), bus[-1])
    lo = max([b for b in bus if b <= bu])
    hi = min([b for b in bus if b >= bu])

    def at(b):
        vs = sorted(v for v, r in tab[b].items() if r is not None)
        if not vs:
            return 1.0
        v = min(max(void_fraction, vs[0]), vs[-1])
        for i in range(len(vs) - 1):
            if vs[i] <= v <= vs[i + 1]:
                f = (v - vs[i]) / (vs[i + 1] - vs[i])
                a, b2 = tab[b][vs[i]][0], tab[b][vs[i + 1]][0]
                return a + f * (b2 - a)
        return tab[b][vs[-1]][0]

    if lo == hi:
        return at(lo)
    f = (bu - lo) / (hi - lo)
    return at(lo) + f * (at(hi) - at(lo))


if __name__ == "__main__":
    tab = ratio_table()
    voids = sorted({v for row in tab.values() for v in row})
    print("VOID-COEFFICIENT BRACKET  r = dRho_OpenMC / dRho_DRAGON")
    print("(branch reactivity relative to 0.72 g/cm3 at the same burnup)")
    print("=" * 80)
    print(f"{'BU':>7} | " + "".join(f"{f'v={v:.3f}':>18}" for v in voids))
    print("-" * 80)
    for bu in sorted(tab):
        cells = ""
        for v in voids:
            e = tab[bu].get(v)
            cells += ("{:>18}".format("--") if e is None
                      else f"{e[0]:>11.2f} +/-{e[1]:<4.2f}")
        print(f"{bu:>7} | {cells}")
    print("-" * 80)
    print("""
The ratio is STABLE only where the DRAGON denominator is large.  At 20 MWd/t --
the accident condition -- it is 1.83-1.98 across the whole density range and the
two curves have the same SHAPE, so a single multiplier near 1.9 describes the
disagreement.  At 5 MWd/t DRAGON's own void worth dips to +155 pcm, so the
ratio there (3.1-5.5x) is a small number divided by a smaller one and carries no
information.  Fresh fuel is worse still: the curves disagree in shape, DRAGON
being non-monotonic in density while OpenMC is not.

Neither of those is the state the reactor was in.  Use the high-burnup rows.""")
    print("\nspot values from bracket_multiplier():")
    for bu in (0, 10000, 20000):
        for vf in (0.5, 0.8, 0.972):
            print(f"  BU {bu:>6d} MWd/t   void {vf:.3f}   "
                  f"r = {bracket_multiplier(bu, vf):.2f}")
