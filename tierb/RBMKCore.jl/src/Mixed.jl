# Mixed-dual (Raviart-Thomas RT0) diffusion, the scheme of TRIVAC's
# DUAL 1 1 (ielem 1, icol 1: analytic integration, i.e. the CONSISTENT
# current mass matrix).  The A6 CPS cross sections are SPH-equivalenced on
# exactly this discretisation at 25 cm (COMPO comment "SPH (TRIVAT DUAL 1
# 1)"), so it is the consistent spatial method for them: mesh-centred FD
# (= RT0 with a LUMPED mass, TRIVAC MCFD 1) differs by ~420 pcm at 25 cm and
# does not converge to it under refinement (B1 study: p ~ 0.3).
#
# Per group, unknowns are the face currents J (one per face of a non-void
# cell; a face on the box or next to a void cell is a vacuum face) and the
# cell fluxes phi.  Along a line of cells in direction d with lengths h and
# diffusion coefficients D, RT0 gives, per unit face area,
#   Fick:     sum_cells (h/(3D) J_f + h/(6D) J_f')  - (phi_left - phi_right) = 0
#             (f' the cell's other face in the same direction; at a vacuum
#              face phi_outside = 2 J_out, which adds 2 to the diagonal)
#   balance:  sum_faces A_f s_if J_f + V_i Sigma_r phi_i = q_i  (volume-integrated)
# With face areas: (A M) J - D'^T phi = 0, D' J + R phi = q, D'[i,f] = A_f s_if,
# R = diag(V Sigma_r).  Eliminating phi = R^{-1}(q - D'J) leaves an SPD face
# system  K J = D'^T R^{-1} q,  K = A M + D'^T R^{-1} D'.

module Mixed

using SparseArrays, LinearAlgebra, AlgebraicMultigrid, Krylov, KrylovKit
using ..Diffusion: Mesh

export DualProblem, build_dual, solve_k_dual, dual_power_density

struct DualProblem
    mesh::Mesh
    cell::Vector{Int}                          # unknown cell -> element
    vol::Vector{Float64}
    Dp::SparseMatrixCSC{Float64,Int}           # D'[cell, face] = A_f s_if
    K::Vector{SparseMatrixCSC{Float64,Int}}    # per group face operator
    R::Vector{Vector{Float64}}                 # per group V*Sigma_r
    S::Matrix{Vector{Float64}}                 # off-diagonal transfer, volume-integrated
    F::Matrix{Vector{Float64}}                 # fission production, volume-integrated
    hfac::Matrix{Float64}
end

