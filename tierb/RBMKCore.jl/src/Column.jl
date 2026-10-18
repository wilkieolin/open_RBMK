# B3b: an implicit channel solver that replaces THMTRS's flow iteration.
#
# THMTRS solves each channel step by a fixed point: march up with the
# cell's own density LAGGED in the continuity term, recompute densities,
# repeat.  Its gain is ~1/(dt G) (PROGRESS 28): at low flow it diverges
# unless relaxed to a crawl, and it fails outright after the peak in three
# of five band cases (PROGRESS 39/40).
#
# Here the same physics (THM's closures: THMH2O, THMROD, IF97) is written
# as a conservative finite-volume scheme, fully implicit (backward Euler),
# cells = fuel slices, mass fluxes on faces, donor-cell enthalpy:
#   mass    (rho_k - rho0_k) dz/dt + G_top - G_bot = 0
#   energy  (rho_k h_k - rho0_k h0_k) dz/dt + G_top h_out - G_bot h_in = Q_k dz
# With upward flow the column is block lower-triangular and is solved
# EXACTLY in one upward march -- no flow iteration at all.  When G_top >= 0
# the two equations combine to
#   h_k = (rho0_k h0_k dz/dt + G_bot h_in + Q_k dz) / (G_bot + rho0_k dz/dt)
# (the cell's new density cancels), explicit but for the wall heat Q_k(h_k),
# a contraction solved by substitution; rho_k then follows from the closure
# and G_top from continuity.  A reversed top face (G_top < 0) couples the
# cell to the one above; there each cell is solved by a bracketed root find
# of the full residual (continuous through G_top = 0) inside Gauss-Seidel
# sweeps over the column, and a step that still fails is sub-stepped.
#
# The rod and wall are solved inside every cell evaluation (THMROD's
# conduction, THMH2O's wall balance against the rod's response), so a
# converged cell is converged in all of its fields.
#
# Pressure: without `mom` this is THM's assumption (p = outlet pressure in
# every cell, inlet mass flux prescribed).  With `mom` the pressure marches up
# the column through each cell's momentum balance, and `Lines` puts the
# channel between its group header and drum (inlet line + ZRK valve, outlet
# line) -- B3b-2.
#
# Marching (and shooting on the inlet flux) is the wrong tool once pressure
# matters: in a boiling cell a pressure error returns through the void as a
# flux error ~ dz/dt d(rho)/dp, a gain > 1 per cell at small dt near
# saturation.  `Lines.col_step_newton` therefore solves every cell's mass,
# energy and momentum balance and both line equations simultaneously (Newton,
# banded finite-difference Jacobian).  For that the closures must be smooth
# functions of (h, p, G); THM's are not, in four places, all fixed only on
# this path (`tight` / `localonset` in Channel.thmh2o, cell_eval):
#   1. Saha-Zuber onset carried up the column from the first cell past onset
#      (the void of the next cell jumps from 0 when onset changes cell): here
#      the local-conditions form, onset subcooling from the cell's own flux;
#   2. inner tolerances (rod <-> wall 1e-3 K, THMH2O's wall 1e-5, THMPH 1e-5,
#      the 0.1 K saturation switch): iterated to fixed points;
#   3. THMH2O's sticky KWA = 0 wall iteration, which stops on either side of
#      saturation path-dependently: a bracketed root with the regime a
#      function of T_w alone;
#   4. prop_pT evaluated at exactly Tsat, which rounds to either phase.
# With these the Newton converges quadratically (3-4 iterations a step) and
# the solution converges in dt (test/b3b_lines.jl, PROGRESS 41).

module Column

import ..Channel as Ch
using ..Channel: thmh2o, thmrod, H2OSave, RodWork, prop_pT, tsat, XS
using Printf

export ColState, col_from_steady, col_step, col_state_fields, MomBC, dfric, bundle_chi

mutable struct ColState
    temps::Matrix{Float64}    # [NDTOT, NZ] rod nodes 1..NDTOT-1, wall NDTOT
    rho::Vector{Float64}      # cell mixture density (kg/m3)
    rhol::Vector{Float64}     # THMH2O's Gauss-averaged liquid density (D-COOL source in THM)
    h::Vector{Float64}        # cell mixture enthalpy (J/kg)
    G::Vector{Float64}        # mass flux through the TOP face of cell k (kg/m2/s)
    Gin::Float64              # mass flux through the bottom face of the first fuel cell
    p::Vector{Float64}        # cell pressure (Pa)
    tcomb::Vector{Float64}
    tcool::Vector{Float64}
    tsurf::Vector{Float64}
    tcent::Vector{Float64}
    xfl::Vector{Float64}
    eps::Vector{Float64}
    kwa::Vector{Int}
    hin::Float64              # inlet enthalpy
    tin::Float64
    pout::Float64
    ptop::Float64             # pressure at the top face of the last fuel cell (momentum mode)
    sweeps::Int               # diagnostics of the last step
    substeps::Int
end

"""Start from a THMDRV steady state (Channel.thm_steady): uniform mass flux."""
function col_from_steady(s::Ch.ChanState, g::Ch.ChanGeom, speed, tin, pout)
    a = prop_pT(pout, tin)
    Gin = speed * a.rho
    nz = length(s.dcool)
    ColState(copy(s.temps), copy(s.dcool), copy(s.dliq), copy(s.enth), fill(Gin, nz), Gin, copy(s.pres),
             copy(s.tcomb), copy(s.tcool), copy(s.tsurf), copy(s.tcent), copy(s.xfl), copy(s.eps), copy(s.kwa),
             a.h, tin, pout, pout, 0, 0)
end

# one evaluation of cell k at enthalpy h: closure, rod and wall, given the
# face mass flux Gtop used by the correlations.  Returns the results without
# committing THMH2O's save state.
struct CellEval
    rho::Float64; rhoY::Float64; rhol::Float64; tcalo::Float64; tsclad::Float64; xfl::Float64; eps::Float64
    kwa::Int; k0::Int; phi::Float64; tc1::Float64; qwall::Float64; sv::H2OSave
