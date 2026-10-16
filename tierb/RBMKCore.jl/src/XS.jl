# Cross sections exported from the Tier A COMPOs by tools/tierb_export_xs.py.
#
# The export holds DONJON NCR's own macrolib at every COMPO grid node
# (1728 = 12 burnup x 6 TF x 3 TG x 8 DCA for the fuel).  `interp` is
# multilinear between nodes, which is what NCR's LINEAR option does; the B0
# gate (test/b0_xs.jl) compares it with NCR at off-grid states.
#
# NCR interpolates nu*Sigma_f and chi per fissile isotope, separately, so the
# fission source is formed only AFTER interpolation (`fission_matrix`).
# The diffusion coefficient is interpolated as 1/D, i.e. linearly in the
# transport cross section: measured against NCR, D itself is off by up to
# 8e-5 and 1/D by 1.3e-7 (float32 storage).

module XS

using HDF5

export FuelXS, RefXS, MacroXS, load_fuel, load_ref, interp, fission_matrix,
       delayed_matrices

"""Fuel cross-section table on the COMPO grid.  Arrays are [.., state] with
the state index running over `keys` with the LAST key fastest
(itertools.product order in the exporter)."""
struct FuelXS
    keys::Vector{String}
    axes::Vector{Vector{Float64}}
    ntot::Matrix{Float64}        # [g, s]
    diff::Matrix{Float64}        # [g, s]
    overv::Matrix{Float64}       # [g, s]  1/v
    hfac::Matrix{Float64}        # [g, s]  H-FACTOR (energy per volume, power)
    scat::Array{Float64,3}       # [g_from, g_to, s] as read; see `interp`
    nusigf::Array{Float64,3}     # [g, iso, s]
    chi::Array{Float64,3}        # [g, iso, s]
    nusigfd::Array{Float64,4}    # [g, iso, d, s]
    chid::Array{Float64,4}       # [g, iso, d, s]
    lambda::Vector{Float64}      # [d]
    source::Dict{String,String}  # COMPO file names and md5s
end

"""Macroscopic cross sections of one mixture at one state."""
struct MacroXS
    ntot::Vector{Float64}        # [g]
    diff::Vector{Float64}        # [g]
    overv::Vector{Float64}       # [g]
    hfac::Vector{Float64}        # [g]
    scat::Matrix{Float64}        # [g_to, g_from]
    nusigf::Matrix{Float64}      # [g, iso]
    chi::Matrix{Float64}         # [g, iso]
    nusigfd::Array{Float64,3}    # [g, iso, d]
    chid::Array{Float64,3}       # [g, iso, d]
end

# h5py writes C order; HDF5.jl returns the reversed dimensions, so a numpy
# [s, g] dataset arrives here as [g, s], [s, iso, g] as [g, iso, s], and the
# numpy SCAT[s, g_to, g_from] as [g_from, g_to, s].
function load_fuel(path::AbstractString)
    h5open(path, "r") do h
        f = h["fuel"]
        pkeys = String.(read_attribute(f, "keys"))
        paxes = [read(f["axis_" * k]) for k in pkeys]
        src = Dict{String,String}()
        for a in keys(attributes(h))
            (startswith(a, "md5 ") || startswith(a, "file ")) && (src[a] = string(read_attribute(h, a)))
        end
        FuelXS(pkeys, paxes, read(f["NTOT0"]), read(f["DIFF"]), read(f["OVERV"]),
               read(f["H-FACTOR"]), read(f["SCAT"]), read(f["NUSIGF"]), read(f["CHI"]),
               read(f["NUSIGFd"]), read(f["CHId"]), read(f["LAMBDA-D"]), src)
    end
end

"""Reference (non-fuel) mixtures, one state each: a vector of MacroXS."""
function load_ref(path::AbstractString)
    h5open(path, "r") do h
        r = h["ref"]
        ntot, diff, overv, hfac = read(r["NTOT0"]), read(r["DIFF"]), read(r["OVERV"]), read(r["H-FACTOR"])
        scat = read(r["SCAT"])
        ng, nmix = size(ntot)
        [MacroXS(ntot[:, m], diff[:, m], overv[:, m], hfac[:, m],
                 permutedims(scat[:, :, m]), zeros(ng, 0), zeros(ng, 0),
                 zeros(ng, 0, 0), zeros(ng, 0, 0)) for m in 1:nmix]
    end
