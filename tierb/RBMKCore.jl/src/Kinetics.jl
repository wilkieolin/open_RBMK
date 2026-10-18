# Space-time kinetics, theta scheme, as TRIVAC's KINSOL: (TIER_B_WORKPLAN.md,
# B2).  Written against Trivac/src/KINXSD.f, KINSRC.f and KINPRC.f:
#
#   * nu*Sigma_f (total) and the delayed nu*Sigma_f,d are divided by the
#     initial k_eff, so the transient starts exactly critical (KINXSD);
#   * flux:  (1/(v dt)) (phi1 - phi0) = th R(phi1, C1) + (1-th) R(phi0, C0)
#     with R(phi, C) = -A phi + chi SGF phi - sum_d chi_d SGD_d phi
#                      + sum_d lambda_d chi_d C_d,
#     the explicit half evaluated with the NEW step's operators, as KINSRC
#     does (it applies the current SYSTEM and macrolib to the old flux);
#   * precursors (KINPRC): C1 = TK1 C0 + dt (thp SGD1 phi1 + (1-thp) SGO phi0)
#     / (1 + thp lambda dt), TK1 = (1 - (1-thp) lambda dt)/(1 + thp lambda dt),
#     SGO the previous step's delayed production;
#   * no exponential transformation (IEXP = 0, the A8 decks' setting).
#
# Precursors are kept per fissile isotope, as KINPRC's PC(NUP,NDG,NBFIS):
# each isotope's precursors decay into that isotope's delayed spectrum.  In
# the step matrix the isotope sum collapses into Fd[g,g',d] = sum_iso
# chi_d,iso[g] nusigf_d,iso[g'], so only the precursor source needs them.  Each step is
# one coupled two-group sparse system, solved by GMRES preconditioned with
# per-group AMG on the diagonal blocks.

module Kinetics

using SparseArrays, LinearAlgebra, AlgebraicMultigrid, Krylov
using ..Diffusion

export KinXS, KinState, kin_xs, kin_init, kin_step!, kin_power

"""Per-unknown kinetics data of one step (volume-integrated, per Problem)."""
struct KinXS
    p::Problem                       # leakage + removal operators, S, F (prompt+delayed)
    Fd::Array{Vector{Float64},3}     # Fd[g_to, g_from, d] = sum_iso chi_d nusigf_d, vol, /k0
    Pd::Array{Vector{Float64},3}     # Pd[g_from, d, iso] nusigf_d,iso, vol, /k0
    chid::Array{Vector{Float64},3}   # chid[g_to, d, iso]
    overv::Matrix{Float64}           # [unknown, g] 1/v
end

mutable struct KinState
    phi::Vector{Vector{Float64}}
    C::Matrix{Vector{Float64}}       # C[d, iso] per unknown
    Pd_old::Array{Vector{Float64},3}
    t::Float64
    k0::Float64
end

"""
    kin_xs(p, fissd, prodd, chieff, overv, k0)

`p` is a Diffusion.Problem built with fission divided by nothing; `fissd`
[r-indexed] etc. are mapped onto p's unknowns here.  All fission terms are
divided by k0.
"""
function kin_xs(p::Problem, Fd_unk, Pd_unk, chid_unk, overv_unk, k0)
    pk = Problem(p.mesh, p.cell, p.vol, p.A, p.S, [f ./ k0 for f in p.F], p.hfac)
    KinXS(pk, map(f -> f ./ k0, Fd_unk), map(f -> f ./ k0, Pd_unk), chid_unk, overv_unk)
end

"""Steady initial precursors: C_d,iso = Pd_iso . phi / lambda_d."""
function kin_init(x::KinXS, phi, lambda, k0)
    nd = length(lambda); ng = length(phi); ni = size(x.Pd, 3)
    C = [sum(x.Pd[g, d, i] .* phi[g] for g in 1:ng) ./ lambda[d] for d in 1:nd, i in 1:ni]
    KinState([copy(f) for f in phi], C, copy(x.Pd), 0.0, k0)
end

# Assemble the full 2-group step matrix M phi1 = rhs.
function step_matrix(x::KinXS, lambda, dt, th, thp)
    p = x.p
    ng = length(p.A); n = length(p.cell); nd = length(lambda)
    blocks = Matrix{SparseMatrixCSC{Float64,Int}}(undef, ng, ng)
    for g in 1:ng, gp in 1:ng
        d = zeros(n)
        if g == gp
            d .+= p.vol .* x.overv[:, g] ./ dt
        else
            d .-= th .* p.S[g, gp]
        end
        d .-= th .* p.F[g, gp]                         # total fission, chi_total
        for dd in 1:nd
            fac = lambda[dd] * dt * thp / (1 + thp * lambda[dd] * dt)
            d .+= th .* x.Fd[g, gp, dd]                # remove delayed from prompt
            d .-= th .* fac .* x.Fd[g, gp, dd]         # implicit precursor return
        end
        B = spdiagm(0 => d)
        g == gp && (B = B + th .* p.A[g])
        blocks[g, gp] = B
    end
    hvcat(ntuple(_ -> ng, ng), [blocks[g, gp] for g in 1:ng for gp in 1:ng]...)