end

function cell_eval(g, o, k, h, hinflow, Gcorr, p, sv0::H2OSave, k0in, xfl0, eps0, tre10, tre11, tsclad0,
                   qfuel, qcool, burn, dtinv, w::RodWork; tight=false, localonset=false)
    nd = g.ndtot
    sv = H2OSave(sv0.dhsub, sv0.dsat)
    tsclad = tsclad0
    local r, tc1, x2, x3
    # tight: THMROD's conductivities are evaluated on the guess tre11 and the wall loop
    # stops at 1e-3 K, so the cell's result depends on its starting guess; iterate both
    # to a fixed point so it is a function of (h, p, G) alone (the Newton solver needs that)
    for outer in 1:(tight ? 40 : 1)
    for it in 1:(tight ? 60 : 4)                          # rod <-> wall consistency
        tc1, x2, x3, zf = thmrod(g, o, dtinv, tre10, tre11, qfuel, tsclad, burn, w)
        phi0 = (zf[1] - tsclad * zf[2]) / g.rad[nd-1]
        delth = h - hinflow
        ent = ntuple(i -> hinflow + (1.0 + XS[i]) / 2.0 * delth, 4)
        sv.dhsub = sv0.dhsub; sv.dsat = sv0.dsat
        r = thmh2o(sv, 1, k, k0in, p, Gcorr, h, ent, g.hd, g.rad[nd-1], zf, phi0, xfl0, eps0, g.acool, g.pch, g.hz[k]; localonset, tight)
        abs(r.tsclad - tsclad) < (tight ? 1e-9 : 1e-3) && (tsclad = r.tsclad; break)
        tsclad = r.tsclad
    end
    dmax = 0.0
    for l in 1:nd-1                                        # rod temperatures for this wall
        tn = x2[l] + r.tsclad * x3[l]
        dmax = max(dmax, abs(tn - tre11[l])); tre11[l] = tn
    end
    (!tight || dmax < 1e-9) && break
    end
    qwall = qcool + r.phi * g.pch / g.acool                # W/m3 of coolant volume
    # the density THM: writes to the FMAP (THMTRS's post-sweep D-COOL), used as THE
    # cell density here so the neutronics sees the quantity the scheme conserves
    rhoY = r.eps > 0.0 ? r.rhol * (1.0 - r.eps) + r.eps * Ch.prop_Tx(tsat(p), 1.0).rho : r.rhol
    CellEval(r.rho, rhoY, r.rhol, r.tcalo, r.tsclad, r.xfl, r.eps, r.kwa, r.k0, r.phi, tc1, qwall, sv)
end

"""
Momentum mode: the pressure at the bottom face of the first fuel cell is
given (it comes from the header through the inlet line, `ColLoop`), and the
pressure marches up the column with each cell's momentum balance:
  p_top = p_bot - dz/dt (G_c - G_c0) - (G_t^2/rho_k - G_b^2/rho_b) - F_k - rho_k g dz
F_k is the design friction method of [D] pp. 68-69 (Fig. 3.9: validated on
the full-scale heated channel rig), see `dfric`.
"""
struct MomBC
    pbot::Float64            # Pa, bottom face of the first fuel cell
    eps_bundle::Float64      # rod-bundle relative density ([D] p. 69, chi)
end

const GRAV = 9.81
# Outside [PMIN, PMAX] the column has left the range the water properties are
# ported for (IF97 regions 1/2/4; region 3 starts at 16.53 MPa); a trial flow
# that gets there is not a solution, and the loop solver reads it as "too much
# flow" (below PMIN) or "too little" (above PMAX).
const PMIN = 1.0e5
const PMAX = 16.5e6
struct PressureCollapse <: Exception
    k::Int
    p::Float64
end
"""[D] pp. 68-69: smooth-bundle friction factor lambda = [1.82 lg(Re chi) - 1.64]^-2,
chi = 2e/(1-e)^2 (e/2 - 3/2 - ln e/(1-e))."""
bundle_chi(e) = 2e / (1 - e)^2 * (e / 2 - 1.5 - log(e) / (1 - e))
lambda_bundle(Re, chi) = (1.82 * log10(max(Re * chi, 10.0)) - 1.64)^-2
"""[D] p. 68: two-phase friction gradient (Pa/m) for mass flux G (kg/m2/s), flow
quality x, hydraulic diameter dh, saturated rho_l, rho_g, liquid viscosity mu_l:
  -dP/dz = (lambda/dh) G|G|/(2 rho_l) psi [1 + x (rho_l/rho_g - 1)],
  psi = 1 + 0.57 (1/(0.2 + w0/sqrt(g dh) rho_g/rho_l) - 5.2 x^2) x^0.125 (1-x)^2,
  w0 = G/rho_l."""
function dfric(G, x, dh, rhol, rhog, mul, chi)
    Re = abs(G) * dh / mul
    lam = lambda_bundle(Re, chi)
    xx = clamp(x, 0.0, 1.0)
    w0 = abs(G) / rhol
    psi = 1 + 0.57 * (1 / (0.2 + w0 / sqrt(GRAV * dh) * rhog / rhol) - 5.2xx^2) * xx^0.125 * (1 - xx)^2
    lam / dh * G * abs(G) / (2rhol) * psi * (1 + xx * (rhol / rhog - 1))
end

