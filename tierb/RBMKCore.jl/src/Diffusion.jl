# Two-group mesh-centred finite-difference diffusion on the DONJON Cartesian
# mesh (TIER_B_WORKPLAN.md, B1).
#
#   -div D_g grad phi_g + Sigma_t,g phi_g - sum_g' S[g,g'] phi_g'
#        = (1/k) sum_g' F[g,g'] phi_g'
#
# One unknown per group per non-void element (INDEX > 0).  Interface
# coupling uses the harmonic mean of D; a face on the box boundary or next to
# a void element (DONJON GEO: VOID) is a vacuum (Marshak) face, zero incoming
# partial current: J = phi_s / 2, which over a half cell gives the face
# coefficient 1 / (h/(2D) + 2) per unit area.
#
# Solver: block Gauss-Seidel over the two groups, each group a symmetric
# positive-definite system solved by conjugate gradients preconditioned with
# smoothed-aggregation algebraic multigrid; the eigenvalue by power
# iteration on A^{-1} F with Wielandt-free Chebyshev-free plain iteration
# accelerated by a final Arnoldi polish (KrylovKit) -- correctness first,
# the GPU path is B6.

module Diffusion

using SparseArrays, LinearAlgebra, AlgebraicMultigrid, Krylov, KrylovKit

export Mesh, Problem, build_problem, solve_k, solve_k_arnoldi, power_density, refine

struct Mesh
    nx::Int; ny::Int; nz::Int
    hx::Vector{Float64}; hy::Vector{Float64}; hz::Vector{Float64}
    index::Vector{Int}            # element -> region (0 = void), x fastest
end

"""Per-unknown (non-void element) cross sections."""
struct Problem
    mesh::Mesh
    cell::Vector{Int}             # unknown -> element
    vol::Vector{Float64}
    A::Vector{SparseMatrixCSC{Float64,Int}}   # per group: leakage + Sigma_t - S_gg
    S::Matrix{Vector{Float64}}    # S[g_to, g_from] off-diagonal transfer, per unknown
    F::Matrix{Vector{Float64}}    # F[g_to, g_from] fission production, per unknown
    hfac::Matrix{Float64}         # [unknown, g] energy release (power)
end

"""
    build_problem(mesh, ntot, diff, scat, fiss, hfac)

Region-wise data indexed by region number: `ntot[r, g]`, `diff[r, g]`,
`scat[r, g_to, g_from]`, `fiss[r, g_to, g_from]`, `hfac[r, g]`.
"""
function build_problem(mesh::Mesh, ntot, diff, scat, fiss, hfac)
    nx, ny, nz = mesh.nx, mesh.ny, mesh.nz
    ng = size(ntot, 2)
    cells = findall(>(0), mesh.index)
    n = length(cells)
    uid = zeros(Int, length(mesh.index))
    uid[cells] .= 1:n
    reg = mesh.index[cells]
    lin(i, j, k) = i + (j - 1) * nx + (k - 1) * nx * ny
    vol = [mesh.hx[(c-1)%nx+1] * mesh.hy[((c-1)÷nx)%ny+1] * mesh.hz[(c-1)÷(nx*ny)+1] for c in cells]
    A = SparseMatrixCSC{Float64,Int}[]
    for g in 1:ng
        I = Int[]; J = Int[]; V = Float64[]
        diag = zeros(n)
        for (u, c) in enumerate(cells)
            i = (c - 1) % nx + 1; j = ((c - 1) ÷ nx) % ny + 1; k = (c - 1) ÷ (nx * ny) + 1
            Du = diff[reg[u], g]
            h = (mesh.hx[i], mesh.hy[j], mesh.hz[k])
            area = (mesh.hy[j] * mesh.hz[k], mesh.hx[i] * mesh.hz[k], mesh.hx[i] * mesh.hy[j])
            for (dir, (di, dj, dk)) in enumerate(((1,0,0),(0,1,0),(0,0,1)))
                for s in (-1, 1)
                    ii, jj, kk = i + s*di, j + s*dj, k + s*dk
                    nb = (1 <= ii <= nx && 1 <= jj <= ny && 1 <= kk <= nz) ? uid[lin(ii, jj, kk)] : 0
                    if nb == 0
                        # vacuum face: 1 / (h/(2D) + 2)
                        diag[u] += area[dir] / (h[dir] / (2Du) + 2.0)
                    else
                        Dn = diff[reg[nb], g]
                        hn = dir == 1 ? mesh.hx[ii] : dir == 2 ? mesh.hy[jj] : mesh.hz[kk]
                        # series resistance of the two half cells
                        coef = area[dir] / (h[dir] / (2Du) + hn / (2Dn))
                        diag[u] += coef
                        push!(I, u); push!(J, nb); push!(V, -coef)
                    end
                end
            end
            diag[u] += vol[u] * (ntot[reg[u], g] - scat[reg[u], g, g])
        end
        append!(I, 1:n); append!(J, 1:n); append!(V, diag)
        push!(A, sparse(I, J, V, n, n))
    end
    S = [g == gp ? zeros(n) : vol .* scat[reg, g, gp] for g in 1:ng, gp in 1:ng]
    F = [vol .* fiss[reg, g, gp] for g in 1:ng, gp in 1:ng]
    H = hcat([hfac[reg, g] for g in 1:ng]...)
    Problem(mesh, cells, vol, A, S, F, H)
