# B3b-3: the main circulation circuit (MCC) around the channels -- SCAFFOLD.
#
# One loop half (two drums, their downcomers, the suction header, the pumps, the
# pressure header and the group distribution headers) feeding its ~830 channels.
# The channels are Column.Lines Newton columns between the group-header pressure
# ph and the drum pressure pd.  The loop supplies those two pressures:
#
#   drum      lumped, saturated two-phase volume: mass M and internal energy U in a
#             fixed volume V (drums + steam space up to the stop valves); pd(M, U)
#             by inverting IF97 on the saturation line.  In: channel outflow,
#             feedwater.  Out: downcomer liquid (saturated), steam (boundary
#             condition: turbine / relief valves).
#   leg       drum liquid -> downcomers -> suction header -> pumps -> pressure
#             header -> group headers, single phase, one lumped momentum equation
#             in the total pump flow W: inertia I = sum L/A, friction, static head
#             between drum level and group headers, pump head.
#   pumps     per pump: first-quadrant homologous head and torque curves on the
#             rated point; speed fixed (grid), free coastdown on the sourced
#             inertia, or prescribed (e.g. TG-8 run-down, or DREG flows as input).
#   closure   sum over channels of their inlet mass flow = W.  Each channel's
#             converged Newton step exposes dGin/dph (Column.Lines.NewtonCache),
#             so ph and W are found by a 2x2 Newton (the channels' Schur
#             complement) instead of nested channel solves.
#
# Sources: sources/derived/{mochizuki2007_loop.csv, b3b_loop_data.md,
# ignalina_zrk_valve.csv, dreg_0123_mfcc.csv}.  Every number below carries its
# tag; numbers marked ASSUMPTION have no source and must enter B5 as a bracket,
# never be fitted to the accident record.

module Loop

using ..IF97: tsat97, psat97, prop_pT97, prop_Tx97
using ..Column: ColState
using ..Column.Lines: ChanLines, col_step_newton, NewtonCache
using Printf

export leg_state, pump_flow, pumps_dp, DrumState, drum_pressure, drum_init, drum_step, PumpParams, pump_head, pump_torque, LegParams,
       leg_unit4, pump_mcp, LoopHalf, loop_step!

const GRAV = 9.81
const KGF = 98066.5

# ------------------------------------------------------------------ drum
"""Saturated lumped drum: total mass M (kg) and internal energy U (J) in volume V (m3)."""
struct DrumState
    M::Float64
    U::Float64
end

sat(p) = (ts = tsat97(p); l = prop_Tx97(ts, 0.0); g = prop_Tx97(ts, 1.0);
          (ts=ts, vl=1 / l.rho, vg=1 / g.rho, ul=l.h - p / l.rho, ug=g.h - p / g.rho, hl=l.h, hg=g.h))

"""Equilibrium pressure of a drum: the p at which the qualities implied by the specific
volume V/M and by the specific internal energy U/M agree.  Returns (p, x, level data)."""
function drum_pressure(d::DrumState, V; plo=1.0e6, phi=16.0e6)
    v = V / d.M; u = d.U / d.M
    f(p) = (s = sat(p); (v - s.vl) / (s.vg - s.vl) - (u - s.ul) / (s.ug - s.ul))
    a, b = plo, phi; fa, fb = f(a), f(b)
    fa * fb < 0 || error("drum_pressure: no saturated state for v=$v u=$u")
    for _ in 1:200                                   # bisection + secant (Illinois)
        c = (a * fb - b * fa) / (fb - fa); fc = f(c)
        (abs(fc) < 1e-13 || abs(b - a) < 1e-6) && return c, sat(c)
        if fa * fc < 0; b, fb = c, fc; fa /= 2 else; a, fa = c, fc; fb /= 2 end
    end
    c = 0.5(a + b); c, sat(c)
end

"""Drum state holding saturated liquid volume Vl and vapour above it, at pressure p."""
function drum_init(p, V, Vl)
    s = sat(p)
    Ml = Vl / s.vl; Mg = (V - Vl) / s.vg
    DrumState(Ml + Mg, Ml * s.ul + Mg * s.ug)
end