function build_dual(mesh::Mesh, ntot, diff, scat, fiss, hfac)
    nx, ny, nz = mesh.nx, mesh.ny, mesh.nz
    ng = size(ntot, 2)
    cells = findall(>(0), mesh.index)
    n = length(cells)
    uid = zeros(Int, length(mesh.index)); uid[cells] .= 1:n
    reg = mesh.index[cells]
    lin(i, j, k) = i + (j - 1) * nx + (k - 1) * nx * ny
    ijk(c) = ((c - 1) % nx + 1, ((c - 1) ÷ nx) % ny + 1, (c - 1) ÷ (nx * ny) + 1)
    hs = (mesh.hx, mesh.hy, mesh.hz)
    vol = [mesh.hx[i] * mesh.hy[j] * mesh.hz[k] for (i, j, k) in ijk.(cells)]
    # faces: for each cell and direction, its low and high face.  A face
    # between two non-void cells is shared (owned by the low cell's high side).
    nfaces = 0
    lo = zeros(Int, n, 3); hi = zeros(Int, n, 3)
    area = Float64[]; dirf = Int[]
    for u in 1:n, d in 1:3
        i, j, k = ijk(cells[u])
        a = d == 1 ? mesh.hy[j] * mesh.hz[k] : d == 2 ? mesh.hx[i] * mesh.hz[k] : mesh.hx[i] * mesh.hy[j]
        # low face: shared with the low neighbour if it exists
        ii, jj, kk = i - (d == 1), j - (d == 2), k - (d == 3)
        nb = (ii >= 1 && jj >= 1 && kk >= 1) ? uid[lin(ii, jj, kk)] : 0
        if nb > 0
            lo[u, d] = hi[nb, d]            # neighbour's high face (already made: lower index)
        else
            nfaces += 1; lo[u, d] = nfaces; push!(area, a); push!(dirf, d)
        end
        nfaces += 1; hi[u, d] = nfaces; push!(area, a); push!(dirf, d)
    end
    # a high face with no high neighbour is a vacuum face; mark boundary faces
    vac = falses(nfaces)
    for u in 1:n, d in 1:3
        i, j, k = ijk(cells[u])
        ii, jj, kk = i + (d == 1), j + (d == 2), k + (d == 3)
        nb = (ii <= nx && jj <= ny && kk <= nz) ? uid[lin(ii, jj, kk)] : 0
        nb == 0 && (vac[hi[u, d]] = true)
        ii, jj, kk = i - (d == 1), j - (d == 2), k - (d == 3)
        nb = (ii >= 1 && jj >= 1 && kk >= 1) ? uid[lin(ii, jj, kk)] : 0
        nb == 0 && (vac[lo[u, d]] = true)
    end
    # D'[cell, face] = A_f s_if (outward +1 on the high face, -1 on the low)
    Is = Int[]; Js = Int[]; Vs = Float64[]
    for u in 1:n, d in 1:3
        push!(Is, u); push!(Js, hi[u, d]); push!(Vs, area[hi[u, d]])
        push!(Is, u); push!(Js, lo[u, d]); push!(Vs, -area[lo[u, d]])
    end
    Dp = sparse(Is, Js, Vs, n, nfaces)
    K = SparseMatrixCSC{Float64,Int}[]; R = Vector{Float64}[]
    for g in 1:ng
        Im = Int[]; Jm = Int[]; Vm = Float64[]
        for u in 1:n, d in 1:3
            i, j, k = ijk(cells[u])
            h = hs[d][d == 1 ? i : d == 2 ? j : k]
            D = diff[reg[u], g]
            a = area[hi[u, d]]
            fl, fh = lo[u, d], hi[u, d]
            # A * per-unit-area mass: h/(3D) on the cell's two faces, h/(6D) between them
            push!(Im, fl); push!(Jm, fl); push!(Vm, a * h / (3D))
            push!(Im, fh); push!(Jm, fh); push!(Vm, a * h / (3D))
            push!(Im, fl); push!(Jm, fh); push!(Vm, a * h / (6D))
            push!(Im, fh); push!(Jm, fl); push!(Vm, a * h / (6D))
        end
        for f in 1:nfaces                     # Marshak vacuum: phi_out = 2 J_out
            vac[f] && (push!(Im, f); push!(Jm, f); push!(Vm, 2.0 * area[f]))
        end
        AM = sparse(Im, Jm, Vm, nfaces, nfaces)
        r = vol .* (ntot[reg, g] .- scat[reg, g, g])
        push!(R, r)
        push!(K, AM + Dp' * spdiagm(0 => 1 ./ r) * Dp)
    end
    S = [g == gp ? zeros(n) : vol .* scat[reg, g, gp] for g in 1:ng, gp in 1:ng]
    F = [vol .* fiss[reg, g, gp] for g in 1:ng, gp in 1:ng]
    H = hcat([hfac[reg, g] for g in 1:ng]...)
    DualProblem(mesh, cells, vol, Dp, K, R, S, F, H)
end

struct DualInverse
    p::DualProblem
    ml::Vector{Any}
    rtol::Float64
    sweeps::Int
    J::Vector{Vector{Float64}}
end

DualInverse(p::DualProblem; rtol=1e-11, sweeps=6) =
    DualInverse(p, Any[aspreconditioner(smoothed_aggregation(K)) for K in p.K], rtol, sweeps,
                [zeros(size(p.K[1], 1)) for _ in p.K])

"""phi = A^{-1} q per group by Gauss-Seidel over groups (q volume-integrated)."""
function apply_dual!(phi, inv::DualInverse, q)
    p = inv.p; ng = length(p.K)
    for sweep in 1:inv.sweeps, g in 1:ng
        rhs = copy(q[g])
        for gp in 1:ng
            gp != g && (rhs .+= p.S[g, gp] .* phi[gp])
        end
        b = p.Dp' * (rhs ./ p.R[g])
        J, st = cg(p.K[g], b, inv.J[g]; M=inv.ml[g], ldiv=true, rtol=inv.rtol, atol=0.0, itmax=1000)
        inv.J[g] .= J
        phi[g] .= (rhs .- p.Dp * J) ./ p.R[g]
    end
    phi
end

fission_source(p::DualProblem, phi) = [sum(p.F[g, gp] .* phi[gp] for gp in eachindex(phi)) for g in eachindex(phi)]

"""Dominant k by Arnoldi on A^{-1}F, polished by warm power iterations."""
function solve_k_dual(p::DualProblem; tol=1e-9, krylovdim=30, verbose=false, maxpolish=500)
    ng = length(p.K); n = length(p.cell)
    inv = DualInverse(p)
    napp = Ref(0)
    function op(x)
        napp[] += 1
        q = fission_source(p, [x[(g-1)*n+1:g*n] for g in 1:ng])
        out = [zeros(n) for _ in 1:ng]
        fill!.(inv.J, 0.0)
        apply_dual!(out, inv, q)
        vcat(out...)
    end
    vals, vecs, info = eigsolve(op, ones(ng * n), 1, :LM; tol=tol, krylovdim=krylovdim,
                                ishermitian=false, verbosity=0)
    k = real(vals[1]); v = real.(vecs[1]); v .*= sign(sum(v))
    phi = [v[(g-1)*n+1:g*n] for g in 1:ng]
    verbose && println("  arnoldi: k $k, $(napp[]) applications")
    src = fission_source(p, phi)
    tot(s) = sum(sum, s)
    for it in 1:maxpolish
        apply_dual!(phi, inv, [s ./ k for s in src])
        new = fission_source(p, phi)
        knew = k * tot(new) / tot(src)
        dk = abs(knew - k); k, src = knew, new
        if dk < tol
            verbose && println("  polish converged it $it k $k")
            break
        end
    end
    k, phi
end

dual_power_density(p::DualProblem, phi) = sum(p.hfac[:, g] .* phi[g] for g in eachindex(phi))

end # module