"""
    col_step(g, o, s0, pow, burn, Gin, tin, dt; maxsweep=200, tol=1e-10) -> s1

One backward-Euler step of the column with the inlet mass flux `Gin`
prescribed and the pressure fixed (THM's assumptions).  Sub-steps itself if
a step fails to converge.
"""
function col_step(g, o, s0::ColState, pow, burn, Gin, tin, dt; maxsweep=200, tol=1e-10, depth=0, scheme=:thm,
                  mom::Union{Nothing,MomBC}=nothing)
    s1 = try
        col_step1(g, o, s0, pow, burn, Gin, tin, dt; maxsweep, tol, scheme, mom)
    catch e
        (e isa ColFailure && depth < 8) || rethrow()
        nothing
    end
    s1 !== nothing && return s1
    # sub-step: two halves, the power held, the inlet linearly in between
    mom === nothing || throw(ColFailure("momentum mode: sub-stepping belongs to the loop solver"))
    sh = col_step(g, o, s0, pow, burn, 0.5 * (s0.Gin + Gin), tin, 0.5dt; maxsweep, tol, depth=depth + 1, scheme)
    s2 = col_step(g, o, sh, pow, burn, Gin, tin, 0.5dt; maxsweep, tol, depth=depth + 1, scheme)
    s2.substeps += sh.substeps + 1
    s2
end

struct ColFailure <: Exception
    msg::String
end

function col_step1(g, o, s0::ColState, pow, burn, Gin, tin, dt; maxsweep, tol, scheme, mom=nothing)
    nz = length(pow); nd = g.ndtot; dtinv = 1.0 / dt
    cells = findall(!=(0.0), pow)
    kmin, kmax = first(cells), last(cells)
    @assert cells == collect(kmin:kmax) "fuel slices must be contiguous"
    mom === nothing || scheme === :fv || throw(ArgumentError("momentum mode needs scheme = :fv"))
    p = s0.pout
    ai = prop_pT(mom === nothing ? p : mom.pbot, tin); hin = ai.h; rhoin = ai.rho
    ai0 = prop_pT(s0.pout, s0.tin); hin0 = ai0.h; rhoin0 = ai0.rho
    dv = g.sass .* g.hz
    qfuel = pow .* g.ffuel ./ dv
    qcool = pow .* g.fcool ./ dv
    s = deepcopy(s0); s.Gin = Gin; s.hin = hin; s.tin = tin; s.sweeps = 0; s.substeps = 0
    w = RodWork(nd - 1)
    tre10 = zeros(nd - 1); tre11 = zeros(nd - 1)
    hprev = copy(s.h); Gprev = copy(s.G)
    for sweep in 1:maxsweep
        s.sweeps = sweep
        sv = H2OSave(); k0 = 0
        reversed = false
        pf = mom === nothing ? p : mom.pbot              # pressure at the cell's bottom face
        chi = mom === nothing ? 0.0 : bundle_chi(mom.eps_bundle)
        for k in kmin:kmax
            dz = g.hz[k]; a = dz * dtinv
            pk = pf                                       # closure pressure of cell k
            dpk = mom === nothing ? 0.0 : (pk - s0.p[k]) * a   # the dp/dt term of the energy equation
            Gbot = k == kmin ? Gin : s.G[k-1]
            hbelow = k == kmin ? hin : s.h[k-1]
            habove = k < kmax ? s.h[k+1] : s.h[k]        # inflow through a reversed top face
            xfl0 = k > kmin ? s.xfl[k-1] : s0.xfl[k]
            eps0 = k > kmin ? s.eps[k-1] : s0.eps[k]
            for l in 1:nd-1
                tre10[l] = s0.temps[l, k]; tre11[l] = s.temps[l, k]
            end
            ts0 = s.temps[nd, k]
            rho0 = s0.rho[k]; h0 = s0.h[k]
            rhob = k == kmin ? rhoin : s.rho[k-1]          # below: this sweep's value
            rhob0 = k == kmin ? rhoin0 : s0.rho[k-1]
            hb0 = k == kmin ? hin0 : s0.h[k-1]
            hinflow = Gbot >= 0.0 ? hbelow : habove
            ev(hh, Gc) = cell_eval(g, o, k, hh, hinflow, Gc, pk, sv, k0, xfl0, eps0, tre10, tre11, ts0,
                                   qfuel[k], qcool[k], burn[k], dtinv, w)
            # face flux out of the top and the residual of cell k at enthalpy hh, density rr
            if scheme === :thm
                # THMTRS's discretisation (nodes = slice outlets, storage split between
                # node k and node k-1), solved for its own fixed point
                Gtop_of(rr) = Gbot + 0.5 * ((rho0 - rr) + (rhob0 - rhob)) * a
                function Rthm(hh, rr, q)
                    Gt = Gtop_of(rr)
                    P1 = 0.5 * rr * a + ((Gt >= 0.0 || k == kmax) ? Gt : 0.0)
                    P2 = 0.5 * rho0 * h0 * a - ((Gt < 0.0 && k < kmax) ? Gt * habove : 0.0) +
                         0.5 * (rhob0 * hb0 - rhob * hbelow) * a
                    Gbot >= 0.0 ? (P2 += Gbot * hbelow) : (P1 -= Gbot)
                    P1 * hh - P2 - q * dz
                end
                # G_top, G_bot >= 0: rho_k cancels; h explicit but for Q(h)
                hexp(q) = (0.5 * rho0 * h0 * a + 0.5 * (rhob0 * hb0 - rhob * hbelow) * a + Gbot * hbelow + q * dz) /
                          (Gbot + 0.5 * rho0 * a + 0.5 * (rhob0 - rhob) * a)
                Rf, Gf, hx = Rthm, Gtop_of, hexp
            else
                Gtop_fv(rr) = Gbot - (rr - rho0) * a
                function Rfv(hh, rr, q)
                    Gt = Gtop_fv(rr)
                    hout = Gt >= 0.0 ? hh : habove
                    hbin = Gbot >= 0.0 ? hbelow : hh
                    (rr * hh - rho0 * h0) * a - dpk + Gt * hout - Gbot * hbin - q * dz
                end
                hexp_fv(q) = Gbot >= 0.0 ? (rho0 * h0 * a + dpk + Gbot * hbelow + q * dz) / (Gbot + rho0 * a) :
                                           h0 + (q * dz + dpk) / (rho0 * a)
                Rf, Gf, hx = Rfv, Gtop_fv, hexp_fv
            end
            # (a) substitution on the explicit form (exact when the faces are upward)
            h = s.h[k]; Gc = s.G[k]; ce = ev(h, Gc)
            for it in 1:30
                hn = hx(ce.qwall)
                ce = ev(hn, Gc); Gc = Gf(ce.rhoY)
                conv = abs(hn - h) <= tol * abs(hn) + 1e-6
                h = hn
                conv && break
            end
            Gtop = Gf(ce.rhoY)
            if (Gtop < 0.0 && k < kmax) || Gbot < 0.0 || abs(Rf(h, ce.rhoY, ce.qwall)) > 1e-6 * (abs(Gbot) + rho0 * a) * abs(h)
                # (b) reversed faces (or the substitution stalled): bracketed root of the
                # full residual, continuous through G_top = 0
                reversed = true
                save = copy(tre11)
                function R(hh)
                    tre11 .= save
                    c = ev(hh, Gc)
                    Rf(hh, c.rhoY, c.qwall)
                end
                h = brent(R, 0.5 * min(h, h0, hbelow), 2.0 * max(h, h0, hbelow) + 1e6; tol=tol)
                tre11 .= save
                ce = ev(h, Gc)
                Gtop = Gf(ce.rhoY)
            end
            # commit cell k
            sv = ce.sv; k0 = ce.k0
            s.h[k] = h; s.G[k] = Gtop; s.rho[k] = ce.rhoY; s.rhol[k] = ce.rhol
            s.xfl[k] = ce.xfl; s.eps[k] = ce.eps; s.kwa[k] = ce.kwa
            for l in 1:nd-1
                s.temps[l, k] = tre11[l]
            end
            s.temps[nd, k] = ce.tsclad
            s.tcomb[k] = (1.0 - o.wteff) * ce.tc1 + o.wteff * tre11[g.nfd]
            s.tcent[k] = ce.tc1; s.tsurf[k] = tre11[g.nfd]; s.tcool[k] = ce.tcalo
            s.p[k] = pk
            if mom !== nothing                            # momentum: march the pressure up
                Gc = 0.5 * (Gbot + Gtop); Gc0 = 0.5 * ((k == kmin ? s0.Gin : s0.G[k-1]) + s0.G[k])
                ts = tsat(pk); L = Ch.prop_Tx(ts, 0.0); V = Ch.prop_Tx(ts, 1.0)
                Fk = dfric(Gc, ce.xfl, g.hd, L.rho, V.rho, L.mu, chi) * dz
                pf = pk - a * (Gc - Gc0) - (Gtop^2 / ce.rhoY - Gbot^2 / rhob) - Fk - ce.rhoY * GRAV * dz
                (pf < PMIN || pf > PMAX) && throw(PressureCollapse(k, pf))
            end
        end
        s.ptop = pf
        reversed || return s                        # lower-triangular: one sweep is exact
        dh = maximum(abs(s.h[k] - hprev[k]) / abs(s.h[k]) for k in kmin:kmax)
        dG = maximum(abs(s.G[k] - Gprev[k]) for k in kmin:kmax) / max(abs(Gin), 1.0)
        (dh < 1e-8 && dG < 1e-7) && (s.ptop = pf; return s)
        hprev .= s.h; Gprev .= s.G
    end
    throw(ColFailure("reversed-flow sweeps did not converge"))
