# Space-time kinetics on the mixed-dual (RT0, TRIVAC DUAL 1 1) operator, the
# theta scheme of KINSOL (see Kinetics.jl for the formulation, written
# against Trivac KINXSD/KINSRC/KINPRC).
#
# In mixed form the leakage of a cell flux vector phi is
#     L(phi) = D' J(phi),   (A M) J = D'^T phi        (Fick, per group)
# so the condensed operator is  A phi = D' (A M)^{-1} D'^T phi + V Sigma_r phi.
# A theta step multiplies the leakage by theta: with J~ = theta J the Fick
# system becomes (A M / theta) J~ = D'^T phi, i.e. the same structure with the
# current mass scaled by 1/theta, and the cell term R' = V (1/(v dt)
# + theta Sigma_r).  The step operator on cells,
#     T phi = D' (A M/theta)^{-1} D'^T phi + R' phi - theta C phi,
# (C: scattering and the effective fission couplings), is applied with one
# sparse Cholesky solve of A M per group (factored once per step), and the
# system is solved by GMRES preconditioned with the per-group face system
#     K'_g = A M_g / theta + D'^T R'_g^{-1} D'      (AMG-CG).
# The explicit half uses the NEW step's operator on the old flux, as KINSRC.

module DualKinetics

using SparseArrays, LinearAlgebra, AlgebraicMultigrid, Krylov, Printf
using ..Mixed

export DualKinXS, DualKinState, DualStepCache, dual_kin_xs, dual_kin_init, dual_kin_step!, dual_kin_power, dual_steady_residual, dual_wielandt_polish

struct DualKinXS
    p::DualProblem                    # F already divided by k0
    AM::Vector{SparseMatrixCSC{Float64,Int}}
    sigr::Vector{Vector{Float64}}     # V Sigma_r per group (= p.R)
    Fd::Array{Vector{Float64},3}      # [g_to, g_from, d], vol, /k0
    Pd::Array{Vector{Float64},3}      # [g_from, d, iso], vol, /k0
    chid::Array{Vector{Float64},3}    # [g_to, d, iso]
    overv::Matrix{Float64}            # [cell, g]
end

mutable struct DualKinState
    phi::Vector{Vector{Float64}}
    C::Matrix{Vector{Float64}}        # [d, iso]
    Pd_old::Array{Vector{Float64},3}
    t::Float64
    k0::Float64
end