"""
Backward-Euler drum step.  win/hin: mass flow and enthalpy entering (channel
mixture + feedwater, any number of streams as vectors); wdc: liquid to the
downcomers (leaves at h_l,sat); wst: steam out (leaves at h_g,sat).  The outflow
enthalpies are taken at the new pressure (a short fixed point).
"""
function drum_step(d::DrumState, V, dt, win, hin, wdc, wst)
    Min = sum(win) * dt; Hin = sum(win .* hin) * dt
    M = d.M + Min - (wdc + wst) * dt
    p, s = drum_pressure(d, V)
    local U
    for _ in 1:20
        U = d.U + Hin - (wdc * s.hl + wst * s.hg) * dt
        p1, s1 = drum_pressure(DrumState(M, U), V)
        abs(p1 - p) < 1e-3 && (p = p1; s = s1; break)
        p, s = p1, s1
    end
    DrumState(M, U), p
end

# ------------------------------------------------------------------ pumps
"""
Main circulation pump, first quadrant only (forward flow, forward rotation) --
enough for 01:19 to the end of the run (DREG: every pump flow stays positive).

Head  h = H/Hr = hsh a^2 - (hsh - 1) v^2      (a = w/wr, v = Q/Qr)
Torque b = T/Tr = h v / a                      (efficiency held at its rated value)

Rated point: 8000 m3/h, 200 m, 1000 rpm ([D] p. 80; [ALM98] Table 5.6 for the
RBMK-1500's CVN-8: 8000 +- 200 m3/h, 200 +- 20 m, 4300 +- 300 kW shaft, specific
speed 102).  Inertia: [ALM98] J = 3741 kg m2 (pump + motor + flywheel), GD2 = 4J =
15 t m2 = [D].  hsh, the shut-off head ratio, is an ASSUMPTION (typical of a
radial pump of this specific speed); the constant-efficiency torque is an
ASSUMPTION.  Both go into B5 as brackets; the DREG per-pump flows of the four
run-down pumps (01:23:04-01:23:43) are a test of them, not a target.
"""
Base.@kwdef struct PumpParams
    Qr::Float64 = 8000.0 / 3600.0      # m3/s
    Hr::Float64 = 200.0                # m
    wr::Float64 = 1000.0 * 2pi / 60    # rad/s
    Pshaft::Float64 = 4.3e6            # W, rated shaft power ([ALM98] 4300 +- 300 kW)
    J::Float64 = 3741.0                # kg m2 ([ALM98] Table 5.6)
    hsh::Float64 = 1.2                 # ASSUMPTION: shut-off head / rated head
end
pump_mcp() = PumpParams()

"""Pump head (Pa) at speed w (rad/s) and volumetric flow Q (m3/s), fluid density rho."""
function pump_head(p::PumpParams, w, Q, rho)
    a = w / p.wr; v = Q / p.Qr
    rho * GRAV * p.Hr * (p.hsh * a * abs(a) - (p.hsh - 1) * v * abs(v))
end

"""Flow (m3/s) through one pump at speed w delivering pressure rise dp (Pa): the
first-quadrant head curve inverted (0 when the pump cannot reach dp)."""
function pump_flow(p::PumpParams, w, dp, rho)
    a = w / p.wr
    r = (p.hsh * a * a - dp / (rho * GRAV * p.Hr)) / (p.hsh - 1)
    r > 0 ? p.Qr * sqrt(r) : 0.0
end

"""Common pressure rise of parallel pumps at speeds ws carrying total flow Q (m3/s),
and its derivative d(dp)/dQ."""
function pumps_dp(p::PumpParams, ws, Q, rho)
    hi = rho * GRAV * p.Hr * p.hsh * maximum(ws ./ p.wr)^2; lo = -hi
    f(dp) = sum(pump_flow(p, w, dp, rho) for w in ws) - Q
    for _ in 1:100
        m = 0.5(lo + hi); f(m) > 0 ? (lo = m) : (hi = m)
        hi - lo < 1e-6 && break
    end
    dp = 0.5(lo + hi); h = 1.0
    dp, -2h / (f(dp + h) - f(dp - h))      # dQ/d(dp) by central difference, inverted
end

"""Hydraulic torque (N m) on the pump at speed w, flow Q (constant-efficiency form)."""
function pump_torque(p::PumpParams, w, Q, rho)
    a = w / p.wr; v = Q / p.Qr
    Tr = p.Pshaft / p.wr
    a <= 1e-6 && return 0.0
    h = p.hsh * a * a - (p.hsh - 1) * v * abs(v)
    Tr * h * v / a
end