end

# Brent's method on a bracket expanded until the residual changes sign
function brent(f, a, b; tol=1e-10, maxit=200)
    fa = f(a); fb = f(b)
    for _ in 1:40
        fa * fb <= 0 && break
        a = 0.5a; b = 2b
        fa = f(a); fb = f(b)
    end
    fa * fb > 0 && throw(ColFailure("no bracket"))
    c, fc = a, fa; d = e = b - a
    for _ in 1:maxit
        if fb * fc > 0
            c, fc = a, fa; d = e = b - a
        end
        if abs(fc) < abs(fb)
            a, b, c = b, c, b; fa, fb, fc = fb, fc, fb
        end
        tol1 = 2eps() * abs(b) + 0.5 * tol * abs(b); xm = 0.5 * (c - b)
        (abs(xm) <= tol1 || fb == 0) && return b
        if abs(e) >= tol1 && abs(fa) > abs(fb)
            s_ = fb / fa
            if a == c
                pp = 2xm * s_; q = 1 - s_
            else
                q = fa / fc; r = fb / fc
                pp = s_ * (2xm * q * (q - r) - (b - a) * (r - 1)); q = (q - 1) * (r - 1) * (s_ - 1)
            end
            pp > 0 ? (q = -q) : (pp = -pp)
            if 2pp < min(3xm * q - abs(tol1 * q), abs(e * q))
                e = d; d = pp / q
            else
                d = xm; e = d
            end
        else
            d = xm; e = d
        end
        a, fa = b, fb
        b += abs(d) > tol1 ? d : copysign(tol1, xm)
        fb = f(b)
    end
    throw(ColFailure("brent did not converge"))
end

"""T-FUEL and D-COOL (g/cm3) per slice, as THM: writes them to the FMAP."""
col_state_fields(s::ColState) = (s.tcomb, s.rho ./ 1e3)


# ---------------------------------------------------------------------------
# B3b-2: the channel between a group header and its drum.  The inlet mass flux
# is no longer prescribed: it is the one that carries the header pressure
# through the inlet line (water line + ZRK valve), the column and the outlet
# (steam-water) line to the drum pressure.  Every geometric number here must
# come from sources/derived/b3b_loop_data.md.

module Lines
using ..Column: ColState, col_step1, MomBC, dfric, ColFailure, brent, GRAV, PMIN, PMAX, PressureCollapse,
                cell_eval, bundle_chi, H2OSave, RodWork
using LinearAlgebra
using ...Channel: prop_pT, tsat
import ...Channel as Ch

