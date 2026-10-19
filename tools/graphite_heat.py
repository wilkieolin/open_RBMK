#!/usr/bin/env python3
"""Graphite-to-coolant heat at 01:23 on 26 April 1986 (B3b loop model, open item 4).

[MOC07] (Mochizuki 2007) used ~20 MW per quarter-loop, "investigated", with the graphite
held at 400 C.  Here the number is derived instead, from a lumped graphite stack:

    C dTg/dt = f_g P(t) - G (Tg - Tc)

  f_g   fraction of fission energy deposited in the graphite: 5 % ([ALM98] p. 56,
        "95 % ... in the fuel element and an additional 5 % is released in the graphite
        during neutron moderation and gamma absorption").
  G     stack-to-channel conductance, CLOSED at nominal: G = f_g P_nom / (Tg_nom - Tc),
        with Tg_nom bracketed by the two [D] figures for the stack temperature at nominal
        power, 570 C (the operating-unit table, [D] p. ~6198 of the text) and 700-750 C
        (the design regime maintained by the He-N2 gas, [D] Sec. on the graphite stack).
        These are MAXIMA; a lumped stack is represented by them, which over-states the
        conductance-weighted mean and so brackets the released heat from above.
  C     stack heat capacity: graphite volume from the core model's geometry (2488
        columns [D] x 0.25 m x 0.25 m x 8 m stack height, less one 114 mm bore per channel
        position), density 1.7 g/cm3 (RBMK graphite GR-280, ~1.65-1.75), cp(T) of
        graphite (~1.3-1.6 kJ/kg K over 300-600 C; a bracket).
  P(t)  the sourced power history (INSAG-7 Table I-I and Sec. I-4.7.6, as in a6b_xenon.py),
        from equilibrium at 3200 MW before 01:06 on 25 April.
  Tc    coolant temperature, 285 C nominal (a single value: Tc moves by a few K against
        Tg - Tc of 100-400 K).

Part of the heat goes to the 227 CPS/detector channels, which have their own circuit
([D]: "partly to the CPS channels"); the fuel channels' share is taken by count,
1661/(1661+227).

Outputs Q at 01:23:04 (the start of the run-down) for the corners of the bracket.
"""
import math

HISTORY = [                      # minutes from 25 Apr 01:06, MW (copied from a6b_xenon.py)
    (0.0, 3200.0), (2 * 60 + 41, 1600.0), (3 * 60 + 7, 1600.0), (22 * 60 + 4, 1500.0),
    (22 * 60 + 59, 720.0), (23 * 60 + 22, 500.0), (23 * 60 + 27, 30.0), (23 * 60 + 54, 200.0),
    (24 * 60 + 17, 200.0)]


def power(tmin):
    for (t0, p0), (t1, p1) in zip(HISTORY, HISTORY[1:]):
        if t0 <= tmin <= t1:
            return p0 + (p1 - p0) * (tmin - t0) / (t1 - t0)
    return HISTORY[-1][1]


def stack_capacity(cp):
    ncol, pitch, height = 2488, 0.25, 8.0
    nhole = 1661 + 227                      # fuel + CPS/detector bores
    vol = ncol * pitch ** 2 * height - nhole * math.pi / 4 * 0.114 ** 2 * height
    return vol * 1700.0 * cp, vol


def run(Tg_nom, cp, f_g=0.05, P_nom=3200e6, Tc=285.0):
    G = f_g * P_nom / (Tg_nom - Tc)
    C, vol = stack_capacity(cp)
    Tg = Tg_nom                              # equilibrium at 3200 MW before 01:06, 25 Apr
    dt = 10.0
    t = 0.0
    tend = (24 * 60 + 17) * 60.0 - 36.0      # 01:23:04
    while t < tend:
        P = power(t / 60.0) * 1e6
        Tg += dt * (f_g * P - G * (Tg - Tc)) / C
        t += dt
    Q = G * (Tg - Tc)
    return dict(G=G, C=C, tau_h=C / G / 3600, Tg=Tg, Q=Q, Q_fuel=Q * 1661 / (1661 + 227),
                Qeq200=f_g * 200e6, vol=vol)


if __name__ == "__main__":
    print("graphite stack: volume %.0f m3, mass %.0f t" % (stack_capacity(1.0)[1], stack_capacity(1.0)[1] * 1.7))
    print(" Tg_nom  cp    tau(h)  Tg(01:23)  Q_total  Q_fuel_ch  per quarter  (equilibrium at 200 MW: %.0f MW)"
          % (0.05 * 200))
    for Tg_nom in (570.0, 660.0, 750.0):
        for cp in (1300.0, 1450.0, 1600.0):
            r = run(Tg_nom, cp)
            print(" %5.0f  %5.0f  %5.2f   %7.1f C  %6.1f MW  %6.1f MW   %6.1f MW" %
                  (Tg_nom, cp, r["tau_h"], r["Tg"], r["Q"] / 1e6, r["Q_fuel"] / 1e6, r["Q_fuel"] / 4e6))
