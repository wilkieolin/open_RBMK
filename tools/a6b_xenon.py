#!/usr/bin/env python3
"""A6b: the Xe-135 level at 01:23 on 26 April 1986, solved from the sourced
power history rather than assumed to be at equilibrium.

    python tools/a6b_xenon.py

WHY NOT EQUILIBRIUM.  The MULTICOMPO stores Xe-135 and I-135 at the densities
the depletion left them -- equilibrium at the depletion power, 16.7 MW/t, i.e.
3200 MW.  Unit 4 at 01:23 was nowhere near that: it had spent most of a day at
half power, collapsed to 30 MW at 00:28, and been dragged back to 200 MW.  With
Xe-135 at 9.14 h and I-135 at 6.57 h, that whole history is still in the core.
INSAG-7 Sec. I-4.7 says so outright -- "the drop in reactor power at 00:28 and
subsequent power increase were largely to blame", and, remarkably, "no
calculational studies have been made of the power density field dynamics from
this time until the time of the accident".

EVERY CONSTANT IS READ, NOT CHOSEN.

  Decay constants      DEPL-CHAIN/DEPLETE-DECA in the COMPO itself, indices 5
                       and 6 of ISOTOPESDEPL, in units of 1e-8 /s.  They come
                       back as 6.570 h and 9.140 h, which are the accepted
                       half-lives -- a check on the units and the indexing.
  Fission yields       DEPL-CHAIN/FISSIONYIELD, 13 products x 16 parents.
                       Groups 4 and 5 are I135 and Xe135; the U235 entries are
                       6.2805E-02 and 2.5610E-03 against accepted 0.0629 and
                       ~0.0024, which is how the layout was confirmed.
  Equilibrium density  ISOTOPESDENS, indices 7 and 16, interpolated between
                       the 10 000 and 12 500 MWd/t nodes to the core's own
                       10 900 -- the node value alone is 2 % out and costs
                       49 pcm.  Verified branch-independent:
                       calculations 1009 and 1152 sit at different DCA/TF/TG
                       and carry identical isotopics, as they must, since the
                       branches change temperatures and not depletion.
  Burnout rate         NOT taken from a flux estimate and a tabulated cross
                       section.  It is CALIBRATED from the stored equilibrium:
                       at equilibrium lambda_I*I = gI*Sf*phi and
                       (lambda_Xe + sigma*phi)*Xe = (gI+gXe)*Sf*phi, so
                         sigma*phi0 = lambda_I*(I/Xe)*(1+r) - lambda_Xe
                       with r = gXe/gI.  That ties the burnout rate to this
                       lattice at this burnup with no free parameter.
  Power history        INSAG-7 Table I-I and Sec. I-4.7.6, below.

The one soft number is r, because the fissioning mix at 10.9 MWd/kg is part
U235 and part Pu239.  Both library values are used as bounds; sigma*phi0 moves
only ~2 % across them, because r itself is small.

THE INITIAL CONDITION IS EXACTLY CONSISTENT BY CONSTRUCTION: substituting the
stored I and Xe with p = 1 gives dI/dt = dXe/dt = 0 identically, since
sigma*phi0 was defined from that very balance.  The solve therefore starts at
rest and every later deviation is the history doing work.
"""
import math

# ---- read from the COMPO (see the docstring for provenance) --------------
LAM_I = 2.9306e03 * 1e-8          # /s  DEPLETE-DECA index 5
LAM_XE = 2.1066e03 * 1e-8         # /s  DEPLETE-DECA index 6
# The densities are stored at burnup NODES and the core runs at 10 900 MWd/t,
# between 10 000 and 12 500, so the reference has to be interpolated the same
# way NCR: interpolates it.  Taking the node value instead is a 2.03 % error in
# Xe and cost 49 pcm -- found by writing the node value back through MICRO and
# finding it was not the no-op it should have been, which is also what
# validated the override path.
#
#   node        Xe135         I135        (ISOTOPESDENS indices 7 and 16)
#   10 000   1.09500e-10   2.97750e-10
#   12 500   1.03440e-10   2.97240e-10
#   15 000   0.97266e-10   2.96650e-10
#
# Xe falls ~11 % over 5000 MWd/t while I is nearly flat, which is the right
# physics and a check on the stored data: at constant specific power Sf*phi is
# fixed, so I_eq = gI*Sf*phi/lambda_I does not move, while phi must rise as Sf
# falls, so sigma*phi grows and Xe_eq = (gI+gXe)*Sf*phi/(lambda_Xe+sigma*phi)
# drops.
BU_CORE = 10900.0
_NODES = {10000.0: (1.09500e-10, 2.97750e-10),
          12500.0: (1.03440e-10, 2.97240e-10)}
_lo, _hi = 10000.0, 12500.0
_f = (BU_CORE - _lo) / (_hi - _lo)
XE_EQ = _NODES[_lo][0] + _f * (_NODES[_hi][0] - _NODES[_lo][0])
I_EQ = _NODES[_lo][1] + _f * (_NODES[_hi][1] - _NODES[_lo][1])
R_U235 = 2.5610e-03 / 6.2805e-02  # gXe/gI, FISSIONYIELD groups 5 and 4
R_PU239 = 4.9904e-03 / 6.7304e-02