export ChanLines, valve_area, col_step_loop, col_step_newton, col_step_newton_flux, NewtonCache
LAST_MISMATCH = nothing      # (debug: the last step's residual function)
NEWTON_DEBUG = nothing
const NEWTON_LOG = Ref(false)

Base.@kwdef struct ChanLines
    Ach::Float64          # channel flow area (m2): W = G Ach (THM's mass flux)
    Ain::Float64; Din::Float64; Lin::Float64; dzin::Float64     # water line (+ unheated inlet)
    xi_valve::Float64     # ZRK: dp = xi rho v_throat^2/2 ([D] Table 3.1, p. 62)
    Aout::Float64; Dout::Float64; Lout::Float64; dzout::Float64 # steam-water line (+ unheated outlet)
    Kout::Float64         # local losses of the outlet line (velocity heads at Aout)
    eps_bundle::Float64   # [D] p. 69
    sourced::Bool         # false while any entry is a placeholder (b3b_loop_data.md gaps)
end

lam_pipe(Re) = (1.82 * log10(max(Re, 10.0)) - 1.64)^-2   # smooth pipe (Filonenko; chi = 1 in [D]'s form)

"""Pressure drop of the inlet line at mass flow W (kg/s): static + valve + friction + inertia."""
function dp_inlet(L::ChanLines, Av, W, W0, rho, mu, dt)
    vth = W / (rho * Av); vl = W / (rho * L.Ain)
    rho * GRAV * L.dzin + L.xi_valve * rho * vth * abs(vth) / 2 +
        lam_pipe(abs(vl) * rho * L.Din / mu) * L.Lin / L.Din * rho * vl * abs(vl) / 2 +
        L.Lin / L.Ain * (W - W0) / dt
end

"""Pressure drop of the outlet line for mixture flow W at quality x, density rhom."""
function dp_outlet(L::ChanLines, W, W0, x, rhom, p, dt)
    ts = tsat(p); Lq = Ch.prop_Tx(ts, 0.0); V = Ch.prop_Tx(ts, 1.0)
    G = W / L.Aout
    rhom * GRAV * L.dzout + dfric(G, x, L.Dout, Lq.rho, V.rho, Lq.mu, 1.0) * L.Lout +
        L.Kout * G * abs(G) / (2rhom) + L.Lout / L.Aout * (W - W0) / dt
end

"""
    col_step_loop(g, o, s0, pow, burn, L, Av, ph, pd, tin, dt) -> s1

One step with the channel between header pressure `ph` and drum pressure
`pd`: the inlet mass flux is found by a bracketed shooting solve.
"""
function col_step_loop(g, o, s0::ColState, pow, burn, L::ChanLines, Av, ph, pd, tin, dt; tol=1e-10, depth=0)
    try
        col_step_loop1(g, o, s0, pow, burn, L, Av, ph, pd, tin, dt; tol)
    catch e
        (e isa ColFailure && depth < 8) || rethrow()
        # the step's end values are held over both halves (as THM's sub-stepping)
        sh = col_step_loop(g, o, s0, pow, burn, L, Av, ph, pd, tin, dt / 2; tol, depth=depth + 1)
        s1 = col_step_loop(g, o, sh, pow, burn, L, Av, ph, pd, tin, dt / 2; tol, depth=depth + 1)
        s1.substeps = sh.substeps + s1.substeps + 1
        s1
    end
end

function col_step_loop1(g, o, s0::ColState, pow, burn, L::ChanLines, Av, ph, pd, tin, dt; tol=1e-10)
    kmax = findlast(!=(0.0), pow)
    a = prop_pT(ph, tin)
    W0in = s0.Gin * L.Ach; W0out = s0.G[kmax] * L.Ach
    last = Ref{Any}(nothing)
    global LAST_MISMATCH
    function mismatch(Gin)
        W = Gin * L.Ach
        pbot = ph - dp_inlet(L, Av, W, W0in, a.rho, a.mu, dt)
        pbot < PMIN && return PMIN - pd                 # (continuous with a collapsed column)
        pbot > PMAX && return PMAX - pd
        s = try
            col_step1(g, o, s0, pow, burn, Gin, tin, dt; maxsweep=200, tol, scheme=:fv, mom=MomBC(pbot, L.eps_bundle))
        catch e
            e isa PressureCollapse || rethrow()
            return (e.p < PMIN ? PMIN : PMAX) - pd
        end
        last[] = s
        s.ptop - dp_outlet(L, s.G[kmax] * L.Ach, W0out, s.xfl[kmax], s.rho[kmax], s.ptop, dt) - pd
    end
    LAST_MISMATCH = mismatch
    # the mismatch falls with Gin: bracket outward from the last step's flux
    G0 = s0.Gin; d = 0.02 * abs(G0) + 10.0
    lo, hi = G0 - d, G0 + d
    flo, fhi = mismatch(lo), mismatch(hi)
    for _ in 1:30
        flo * fhi <= 0 && break
        if flo < 0
            hi, fhi = lo, flo; d *= 2; lo = hi - d; flo = mismatch(lo)
        else
            lo, flo = hi, fhi; d *= 2; hi = lo + d; fhi = mismatch(hi)
        end
    end
    flo * fhi > 0 && throw(ColFailure("loop: no flow bracket"))
    Gin = brent(mismatch, lo, hi; tol=1e-9)
    last[] = nothing
    r = mismatch(Gin)
    (last[] === nothing || abs(r) > 1e3) && throw(ColFailure("loop: the flow root sits on the property-range guard"))
    last[]
end

