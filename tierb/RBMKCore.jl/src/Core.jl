# The Unit 4 core as a generated DONJON deck describes it (TIER_B_WORKPLAN.md,
# B0/B1).  The engine reads the deck itself -- the single source DONJON reads
# -- rather than a sidecar from the generator, so the two cannot drift.
#
#   GEO:     CAR3D nx ny nz, per-plane mixture maps (PLANE k [SAME j]),
#            MESHX/MESHY/MESHZ in cm.  Mixtures: 1 CPS water, 2 absorber,
#            3 displacer, 4-7 reflector rings, 8 fuel, 0 void.
#   RESINI:  INST-BVAL BUND -- burnup per bundle, bundle-major (IB outer,
#            ICH inner), bundle 1 at the bottom (RESPAR.f:518-531,
#            RESPFM.f:65-72): exactly the element-scan order of the fuel
#            elements (x fastest, then y, then z).
#   DEVINI:  ROD blocks -- AXIS Z, FROM H+/H-, LEVEL, one MAXPOS box, DMIX.
#
# Rod devices follow NEWMAC (NEWMVF.f/NEWMXS.f): each element a rod box
# overlaps gets Sigma += VF*(Sigma_DMIX1 - Sigma_DMIX2) for every additive
# record and 1/D += VF*(1/D_1 - 1/D_2), VF the overlap volume fraction.  The
# box is placed as DEVGET.f/MOVCHK.f do for a single-part MOVE rod along Z:
#   FROM H+:  bottom = z_max - LEVEL*(z_max - z1), top = bottom + (z2 - z1)
#   FROM H-:  top = z_min + LEVEL*(z2 - z_min),    bottom = top - (z2 - z1)
# clamped to the mesh; a rod with LEVEL < 1e-4 is skipped (NEWMDV.f:92).

module CoreModel

using ..XS

export Deck, Rod, read_deck, element_xs, element_base, rod_box, rod_boxes, apply_rods

struct Rod
    name::String
    from::Int                  # +1 = H+ (top), -1 = H- (bottom)
    level::Float64
    box::NTuple{6,Float64}     # MAXPOS x1 x2 y1 y2 z1 z2
    dmix::Tuple{Int,Int}       # (inserted mixture, replaced mixture)
end

struct Deck
    nx::Int; ny::Int; nz::Int
    meshx::Vector{Float64}; meshy::Vector{Float64}; meshz::Vector{Float64}
    mix::Vector{Int}           # element mixture, x fastest
    burnup::Vector{Float64}    # per fuel element, scan order
    rods::Vector{Rod}
    groups::Dict{Int,Vector{Int}}     # DEVINI CREATE ROD-GR: group -> rod ids
    fuelstate::Dict{String,Float64}   # SET values on the fuel NCR (static decks)
end

function numbers_until(lines, i, stop)
    v = Float64[]
    while i <= length(lines)
        l = lines[i]
        occursin(stop, l) && break
        for t in split(l)
            x = tryparse(Float64, t)
            x === nothing && @goto done
            push!(v, x)
        end
        i += 1
    end
    @label done
    v, i
end