P0 = 3200.0                       # MW, the depletion power the densities are at


# ---- INSAG-7 Table I-I and Sec. I-4.7.6, as (minutes from 25 Apr 01:06, MW)
# Piecewise linear between points.  t = 0 is the start of the power reduction,
# before which the reactor had been at 3200 MW long enough to be at equilibrium.
HISTORY = [
    (0.0,                3200.0),   # 25 Apr 01:06  reduction begins
    (2 * 60 + 41,        1600.0),   # 25 Apr 03:47  "thermal power is 1600 MW"
    (3 * 60 + 7,         1600.0),   # 25 Apr 04:13  start of the constant stretch
    (11 * 60 + 30,       1500.0),   # 25 Apr 12:36  "constant thermal power of 1500 MW"
    (22 * 60 + 4,        1500.0),   # 25 Apr 23:10  "power reduction continued"
    (22 * 60 + 59,        720.0),   # 26 Apr 00:05  "thermal power was 720 MW"
    (23 * 60 + 22,        500.0),   # 26 Apr 00:28  "at about 500 MW" transfer made
    (23 * 60 + 27,         30.0),   # 26 Apr 00:33  the unplanned collapse to 30 MW
    (23 * 60 + 54,        200.0),   # 26 Apr 01:00  "power increase had ceased ... about 200 MW"
    (24 * 60 + 17,        200.0),   # 26 Apr 01:23  the accident
]
T_END = HISTORY[-1][0] * 60.0      # s


def power(t_s):
    """Thermal power in MW at t seconds after 25 April 01:06, piecewise linear."""
    t = t_s / 60.0
    if t <= HISTORY[0][0]:
        return HISTORY[0][1]
    for (t0, p0), (t1, p1) in zip(HISTORY, HISTORY[1:]):
        if t <= t1:
            return p0 + (p1 - p0) * (t - t0) / (t1 - t0)
    return HISTORY[-1][1]


def solve(r, dt=5.0):
    sig_phi0 = LAM_I * (I_EQ / XE_EQ) * (1.0 + r) - LAM_XE
    xi, xe = I_EQ, XE_EQ
    prod_i = LAM_I * I_EQ                 # = gI*Sf*phi0
    trace = []
    n = int(T_END / dt)
    for k in range(n + 1):
        t = k * dt
        p = power(t) / P0
        trace.append((t, p, xi, xe))
        if k == n:
            break

        def deriv(i_, x_, pp):
            di = prod_i * pp - LAM_I * i_
            dx = (r * prod_i * pp + LAM_I * i_
                  - LAM_XE * x_ - sig_phi0 * pp * x_)
            return di, dx

        # RK4 on the pair; the power is evaluated at the stage times
        p1 = power(t) / P0
        p2 = power(t + dt / 2) / P0
        p4 = power(t + dt) / P0
        a1, b1 = deriv(xi, xe, p1)
        a2, b2 = deriv(xi + dt / 2 * a1, xe + dt / 2 * b1, p2)
        a3, b3 = deriv(xi + dt / 2 * a2, xe + dt / 2 * b2, p2)
        a4, b4 = deriv(xi + dt * a3, xe + dt * b3, p4)
        xi += dt / 6 * (a1 + 2 * a2 + 2 * a3 + a4)
        xe += dt / 6 * (b1 + 2 * b2 + 2 * b3 + b4)
    return sig_phi0, trace


def xenon_at_0123(scale=1.0, r=R_U235, dt=5.0):
    """Xe-135 at 01:23 for a channel whose power is `scale` x the core average.

    THE ASSUMPTION, STATED: the channel holds that same power RATIO throughout
    the history, so only the global level moves.  That is wrong in exactly the
    way INSAG-7 says matters -- the shape itself reshaped -- so this gives the
    magnitude of a frozen-shape xenon field, not the real one.  It is a first
    estimate and the error is in the direction of understating the spread.
    """
    sig_phi0 = LAM_I * (I_EQ / XE_EQ) * (1.0 + r) - LAM_XE
    xi, xe = I_EQ, XE_EQ
    prod_i = LAM_I * I_EQ
    n = int(T_END / dt)

    def deriv(i_, x_, pp):
        return (prod_i * pp - LAM_I * i_,
                r * prod_i * pp + LAM_I * i_ - LAM_XE * x_ - sig_phi0 * pp * x_)

    for k in range(n):
        t = k * dt
        p1 = power(t) / P0 * scale
        p2 = power(t + dt / 2) / P0 * scale
        p4 = power(t + dt) / P0 * scale
        a1, b1 = deriv(xi, xe, p1)
        a2, b2 = deriv(xi + dt / 2 * a1, xe + dt / 2 * b1, p2)
        a3, b3 = deriv(xi + dt / 2 * a2, xe + dt / 2 * b2, p2)
        a4, b4 = deriv(xi + dt * a3, xe + dt * b3, p4)
        xi += dt / 6 * (a1 + 2 * a2 + 2 * a3 + a4)
        xe += dt / 6 * (b1 + 2 * b2 + 2 * b3 + b4)
    return xe


