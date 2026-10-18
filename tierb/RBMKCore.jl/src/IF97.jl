# Pure-Julia IAPWS-IF97 as freesteam computes it, for the parts THM: uses
# (Water.jl's API): regions 1, 2 and the region-4 saturation line, with
# freesteam's own viscosity (IAPWS 1985 form, no critical enhancement) and
# thermal conductivity (IAPWS 1985) as functions of (rho, T).  Scalar,
# allocation-free and branch-light, so the same functions run inside GPU
# kernels.  Coefficients are generated from the C sources
# (tools/tierb_gen_if97.py -> IF97Tables.jl), and the functions are
# verified against the freesteam library itself (test/b6_if97.jl).
#
# freesteam_set_pT's region choice: T < 623.15 K -> region 1 if p > psat(T)
# else 2; T >= 623.15 K -> region 2 if p < p_B23(623.15) = 16.53 MPa (always,
# at RBMK pressures) -- region 3 is not ported and is an error.
# free_Tx is only ever called with x = 0 or 1 by THM:, i.e. region 1 / 2 at
# (psat(T), T).

module IF97

export tsat97, psat97, prop_pT97, prop_Tx97

include("IF97Tables.jl")

const R = 461.526
const TCRIT = 647.096
const RHOCRIT = 322.0
const REGION1_TMAX = 623.15
const P23MIN = 16.529164252605e6        # freesteam_b23_p_T(623.15)

@inline function ipow(x::Float64, n::Int)
    n == 0 && return 1.0
    if n < 0
        n = -n; x = 1.0 / x
    end
    x == 0.0 && return 0.0
    t = 1.0
    while true
        (n & 1) == 1 && (t *= x)
        n >>= 1
        n == 0 && break
        x *= x
    end
    t
end

# --- region 4 ----------------------------------------------------------------
@inline function psat97(T::Float64)
    n = R4_N
    ups = T + n[10] / (T - n[11])
    A = ups^2 + n[2] * ups + n[3]
    B = n[4] * ups^2 + n[5] * ups + n[6]
    C = n[7] * ups^2 + n[8] * ups + n[9]
    e = 2.0 * C / (-B + sqrt(B^2 - 4.0 * A * C))
    (e^2)^2 * 1e6
end
@inline function tsat97(p::Float64)
    n = R4_N
    beta = (p / 1e6)^0.25
    E = beta^2 + n[4] * beta + n[7]
    F = n[2] * beta^2 + n[5] * beta + n[8]
    G = n[3] * beta^2 + n[6] * beta + n[9]
    D = 2.0 * G / (-F - sqrt(F^2 - 4.0 * E * G))
    0.5 * (n[11] + D - sqrt((n[11] + D)^2 - 4.0 * (n[10] + n[11] * D)))
end

# --- region 1: (gampi, gamtau, gamtautau) at pi = p/16.53 MPa, tau = 1386/T
@inline function r1_derivs(p, T)
    pi = p / 16.53e6; tau = 1386.0 / T
    a = 7.1 - pi; b = tau - 1.222
    gp = 0.0; gt = 0.0; gtt = 0.0
    @inbounds for k in 1:length(R1_N)
        I = R1_I[k]; J = R1_J[k]; n = R1_N[k]
        gp += -n * I * ipow(a, I - 1) * ipow(b, J)
        gt += n * ipow(a, I) * J * ipow(b, J - 1)
        gtt += n * ipow(a, I) * J * (J - 1) * ipow(b, J - 2)
    end
    pi, tau, gp, gt, gtt
end
@inline function r1(p, T)
    pi, tau, gp, gt, gtt = r1_derivs(p, T)
    v = (R * T / p) * pi * gp
    h = R * T * tau * gt
    cp = R * (-tau^2 * gtt)
    1.0 / v, h, cp
end