function dual_kin_xs(p::DualProblem, Fd, Pd, chid, overv, k0)
    # recover A M from K = A M + D'^T R^{-1} D'
    AM = [p.K[g] - p.Dp' * spdiagm(0 => 1 ./ p.R[g]) * p.Dp for g in eachindex(p.K)]
    pk = DualProblem(p.mesh, p.cell, p.vol, p.Dp, p.K, p.R, p.S, [f ./ k0 for f in p.F], p.hfac)
    DualKinXS(pk, AM, p.R, map(f -> f ./ k0, Fd), map(f -> f ./ k0, Pd), chid, overv)
end

function dual_kin_init(x::DualKinXS, phi, lambda, k0)
    nd = length(lambda); ng = length(phi); ni = size(x.Pd, 3)
    C = [sum(x.Pd[g, d, i] .* phi[g] for g in 1:ng) ./ lambda[d] for d in 1:nd, i in 1:ni]
    DualKinState([copy(f) for f in phi], C, copy(x.Pd), 0.0, k0)
end

# leakage D' (AM/s)^{-1} D'^T phi using a factorization of AM
leak(fact, Dp, phi, s) = Dp * (s .* (fact \ (Dp' * phi)))

# coupling C phi (per group): scattering + total fission - delayed + implicit return
function couple(x::DualKinXS, phi, lambda, dt, thp)
    p = x.p; ng = length(phi); nd = length(lambda)
    out = [zeros(length(phi[1])) for _ in 1:ng]
    for g in 1:ng, gp in 1:ng
        g != gp && (out[g] .+= p.S[g, gp] .* phi[gp])
        out[g] .+= p.F[g, gp] .* phi[gp]
        for d in 1:nd
            fac = lambda[d] * dt * thp / (1 + thp * lambda[d] * dt)
            out[g] .-= (1 - fac) .* x.Fd[g, gp, d] .* phi[gp]
        end
    end
    out
end

function couple_explicit(x::DualKinXS, phi, lambda)
    p = x.p; ng = length(phi); nd = length(lambda)
    out = [zeros(length(phi[1])) for _ in 1:ng]
    for g in 1:ng, gp in 1:ng
        g != gp && (out[g] .+= p.S[g, gp] .* phi[gp])
        out[g] .+= p.F[g, gp] .* phi[gp]
        for d in 1:nd
            out[g] .-= x.Fd[g, gp, d] .* phi[gp]
        end
    end
    out
end

struct StepOp{F}
    f::F
    n::Int
end
Base.size(A::StepOp) = (A.n, A.n)
Base.size(A::StepOp, i) = A.n
Base.eltype(::StepOp) = Float64
LinearAlgebra.mul!(y, A::StepOp, v) = (y .= A.f(v); y)

# Block Gauss-Seidel over groups (lower triangle: the downscatter and the
# fast-from-thermal fission terms of g' < g), each group by AMG-CG on K'_g.
struct DualStepPre
    ml::Vector{Any}
    K::Vector{SparseMatrixCSC{Float64,Int}}
    Dp::SparseMatrixCSC{Float64,Int}
    Rp::Vector{Vector{Float64}}
    Cl::Matrix{Vector{Float64}}       # theta * coupling coefficient g <- g'
    n::Int
    tol::Float64
end
function LinearAlgebra.ldiv!(y, P::DualStepPre, r)
    ng = length(P.K)
    for g in 1:ng
        rg = r[(g-1)*P.n+1:g*P.n]
        for gp in 1:g-1
            rg = rg .+ P.Cl[g, gp] .* y[(gp-1)*P.n+1:gp*P.n]
        end
        b = P.Dp' * (rg ./ P.Rp[g])
        J, _ = cg(P.K[g], b; M=P.ml[g], ldiv=true, rtol=P.tol, atol=0.0, itmax=200)
        y[(g-1)*P.n+1:g*P.n] .= (rg .- P.Dp * J) ./ P.Rp[g]
    end
    y
end
LinearAlgebra.ldiv!(P::DualStepPre, r) = (y = similar(r); ldiv!(y, P, r); r .= y)

"""AMG hierarchies for the step face systems, reusable across steps (rods
move only a few planes per step; a stale hierarchy is still a preconditioner)."""
mutable struct DualStepCache
    ml::Vector{Any}
    age::Int
end
DualStepCache() = DualStepCache(Any[], typemax(Int) ÷ 2)

"""
    dual_kin_step!(s, x, lambda, dt; th=0.8, thp=0.8)
"""
function dual_kin_step!(s::DualKinState, x::DualKinXS, lambda, dt; th=0.8, thp=0.8, rtol=1e-9,
                        cache=DualStepCache(), amg_every=20, inner=1e-4, timing=nothing)
    p = x.p; ng = length(s.phi); n = length(p.cell); nd = length(lambda)
    t0 = time()
    facts = [cholesky(Symmetric(AM)) for AM in x.AM]
    # explicit half (new operators on the old state)
    Cex = couple_explicit(x, s.phi, lambda)
    rhs = Vector{Vector{Float64}}(undef, ng)
    for g in 1:ng
        R0 = -leak(facts[g], p.Dp, s.phi[g], 1.0) .- x.sigr[g] .* s.phi[g] .+ Cex[g]
        for d in 1:nd, i in axes(s.C, 2)
            R0 .+= lambda[d] .* x.chid[g, d, i] .* s.C[d, i]
        end
        rhs[g] = p.vol .* x.overv[:, g] ./ dt .* s.phi[g] .+ (1 - th) .* R0
        for d in 1:nd, i in axes(s.C, 2)
            tk1 = (1 - (1 - thp) * lambda[d] * dt) / (1 + thp * lambda[d] * dt)
            fac = lambda[d] * dt * (1 - thp) / (1 + thp * lambda[d] * dt)
            expl = sum(s.Pd_old[gp, d, i] .* s.phi[gp] for gp in 1:ng)
            rhs[g] .+= th .* lambda[d] .* x.chid[g, d, i] .* (tk1 .* s.C[d, i] .+ fac ./ lambda[d] .* expl)
        end
    end
    Rp = [p.vol .* x.overv[:, g] ./ dt .+ th .* x.sigr[g] for g in 1:ng]
    function T(v)
        phi = [v[(g-1)*n+1:g*n] for g in 1:ng]
        Cp = couple(x, phi, lambda, dt, thp)
        vcat([leak(facts[g], p.Dp, phi[g], th) .+ Rp[g] .* phi[g] .- th .* Cp[g] for g in 1:ng]...)
    end
    op = StepOp(T, ng * n)
    Kp = [x.AM[g] ./ th + p.Dp' * spdiagm(0 => 1 ./ Rp[g]) * p.Dp for g in 1:ng]
    t1 = time()
    if cache.age >= amg_every
        cache.ml = Any[aspreconditioner(smoothed_aggregation(K)) for K in Kp]; cache.age = 0
    end
    cache.age += 1
    Cl = [zeros(n) for g in 1:ng, gp in 1:ng]
    for g in 1:ng, gp in 1:g-1
        Cl[g, gp] = th .* (p.S[g, gp] .+ p.F[g, gp] .- sum((1 - lambda[d] * dt * thp / (1 + thp * lambda[d] * dt)) .* x.Fd[g, gp, d] for d in 1:nd))
    end
    P = DualStepPre(cache.ml, Kp, p.Dp, Rp, Cl, n, inner)
    t2 = time()
    # the preconditioner holds an inexact inner CG: flexible GMRES
    # Krylov.jl's rtol is relative to the initial residual, which the old
    # flux already makes small: stop on rtol * |b| instead
    b = vcat(rhs...)
    sol, st = fgmres(op, b, vcat(s.phi...); N=P, ldiv=true, rtol=0.0, atol=rtol * norm(b),
                     itmax=200, memory=50)
    st.solved || @warn "dual_kin_step!: FGMRES not converged" st.niter
    t3 = time()
    timing === nothing || push!(timing, (setup=t1 - t0, amg=t2 - t1, solve=t3 - t2))
    phi1 = [sol[(g-1)*n+1:g*n] for g in 1:ng]
    for d in 1:nd, i in axes(s.C, 2)
        tk1 = (1 - (1 - thp) * lambda[d] * dt) / (1 + thp * lambda[d] * dt)
        prod1 = sum(x.Pd[gp, d, i] .* phi1[gp] for gp in 1:ng)
        prod0 = sum(s.Pd_old[gp, d, i] .* s.phi[gp] for gp in 1:ng)
        s.C[d, i] = tk1 .* s.C[d, i] .+ dt .* (thp .* prod1 .+ (1 - thp) .* prod0) ./ (1 + thp * lambda[d] * dt)
    end
    s.phi = phi1; s.Pd_old = copy(x.Pd); s.t += dt
    st.niter
end

"""
    dual_wielandt_polish(p, k, phi; delta=0.01, tol=1e-10, maxit=20)

Wielandt (shifted inverse) iterations on a DualProblem eigenpair:
(L + R - S - mu F) psi = F phi with mu = 1/(k + delta), converging at
~delta/(delta + k - k2) per iteration, until the steady residual
|L phi + R phi - S phi - F phi/k| / |F phi/k| < tol.  The power-iteration
polish of solve_k_dual leaves ~1e-7, the floor of a null transient.
"""
function dual_wielandt_polish(p::DualProblem, k, phi; delta=0.01, tol=1e-10, maxit=20, verbose=false)
    ng = length(phi); n = length(p.cell)
    AM = [p.K[g] - p.Dp' * spdiagm(0 => 1 ./ p.R[g]) * p.Dp for g in 1:ng]
    facts = [cholesky(Symmetric(A)) for A in AM]
    ml = Any[aspreconditioner(smoothed_aggregation(K)) for K in p.K]
    Fphi(ph) = [sum(p.F[g, gp] .* ph[gp] for gp in 1:ng) for g in 1:ng]
    Aphi(ph) = [leak(facts[g], p.Dp, ph[g], 1.0) .+ p.R[g] .* ph[g] .-
                sum((gp == g ? zeros(n) : p.S[g, gp] .* ph[gp]) for gp in 1:ng) for g in 1:ng]
    resid(k, ph) = (a = vcat(Aphi(ph)...); f = vcat(Fphi(ph)...) ./ k; norm(a .- f) / norm(f))
    phi = [copy(f) for f in phi]
    r = resid(k, phi); verbose && @printf("  wielandt it 0: k %.9f residual %.2e\n", k, r)
    for it in 1:maxit
        r < tol && break
        mu = 1 / (k + delta)
        T(v) = (ph = [v[(g-1)*n+1:g*n] for g in 1:ng]; a = Aphi(ph); f = Fphi(ph);
                vcat([a[g] .- mu .* f[g] for g in 1:ng]...))
        Cl = [zeros(n) for g in 1:ng, gp in 1:ng]
        for g in 1:ng, gp in 1:g-1
            Cl[g, gp] = p.S[g, gp] .+ mu .* p.F[g, gp]
        end
        P = DualStepPre(ml, p.K, p.Dp, p.R, Cl, n, 1e-4)
        b = vcat(Fphi(phi)...)
        sol, st = fgmres(StepOp(T, ng * n), b, vcat(phi...) ./ (1 / k - mu);   # exact for an exact eigenpair
                        
                         N=P, ldiv=true, rtol=0.0, atol=1e-12 * norm(b), itmax=400, memory=100)
        psi = [sol[(g-1)*n+1:g*n] for g in 1:ng]
        # k from the balance  sum F psi / sum (A - S) psi
        k = sum(sum, Fphi(psi)) / sum(sum, Aphi(psi))
        s = sum(sum, psi); phi = [f ./ s .* sum(sum, phi) for f in psi]
        r = resid(k, phi)
        verbose && @printf("  wielandt it %d: k %.9f residual %.2e (%d fgmres)\n", it, k, r, st.niter)
    end
    k, phi, r
end

"""Relative steady residual |A phi - S phi - F phi| / |F phi| of the t = 0 state
(F already divided by k0): the floor of a null transient."""
function dual_steady_residual(x::DualKinXS, phi)
    p = x.p; ng = length(phi)
    facts = [cholesky(Symmetric(AM)) for AM in x.AM]
    r = [leak(facts[g], p.Dp, phi[g], 1.0) .+ x.sigr[g] .* phi[g] for g in 1:ng]
    f = [zeros(length(phi[1])) for _ in 1:ng]
    for g in 1:ng, gp in 1:ng
        g != gp && (r[g] .-= p.S[g, gp] .* phi[gp])
        f[g] .+= p.F[g, gp] .* phi[gp]
    end
    norm(vcat(r...) .- vcat(f...)) / norm(vcat(f...))
end

dual_kin_power(x::DualKinXS, s::DualKinState) =
    sum(sum(x.p.hfac[:, g] .* s.phi[g] .* x.p.vol) for g in eachindex(s.phi))

end # module
