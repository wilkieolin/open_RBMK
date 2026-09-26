"""
The void-reactivity bracket, as additive corrections (METHOD_CONVERGENCE_PLAN C3 / C5).

Three variants of the void reactivity dRho(BU, v), measured relative to the
nominal 0.72 g/cm3 at the same burnup (v = 1 - dca/0.72 is the void fraction):

  A    DRAGON production as computed: the A5b COMPO (SHEM-361, Zr self-shielded,
       production mesh, collision probabilities).  dragon_a5b_void.json.
  A'   A + the measured method correction: what DRAGON's converged settings
       (4x flat-flux mesh + MOC with P1 scattering) add on top of production.
       Measured, never fitted: rbmk_meth_bestmoc - zr361 (fresh) and
       oedbest<bu> - oed<bu> (10, 15 MWd/kg, same fuel, only the method differs).
  B    OpenMC: DRAGON's full-void worth REPLACED by OpenMC's matched value
       (deposited-energy burnup scale, DRAGON's 10P graphite): method_study.json
       g10p (fresh) and accident_ref.json (10, 15 MWd/kg).  At partial void it
       follows DRAGON's own void shape, because OpenMC has matched points only at
       full void.  The shapes agree: fresh, dRho(0.35)/dRho(0.02) is 0.65 in
       OpenMC and 0.69 / 0.72 in DRAGON production / converged.

The corrections are additive in dRho and are applied by the consumer (A7/A8)
on top of the COMPO, which stays the single source of truth for the physics.
DRAGON cannot write a scaled COMPO (no cross-section scaling facility anywhere in
LIB:, EDI: or COMPO:), which is why this is a table.

The multiplicative r = dRho_OpenMC / dRho_DRAGON of the 2026-09-23 version is
retired.  On the 172-group library DRAGON's void worth crossed zero near
5 MWd/kg, which made r a small number over a smaller one.

Between correction nodes both corrections are linear in BU and in v (zero at
v = 0).  Above 15 MWd/kg they are held at their 15 MWd/kg values (flagged):
there is no matched OpenMC point at 20, and Unit 4 had nothing near 20.

    python void_bracket.py        # table at every COMPO burnup, pcm and $
"""
import json
import os
import platform
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = os.environ.get("DRAGON_ARCH", f"Linux_{platform.machine()}")
DRA = os.path.join(ROOT, "5.1", "Dragon", ARCH)
DON = os.path.join(ROOT, "5.1", "Donjon", ARCH)
NOMINAL = 0.72
NUM = r"([-+]?\d+\.\d+[eE][-+]\d+)"

rho = lambda k: 1 - 1 / k
vf = lambda dca: 1 - dca / NOMINAL


def _methtab(vid):
    """{dca: k} from the METHTAB rows of rbmk_meth_<vid>.result."""
    out = {}
    for line in open(os.path.join(DRA, f"rbmk_meth_{vid}.result"), errors="ignore"):
        m = re.search(r">\|METHTAB\s+\d+\s+" + NUM + r"\s+" + NUM, line)
        if m:
            out[round(float(m.group(1)), 2)] = float(m.group(2))
    return out


def _drho(rows, d):
    return rho(rows[d]) - rho(rows[NOMINAL])


def dragon():
    """A: {bu: {dca: dRho}} at TF 900 / TG 750 from the COMPO run."""
    raw = json.load(open(os.path.join(HERE, "dragon_a5b_void.json")))
    return {int(bu): {float(d): rho(k) - rho(row[str(NOMINAL)]) for d, k in row.items()}
            for bu, row in raw.items()}


def method_correction():
    """A' - A: {bu: {dca: dRho}} at the measured nodes."""
    pairs = {0: ("zr361", "bestmoc"), 10000: ("oed10", "oedbest10"),
             15000: ("oed15", "oedbest15")}
    out = {}
    for bu, (prod, best) in pairs.items():
        p, b = _methtab(prod), _methtab(best)
        out[bu] = {d: _drho(b, d) - _drho(p, d) for d in (0.35, 0.02)}
    return out


def openmc_full_void():
    """B at full void: {bu: (dRho(0.02), sigma)} on the matched basis."""
    out = {}
    ms = {(r["variant"], round(r["dca"], 2)): (r["k"], r["sd"])
          for r in json.load(open(os.path.join(HERE, "method_study.json")))}
    (kn, sn), (kv, sv) = ms[("g10p", 0.72)], ms[("g10p", 0.02)]
    out[0] = (rho(kv) - rho(kn), ((sv / kv**2) ** 2 + (sn / kn**2) ** 2) ** 0.5)
    ar = {(int(round(r["bu"] * 1000)), r["dca"]): (r["k"], r["sd"])
          for r in json.load(open(os.path.join(HERE, "accident_ref.json")))}
    for bu in (10000, 15000):
        (kn, sn), (kv, sv) = ar[(bu, 0.72)], ar[(bu, 0.02)]
        out[bu] = (rho(kv) - rho(kn), ((sv / kv**2) ** 2 + (sn / kn**2) ** 2) ** 0.5)
    return out