"""
    valve_area(g, o, s, pow, burn, L, ph, pd, tin, Gin; newton=true) -> (Av, dp_valve, st)

Close one channel's ZRK throat area from a steady state with its flow known
(the A7 valving) and the header and drum pressures: the valve takes what the
lines and the column do not.  Errors if the header cannot drive that flow.
With `newton`, the steady state is then re-solved with `col_step_newton`'s
model (local onset, tight closures; a backward-Euler step of 1e5 s is the
steady state) and Av corrected by secant until that model carries `Gin`, so
a transient started from `st` begins at rest.
"""
function valve_area(g, o, s::ColState, pow, burn, L::ChanLines, ph, pd, tin, Gin; dtss=1e5, newton=true)
    kmax = findlast(!=(0.0), pow)
    a = prop_pT(ph, tin)
    W = Gin * L.Ach
    pbot = pd + 1e5; st = s
    for it in 1:6                             # the column's dp barely depends on its pressure level
        st = col_step1(g, o, s, pow, burn, Gin, tin, dtss; maxsweep=200, tol=1e-10, scheme=:fv, mom=MomBC(pbot, L.eps_bundle))
        pdc = st.ptop - dp_outlet(L, st.G[kmax] * L.Ach, st.G[kmax] * L.Ach, st.xfl[kmax], st.rho[kmax], st.ptop, dtss)
        abs(pdc - pd) < 1.0 && break
        pbot += pd - pdc
    end
    dpv = ph - pbot - (dp_inlet(L, 1e9, W, W, a.rho, a.mu, dtss))     # (Av huge: the line without its valve)
    dpv > 0 || error("valve_area: the header (ph - pd = $(ph - pd) Pa) cannot drive this channel's flow")
    Av = W / sqrt(2a.rho * dpv / L.xi_valve)
    newton || return Av, dpv, st
    # the same closure in the Newton model: secant on log Av against log Gin
    solve(A) = (x = st; for _ in 1:3; x = col_step_newton(g, o, x, pow, burn, L, A, ph, pd, tin, dtss); end; x)
    A0 = Av; s0n = solve(A0); A1 = Av * Gin / s0n.Gin; s1n = solve(A1)
    for it in 1:20
        abs(s1n.Gin - Gin) < 1e-9 * Gin && break
        A2 = exp(log(A1) + (log(Gin) - log(s1n.Gin)) * (log(A1) - log(A0)) / (log(s1n.Gin) - log(s0n.Gin)))
        A0, s0n = A1, s1n; A1 = A2; s1n = solve(A1)
    end
    abs(s1n.Gin - Gin) < 1e-6 * Gin || error("valve_area: Newton closure did not converge (Gin $(s1n.Gin) vs $Gin)")
    vth = W / (a.rho * A1)
    A1, L.xi_valve * a.rho * vth^2 / 2, s1n
end

"""
    col_step_newton(g, o, s0, pow, burn, L, Av, ph, pd, tin, dt) -> s1

The same step as `col_step_loop`, solved simultaneously instead of by
shooting.  Shooting marches the pressure up from a trial inlet flux, and in a
boiling cell a pressure error comes back through the void (flashing or
condensing: dz/dt * d(rho)/dp) as a mass-flux error, and again as a pressure
error through the cell's inertia: a gain of ~ (dz/dt)^2 drho/dp per cell,
> 1 at small dt near saturation, so the residual in Gin becomes steep and
discontinuous.  Here every cell's mass, energy and momentum balance and both
line equations are one nonlinear system,
  x = [Gin; (h_j, p_j, G_j) for the fuel cells; p_top]
(p_j = pressure on the bottom face of cell j, G_j = mass flux on its top face),
solved by Newton with a banded finite-difference Jacobian (3 colours of cells
x 3 unknowns = 9 residual evaluations) and backtracking.  The THMH2O/THMROD
closures are evaluated upward in order (their onset and save state carry from
the cell below), exactly as in the march; the Jacobian keeps only the
nearest-neighbour coupling, so the iteration is an inexact Newton.
"""
function col_step_newton(g, o, s0::ColState, pow, burn, L::ChanLines, Av, ph, pd, tin, dt;
                         tol=1e-9, maxit=40, depth=0, localonset=true, cache=nothing)
    newton_substep(g, o, s0, pow, burn, (:loop, L, Av, ph, pd), tin, dt; tol, maxit, depth, localonset, cache)
end

"""
    col_step_newton_flux(g, o, s0, pow, burn, Gin, tin, dt; eps_bundle, cache) -> s1

THM's boundary conditions (inlet mass flux prescribed, every cell at the
outlet pressure s0.pout) on the Newton path: the column's mass and energy
balances solved simultaneously, with the same smooth closures.  `cache` (a
`NewtonCache`, one per channel) keeps the factorised Jacobian between
iterations and steps (chord Newton, rebuilt when it stops contracting).
"""
function col_step_newton_flux(g, o, s0::ColState, pow, burn, Gin, tin, dt;
                              tol=1e-9, maxit=40, depth=0, localonset=true, cache=nothing)
    newton_substep(g, o, s0, pow, burn, (:flux, Gin), tin, dt; tol, maxit, depth, localonset, cache)
end

mutable struct NewtonCache
    F::Any                   # LU of the last Jacobian (or nothing)
    n::Int
    dt::Float64
    nbuild::Int              # diagnostics: Jacobians built, residual evaluations
    nres::Int
end
NewtonCache() = NewtonCache(nothing, 0, 0.0, 0, 0)

function newton_substep(g, o, s0, pow, burn, bc, tin, dt; tol, maxit, depth, localonset, cache)
    try
        col_step_newton1(g, o, s0, pow, burn, bc, tin, dt; tol, maxit, localonset, cache)
    catch e
        (e isa ColFailure && depth < 8) || rethrow()
        NEWTON_LOG[] && println("  substep at depth $depth (dt $dt): ", first(e.msg, 160))
        # (the step's end values held over both halves; a flux BC is interpolated)
        bch = bc[1] === :flux ? (:flux, 0.5 * (s0.Gin + bc[2])) : bc
        sh = newton_substep(g, o, s0, pow, burn, bch, tin, dt / 2; tol, maxit, depth=depth + 1, localonset, cache)
        s1 = newton_substep(g, o, sh, pow, burn, bc, tin, dt / 2; tol, maxit, depth=depth + 1, localonset, cache)
        s1.substeps = sh.substeps + s1.substeps + 1
        s1
    end