end

# Bracketing index and weight on one axis.  Outside the axis is an error, as
# in NCR (NCRRGR "OUTSIDE THE DOMAIN"), unless `clamp` is set -- the analogue
# of patch 0014's opt-in NCR CLAMP.
function bracket(ax::Vector{Float64}, x::Real; clamp::Bool=false)
    n = length(ax)
    if x < ax[1] || x > ax[n]
        clamp || error("XS: value $x outside axis [$(ax[1]), $(ax[n])]")
        x = min(max(x, ax[1]), ax[n])
    end
    i = searchsortedlast(ax, x)
    i == n && (i = n - 1)
    w = (x - ax[i]) / (ax[i+1] - ax[i])
    return i, w
end

"""
    interp(xs, state; clamp=false) -> MacroXS

Multilinear interpolation of the fuel table at `state` (values in the order
of `xs.keys`).
"""
function interp(xs::FuelXS, state; clamp::Bool=false)
    nk = length(xs.keys)
    br = [bracket(xs.axes[k], state[k]; clamp) for k in 1:nk]
    dims = length.(xs.axes)
    ng = size(xs.ntot, 1)
    niso = size(xs.nusigf, 2)
    nd = size(xs.nusigfd, 3)
    ntot = zeros(ng); diff = zeros(ng); overv = zeros(ng); hfac = zeros(ng)
    scat = zeros(ng, ng)
    nusigf = zeros(ng, niso); chi = zeros(ng, niso)
    nusigfd = zeros(ng, niso, nd); chid = zeros(ng, niso, nd)
    for corner in 0:(2^nk - 1)
        w = 1.0
        idx = 0
        for k in 1:nk
            bit = (corner >> (k - 1)) & 1
            i, t = br[k]
            w *= bit == 1 ? t : (1 - t)
            idx = idx * dims[k] + (i - 1 + bit)          # last key fastest
        end
        w == 0 && continue
        s = idx + 1
        @views begin
            ntot .+= w .* xs.ntot[:, s]
            diff .+= w ./ xs.diff[:, s]          # NCR interpolates 1/D (3 Sigma_tr)
            overv .+= w .* xs.overv[:, s]
            hfac .+= w .* xs.hfac[:, s]
            scat .+= w .* permutedims(xs.scat[:, :, s])  # -> [g_to, g_from]
            nusigf .+= w .* xs.nusigf[:, :, s]
            chi .+= w .* xs.chi[:, :, s]
            nusigfd .+= w .* xs.nusigfd[:, :, :, s]
            chid .+= w .* xs.chid[:, :, :, s]
        end
    end
    MacroXS(ntot, 1 ./ diff, overv, hfac, scat, nusigf, chi, nusigfd, chid)
end

"""F[g_to, g_from] = sum over isotopes of chi_iso[g_to] * nuSigma_f,iso[g_from]
(prompt + delayed, as the steady-state source)."""
function fission_matrix(m::MacroXS)
    ng = length(m.ntot)
    F = zeros(ng, ng)
    for i in axes(m.nusigf, 2), gf in 1:ng, gt in 1:ng
        F[gt, gf] += m.chi[gt, i] * m.nusigf[gf, i]
    end
    F
end

"""Per delayed group d: Fd[g_to, g_from, d] = sum_iso chid * nusigfd."""
function delayed_matrices(m::MacroXS)
    ng = length(m.ntot)
    nd = size(m.nusigfd, 3)
    Fd = zeros(ng, ng, nd)
    for d in 1:nd, i in axes(m.nusigfd, 2), gf in 1:ng, gt in 1:ng
        Fd[gt, gf, d] += m.chid[gt, i, d] * m.nusigfd[gf, i, d]
    end
    Fd
end

end # module