def _lin(nodes, x):
    """Piecewise-linear interpolation over sorted (x, y) nodes, clamped at the ends."""
    xs = [n[0] for n in nodes]
    if x <= xs[0]:
        return nodes[0][1]
    if x >= xs[-1]:
        return nodes[-1][1]
    for (x0, y0), (x1, y1) in zip(nodes, nodes[1:]):
        if x0 <= x <= x1:
            return y0 + (x - x0) / (x1 - x0) * (y1 - y0)


def _dragon_at(D, bu, dca):
    """DRAGON dRho at (bu, dca): linear in void fraction, then in BU."""
    def at(b):
        pts = sorted((vf(d), v) for d, v in D[b].items())
        return _lin(pts, vf(dca))
    bus = sorted(D)
    if bu in D:
        return at(bu)
    lo = max(b for b in bus if b <= bu); hi = min(b for b in bus if b >= bu)
    return at(lo) + (bu - lo) / (hi - lo) * (at(hi) - at(lo))


def corrections(bu, dca, D=None, M=None, O=None):
    """(dRho_A, dRho_A', dRho_B) at one state, in absolute reactivity."""
    D = D or dragon(); M = M or method_correction(); O = O or openmc_full_void()
    a = _dragon_at(D, bu, dca)
    v = vf(dca)
    # A': method correction, linear in v through (0, 0) and the 0.35 / 0.02 nodes
    def mc(b):
        return _lin([(0.0, 0.0), (vf(0.35), M[b][0.35]), (vf(0.02), M[b][0.02])], v)
    a1 = a + _lin([(b, mc(b)) for b in sorted(M)], bu)
    # B: OpenMC's full-void worth, with DRAGON's void shape at partial void
    def ob(b):
        full = _dragon_at(D, b, 0.02)
        return O[b][0] * (_dragon_at(D, b, dca) / full) - _dragon_at(D, b, dca)
    b_ = a + _lin([(b, ob(b)) for b in sorted(O)], bu)
    return a, a1, b_


def beta_curve():
    """{bu: beta_eff} at nominal state from rbmk_a5b_beta.don (DONJON on the COMPO)."""
    out = {}
    p = os.path.join(DON, "rbmk_a5b_beta.don.result")
    for line in open(p, errors="ignore"):
        m = re.search(r">\|A5BBETA\s+" + r"\s+".join([NUM] * 5), line)
        if m:
            bu, dca, tf, tg, b = (float(x) for x in m.groups())
            if abs(dca - NOMINAL) < 1e-6 and abs(tf - 900) < 1e-3 and abs(tg - 750) < 1e-3:
                out[int(round(bu))] = b
    return out


if __name__ == "__main__":
    D, M, O = dragon(), method_correction(), openmc_full_void()
    try:
        B = beta_curve()
    except FileNotFoundError:
        B = {}
    print("Method correction A' - A (pcm), measured:")
    for bu in sorted(M):
        print(f"  BU {bu:>6d}: dca 0.35 {1e5 * M[bu][0.35]:+6.0f}   dca 0.02 {1e5 * M[bu][0.02]:+6.0f}")
    print("OpenMC full-void reference (pcm), matched basis:")
    for bu in sorted(O):
        print(f"  BU {bu:>6d}: {1e5 * O[bu][0]:+6.0f} +/- {1e5 * O[bu][1]:.0f}")
    print("\nFull-void (0.02 g/cm3) worth, three variants" + (" (pcm and $)" if B else " (pcm)"))
    print(f"  {'BU':>6} {'A':>8} {'A-prime':>8} {'B':>8}" + (f" {'beta':>8} {'A $':>6} {'A-p $':>6} {'B $':>6}" if B else ""))
    bus = sorted(set(D) | {10900})
    for bu in bus:
        a, a1, b = corrections(bu, 0.02, D, M, O)
        flag = "  (held at 15 MWd/kg correction)" if bu > 15000 else ""
        line = f"  {bu:>6d} {1e5 * a:+8.0f} {1e5 * a1:+8.0f} {1e5 * b:+8.0f}"
        if B:
            bb = _lin(sorted(B.items()), bu)
            line += f" {bb:8.6f} {a / bb:+6.2f} {a1 / bb:+6.2f} {b / bb:+6.2f}"
        print(line + flag + ("   <- Unit 4 average" if bu == 10900 else ""))
