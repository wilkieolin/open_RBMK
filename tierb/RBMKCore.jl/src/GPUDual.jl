# The RT0 mixed-dual solvers on the GPU (B6): the same algebra as Mixed.jl
# and DualKinetics.jl, with every sparse solve a Jacobi-preconditioned CG
# on cuSPARSE CSR.  Measured on the B1 core (test/b6_gpu_bench.jl): the
# face system K_g J = b in 38 / 129 iterations, 0.034 / 0.044 s, against
# 0.65 / 2.0 s for AMG-CG on the CPU, agreeing to 1e-11.  The current mass
# A M is tridiagonal along each mesh line with condition <= 3 (h/3D, h/6D),
# so its solve is also Jacobi-CG, in a handful of iterations.
#
# Verified against the CPU solvers, which stay the reference.
#
# Memory (asserted through Budget.jl at construction): per group K (~2.6M
# nnz) and A M (~0.7M nnz) in CSR at 12 B/nnz, D' and D'^T (~0.6M nnz
# each), ~60 cell/face vectors of the kinetic data and Krylov work:
# ~0.25 GB for the Unit 4 core.

module GPUDual

using CUDA, CUDA.CUSPARSE, SparseArrays, LinearAlgebra, Krylov, KrylovKit, Printf
using ..Mixed, ..DualKinetics
import ..reserve!, ..release!

export GDual, gdual, gfree!, gkin_xs, gkin_free!, gsolve_k, gwielandt, GKinState, gkin_init, gkin_step!, gkin_power, gsteady_residual

const CV = CuVector{Float64}

struct JCG                          # x = A \ b by Jacobi-PCG
    A::CuSparseMatrixCSR{Float64,Int32}
    dinv::CV
    rtol::Float64
end
JCG(A::SparseMatrixCSC, rtol) = JCG(CuSparseMatrixCSR(A), CV(1 ./ diag(A)), rtol)
function solve(s::JCG, b, x0=nothing; rtol=s.rtol, itmax=20000)
    x, st = x0 === nothing ? cg(s.A, b; M=Diagonal(s.dinv), rtol=rtol, atol=0.0, itmax=itmax) :
                             cg(s.A, b, x0; M=Diagonal(s.dinv), rtol=0.0, atol=rtol * norm(b), itmax=itmax)
    x
end

"""Device copy of a DualProblem (fission already divided by k0 if it was)."""
struct GDual
    n::Int
    nf::Int
    Dp::CuSparseMatrixCSR{Float64,Int32}
    DpT::CuSparseMatrixCSR{Float64,Int32}
    K::Vector{JCG}
    AM::Vector{JCG}
    AMcpu::Vector{SparseMatrixCSC{Float64,Int}}
    Dpcpu::SparseMatrixCSC{Float64,Int}
    R::Vector{CV}
    S::Matrix{CV}
    F::Matrix{CV}
    vol::CV
    hfac::Matrix{Float64}
    bytes::Int
end

# CUDA.jl frees device arrays only when the Julia GC finalises them, and on
# the GB10's unified memory its pool can grow toward the whole 110 GB (a
# kinetics run did ~5 GB/step before this was found).  Every GPU run must
# therefore cap the pool, so that it collects or fails instead of paging:
#   JULIA_CUDA_HARD_MEMORY_LIMIT=8GiB julia ...
function check_pool_limit()
    haskey(ENV, "JULIA_CUDA_HARD_MEMORY_LIMIT") ||
        error("GPUDual: set JULIA_CUDA_HARD_MEMORY_LIMIT (e.g. 8GiB) -- unified memory, see GPUDual.jl")
end

