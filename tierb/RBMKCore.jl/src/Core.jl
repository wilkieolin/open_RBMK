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

export Deck, Rod, read_deck, element_xs, rod_box

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
    Deck(nx, ny, nz, mx, my, mz, mix, burn, rods, fs)
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
    element_xs(deck, fuel, ref; fuelstate=deck.fuelstate)

Per-element macroscopic data for every non-void element, as NCR + MACINI +
NEWMAC build them.  Returns named arrays indexed by element:
ntot[e,g], invd[e,g] (1/D), scat[e,gt,gf], fiss[e,gt,gf], hfac[e,g].
"""
function element_xs(d::Deck, fuel::FuelXS, ref::Vector{MacroXS}; fuelstate=d.fuelstate)
    ne = length(d.mix); ng = 2
    ntot = zeros(ne, ng); invd = zeros(ne, ng); hfac = zeros(ne, ng)
    scat = zeros(ne, ng, ng); fiss = zeros(ne, ng, ng)
    ifuel = 0
    st(b) = [k == "burnup" ? b : fuelstate[k] for k in fuel.keys]
    put!(e, m::MacroXS, F) = begin
        ntot[e, :] .= m.ntot; invd[e, :] .= 1 ./ m.diff; hfac[e, :] .= m.hfac
        scat[e, :, :] .= m.scat; fiss[e, :, :] .= F
    end
    refF = [fission_matrix(m) for m in ref]
    for e in 1:ne
        mx = d.mix[e]
        mx == 0 && continue
        if mx == 8
            ifuel += 1
            m = interp(fuel, st(d.burnup[ifuel]))
            put!(e, m, fission_matrix(m))
        else
            put!(e, ref[mx], refF[mx])
        end
    end
    # rod devices
    nx, ny = d.nx, d.ny
    zmin, zmax = d.meshz[1], d.meshz[end]
    for r in d.rods
        r.level < 1e-4 && continue
        x1, x2, y1, y2, z1, z2 = rod_box(r, zmin, zmax)
        m1, m2 = ref[r.dmix[1]], ref[r.dmix[2]]
        dS = m1.ntot .- m2.ntot; dI = 1 ./ m1.diff .- 1 ./ m2.diff
        dH = m1.hfac .- m2.hfac; dSc = m1.scat .- m2.scat
        for k in 1:d.nz, j in 1:ny, i in 1:nx
            fx = overlap(x1, x2, d.meshx[i], d.meshx[i+1]); fx == 0 && continue
            fy = overlap(y1, y2, d.meshy[j], d.meshy[j+1]); fy == 0 && continue
            fz = overlap(z1, z2, d.meshz[k], d.meshz[k+1]); fz == 0 && continue
            e = i + (j - 1) * nx + (k - 1) * nx * ny
            d.mix[e] == 0 && continue
            vf = fx * fy * fz
            vf > 1e-4 || continue
            ntot[e, :] .+= vf .* dS
            invd[e, :] .+= vf .* dI
            for g in 1:ng                       # NEWMXS: only where nonzero
                hfac[e, g] != 0 && (hfac[e, g] += vf * dH[g])
            end
            scat[e, :, :] .+= vf .* dSc
        end
    end
    (; ntot, invd, scat, fiss, hfac)
end

end # module