end

const FLOOR = 1e-6       # scaled residual the closures' inner tolerances allow (see the line search)

function col_step_newton1(g, o, s0::ColState, pow, burn, bc, tin, dt; tol, maxit, localonset, cache)
    loop = bc[1] === :loop
    L, Av, ph, pd = loop ? bc[2:5] : (nothing, 0.0, 0.0, 0.0)
    Gbc = loop ? 0.0 : bc[2]; pout = s0.pout
    nd = g.ndtot; dtinv = 1.0 / dt
    cells = findall(!=(0.0), pow)
    kmin, kmax = first(cells), last(cells); N = kmax - kmin + 1
    a_in = prop_pT(loop ? ph : pout, tin)
    dv = g.sass .* g.hz
    qfuel = pow .* g.ffuel ./ dv
    qcool = pow .* g.fcool ./ dv
    chi = loop ? bundle_chi(L.eps_bundle) : 0.0
    W0in = loop ? s0.Gin * L.Ach : 0.0; W0out = loop ? s0.G[kmax] * L.Ach : 0.0
    w = RodWork(nd - 1)
    T11 = s0.temps[1:nd-1, :]                         # rod-temperature guesses (per cell)
    tre10 = zeros(nd - 1); tre11 = zeros(nd - 1)
    n = 3N + 2
    ix(j, c) = 1 + 3(j - 1) + c                       # c = 1 h, 2 p, 3 G
    # residual scales: mass by the cell's storage + throughflow, energy by that x h0, momentum by 1 bar
    smass = [s0.rho[kmin+j-1] * g.hz[kmin+j-1] * dtinv + abs(s0.Gin) + 1.0 for j in 1:N]
    sen = [smass[j] * s0.h[kmin+j-1] for j in 1:N]
    sp = 1e5
    ces = Vector{Any}(undef, N)
    function resid!(r, x; keep=false)
        Gin = x[1]; ptop = x[n]
        (PMIN <= x[ix(1, 2)] <= PMAX) || return false
        hin = prop_pT(x[ix(1, 2)], tin).h
        r[1] = loop ? (x[ix(1, 2)] - (ph - dp_inlet(L, Av, Gin * L.Ach, W0in, a_in.rho, a_in.mu, dt))) / sp :
                      (Gin - Gbc) / smass[1]
        sv = H2OSave(); k0 = 0
        rhob = prop_pT(x[ix(1, 2)], tin).rho
        for j in 1:N
            k = kmin + j - 1; dz = g.hz[k]; a = dz * dtinv
            h = x[ix(j, 1)]; pk = x[ix(j, 2)]; Gt = x[ix(j, 3)]
            Gb = j == 1 ? Gin : x[ix(j - 1, 3)]
            hb = j == 1 ? hin : x[ix(j - 1, 1)]
            ha = j < N ? x[ix(j + 1, 1)] : h
            pnext = j < N ? x[ix(j + 1, 2)] : ptop
            (PMIN <= pk <= PMAX && h > 0.0) || return false
            hinflow = Gb >= 0.0 ? hb : ha
            xfl0 = j > 1 ? ces[j-1].xfl : s0.xfl[k]; eps0 = j > 1 ? ces[j-1].eps : s0.eps[k]
            for l in 1:nd-1
                tre10[l] = s0.temps[l, k]; tre11[l] = T11[l, k]
            end
            ce = cell_eval(g, o, k, h, hinflow, Gt, pk, sv, k0, xfl0, eps0, tre10, tre11, s0.temps[nd, k],
                           qfuel[k], qcool[k], burn[k], dtinv, w; tight=true, localonset)
            keep && (T11[:, k] .= tre11)
            ces[j] = ce; sv = ce.sv; k0 = ce.k0
            rho0 = s0.rho[k]; h0 = s0.h[k]
            hout = Gt >= 0.0 ? h : ha
            hbin = Gb >= 0.0 ? hb : h
            r[ix(j, 1)] = ((ce.rhoY - rho0) * a + Gt - Gb) / smass[j]
            r[ix(j, 2)] = ((ce.rhoY * h - rho0 * h0) * a - (pk - s0.p[k]) * a + Gt * hout - Gb * hbin - ce.qwall * dz) / sen[j]
            if loop
                Gc = 0.5 * (Gb + Gt); Gc0 = 0.5 * ((j == 1 ? s0.Gin : s0.G[k-1]) + s0.G[k])
                ts = tsat(pk); Lq = Ch.prop_Tx(ts, 0.0); V = Ch.prop_Tx(ts, 1.0)
                Fk = dfric(Gc, ce.xfl, g.hd, Lq.rho, V.rho, Lq.mu, chi) * dz
                r[ix(j, 3)] = (pnext - (pk - a * (Gc - Gc0) - (Gt^2 / ce.rhoY - Gb^2 / rhob) - Fk - ce.rhoY * GRAV * dz)) / sp
            else
                r[ix(j, 3)] = (pnext - pout) / sp            # THM: no momentum, p = outlet pressure
            end
            rhob = ce.rhoY
        end
        (PMIN <= ptop <= PMAX) || return false
        cN = ces[N]
        r[n] = loop ? (ptop - dp_outlet(L, x[ix(N, 3)] * L.Ach, W0out, cN.xfl, cN.rhoY, ptop, dt) - pd) / sp :
                      (x[ix(1, 2)] - pout) / sp         # (flux: closes p_1; its Jacobian row is set exactly)
        true
    end
    # initial iterate: the old state
    x = zeros(n); x[1] = s0.Gin; x[n] = s0.ptop
    for j in 1:N
        k = kmin + j - 1
        x[ix(j, 1)] = s0.h[k]; x[ix(j, 2)] = s0.p[k]; x[ix(j, 3)] = s0.G[k]
    end
    r = zeros(n); rp = zeros(n); J = zeros(n, n); xp = similar(x)
    resid!(r, x; keep=true) || throw(ColFailure("newton: old state outside the property range"))
    blk(i) = i == 1 ? 0 : (i == n ? N + 1 : (i - 2) ÷ 3 + 1)   # block (cell) of unknown/row i
    del(i) = i == 1 || (i - 2) % 3 == 2 ? 1e-6 * (abs(x[i]) + 10.0) : (i == n || (i - 2) % 3 == 1 ? 10.0 : 1e-6 * abs(x[i]))
    nr = norm(r, Inf); its = 0
    nres = 1; nbuild = 0
    F = (cache !== nothing && cache.F !== nothing && cache.n == n && cache.dt == dt) ? cache.F : nothing
    fresh = false
    for it in 1:maxit
        its = it
        nr < tol && break
        if F === nothing
        nbuild += 1
        fill!(J, 0.0)
        # blocks whose unknowns reach beyond the band: the onset cell and the one below it
        # (THMH2O's Saha-Zuber save state dhsub/dsat is set there and carried to every cell
        # above), and a cell whose xfl/eps are passed up through non-boiling walls (kwa = 0)
        dirty = falses(N + 2)                          # index = block + 1
        for j in 1:N
            if !localonset && (ces[j].sv.dhsub != (j == 1 ? 0.0 : ces[j-1].sv.dhsub) || ces[j].sv.dsat != (j == 1 ? 0.0 : ces[j-1].sv.dsat))
                dirty[j+1] = true; dirty[j] = true
            end
            j < N && ces[j+1].kwa == 0 && ces[j].xfl > 0.0 && (dirty[j+1] = true)
        end
        for col in 0:2, c in 1:3                       # colour = block mod 3, component c
            cols = [i for i in 1:n if !dirty[blk(i)+1] && blk(i) % 3 == col && (i == 1 || i == n ? c == 1 : (i - 2) % 3 == c - 1)]
            isempty(cols) && continue
            copyto!(xp, x)
            for i in cols; xp[i] += del(i); end
            resid!(rp, xp) || throw(ColFailure("newton: Jacobian probe outside the property range"))
            for i in cols, row in 1:n
                abs(blk(row) - blk(i)) <= 1 && (J[row, i] = (rp[row] - r[row]) / del(i))
            end
        end
        for i in 1:n                                   # full columns for the dirty blocks
            dirty[blk(i)+1] || continue
            copyto!(xp, x); xp[i] += del(i)
            resid!(rp, xp) || throw(ColFailure("newton: Jacobian probe outside the property range"))
            for row in 1:n
                J[row, i] = (rp[row] - r[row]) / del(i)
            end
        end
        loop || (J[n, :] .= 0.0; J[n, ix(1, 2)] = 1.0 / sp)
        F = try
            lu(J)
        catch e
            throw(ColFailure("newton: singular Jacobian ($e)"))
        end
        fresh = true
        end
        dx = -(F \ r)
        lam = 1.0; ok = false
        for _ in 1:(fresh ? 12 : 2)                    # backtracking on the inf-norm
            xp .= x .+ lam .* dx
            nres += 1
            if resid!(rp, xp) && norm(rp, Inf) < (1 - 1e-4lam) * nr
                ok = true; break
            end
            lam /= 2
        end
        if !ok && !fresh                               # a stale Jacobian: rebuild and retry
            F = nothing; continue
        end
        if !ok
            # the closures carry their own inner tolerances (rod <-> wall to 1e-3 K, THMH2O's
            # iterations), so |r| has a noise floor; a stall below FLOOR is convergence to it
            nr < FLOOR && break
            global NEWTON_DEBUG = (; resid!, x=copy(x), dx=copy(dx), r=copy(r), J=copy(J), ces, kmin, N)
            im = argmax(abs.(r)); jb = blk(im)
            throw(ColFailure("newton: line search failed at |r| = $nr (row $im: cell $(jb + kmin - 1) eq $(im in (1, n) ? "line" : ("mass", "energy", "momentum")[(im-2)%3+1]); k0 = $(ces[end].k0), eps = $(round.([c.eps for c in ces]; digits=3)))"))
        end
        nrold = nr
        copyto!(x, xp); resid!(r, x; keep=true); nr = norm(r, Inf); nres += 1
        # chord Newton: keep the factorisation while it contracts well
        (!fresh && nr > 0.3nrold && nr >= tol) && (F = nothing)
        fresh = false
    end
    if cache !== nothing
        cache.F = F; cache.n = n; cache.dt = dt; cache.nbuild += nbuild; cache.nres += nres + 9nbuild
    end
    nr < FLOOR || throw(ColFailure("newton: $its iterations, |r| = $nr"))
    # commit
    s = deepcopy(s0); s.Gin = x[1]; s.ptop = x[n]; s.sweeps = its; s.substeps = 0
    s.hin = prop_pT(x[ix(1, 2)], tin).h; s.tin = tin
    for j in 1:N
        k = kmin + j - 1; ce = ces[j]
        s.h[k] = x[ix(j, 1)]; s.p[k] = x[ix(j, 2)]; s.G[k] = x[ix(j, 3)]
        s.rho[k] = ce.rhoY; s.rhol[k] = ce.rhol; s.xfl[k] = ce.xfl; s.eps[k] = ce.eps; s.kwa[k] = ce.kwa
        s.temps[1:nd-1, k] .= T11[:, k]; s.temps[nd, k] = ce.tsclad
        s.tcomb[k] = (1.0 - o.wteff) * ce.tc1 + o.wteff * T11[g.nfd, k]
        s.tcent[k] = ce.tc1; s.tsurf[k] = T11[g.nfd, k]; s.tcool[k] = ce.tcalo
    end
    s
end

end # module Lines

end # module Column
