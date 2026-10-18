# B1 solver gate: the FD solver on DONJON's own final per-region macrolib
# (MACRD after NCR + MACINI + NEWMAC; tools/tierb_export_core.py), so the
# comparison isolates the spatial method (FD here, TRIVAT DUAL 1 1 there).
using RBMKCore.Diffusion, HDF5

const REF = joinpath(@__DIR__, "..", "..", "xs", "rbmk_unit4_core_dev_axf527ca_cB4af83e", "b1ref.h5")

function load_b1(path)
    h5open(path, "r") do h
        m, x = h["macrd"], h["matex"]
        ntot = permutedims(read(m["NTOT0"]))                 # [r, g]
        diff = permutedims(read(m["DIFF"]))
        hfac = permutedims(read(m["H-FACTOR"]))
        sc = read(m["SCAT"])                                  # [g_from, g_to, r]
        nr = size(ntot, 1); ng = size(ntot, 2)
        scat = zeros(nr, ng, ng)
        for r in 1:nr, gt in 1:ng, gf in 1:ng
            scat[r, gt, gf] = sc[gf, gt, r]
        end
        nu = read(m["NUSIGF"]); chi = read(m["CHI"])          # [g, iso, r]
        fiss = zeros(nr, ng, ng)
        for r in 1:nr, i in axes(nu, 2), gf in 1:ng, gt in 1:ng
            fiss[r, gt, gf] += chi[gt, i, r] * nu[gf, i, r]
        end
        mx, my, mz = read(x["MESHX"]), read(x["MESHY"]), read(x["MESHZ"])
        mesh = Mesh(length(mx)-1, length(my)-1, length(mz)-1, diff_(mx), diff_(my), diff_(mz),
                    Int.(read(x["INDEX"])))
        k = read_attribute(h, "keff")
        mesh, ntot, diff, scat, fiss, hfac, k
    end
end
diff_(m) = m[2:end] .- m[1:end-1]

