# PROGRESS (46): the drum heating rate needed for the recorded post-AZ-5 rises (1 s, from saturated
# drums -- a lower bound), against the model's own; per loop half.
# Energy bound: drum heating rate (riser mixture, separated in the drum) needed for a 1 s pressure rise
using RBMKCore.Loop, RBMKCore.IF97, Printf
const KGF = 98066.5
R = 1.3; h = 1.8; Al = R^2 * acos((R - h) / R) - (R - h) * sqrt(2R * h - h^2)
Vdr = 2 * pi / 4 * 2.6^2 * 30.0
W = 5400.0                                     # kg/s per half (the runs' flow at +5..+7 s)
function dp1(p0, V, tau, X; dt=0.01)
    d = drum2_from(drum_init(p0, V, Al * 60.0), V, tau); p = p0
    for _ in 1:round(Int, 1.0 / dt)
        hl = drum_hl(d, p); s = Loop.sat(p)
        d, p = drum_step(d, V, dt, [W], [s.hl + X / W], W, 0.0)
    end
    p - p0
end
function solveX(p0, V, tau, target)
    a, b = 0.0, 5e10
    for _ in 1:60
        m = 0.5(a + b); dp1(p0, V, tau, m) < target ? (a = m) : (b = m)
    end
    0.5(a + b)
end
println("per loop half; X = heating rate reaching the drum (GW) for the 1 s rise; model's own rise vs the record")
for (lab, tau, Vst, pL, dpL_mod, pR, dpR_mod) in (("tau 1 s, V 150", 1.0, 150.0, 68.63, 1.75, 71.14, 2.20),
                                                ("tau 3 s, V 296", 3.0, 296.0, 68.43, 1.77, 70.98, 2.60),
                                                ("tau 10 s, V 450", 10.0, 450.0, 68.46, 2.15, 71.39, 3.42))
    V = Vdr + Vst
    xLm = solveX(pL * KGF, V, tau, dpL_mod * KGF); xLr = solveX(pL * KGF, V, tau, 5.3 * KGF)
    xRm = solveX(80.1 * KGF, V, tau, dpR_mod * KGF); xRr = solveX(80.1 * KGF, V, tau, 8.3 * KGF)
    @printf("%-16s L (+5->+6 s): model %.2f GW, record (+5.3) %.2f GW, extra %.2f GW | R (+7->+8 s, from 80.1): model-rate %.2f GW, record (+8.3) %.2f GW, extra %.2f GW\n",
            lab, xLm / 1e9, xLr / 1e9, (xLr - xLm) / 1e9, xRm / 1e9, xRr / 1e9, (xRr - xRm) / 1e9)
end
println("\nfrozen liquid (tau = Inf), the most pressure-effective delivery -- the floor:")
for Vst in (150.0, 296.0, 450.0)
    V = Vdr + Vst
    @printf("  V %3.0f: L +5.3 needs %.2f GW; R +8.3 from 80.1 needs %.2f GW\n", Vst,
            solveX(68.5KGF, V, Inf, 5.3KGF) / 1e9, solveX(80.1KGF, V, Inf, 8.3KGF) / 1e9)
end