function read_deck(path::AbstractString)
    L = [l for l in readlines(path) if !startswith(l, "*")]
    # --- GEO: the first CAR3D is the reactor geometry
    i = findfirst(l -> occursin("GEO: :: CAR3D", l), L)
    nx, ny, nz = parse.(Int, split(split(L[i], "CAR3D")[2])[1:3])
    planes = Dict{Int,Vector{Int}}()
    order = Int[]
    j = i
    while !startswith(strip(L[j]), "MESHX")
        s = strip(L[j])
        if startswith(s, "PLANE")
            t = split(s)
            k = parse(Int, t[2])
            push!(order, k)
            if length(t) >= 4 && t[3] == "SAME"
                planes[k] = planes[parse(Int, t[4])]
                j += 1
            else
                v = Int[]
                j += 1
                while length(v) < nx * ny
                    append!(v, parse.(Int, split(L[j])))
                    j += 1
                end
                planes[k] = v
            end
        else
            j += 1
        end
    end
    mix = vcat([planes[k] for k in 1:nz]...)
    function mesh_after(key, j)
        j = findnext(l -> strip(l) == key, L, j)
        v = Float64[]; j += 1
        while true
            x = tryparse.(Float64, split(L[j]))
            (isempty(x) || any(isnothing, x)) && break
            append!(v, x); j += 1
        end
        v, j
    end
    mx, j = mesh_after("MESHX", j)
    my, j = mesh_after("MESHY", j)
    mz, j = mesh_after("MESHZ", j)
    # --- burnups
    b = findfirst(l -> occursin("INST-BVAL BUND", l), L)
    burn = Float64[]
    if b !== nothing
        k = b + 1
        while true
            x = tryparse.(Float64, split(L[k]))
            (isempty(x) || any(isnothing, x)) && break
            append!(burn, x); k += 1
        end
    end
    # --- rods
    rods = Rod[]
    k = 1
    while (k = findnext(l -> startswith(strip(l), "ROD ") && length(split(l)) == 2, L, k)) !== nothing
        name = ""; from = 0; level = -1.0; box = (0.0,0.0,0.0,0.0,0.0,0.0); dmix = (0, 0)
        k += 1
        while strip(L[k]) != "ENDROD"
            t = split(L[k])
            if t[1] == "ROD-NAME"; name = t[2]
            elseif t[1] == "AXIS"; t[2] == "Z" || error("rod $name: only AXIS Z")
                from = t[4] == "H+" ? 1 : -1
            elseif t[1] == "LEVEL"; level = parse(Float64, t[2])
            elseif t[1] == "MAXPOS"; box = Tuple(parse.(Float64, t[2:7]))
            elseif t[1] == "DMIX"; dmix = (parse(Int, t[2]), parse(Int, t[3]))
            end
            k += 1
        end
        push!(rods, Rod(name, from, level, box, dmix))
    end
    # --- rod groups
    groups = Dict{Int,Vector{Int}}()
    gi = findfirst(l -> occursin("CREATE ROD-GR", l), L)
    if gi !== nothing
        k = gi + 1
        cur = 0
        while strip(L[k]) != ";"
            t = split(L[k])
            if !isempty(t) && t[1] == "GROUP-ID"
                cur = parse(Int, t[2]); groups[cur] = Int[]
            else
                for w in t
                    x = tryparse(Int, w); x === nothing || push!(groups[cur], x)
                end
            end
            k += 1
        end
    end
    # --- static fuel state (SET on the fuel NCR)
    fs = Dict{String,Float64}()
    f = findfirst(l -> occursin("MACFUEL := NCR:", l), L)
    if f !== nothing
        e = findnext(l -> strip(l) == ";", L, f)
        txt = join(L[f:e], " ")
        for m in eachmatch(r"SET '([^']+)' ([0-9.Ee+-]+)", txt)
            fs[m.captures[1]] = parse(Float64, m.captures[2])
        end
    end
    Deck(nx, ny, nz, mx, my, mz, mix, burn, rods, groups, fs)
end

"""Current box of a rod (DEVGET/MOVCHK, single-part MOVE along Z)."""
function rod_box(r::Rod, zmin::Float64, zmax::Float64)
    x1, x2, y1, y2, z1, z2 = r.box
    len = z2 - z1
    if r.from == 1
        bot = clamp(zmax - r.level * (zmax - z1), zmin, zmax)
        return (x1, x2, y1, y2, bot, bot + len)
    else
        top = clamp(zmin + r.level * (z2 - zmin), zmin, zmax)
        return (x1, x2, y1, y2, top - len, top)
    end
end

overlap(a1, a2, b1, b2) = max(0.0, min(a2, b2) - max(a1, b1)) / (b2 - b1)

"""
    element_base(deck, fuel, ref; tf=nothing, dca=nothing, tg=nothing)

Per-element macroscopic data before rod devices, as NCR + MACINI build it.
Fuel states come from the deck's static SETs, or per fuel element (scan
order) from `tf`/`dca`/`tg` vectors when given (the FMAP fields THM writes).
Returns a NamedTuple of arrays indexed by element: ntot[e,g], invd[e,g],
hfac[e,g], overv[e,g], scat[e,gt,gf], fiss[e,gt,gf] (prompt + delayed),
and for fuel elements the delayed data per isotope:
nud[e,g_from,d,iso], chid[e,g_to,d,iso].
"""
function element_base(d::Deck, fuel::FuelXS, ref::Vector{MacroXS}; tf=nothing, dca=nothing, tg=nothing,
                      clamp::Bool=false)
    ne = length(d.mix); ng = 2
    niso = size(fuel.nusigf, 2); nd = size(fuel.nusigfd, 3)
    ntot = zeros(ne, ng); invd = zeros(ne, ng); hfac = zeros(ne, ng); overv = zeros(ne, ng)
    scat = zeros(ne, ng, ng); fiss = zeros(ne, ng, ng)
    nud = zeros(ne, ng, nd, niso); chid = zeros(ne, ng, nd, niso)
    ifuel = 0
    function st(b, f)
        map(fuel.keys) do k
            k == "burnup" && return b
            k == "TF" && tf !== nothing && return tf[f]
            k == "DCA" && dca !== nothing && return dca[f]
            k == "TG" && tg !== nothing && return tg[f]
            d.fuelstate[k]
        end
    end
    refF = [fission_matrix(m) for m in ref]
    for e in 1:ne
        mx = d.mix[e]
        mx == 0 && continue
        if mx == 8
            ifuel += 1
            m = interp(fuel, st(d.burnup[ifuel], ifuel); clamp)   # NCR CLAMP (patch 0014)
            F = fission_matrix(m)
            nud[e, :, :, :] .= permutedims(m.nusigfd, (1, 3, 2))   # [g, d, iso]
            chid[e, :, :, :] .= permutedims(m.chid, (1, 3, 2))
        else
            m = ref[mx]; F = refF[mx]
        end
        ntot[e, :] .= m.ntot; invd[e, :] .= 1 ./ m.diff; hfac[e, :] .= m.hfac
        overv[e, :] .= m.overv; scat[e, :, :] .= m.scat; fiss[e, :, :] .= F
    end
    (; ntot, invd, hfac, overv, scat, fiss, nud, chid)