end

function residual_op(x::KinXS, phi, C, lambda)
    # R(phi, C) without the time term, per group (volume-integrated)
    p = x.p
    ng = length(p.A); nd = length(lambda)
    out = [-(p.A[g] * phi[g]) for g in 1:ng]
    for g in 1:ng, gp in 1:ng
        g != gp && (out[g] .+= p.S[g, gp] .* phi[gp])
        out[g] .+= p.F[g, gp] .* phi[gp]
        for d in 1:nd
            out[g] .-= x.Fd[g, gp, d] .* phi[gp]
        end
    end
    for g in 1:ng, d in 1:nd, i in axes(C, 2)
        out[g] .+= lambda[d] .* x.chid[g, d, i] .* C[d, i]
    end
    out
end

"""
    kin_step!(s, x, lambda, dt; th=0.8, thp=0.8)

Advance one step with the new step's data `x` (rods already moved).
"""
function kin_step!(s::KinState, x::KinXS, lambda, dt; th=0.8, thp=0.8, rtol=1e-10)
    p = x.p
    ng = length(p.A); n = length(p.cell); nd = length(lambda)
    R0 = residual_op(x, s.phi, s.C, lambda)
    rhs = [p.vol .* x.overv[:, g] ./ dt .* s.phi[g] .+ (1 - th) .* R0[g] for g in 1:ng]
    for g in 1:ng, d in 1:nd, i in axes(s.C, 2)
        tk1 = (1 - (1 - thp) * lambda[d] * dt) / (1 + thp * lambda[d] * dt)
        fac = lambda[d] * dt * (1 - thp) / (1 + thp * lambda[d] * dt)
        expl = sum(s.Pd_old[gp, d, i] .* s.phi[gp] for gp in 1:ng)
        rhs[g] .+= th .* lambda[d] .* x.chid[g, d, i] .* (tk1 .* s.C[d, i] .+ fac ./ lambda[d] .* expl)
    end
    M = step_matrix(x, lambda, dt, th, thp)
    P = [aspreconditioner(smoothed_aggregation(M[(g-1)*n+1:g*n, (g-1)*n+1:g*n])) for g in 1:ng]
    Pre = BlockPre(P, n)
    b = vcat(rhs...)
    x0 = vcat(s.phi...)
    # Krylov's rtol is relative to the (already small) initial residual: stop on rtol*|b|
    sol, stats = gmres(M, b, x0; M=Pre, ldiv=true, rtol=0.0, atol=rtol * norm(b), itmax=400, memory=60)
    stats.solved || @warn "kin_step!: GMRES not converged" stats.niter
    phi1 = [sol[(g-1)*n+1:g*n] for g in 1:ng]
    # precursors
    for d in 1:nd, i in axes(s.C, 2)
        tk1 = (1 - (1 - thp) * lambda[d] * dt) / (1 + thp * lambda[d] * dt)
        prod1 = sum(x.Pd[gp, d, i] .* phi1[gp] for gp in 1:ng)
        prod0 = sum(s.Pd_old[gp, d, i] .* s.phi[gp] for gp in 1:ng)
        s.C[d, i] = tk1 .* s.C[d, i] .+ dt .* (thp .* prod1 .+ (1 - thp) .* prod0) ./ (1 + thp * lambda[d] * dt)
    end
    s.phi = phi1
    s.Pd_old = copy(x.Pd)
    s.t += dt
    s
end

struct BlockPre{T}
    P::Vector{T}
    n::Int
end
function LinearAlgebra.ldiv!(y, B::BlockPre, x)
    for (g, P) in enumerate(B.P)
        r = (g-1)*B.n+1:g*B.n
        y[r] .= P \ x[r]
    end
    y
end
LinearAlgebra.ldiv!(B::BlockPre, x) = (y = similar(x); ldiv!(y, B, x); x .= y)

"""Total power (arbitrary units until normalised): sum H_g phi_g (H per volume x vol)."""
kin_power(x::KinXS, s::KinState) = sum(sum(x.p.hfac[:, g] .* s.phi[g] .* x.p.vol) for g in eachindex(s.phi))

end # module
