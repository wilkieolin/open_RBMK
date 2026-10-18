# B6 groundwork: the RT0 face system K_g J = b on the GPU (CUDA.jl, cuSPARSE
# CSR, Jacobi-preconditioned CG through Krylov.jl) against the CPU AMG-CG.
# Memory: per group K ~ 244k rows x <= 11 nnz ~ 2.7M nnz -> ~32 MB CSR, two
# groups + D' (~8 MB) + Krylov vectors (~10 x 2 MB): < 200 MB, reserved below.
using RBMKCore, RBMKCore.Diffusion, RBMKCore.Mixed, CUDA, CUDA.CUSPARSE, Krylov, LinearAlgebra, SparseArrays
using AlgebraicMultigrid, Printf
include("b1_solver_load.jl")
mesh, ntot, D, scat, fiss, hfac, kref = load_b1(REF)
p = build_dual(mesh, ntot, D, scat, fiss, hfac)
nf = size(p.K[1], 1)
bytes = sum(nnz(K) * 12 + (nf + 1) * 4 for K in p.K) + nnz(p.Dp) * 12 * 2 + 40 * nf * 8
RBMKCore.reserve!(bytes, "B6 bench: K, D', Krylov work")
@printf("faces %d, nnz K1 %d, device reservation %.1f MiB\n", nf, nnz(p.K[1]), bytes / 2^20)
for g in 1:2
    K = p.K[g]
    b = p.Dp' * (ones(length(p.cell)) .* p.vol ./ p.R[g])
    ml = aspreconditioner(smoothed_aggregation(K))
    cg(K, b; M=ml, ldiv=true, rtol=1e-11, atol=0.0, itmax=1000)           # warm-up
    tc = @elapsed (xc, sc) = cg(K, b; M=ml, ldiv=true, rtol=1e-11, atol=0.0, itmax=1000)
    Kd = CuSparseMatrixCSR(K); bd = CuVector(b)
    Minv = Diagonal(CuVector(1 ./ diag(K)))
    cg(Kd, bd; M=Minv, rtol=1e-11, atol=0.0, itmax=20000)                  # warm-up
    CUDA.synchronize()
    tg = @elapsed begin
        xg, sg = cg(Kd, bd; M=Minv, rtol=1e-11, atol=0.0, itmax=20000)
        CUDA.synchronize()
    end
    rel = norm(Array(xg) .- xc) / norm(xc)
    @printf("group %d: CPU AMG-CG %d it %.3f s | GPU Jacobi-CG %d it %.3f s | rel diff %.2e\n",
            g, sc.niter, tc, sg.niter, tg, rel)
end