end

"""
    rod_boxes(deck; shift=Dict()) -> Vector of current boxes (or nothing)

Each rod's current box (DEVGET/MOVCHK), translated down by `shift[id]` cm
(MOVGRP: a MOVE rod at SPEED v moves its reference position by v*dt; the
reference position is clamped to the mesh).
"""
function rod_boxes(d::Deck; shift=Dict{Int,Float64}())
    zmin, zmax = d.meshz[1], d.meshz[end]
    map(enumerate(d.rods)) do (id, r)
        r.level < 1e-4 && return nothing
        b = rod_box(r, zmin, zmax)
        s = get(shift, id, 0.0)
        s == 0 && return b
        len = b[6] - b[5]
        if r.from == 1                          # reference = bottom
            bot = clamp(b[5] - s, zmin, zmax)
            return (b[1], b[2], b[3], b[4], bot, bot + len)
        else                                    # reference = top
            top = clamp(b[6] - s, zmin, zmax)
            return (b[1], b[2], b[3], b[4], top - len, top)
        end
    end
end

"""
    apply_rods(base, deck, ref, boxes) -> NamedTuple (copies of the arrays
    rods change: ntot, invd, hfac, scat), as NEWMAC does.
"""
function apply_rods(base, d::Deck, ref::Vector{MacroXS}, boxes)
    ntot = copy(base.ntot); invd = copy(base.invd); hfac = copy(base.hfac); scat = copy(base.scat)
    nx, ny, ng = d.nx, d.ny, 2
    for (r, bx) in zip(d.rods, boxes)
        bx === nothing && continue
        x1, x2, y1, y2, z1, z2 = bx
        m1, m2 = ref[r.dmix[1]], ref[r.dmix[2]]
        dS = m1.ntot .- m2.ntot; dI = 1 ./ m1.diff .- 1 ./ m2.diff
        dH = m1.hfac .- m2.hfac; dSc = m1.scat .- m2.scat
        irange = [i for i in 1:nx if d.meshx[i+1] > x1 && d.meshx[i] < x2]
        jrange = [j for j in 1:ny if d.meshy[j+1] > y1 && d.meshy[j] < y2]
        for k in 1:d.nz, j in jrange, i in irange
            fz = overlap(z1, z2, d.meshz[k], d.meshz[k+1]); fz == 0 && continue
            vf = overlap(x1, x2, d.meshx[i], d.meshx[i+1]) *
                 overlap(y1, y2, d.meshy[j], d.meshy[j+1]) * fz
            e = i + (j - 1) * nx + (k - 1) * nx * ny
            (d.mix[e] == 0 || vf <= 1e-4) && continue
            ntot[e, :] .+= vf .* dS
            invd[e, :] .+= vf .* dI
            for g in 1:ng                       # NEWMXS: only where nonzero
                hfac[e, g] != 0 && (hfac[e, g] += vf * dH[g])
            end
            scat[e, :, :] .+= vf .* dSc
        end
    end
    (; ntot, invd, hfac, scat)
end

"""Per-element data with rods at their deck positions (static decks)."""
function element_xs(d::Deck, fuel::FuelXS, ref::Vector{MacroXS}; kw...)
    base = element_base(d, fuel, ref; kw...)
    r = apply_rods(base, d, ref, rod_boxes(d))
    (; ntot=r.ntot, invd=r.invd, scat=r.scat, fiss=base.fiss, hfac=r.hfac)
end

end # module