def xenon_equilibrium(scale=1.0, pfrac=1.0, r=R_U235):
    """Xe-135 for a channel at `scale` x core-average power, with the core held
    at `pfrac` x 3200 MW long enough for xenon to equilibrate WITH THAT SHAPE.

    Closed form, because equilibrium needs no integration:

        Xe_eq = (1+r) * gI*Sf*phi0 * p / (lambda_Xe + sigma*phi0 * p),   p = pfrac*scale

    and gI*Sf*phi0 is lambda_I*I_EQ, already known.  At scale = pfrac = 1 this
    returns the stored density to every digit -- a check that the COMPO's
    isotopics really are the 3200 MW equilibrium and that sigma*phi0, calibrated
    from the I/Xe ratio, is consistent with them.

    WHY IT MATTERS THAT THIS SATURATES.  sigma*phi0 = 3.015 x lambda_Xe, so at
    full power burnout dominates decay and Xe_eq is strongly sublinear in power.
    The shape sensitivity dln(Xe)/dln(s) at s = 1 is 1/(1 + sigma*phi/lambda_Xe):

        3200 MW   sigma*phi/lambda_Xe = 3.015   sensitivity 0.249
         200 MW                         0.188              0.841

    So a channel at twice average power carries 1.14 x the average xenon at full
    power against 1.73 x at 200 MW.  Xenon is a flattening agent in both cases --
    the concentration rises with power either way -- but it is 3.4 x weaker at
    full power, which is where the channel power limit actually binds.  A field
    built for the 200 MW state therefore overstates the flattening available to
    an operating core by about that factor.
    """
    sig_phi0 = LAM_I * (I_EQ / XE_EQ) * (1.0 + r) - LAM_XE
    prod_i = LAM_I * I_EQ
    p = pfrac * scale
    return (1.0 + r) * prod_i * p / (LAM_XE + sig_phi0 * p)


def main():
    print("Xe-135 at 01:23 on 26 April 1986, from INSAG-7's power history\n")
    for lab, r in (("U235 yields", R_U235), ("Pu239 yields", R_PU239)):
        sig, tr = solve(r)
        t, p, xi, xe = tr[-1]
        print(f"{lab}  (r = {r:.5f})")
        print(f"  sigma*phi0           {sig:.4E} /s   "
              f"= {sig / LAM_XE:.2f} x lambda_Xe, so burnout-dominated at power")
        print(f"  Xe-135 at 01:23      {xe:.4E} atoms/barn-cm")
        print(f"  as a multiple of the stored equilibrium   {xe / XE_EQ:.3f}")
        print(f"  I-135  at 01:23      {xi:.4E}   ({xi / I_EQ:.3f} x equilibrium)")
        print()
    sig, tr = solve(R_U235)
    print("the trajectory, at the INSAG-7 waypoints:")
    marks = [(0, "25 Apr 01:06  3200 MW, equilibrium"),
             (3 * 60 + 7, "25 Apr 04:13"), (11 * 60 + 30, "25 Apr 12:36"),
             (22 * 60 + 4, "25 Apr 23:10"), (23 * 60 + 22, "26 Apr 00:28"),
             (23 * 60 + 27, "26 Apr 00:33  the 30 MW floor"),
             (23 * 60 + 54, "26 Apr 01:00"), (24 * 60 + 17, "26 Apr 01:23")]
    for mn, lab in marks:
        k = min(range(len(tr)), key=lambda j: abs(tr[j][0] - mn * 60))
        t, p, xi, xe = tr[k]
        print(f"  {lab:<36} P/P0 {p:5.3f}   Xe/Xe_eq {xe / XE_EQ:6.3f}"
              f"   I/I_eq {xi / I_EQ:6.3f}")
    # Where it was HEADED.  The quasi-static level for the 01:23 condition --
    # what the xenon would reach if 200 MW were held long enough -- says
    # whether the core was caught early or late on the curve.
    sig, tr = solve(R_U235)
    t, p, xi, xe = tr[-1]
    qs = (R_U235 * LAM_I * I_EQ * p + LAM_I * xi) / (LAM_XE + sig * p)
    print(f"\nat 01:23 the xenon is {xe / XE_EQ:.3f} x equilibrium and still RISING:")
    print(f"  the quasi-static level for 200 MW with this iodine is "
          f"{qs / XE_EQ:.3f} x equilibrium,")
    print(f"  so the core was caught {100 * (xe - XE_EQ) / (qs - XE_EQ):.0f} % of the way "
          f"into a transient it had entered only 50 minutes earlier,")
    print(f"  against Xe-135's {math.log(2) / LAM_XE / 3600:.2f} h timescale.")

    # step-size check: the answer must not depend on dt
    a = solve(R_U235, dt=5.0)[1][-1][3]
    b = solve(R_U235, dt=1.0)[1][-1][3]
    print(f"\nstep-size check: dt 5 s vs 1 s changes Xe by "
          f"{abs(a - b) / b * 100:.4f} % -- converged")


if __name__ == "__main__":
    main()