# ------------------------------------------------------------------ the leg
"""
The single-phase leg from the drum liquid to the group headers, lumped.
Lengths/diameters/counts per loop half (two drums) from [MOC07] Fig. 1 (quarter
loop: one drum, two pumps), doubled; mean of the quoted length ranges.
Elevations [MOC07] (EL 0 = pump base): drum centre 33.65, normal level 1.8 m
above the drum bottom (ID 2.6 m), group headers 12.15.
"""
Base.@kwdef struct LegParams
    I::Float64            # sum L/A over the series path, 1/m (parallel branches divided)
    Kf::Float64           # friction: dp = Kf W|W| / rho  (W in kg/s), lumped at rated flow
    dz::Float64           # m, drum normal water level above the group headers
    Vdrum::Float64        # m3, two drums (+ steam space to the stop valves, see note)
    npump::Int            # pumps running in this loop half
    sourced::Bool
end

function leg_unit4(; npump=4)
    A(d) = pi / 4 * d^2
    # (length m, inner diameter m, parallel count) for one loop half = 2 x [MOC07] quarter
    segs = [(0.5 * (23 + 33.5), 0.295, 24),     # downcomers, 12 per drum
            (21.0, 0.9, 1),                     # suction header (flow traverses ~half: lumped as full, conservative)
            (34.0, 0.752, 4),                   # pump suction legs
            (36.0, 0.752, 4),                   # pump discharge legs
            (18.5, 0.9, 1),                     # pressure header
            (24.0, 0.295, 32)]                  # group distribution headers, 16 per quarter
    I = sum(L / (A(d) * n) for (L, d, n) in segs)
    # friction at the rated loop-half flow, smooth pipe, Filonenko; no valve losses
    # (the throttling-regulating valve position at 01:23 is UNKNOWN -- an open item)
    rho = 760.0; mu = 1.0e-4; W = 4 * 8000 / 3600 * rho
    Kf = 0.0
    for (L, d, n) in segs
        w = W / n; v = w / (rho * A(d)); Re = rho * v * d / mu
        lam = (1.82 * log10(Re) - 1.64)^-2
        Kf += lam * L / d / (2 * A(d)^2 * n^2)  # dp = lam L/d rho v^2/2 = [lam L/(2 d A^2 n^2)] W^2/rho
    end
    zdrum_bottom = 33.65 - 1.3
    dz = zdrum_bottom + 1.8 - 12.15
    # two RBMK-1000 drums 30 m x ID 2.6 m ([MOC07]; ID confirmed by [ALM98]); the steam
    # piping to the stop valves (closed from 01:23:04-14) adds compliance: its RBMK-1000
    # volume is NOT sourced ([ALM98] 404.7 m3 per loop is RBMK-1500) -- an open item
    Vdrum = 2 * pi / 4 * 2.6^2 * 30.0
    LegParams(I=I, Kf=Kf, dz=dz, Vdrum=Vdrum, npump=npump, sourced=false)
end

# ------------------------------------------------------------------ one loop half
mutable struct LoopHalf
    leg::LegParams
    pump::PumpParams
    w::Vector{Float64}             # pump speeds, rad/s
    W::Float64                     # total pump mass flow, kg/s
    ph::Float64                    # group-header pressure, Pa
    drum::DrumState
    pd::Float64
    chans::Vector{ColState}
    caches::Vector{NewtonCache}
    lines::Vector{ChanLines}
    Av::Vector{Float64}            # ZRK throat areas (closed from the steady state)
    mult::Vector{Float64}          # channels each column stands for (sum = channels of the half)
end

"""
Enthalpy of the leg liquid: drum liquid (saturated at pd) mixed with the feedwater
(injected into the downcomer flow, [ALM98] Sec. 5.2.1), plus the pumps' shaft power
deposited in the water ([ALM98] Table 5.6: 4300 +- 300 kW per pump at rated, scaled
by the cube of speed -- the affinity law, an ASSUMPTION off the rated point).
Returns (h, T at pressure ph).
"""
function leg_state(pump::PumpParams, ws, pd, ph, W, wfw, hfw)
    hl = Loop.sat(pd).hl
    P = sum(pump.Pshaft * (w / pump.wr)^3 for w in ws)
    h = ((W - wfw) * hl + wfw * hfw + P) / W
    # T(p, h) in the liquid by Newton on IF97 cp
    T = tsat97(ph) - 5.0
    for _ in 1:30
        q = prop_pT97(ph, T); dT = (h - q.h) / q.cp; T += dT
        abs(dT) < 1e-9 && break
    end
    h, T