function gdual(p::DualProblem; rtol=1e-12, Fscale=1.0, topo::Union{Nothing,GDual}=nothing)
    check_pool_limit()
    ng = length(p.K); n = length(p.cell); nf = size(p.K[1], 1)
    AM = [p.K[g] - p.Dp' * spdiagm(0 => 1 ./ p.R[g]) * p.Dp for g in 1:ng]
    bytes = sum(12 * nnz(K) + 4 * (nf + 1) + 8 * nf for K in p.K) +
            sum(12 * nnz(A) + 4 * (nf + 1) + 8 * nf for A in AM) + 24 * nnz(p.Dp) + 8 * n * (2 + ng + 2ng^2)
    reserve!(bytes, "GPUDual operator")
    # D' is the mesh topology: shared with `topo` when given (same core mesh)
    Dp, DpT = topo === nothing ? (CuSparseMatrixCSR(p.Dp), CuSparseMatrixCSR(sparse(p.Dp'))) : (topo.Dp, topo.DpT)
    GDual(n, nf, Dp, DpT,
          [JCG(K, rtol) for K in p.K], [JCG(A, rtol) for A in AM], AM, p.Dp, [CV(r) for r in p.R],
          [CV(s) for s in p.S], [CV(f .* Fscale) for f in p.F], CV(p.vol), p.hfac, bytes)
end
"""Free a GDual's device arrays now (not at some later GC) and return its
reservation; `topology=false` keeps D' for reuse by the next step."""
function gfree!(G::GDual; topology=true)
    for s in (G.K..., G.AM...)
        CUDA.unsafe_free!(s.A); CUDA.unsafe_free!(s.dinv)
    end
    foreach(CUDA.unsafe_free!, G.R); foreach(CUDA.unsafe_free!, G.S); foreach(CUDA.unsafe_free!, G.F)
    if topology
        CUDA.unsafe_free!(G.Dp); CUDA.unsafe_free!(G.DpT); CUDA.unsafe_free!(G.vol)
    end
    release!(G.bytes)
end

leak(G::GDual, g, phi, s) = G.Dp * (s .* solve(G.AM[g], G.DpT * phi))

# phi = A^{-1} q per group, Gauss-Seidel over groups (Mixed.apply_dual!)
function apply_inverse!(phi, G::GDual, q; sweeps=6, rtol=1e-11)
    ng = length(G.K)
    for _ in 1:sweeps, g in 1:ng
        rhs = copy(q[g])
        for gp in 1:ng
            gp != g && (rhs .+= G.S[g, gp] .* phi[gp])
        end
        J = solve(G.K[g], G.DpT * (rhs ./ G.R[g]); rtol)
        phi[g] .= (rhs .- G.Dp * J) ./ G.R[g]
    end
    phi
end
fsource(G::GDual, phi) = [sum(G.F[g, gp] .* phi[gp] for gp in eachindex(phi)) for g in eachindex(phi)]

"""Dominant eigenpair by Arnoldi on A^{-1} F (as Mixed.solve_k_dual)."""
function gsolve_k(G::GDual; tol=1e-9, krylovdim=30, verbose=false)
    ng = length(G.K); n = G.n
    napp = Ref(0)
    function op(x)
        napp[] += 1
        q = fsource(G, [x[(g-1)*n+1:g*n] for g in 1:ng])
        out = [CUDA.zeros(Float64, n) for _ in 1:ng]
        apply_inverse!(out, G, q)
        vcat(out...)
    end
    vals, vecs, info = eigsolve(op, CUDA.ones(Float64, ng * n), 1, :LM; tol, krylovdim, ishermitian=false, verbosity=0)
    k = real(vals[1]); v = real.(vecs[1]); v .*= sign(sum(v))
    verbose && @printf("  gpu arnoldi: k %.9f, %d applications\n", k, napp[])
    k, [v[(g-1)*n+1:g*n] for g in 1:ng]
end

Aphi(G::GDual, phi) = [leak(G, g, phi[g], 1.0) .+ G.R[g] .* phi[g] .-
                       sum((gp == g ? zero(phi[g]) : G.S[g, gp] .* phi[gp]) for gp in eachindex(phi)) for g in eachindex(phi)]
function gsteady_residual(G::GDual, k, phi)
    a = vcat(Aphi(G, phi)...); f = vcat(fsource(G, phi)...) ./ k
    norm(a .- f) / norm(f)
end

struct GOp{F}; f::F; n::Int; end
Base.size(A::GOp) = (A.n, A.n); Base.size(A::GOp, i) = A.n; Base.eltype(::GOp) = Float64
LinearAlgebra.mul!(y, A::GOp, v) = (y .= A.f(v); y)

# block Gauss-Seidel over groups, each group by Jacobi-CG on its face system
struct GPre
    K::Vector{JCG}
    Dp::CuSparseMatrixCSR{Float64,Int32}
    DpT::CuSparseMatrixCSR{Float64,Int32}
    Rp::Vector{CV}
    Cl::Matrix{CV}
    n::Int
    tol::Float64
end
function LinearAlgebra.ldiv!(y, P::GPre, r)
    for g in eachindex(P.K)
        rg = r[(g-1)*P.n+1:g*P.n]
        for gp in 1:g-1
            rg = rg .+ P.Cl[g, gp] .* y[(gp-1)*P.n+1:gp*P.n]
        end
        J = solve(P.K[g], P.DpT * (rg ./ P.Rp[g]); rtol=P.tol)
        y[(g-1)*P.n+1:g*P.n] .= (rg .- P.Dp * J) ./ P.Rp[g]
    end
    y
end
LinearAlgebra.ldiv!(P::GPre, r) = (y = similar(r); ldiv!(y, P, r); r .= y)

"""Wielandt polish to a steady residual < tol (DualKinetics.dual_wielandt_polish)."""
function gwielandt(G::GDual, k, phi; delta=0.01, tol=1e-10, maxit=30, verbose=false)
    ng = length(G.K); n = G.n
    r = gsteady_residual(G, k, phi); verbose && @printf("  gpu wielandt it 0: k %.9f residual %.2e\n", k, r)
    for it in 1:maxit
        r < tol && break
        mu = 1 / (k + delta)
        T(v) = (ph = [v[(g-1)*n+1:g*n] for g in 1:ng]; a = Aphi(G, ph); f = fsource(G, ph);
                vcat([a[g] .- mu .* f[g] for g in 1:ng]...))
        Cl = [CUDA.zeros(Float64, n) for g in 1:ng, gp in 1:ng]
        for g in 1:ng, gp in 1:g-1
            Cl[g, gp] = G.S[g, gp] .+ mu .* G.F[g, gp]
        end
        P = GPre(G.K, G.Dp, G.DpT, G.R, Cl, n, 1e-4)
        b = vcat(fsource(G, phi)...)
        sol, st = fgmres(GOp(T, ng * n), b, vcat(phi...) ./ (1 / k - mu); N=P, ldiv=true, rtol=0.0,
                         atol=1e-12 * norm(b), itmax=400, memory=100)
        psi = [sol[(g-1)*n+1:g*n] for g in 1:ng]
        k = sum(sum, fsource(G, psi)) / sum(sum, Aphi(G, psi))
        s = sum(sum, psi); phi = [f ./ s .* sum(sum, phi) for f in psi]
        r = gsteady_residual(G, k, phi)
        verbose && @printf("  gpu wielandt it %d: k %.9f residual %.2e (%d fgmres)\n", it, k, r, st.niter)
    end
    k, phi, r
end

# ---------------------------------------------------------------------------
# kinetics: the theta scheme of DualKinetics on device data

struct GKin
    G::GDual                          # F divided by k0
    Fd::Array{CV,3}
    Pd::Array{CV,3}
    chid::Array{CV,3}
    overv::Matrix{CV}                 # [1, g] cell vectors
end
function gkin_xs(x::DualKinXS; rtol=1e-12, topo=nothing)
    G = gdual(x.p; rtol, topo)        # x.p.F already / k0
    GKin(G, map(CV, x.Fd), map(CV, x.Pd), map(CV, x.chid), reshape([CV(x.overv[:, g]) for g in 1:size(x.overv, 2)], 1, :))
end
"""Free a step's device data; the mesh topology is kept for the next step."""
function gkin_free!(x::GKin)
    gfree!(x.G; topology=false)
    foreach(CUDA.unsafe_free!, x.Fd); foreach(CUDA.unsafe_free!, x.Pd)
    foreach(CUDA.unsafe_free!, x.chid); foreach(CUDA.unsafe_free!, x.overv)
end

mutable struct GKinState
    phi::Vector{CV}
    C::Matrix{CV}
    Pd_old::Array{CV,3}
    t::Float64
end
gkin_init(s::DualKinState) = GKinState(map(CV, s.phi), map(CV, s.C), map(CV, s.Pd_old), s.t)
gkin_power(x::GKin, s::GKinState) = sum(sum(CV(x.G.hfac[:, g]) .* s.phi[g] .* x.G.vol) for g in eachindex(s.phi))

function gkin_step!(s::GKinState, x::GKin, lambda, dt; th=0.8, thp=0.8, rtol=1e-9, inner=1e-4)
    G = x.G; ng = length(s.phi); n = G.n; nd = length(lambda)
    rhs = Vector{CV}(undef, ng)
    for g in 1:ng
        R0 = -leak(G, g, s.phi[g], 1.0) .- G.R[g] .* s.phi[g]
        for gp in 1:ng
            g != gp && (R0 .+= G.S[g, gp] .* s.phi[gp])
            R0 .+= G.F[g, gp] .* s.phi[gp]
            for d in 1:nd
                R0 .-= x.Fd[g, gp, d] .* s.phi[gp]
            end
        end
        for d in 1:nd, i in axes(s.C, 2)
            R0 .+= lambda[d] .* x.chid[g, d, i] .* s.C[d, i]
        end
        rhs[g] = G.vol .* x.overv[1, g] ./ dt .* s.phi[g] .+ (1 - th) .* R0
        for d in 1:nd, i in axes(s.C, 2)
            tk1 = (1 - (1 - thp) * lambda[d] * dt) / (1 + thp * lambda[d] * dt)
            fac = lambda[d] * dt * (1 - thp) / (1 + thp * lambda[d] * dt)
            expl = sum(s.Pd_old[gp, d, i] .* s.phi[gp] for gp in 1:ng)
            rhs[g] .+= th .* lambda[d] .* x.chid[g, d, i] .* (tk1 .* s.C[d, i] .+ fac ./ lambda[d] .* expl)
        end
    end
    Rp = [G.vol .* x.overv[1, g] ./ dt .+ th .* G.R[g] for g in 1:ng]
    facd = [lambda[d] * dt * thp / (1 + thp * lambda[d] * dt) for d in 1:nd]
    # coupling coefficients g <- g' (scatter + fission - delayed + implicit return)
    Cc = [(g == gp ? zero(G.R[g]) : G.S[g, gp]) .+ G.F[g, gp] .-
          sum((1 - facd[d]) .* x.Fd[g, gp, d] for d in 1:nd) for g in 1:ng, gp in 1:ng]
    function T(v)
        phi = [v[(g-1)*n+1:g*n] for g in 1:ng]
        vcat([leak(G, g, phi[g], th) .+ Rp[g] .* phi[g] .- th .* sum(Cc[g, gp] .* phi[gp] for gp in 1:ng) for g in 1:ng]...)
    end
    Kp = [kprime(G, g, th, Rp[g]) for g in 1:ng]
    Cl = [th .* Cc[g, gp] for g in 1:ng, gp in 1:ng]
    P = GPre(Kp, G.Dp, G.DpT, Rp, Cl, n, inner)
    b = vcat(rhs...)
    sol, st = fgmres(GOp(T, ng * n), b, vcat(s.phi...); N=P, ldiv=true, rtol=0.0, atol=rtol * norm(b),
                     itmax=200, memory=50)
    st.solved || @warn "gkin_step!: FGMRES not converged" st.niter
    phi1 = [sol[(g-1)*n+1:g*n] for g in 1:ng]
    for d in 1:nd, i in axes(s.C, 2)
        tk1 = (1 - (1 - thp) * lambda[d] * dt) / (1 + thp * lambda[d] * dt)
        prod1 = sum(x.Pd[gp, d, i] .* phi1[gp] for gp in 1:ng)
        prod0 = sum(s.Pd_old[gp, d, i] .* s.phi[gp] for gp in 1:ng)
        s.C[d, i] = tk1 .* s.C[d, i] .+ dt .* (thp .* prod1 .+ (1 - thp) .* prod0) ./ (1 + thp * lambda[d] * dt)
    end
    foreach(CUDA.unsafe_free!, s.phi); foreach(CUDA.unsafe_free!, s.Pd_old)
    # deep copy: x's device arrays are freed by gkin_free! after the step
    s.phi = phi1; s.Pd_old = map(copy, x.Pd); s.t += dt
    for K in Kp
        CUDA.unsafe_free!(K.A); CUDA.unsafe_free!(K.dinv)
    end
    GC.gc(false)                      # the Krylov temporaries
    st.niter
end

# K'_g = A M_g / theta + D'^T R'^{-1} D', assembled on the CPU from the cached A M
function kprime(G::GDual, g, th, Rp)
    Dp = G.Dpcpu
    JCG(G.AMcpu[g] ./ th + Dp' * spdiagm(0 => 1 ./ Array(Rp)) * Dp, 1e-12)
end

end # module