# --- region 2: ideal + residual at pi = p/1 MPa, tau = 540/T
@inline function r2(p, T)
    pi = p / 1e6; tau = 540.0 / T
    g0t = 0.0; g0tt = 0.0
    @inbounds for k in 1:length(R2I_N)
        J = R2I_J[k]; n = R2I_N[k]
        g0t += n * J * ipow(tau, J - 1)
        g0tt += n * J * (J - 1) * ipow(tau, J - 2)
    end
    grp = 0.0; grt = 0.0; grtt = 0.0
    b = tau - 0.5
    @inbounds for k in 1:length(R2R_N)
        I = R2R_I[k]; J = R2R_J[k]; n = R2R_N[k]
        grp += n * I * ipow(pi, I - 1) * ipow(b, J)
        grt += n * ipow(pi, I) * J * ipow(b, J - 1)
        grtt += n * ipow(pi, I) * J * (J - 1) * ipow(b, J - 2)
    end
    v = (R * T / p) * pi * (1.0 / pi + grp)
    h = R * T * tau * (g0t + grt)
    cp = R * (-tau^2 * (g0tt + grtt))
    1.0 / v, h, cp
end

# --- transport (freesteam viscosity.c, thcond.c) ---------------------------------
@inline function mu97(rho, T)
    del = rho / RHOCRIT; tau = TCRIT / T
    s0 = 1.67752 + 2.20462 * tau + 0.6366564 * tau^2 - 0.241605 * tau^3
    m0 = 100.0 / (sqrt(tau) * s0)
    H = ((5.20094E-1, 2.22531E-1, -2.81378E-1, 1.61913E-1, -3.25372E-2, 0.0, 0.0),
         (8.50895E-2, 9.99115E-1, -9.06851E-1, 2.57399E-1, 0.0, 0.0, 0.0),
         (-1.08374, 1.88797, -7.72479E-1, 0.0, 0.0, 0.0, 0.0),
         (-2.89555E-1, 1.26613, -4.89837E-1, 0.0, 6.98452E-2, 0.0, -4.35673E-3),
         (0.0, 0.0, -2.57040E-1, 0.0, 0.0, 8.72102E-3, 0.0),
         (0.0, 1.20573E-1, 0.0, 0.0, 0.0, 0.0, -5.93264E-4))
    s = 0.0
    @inbounds for i in 0:5
        t1 = ipow(tau - 1.0, i)
        for j in 0:6
            hij = H[i+1][j+1]
            hij == 0.0 && continue
            s += hij * t1 * ipow(del - 1.0, j)
        end
    end
    1.0e-6 * m0 * exp(del * s)
end
@inline function k97(rho, T)
    Tbar = T / 647.26; rhobar = rho / 317.7
    Troot = sqrt(Tbar); Tpow = Troot
    lam = 0.0
    for a in (0.0102811, 0.0299621, 0.0156146, -0.00422464)
        lam += a * Tpow; Tpow *= Tbar
    end
    lam += -0.397070 + 0.400302 * rhobar + 1.060000 * exp(-0.171587 * (rhobar + 2.392190)^2)
    DTbar = abs(Tbar - 1.0) + 0.00308976
    DTp = DTbar^(3.0 / 5.0)
    Q = 2.0 + 0.0822994 / DTp
    S = Tbar >= 1.0 ? 1.0 / DTbar : 10.0932 / DTp
    r18 = rhobar^1.8; rQ = rhobar^Q
    lam += (0.0701309 / ipow(Tbar, 10) + 0.0118520) * r18 * exp(0.642857 * (1.0 - rhobar * r18)) +
           0.00169937 * S * rQ * exp((Q / (1.0 + Q)) * (1.0 - rhobar * rQ)) +
           -1.0200 * exp(-4.11717 * Troot^3 + -6.17937 / ipow(rhobar, 5))
    lam
end

# --- THM's two entry points --------------------------------------------------
"""(rho, h, k, mu, cp) at (p, T) as freesteam free_pT (regions 1/2)."""
@inline function prop_pT97(p::Float64, T::Float64)
    reg2 = T < REGION1_TMAX ? !(p > psat97(T)) : true
    T >= REGION1_TMAX && p >= P23MIN && error("IF97: region 3 not ported")
    rho, h, cp = reg2 ? r2(p, T) : r1(p, T)
    (rho=rho, h=h, k=k97(rho, T), mu=mu97(rho, T), cp=cp)
end
"""(rho, h, k, mu, cp) of saturated liquid (x <= 0) or vapour (x >= 1) at T."""
@inline function prop_Tx97(T::Float64, x::Float64)
    p = psat97(T)
    rho, h, cp = x <= 0.0 ? r1(p, T) : r2(p, T)
    (rho=rho, h=h, k=k97(rho, T), mu=mu97(rho, T), cp=cp)
end

end # module