end

"""
One step of a loop half.  Unknowns ph (group header) and W (pump flow): the
channels are solved at the current ph, their sensitivities dGin/dph close a 2x2
Newton on [sum channel inflow - W, leg momentum]; the drum is advanced with the
channel outflows (Gauss-Seidel within the step, iterated until pd settles).

`pumpmode`: one mode for all pumps or a vector, per pump :grid (held), :coast
(free, sourced J) or a prescribed speed (rad/s).  `wst`, `wfw`, `hfw`: steam out, feedwater in.
SCAFFOLD: serial over channels; the core run threads it.
"""
function loop_step!(L::LoopHalf, g, o, pows, burns, tin_of, dt; tleg, wst=0.0, wfw=0.0, hfw=0.0,
                    pumpmode=:grid, maxouter=8, tol=1e-6)
    nch = length(L.chans)
    W0 = L.W; ph = L.ph; W = W0; pd = L.pd
    # leg liquid at tleg (SCAFFOLD: given; next, the drum-liquid / feedwater mixing model
    # plus pump heat sets it, and with it the core-inlet subcooling)
    rho_leg = prop_pT97(pd, tleg).rho
    new = similar(L.chans)
    local wnew
    for outer in 1:maxouter
        # pumps at the end of the step (implicit in W, explicit torque balance); per pump:
        # :grid (speed held), :coast (free, sourced J), or a prescribed speed (rad/s)
        modes = pumpmode isa AbstractVector ? pumpmode : fill(pumpmode, length(L.w))
        Hp0, _ = pumps_dp(L.pump, L.w, W / rho_leg, rho_leg)
        wnew = [m === :grid ? w :
                m === :coast ? w - dt * pump_torque(L.pump, w, pump_flow(L.pump, w, Hp0, rho_leg), rho_leg) / L.pump.J :
                Float64(m) for (w, m) in zip(L.w, modes)]
        Hp, dHdQ = pumps_dp(L.pump, wnew, W / rho_leg, rho_leg)    # parallel pumps share the rise
        dHdW = dHdQ / rho_leg
        # channels at this ph
        Win = 0.0; dWdph = 0.0
        for i in 1:nch
            s = col_step_newton(g[i], o, L.chans[i], pows[i], burns[i], L.lines[i], L.Av[i], ph, pd, tin_of(i), dt;
                                cache=L.caches[i])
            new[i] = s
            Win += L.mult[i] * s.Gin * L.lines[i].Ach
            dWdph += L.mult[i] * L.caches[i].dGin_dph * L.lines[i].Ach
        end
        # 2x2 Newton: f1 = Win(ph) - W, f2 = I (W - W0)/dt + Kf W|W|/rho - (pd + rho g dz + Hp) + ph
        f1 = Win - W
        f2 = L.leg.I * (W - W0) / dt + L.leg.Kf * W * abs(W) / rho_leg - (pd + rho_leg * GRAV * L.leg.dz + Hp) + ph
        J11 = dWdph; J12 = -1.0
        J21 = 1.0; J22 = L.leg.I / dt + 2 * L.leg.Kf * abs(W) / rho_leg - dHdW
        det = J11 * J22 - J12 * J21
        dph = -(f1 * J22 - J12 * f2) / det
        dW = -(J11 * f2 - J21 * f1) / det
        ph += dph; W += dW
        (abs(f1) < tol * abs(W) && abs(dph) < 1e-6 * ph) && break
        outer == maxouter && @warn "loop_step!: header closure not converged" f1 dph
    end
    # drum with the converged channel outflows
    kmaxs = [findlast(!=(0.0), pows[i]) for i in 1:nch]
    wout = [L.mult[i] * new[i].G[kmaxs[i]] * L.lines[i].Ach for i in 1:nch]
    hout = [new[i].h[kmaxs[i]] for i in 1:nch]
    d1, pd1 = drum_step(L.drum, L.leg.Vdrum, dt, vcat(wout, wfw), vcat(hout, hfw), W, wst)
    L.chans .= new; L.W = W; L.ph = ph; L.w = wnew; L.drum = d1; L.pd = pd1
    L
end

end # module Loop
