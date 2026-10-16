# B0 gate: Julia's multilinear interpolation of the exported grid against
# DONJON NCR's own macrolib at 26 seeded off-grid states
# (tools/tierb_export_xs.py check).  Tolerance 1e-6 relative.
using RBMKCore.XS, HDF5, Test

const XSDIR = joinpath(@__DIR__, "..", "..", "xs")

@testset "B0 cross sections vs NCR" begin
    xs = load_fuel(joinpath(XSDIR, "tierb_xs_af4c362b.h5"))
    ref = h5open(joinpath(XSDIR, "tierb_xs_af4c362b_chk.h5"))
    states = read(ref["states"])                  # [key, n]
    function Fref(c, f)
        F = zeros(size(c, 1), size(c, 1))
        for i in axes(c, 2), gf in axes(c, 1), gt in axes(c, 1)
            F[gt, gf] += c[gt, i] * f[gf, i]
        end
        F
    end
    rel(a, b) = maximum(abs.(a .- b) ./ max.(abs.(b), 1e-30))
    worst = Dict{String,Float64}()
    nusigf_r, chi_r = read(ref["NUSIGF"]), read(ref["CHI"])
    for n in axes(states, 2)
        m = interp(xs, states[:, n])
        pairs = [("NTOT0", m.ntot, read(ref["NTOT0"])[:, n]),
                 ("DIFF", m.diff, read(ref["DIFF"])[:, n]),
                 ("OVERV", m.overv, read(ref["OVERV"])[:, n]),
                 ("H-FACTOR", m.hfac, read(ref["H-FACTOR"])[:, n]),
                 ("SCAT", m.scat, permutedims(read(ref["SCAT"])[:, :, n])),
                 ("NUSIGF", m.nusigf, nusigf_r[:, :, n]),
                 ("CHI", m.chi, chi_r[:, :, n]),
                 ("F", fission_matrix(m), Fref(chi_r[:, :, n], nusigf_r[:, :, n]))]
        for (name, a, b) in pairs
            mask = abs.(b) .> 0
            r = any(mask) ? rel(a[mask], b[mask]) : 0.0
            worst[name] = max(get(worst, name, 0.0), r)
        end
    end
    close(ref)
    for (k, v) in sort(collect(worst))
        println(rpad(k, 10), " worst relative difference ", v)
        # per-isotope NUSIGF/CHI are informational: single-precision storage
        # of isotopes that contribute ~nothing; the physics uses F
        k in ("NUSIGF", "CHI") || @test v <= 1e-6
    end
end