end

# One application of A^{-1} by block Gauss-Seidel over groups, AMG-PCG inside.
struct Inverse
    p::Problem
    ml::Vector{Any}
    rtol::Float64
    sweeps::Int
end

function Inverse(p::Problem; rtol=1e-10, sweeps=4)
    ml = Any[aspreconditioner(smoothed_aggregation(A)) for A in p.A]
    Inverse(p, ml, rtol, sweeps)
end

function apply!(phi::Vector{Vector{Float64}}, inv::Inverse, q::Vector{Vector{Float64}})
    p = inv.p
    ng = length(p.A)
    for sweep in 1:inv.sweeps
        for g in 1:ng
            rhs = copy(q[g])
            for gp in 1:ng
                gp == g && continue
                rhs .+= p.S[g, gp] .* phi[gp]
            end
            x, stats = cg(p.A[g], rhs, phi[g]; M=inv.ml[g], ldiv=true,
                          rtol=inv.rtol, atol=0.0, itmax=500)
            phi[g] .= x
        end
    end
    phi
end

function fission_source(p::Problem, phi)
    ng = length(p.A)
    [sum(p.F[g, gp] .* phi[gp] for gp in 1:ng) for g in 1:ng]
end

"""
    solve_k(p; tol=1e-9, maxit=2000) -> (k, phi)

Power iteration on A^{-1} F (fission-source normalised), with the inner
Gauss-Seidel sweeps warm-started from the previous flux.
"""
function solve_k(p::Problem; tol=1e-9, maxit=2000, verbose=false, phi0=nothing, k0=1.0)
    ng = length(p.A); n = length(p.cell)
    inv = Inverse(p)
    phi = phi0 === nothing ? [ones(n) for _ in 1:ng] : [copy(f) for f in phi0]
    k = k0
    src = fission_source(p, phi)
    total(s) = sum(sum, s)
    for it in 1:maxit
        q = [s ./ k for s in src]
        apply!(phi, inv, q)
        new = fission_source(p, phi)
        knew = k * total(new) / total(src)
        dk = abs(knew - k)
        err = maximum(maximum(abs.(new[g] ./ total(new) .- src[g] ./ total(src))) for g in 1:ng) *
              n
        k, src = knew, new
        verbose && (it % 25 == 0) && println("  it $it k $k dk $dk src-err $err")
        if dk < tol && err < 1e3 * tol
            verbose && println("  converged it $it k $k")
            break
        end
    end
    k, phi
end

"""
    solve_k_arnoldi(p; tol=1e-9, krylovdim=30) -> (k, phi)

Dominant eigenpair of A^{-1} F by Arnoldi (KrylovKit).  The core's dominance
ratio is ~0.994 (power iteration needs ~1150 iterations); Arnoldi converges
in a few tens of operator applications.  Each application solves A to
`inner` relative tolerance from a zero start.
"""
function solve_k_arnoldi(p::Problem; tol=1e-9, krylovdim=30, inner=1e-11, verbose=false, polish=true)
    ng = length(p.A); n = length(p.cell)
    inv = Inverse(p; rtol=inner, sweeps=6)
    napp = Ref(0)
    function op(x)
        napp[] += 1
        phi = [x[(g-1)*n+1:g*n] for g in 1:ng]
        q = fission_source(p, phi)
        out = [zeros(n) for _ in 1:ng]
        apply!(out, inv, q)
        vcat(out...)
    end
    x0 = ones(ng * n)
    vals, vecs, info = eigsolve(op, x0, 1, :LM; tol=tol, krylovdim=krylovdim,
                                ishermitian=false, verbosity=0)
    k = real(vals[1]); v = real.(vecs[1])
    v .*= sign(sum(v))
    verbose && println("  arnoldi: k $k, $(napp[]) applications, converged $(info.converged)")
    phi = [v[(g-1)*n+1:g*n] for g in 1:ng]
    # Arnoldi on an inexactly applied operator stalls near 1e-6 in k; polish
    # with warm-started power iterations, which converge from here quickly
    polish && ((k, phi) = solve_k(p; tol=tol, phi0=phi, k0=k, verbose=verbose))
    k, phi
end

"""
    refine(mesh, r) -> Mesh

Split every element into r^3, keeping its region (so its homogenised cross
sections): the same problem on a finer mesh, for the spatial-convergence
study of B1.
"""
function refine(m::Mesh, r::Int)
    nx, ny, nz = r*m.nx, r*m.ny, r*m.nz
    idx = zeros(Int, nx*ny*nz)
    for k in 1:nz, j in 1:ny, i in 1:nx
        I = (i-1)÷r + 1; J = (j-1)÷r + 1; K = (k-1)÷r + 1
        idx[i + (j-1)*nx + (k-1)*nx*ny] = m.index[I + (J-1)*m.nx + (K-1)*m.nx*m.ny]
    end
    Mesh(nx, ny, nz, repeat(m.hx ./ r, inner=r), repeat(m.hy ./ r, inner=r),
         repeat(m.hz ./ r, inner=r), idx)
end

"""Power density per unknown (arbitrary normalisation): sum_g H_g phi_g."""
power_density(p::Problem, phi) = sum(p.hfac[:, g] .* phi[g] for g in eachindex(phi))

end # module
