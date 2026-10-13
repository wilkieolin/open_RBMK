#!/usr/bin/env python3
"""A8 transient summary and comparison against INSAG-7.

    tools/a8_insag.py <result> [<result> ...]

Reads the A8STEP / A8THM / A8SHAPE records a kinetic deck from
gen_rbmk_unit4.py writes, and prints for each run:

  - the first-second dip (INSAG-7 p. 121: all three models show a reactivity
    drop during the first second);
  - when total power passes 530 MW and when the period first falls below
    20 s -- the two emergency signals of 01:23:43, 3 s after EPS-5
    (INSAG-7 Table I-1; p. 121: none of the three models reproduces them);
  - the peak, its time, and the energy released;
  - the hottest node's fuel enthalpy, from THM's MAX-T-FUEL through Fink's
    UO2 enthalpy, against the 220 cal/g = 920.5 kJ/kg disintegration
    threshold of INSAG-7 p. 67;
  - the volumetric peaking factor Kv of each printed bundle-power map
    (INSAG-7 p. 121: "approximately 6.0"; p. 67: Kv = 5.5 in Ref. [28]);
  - Model 1's power (Fig. II-11, sources/derived/insag7_fig_II11_model1.csv)
    at the same times, in multiples of the 200 MW initial power.

MAX-T-FUEL is THM's effective (Rowlands-weighted) fuel temperature of the
hottest bundle, not the radial average; for a parabolic profile it sits
1/18 of the centre-to-surface difference above the average, so the
enthalpy read from it is a slight overestimate.  Compared, not tuned.
"""
import math, os, re, sys

H_FAIL = 220.0 * 4.184          # kJ/kg UO2, INSAG-7 p. 67
M_UO2 = 270.03                  # g/mol
P_NOM = 3200.0                  # MW, the unit of Fig. II-11's power axis
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def h_uo2(T):
    """H(T) - H(298.15 K) of UO2 in kJ/kg.  Fink, J. Nucl. Mater. 279 (2000) 1,
    solid below 3120 K; liquid above with Cp = 130 J/mol/K and a 70 kJ/mol
    heat of fusion (same paper)."""
    C1, th, C2, C3, Ea = 81.613, 548.68, 2.285e-3, 2.360e7, 18531.7

    def hs(t):
        return (C1 * th * (1.0 / (math.exp(th / t) - 1.0))
                + C2 * t * t + C3 * math.exp(-Ea / t))
    if T <= 3120.0:
        h = hs(T) - hs(298.15)
    else:
        h = hs(3120.0) - hs(298.15) + 70.0e3 + 130.0 * (T - 3120.0)
    return h / M_UO2


def model1():
    pts = []
    f = os.path.join(ROOT, "sources", "derived", "insag7_fig_II11_model1.csv")
    for l in open(f):
        if l.startswith("#"):
            continue
        s, t, v = l.strip().split(",")
        if s == "power_nominal":
            pts.append((float(t), float(v) * P_NOM))
    return pts


def interp(pts, t):
    if t < pts[0][0] or t > pts[-1][0]:
        return None
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)


def read(res):
    L = open(res, "rb").read().decode("latin1").splitlines()
    step, thm, shapes = [], [], []
    num = re.compile(r"[-+]?\d\.\d+E[-+]\d+")
    i = 0
    while i < len(L):
        l = L[i]
        if l.startswith(">|A8STEP"):
            w = l[2:].split()
            step.append((float(w[3]), float(w[5])))
        elif l.startswith(">|A8THM"):
            w = l[2:].split()
            thm.append((float(w[3]), float(w[5]), float(w[7])))
        elif l.startswith(">|A8SHAPE"):
            t = float(l[2:].split()[3])
            j = i + 1
            while "POWER-BUND" not in L[j]:
                j += 1
            v = []
            j += 1
            while j < len(L):
                x = num.findall(L[j])
                if not x and v and L[j].strip():
                    break
                v += [float(a) for a in x]
                j += 1
                if len(v) >= 46508:
                    break
            shapes.append((t, v))
            i = j
            continue
        i += 1
    end = "normal" if any("A8DONE" in l for l in L[-400:]) else \
        next((l.strip() for l in reversed(L) if "THM" in l and ":" in l and
              ("REACHED" in l or "FAILURE" in l)), "stopped")
    return step, thm, shapes, end


def summary(res):
    step, thm, shapes, end = read(res)
    p0 = float(os.environ.get("A8_P0", "200"))
    tt = [t for t, _ in step]
    pp = [p for _, p in step]
    out = [os.path.basename(res)]
    imin = min(range(len(pp)), key=lambda k: pp[k] if tt[k] <= 2.0 else 1e30)
    out.append(f"  dip            {pp[imin]/p0:.3f} at {tt[imin]:.2f} s")
    t530 = next((t for t, p in step if p >= 530.0), None)
    out.append(f"  530 MW         {'%.2f s' % t530 if t530 else 'not reached'}")
    # period from a 0.1 s centred log-derivative
    tper = None
    for k in range(5, len(pp) - 5):
        r = math.log(pp[k + 5] / pp[k - 5]) / (tt[k + 5] - tt[k - 5])
        if r > 1.0 / 20.0:
            tper = tt[k]
            break
    out.append(f"  period < 20 s  {'%.2f s' % tper if tper else 'never'}")
    k = max(range(len(pp)), key=lambda k: pp[k])
    peak_note = "" if k < len(pp) - 1 else "  (still rising at the end)"
    out.append(f"  peak           {pp[k]/p0:.2f} x at {tt[k]:.2f} s{peak_note}")
    e = sum(0.5 * (pp[j] + pp[j + 1]) * (tt[j + 1] - tt[j])
            for j in range(len(pp) - 1)) / 1000.0
    out.append(f"  energy         {e:.2f} GJ to {tt[-1]:.2f} s ({end})")
    if thm:
        hm = [(t, h_uo2(T), T) for t, T, _ in thm]
        tf = next((t for t, h, _ in hm if h >= H_FAIL), None)
        out.append(f"  hottest fuel   {hm[-1][2]:.0f} K = {hm[-1][1]:.0f} kJ/kg at "
                   f"{hm[-1][0]:.2f} s (from {hm[0][1]:.0f}); 920.5 kJ/kg "
                   + (f"reached at {tf:.2f} s" if tf else "not reached"))
        out.append(f"  min D-COOL     {min(d for _, _, d in thm):.3f} g/cm3")
    for t, v in shapes:
        nz = [x for x in v if x > 0]
        if len(nz) == 46508:
            nb = 28
            nch = len(v) // nb
            ax = [sum(v[b * nch:(b + 1) * nch]) for b in range(nb)]
            low = sum(ax[:14]) / sum(ax)
            out.append(f"  t={t:4.2f} s  Kv {max(nz)/(sum(nz)/len(nz)):.2f}  "
                       f"lower-half share {low:.3f}")
    m1 = model1()
    row = []
    for tq in (1, 2, 3, 4, 5, 6, 7):
        ours = interp(step, tq)
        m = interp(m1, tq)
        row.append(f"{tq} s: {ours/p0:.2f}" if ours else f"{tq} s: -")
        # below ~0.3 nominal units the figure's markers are as large as the
        # values (the 200 MW start reads 0.11 against 0.0625), so Model 1 is
        # quoted only where it can be read
        row[-1] += f" / {m/p0:.1f}" if m and m >= 0.3 * P_NOM else " / -"
    out.append("  P/P0 ours / Model 1:  " + "   ".join(row))
    return "\n".join(out)


if __name__ == "__main__":
    for r in sys.argv[1:]:
        print(summary(r))
        print()
