# One fuel channel's thermal-hydraulics as DONJON THM: computes it -- a
# line-by-line port of THMDRV (steady), THMTRS (transient, with the RBMK
# patches 0009-0015), THMH2O, THMPH, THMROD and the UO2/Zr property
# functions, restricted to the options the Tier A decks use:
#   IFLUID 0 (water, freesteam), IPRES 0 (fixed pressure), IDFM 0 (HEM),
#   IGAP 0 (fuel-clad gap), IHGAP 1 (HGAP given), IHCONV 0 (correlations),
#   ISUBM 2 (SAHA), ICONDF = ICONDC = 0 (built-in UO2 / Zircaloy),
#   IFRCDI 0, FRACPU 0, flat radial power (FRO = 1).
# B3 verifies this port against THM: itself; the momentum / pressure model
# that replaces the fixed-pressure march is built on top of it, not in it.
#
# Units as THM: SI, heights in m, powers in W per bundle, mass flux kg/m2/s.

module Channel

using LinearAlgebra
using ..Water

export ChanGeom, ThmOpts, ChanState, chan_geom, thm_steady, thm_transient

const XS = (-0.861136, -0.339981, 0.339981, 0.861136)     # Gauss points
const WG = (0.347855, 0.652145, 0.652145, 0.347855)
const ZKELV = 273.15

# ---------------------------------------------------------------------------
# geometry and options

struct ChanGeom
    hz::Vector{Float64}     # slice heights (m)
    sass::Float64           # channel cell cross section (m2): HX*HY
    acool::Float64          # coolant flow area (m2)
    pch::Float64            # heated perimeter (m)
    hd::Float64             # hydraulic diameter (m)
    fcool::Float64          # power-density fraction to coolant (x cell/coolant volume)
    ffuel::Float64
    fnfu::Float64           # fuel rods per channel
    rad::Vector{Float64}    # NDTOT-1 radii (m), THM's RVAL
    nfd::Int
    ndtot::Int
end

"""
    chan_geom(hz, sass; pitch, nfuel, rc, rig, rgg, nfd, ndtot, fpuiss=0.974)

THM.f's CLUSTER branch (PITCH > 0) hydraulics and its gap radial mesh.
"""
function chan_geom(hz, sass; pitch, nfuel, rc, rig, rgg, nfd, ndtot, fpuiss=0.974)
    p = 3.141592654
    atothex = 3.0 * pitch^2 * sqrt(3.0) / 2.0
    atigehex = 3.0 * p * rgg^2
    acool = atothex - atigehex
    pm = 6.0 * p * rgg
    pch = pm
    rapcool = 3.0 * sass / (nfuel * acool)
    rapfuel = sass / (nfuel * p * rc^2)
    fcool = (1.0 - fpuiss) * rapcool
    ffuel = fpuiss * rapfuel
    hd = 4.0 * acool / pm
    @assert rc != rig "only the gap mesh (RC /= RIG) is ported"
    arf = 0.5 * rc^2; arci = 0.5 * rig^2; arce = 0.5 * rgg^2
    darf = arf / (nfd - 1); darc = (arce - arci) / (ndtot - nfd - 2)
    rad = zeros(ndtot - 1)
    for i in 1:nfd-1
        rad[i+1] = sqrt(2.0 * i * darf)
    end
    for i in nfd+1:ndtot-1
        rad[i] = sqrt(2.0 * (arci + (i - nfd - 1) * darc))
    end
    ChanGeom(collect(Float64, hz), sass, acool, pch, hd, fcool, ffuel, Float64(nfuel), rad, nfd, ndtot)
end

Base.@kwdef struct ThmOpts
    cflux::Float64 = 2.0e6
    poros::Float64 = 0.05
    wteff::Float64 = 5.0 / 9.0
    khgap::Float64 = 2.8e3
    ermaxt::Float64 = 1.0
    ermaxc::Float64 = 1.0e-3
    maxit1::Int = 50          # conduction
    maxit2::Int = 50          # centre-pellet
    maxitc::Int = 50          # transient flow
    frlx::Float64 = 1.0       # patch 0006 FLOW-RELAX
    cyccap::Float64 = 0.0     # patch 0005 CYCLE-OK
end

"""Per-channel state between calls (THM's MPTHM records)."""
mutable struct ChanState
    temps::Matrix{Float64}    # [NDTOT, NZ]: rod nodes 1..NDTOT-1, wall NDTOT
    dcool::Vector{Float64}    # kg/m3
    dliq::Vector{Float64}
    enth::Vector{Float64}     # J/kg
    vel::Vector{Float64}      # m/s
    pres::Vector{Float64}     # Pa
    tcomb::Vector{Float64}    # effective fuel temperature (K)
    tcool::Vector{Float64}
    tsurf::Vector{Float64}    # pellet surface
    tcent::Vector{Float64}
    xfl::Vector{Float64}
    eps::Vector{Float64}
    kwa::Vector{Int}
    pout::Float64
    tin::Float64
    ncyc::Int                 # flow limit cycles accepted (patch 0005)
    errcyc::Float64
end

# ---------------------------------------------------------------------------
# UO2 and Zircaloy (THMCDI, THMGDI, THMCCD, THMGCD; the ICONDF/ICONDC = 0,
# FRACPU = 0 branches)

function thmcdi(t2k, t1k, burn, poros)
    (min(t1k, t2k) <= 0.0) && error("THMCDI: NEGATIVE TEMPERATURE")
    hv1, hv2, hv3 = 1.3324e-08, -4.3554e-05, 5.8915e-02
    t1 = t1k - ZKELV; t2 = t2k - ZKELV
    t2t1 = t2 - t1; npas = 10; dt = t2t1 / npas; tm = (t1 + t2) / 2
    fpi = 0.124e-02 * burn
    if abs(t2t1) < 10.0
        a = tm > 1000.0 ? 2.0 : 2.58 - 0.58e-03 * tm
        fp = (1.0 - a * poros) / (1.0 - a * 0.034)
        ftp = fp * (hv3 + hv2 * tm + hv1 * tm^2) * 100.0
        return tm == 0.0 ? fp * hv3 * 100.0 : 1.0 / (1.0 / ftp + fpi / tm)
    end
    tt = t1 - dt * 0.5; cint = 0.0
    for _ in 1:npas
        tt += dt
        a = tt > 1000.0 ? 2.0 : 2.58 - 0.58e-03 * tt
        fp = (1.0 - a * poros) / (1.0 - a * 0.034)
        ftp = fp * (hv3 + hv2 * tt + hv1 * tt^2) * 100.0
        cint += tt == 0.0 ? fp * hv3 * 100.0 : 1.0 / (1.0 / ftp + fpi / tt)
    end
    cint * dt / t2t1
end

function thmgdi(t2k, t1k)
    (min(t1k, t2k) <= 0.0) && error("THMGDI: NEGATIVE TEMPERATURE")
    tm = (t1k - ZKELV + t2k - ZKELV) * 0.5
    12.0 + 1.25e-2 * tm
end

function thmccd(temp, poros)
    t2 = max(0.0, temp); t1 = t2 / 1000.0
    corr = 1.0 / (0.99672 + 1.179e-05 * t2 - 2.429e-09 * t2^2 + 1.219e-12 * t2^3)^3
    ro = (1.0 - poros) * 10970.0 * corr
    cp = 193.238 + 325.7294 * t1 - 312.0042 * t1^2 + 116.8224 * t1^3 - 9.7535 * t1^4 - 2.6441 / t1^2
    ro * cp
end

function thmgcd(temp)
    ro = 6690.0 - 0.1855 * temp
    cp = temp <= 1090.0 ? 226.7 + 0.2066 * temp - 0.6492e-04 * temp^2 :
         temp <= 1169.0 ? 6.94 * temp - 7189.0 :
         temp <= 1243.0 ? 9312.9 - 7.177 * temp : 356.0
    ro * cp
end

# ---------------------------------------------------------------------------
# THMPH: (p, h) -> (rho, T)

function thmph(pp, hh)
    ts = tsat(pp)
    v = prop_Tx(ts, 1.0); l = prop_Tx(ts, 0.0)
    rv, hv, r1, hsat = v.rho, v.h, l.rho, l.h
    dt = -0.01
    if abs(hsat - hh) / hsat <= 1.0e-5
        return r1, ts
    elseif hh <= hsat
        A = (0.2873E+03, -0.5098E+00, -0.3459E+00, 0.1910E+00, -0.2840E-01,
             0.8266E+02, 0.1141E+01, -0.2724E+01, 0.1077E+00, -0.1144E+02,
             0.9500E+01, -0.2715E+01, -0.1290E+02, 0.9148E+01, -0.8093E+01)
        t = (hh - 1270.0e3) / 420.0e3; p = (pp - 140.0e5) / 30.0e5
        h1 = A[1] + p * (A[2] + p * (A[3] + p * (A[4] + p * A[5])))
        h2 = A[6] + p * (A[7] + p * (A[8] + p * A[9]))
        h3 = A[10] + p * (A[11] + p * A[12])
        h4 = A[13] + p * A[14]
        t1 = h1 + t * (h2 + t * (h3 + t * (h4 + t * A[15]))) + ZKELV
        t1 < ZKELV && (t1 = 10.0 + ZKELV)
    elseif hh <= hv
        xth = (hh - hsat) / (hv - hsat)
        return 1.0 / (xth / rv + (1.0 - xth) / r1), ts
    else
        t1 = ts
    end
    for it in 1:31
        it > 30 && error("THMPH: CONVERGENCE FAILURE")
        a = prop_pT(pp, t1); b = prop_pT(pp, t1 + dt)
        abs((hh - a.h) / hh) < 1.0e-5 && return a.rho, t1
        t1 = t1 + (hh - a.h) * dt / (b.h - a.h)
        (hh <= hsat && t1 >= ts) && (t1 = ts)
        (hh >= hv && t1 <= ts) && (t1 = ts)
    end
end

# ---------------------------------------------------------------------------
# THMH2O (IFLUID 0, IDFM 0, IHCONV 0, ISUBM 2)

mutable struct H2OSave           # THMH2O's SAVE variables, per channel march
    dhsub::Float64
    dsat::Float64
end
H2OSave() = H2OSave(0.0, 0.0)

"""
Returns (k0, xfl, eps, tcalo, rho, rhol, rhog, tsclad, kwa, phi, hlv).
`zf`/`radcl` are used when itime = 1 (wall temperature from the rod's
surface response), `phi` when itime = 0.
"""
function thmh2o(sv::H2OSave, itime, k, k0, pinlet, mflow, hmavg, ent, hd, radcl, zf,
                phi, xfl, eps, acool, pch, dz)
    hmavg < 0.0 && error("THMH2O: NEGATIVE INPUT ENTHALPY")
    gabs = abs(mflow)
    ts = tsat(pinlet)
    L = prop_Tx(ts, 0.0); G = prop_Tx(ts, 1.0)
    rhol, hlsat, zkl, zmul, cpl = L.rho, L.h, L.k, L.mu, L.cp
    rhog, hgsat, zkg, zmug, cpg = G.rho, G.h, G.k, G.mu, G.cp
    tlx = zeros(4); rhox = zeros(4); cpx = zeros(4)
    for i in 1:4
        hl = min(ent[i], hlsat)
        _, tl_i = thmph(pinlet, hl)
        a = prop_pT(pinlet, tl_i)
        r, c = a.rho, a.cp
        if abs(ts - tl_i) < 0.1
            b = prop_Tx(ts, 0.0); r, c = b.rho, b.cp
        end
        tlx[i] = tl_i; rhox[i] = r; cpx[i] = c
    end
    tl = 0.5 * sum(WG[i] * tlx[i] for i in 1:4)
    rholav = 0.5 * sum(WG[i] * rhox[i] for i in 1:4)
    cplav = 0.5 * sum(WG[i] * cpx[i] for i in 1:4)
    tsclad = 600.0
    k0 > 0 && (tsclad = ts + sv.dsat)
    xfl0 = xfl; eps0 = eps
    lfirst = true
    hlavg = hmavg
    hlv = 0.0
    tcalo = 0.0
    if k0 > 0
        hlv = hgsat - hlsat
        f2 = 0.0; f3 = 0.0
        if hlv > 0.0 && sv.dhsub > 0.0 && hmavg >= hlsat - sv.dhsub
            f2 = (hmavg - hlsat) / hlv
            f3 = (sv.dhsub / hlv) * exp(-(hmavg - hlsat) / sv.dhsub - 1.0)
        end
        if hmavg >= hgsat
            xfl = 1.0; eps = 1.0; hlavg = 0.0
        else
            # ISUBM 2; the transient form is local (patch 0011)
            xfl = itime == 0 ? max(xfl0, (f2 + f3) / (1.0 + f3)) : max(0.0, (f2 + f3) / (1.0 + f3))
            hlavg = min(hlsat, (hmavg - xfl * hgsat) / (1.0 - xfl))
        end
        if hlavg > 0.0
            rhol, tl = thmph(pinlet, hlavg)
            a = prop_pT(pinlet, tl); zkl, zmul, cpl = a.k, a.mu, a.cp
            if hgsat > hlsat
                co = 1.13
                pr = pinlet / 1e6
                sigm = -7.2391e-6 * pr^3 + 2.8345e-4 * pr^2 - 5.1566e-3 * pr + 4.2324e-2
                vgj = 1.18 * ((sigm * 9.81 * (rhol - rhog)) / rhol^2)^0.25
                # drift floor at stagnation (patch 0015)
                f4 = co * ((xfl * rhol) + ((1.0 - xfl) * rhog)) + (rhol * rhog * vgj / max(gabs, rhol * vgj))
                eps = (xfl * rhol) / f4
            end
        else
            rhog, tcalo = thmph(pinlet, hmavg)
            a = prop_pT(pinlet, tcalo); zkg, zmug, cpg = a.k, a.mu, a.cp
        end
    end
    local rho, rel, prl, zkone, cpone
    if xfl == 0.0
        tb = ts - 0.1
        tcalo = tl < tb ? tl : tb
        a = prop_pT(pinlet, tcalo); zkone, zmuone, cpone = a.k, a.mu, a.cp
        rho = rholav
        rel = gabs * hd / zmuone
        prl = zmuone * cpone / zkone
    elseif hmavg < hgsat
        rel = gabs * (1.0 - xfl) * hd / zmul
        prl = zmul * cpl / zkl
        tcalo = eps * ts + (1.0 - eps) * tl
        zkone = zkl; cpone = cpl
        rho = eps * rhog + (1.0 - eps) * rhol
    else
        rho = rhog
        rel = gabs * hd / zmug
        prl = zmug * cpg / zkg
        # THMH2O leaves ZKONE undefined here (stale from an earlier call) and
        # uses it if the single-phase branch below is taken; zkg is our choice
        zkone = zkg; cpone = cpg
    end
    # IHCONV 0: Dittus-Boelter / Chen / Groeneveld-like, iterated on TSCLAD
    kwa = 99
    for iter in 1:501
        iter > 500 && error("THMH2O: HCONV FAILURE IN SLICE $k")
        ha = 0.023 * (zkone / hd) * rel^0.8 * prl^0.4
        f = 1.0; s = 1.0; hb = 0.0
        if xfl == xfl0 || tsclad <= ts || kwa == 0
            kwa = 0; hb = 0.0; k0 = 0; xfl = xfl0; eps = eps0
        elseif hmavg < hgsat
            kwa = hmavg < hlsat ? 1 : 2
            xm = (xfl / (1.0 - xfl))^0.9 * (rhol / rhog)^0.5 * (zmug / zmul)^0.1
            f = xm <= 0.100207 ? 1.0 : 2.35 * (0.213 + xm)^0.736
            re = rel * f^1.25
            s = 1.0 / (1.0 + 2.53e-6 * re^1.17)
            pr = pinlet / 1e6
            sigm = -7.2391e-6 * pr^3 + 2.8345e-4 * pr^2 - 5.1566e-3 * pr + 4.2324e-2
            ha = 0.023 * (zkl / hd) * rel^0.8 * prl^0.4
            dtsat = tsclad - ts
            pw = psat(tsclad)
            dp = pw - pinlet
            hlv = hgsat - hlsat
            hb = 0.00122 * zkl^0.79 * cpl^0.45 * rhol^0.49 / (zmul^0.29 * sigm^0.5 * hlv^0.24 * rhog^0.24) *
                 dtsat^0.24 * dp^0.75
        else
            kwa = 3
            rhow = prop_pT(pinlet, tsclad).rho
            ha = 0.0061 * (zkg / hd) * rel^0.904 * prl^0.684 * (rhow / rho)^0.564
            hb = 0.0
        end
        hconv = f * ha + s * hb
        if !(hconv > 0.0)
            itime == 0 && error("THMH2O: DRY OUT REACHED IN SLICE $k")
            ha = 0.0; hb = 0.0                          # patch 0009: uncooled slice
        end
        if itime == 0
            twal = (phi + s * hb * ts + f * ha * tcalo) / (s * hb + f * ha)
        else
            znum = zf[1] + radcl * s * hb * ts + radcl * f * ha * tcalo
            zden = zf[2] + radcl * s * hb + radcl * f * ha
            twal = max(273.15, znum / zden)
            phi = max(0.0, (zf[1] - twal * zf[2]) / radcl)
        end
        if abs(tsclad - twal) > 1.0e-5 * tsclad
            tsclad = twal
        else
            break
        end
    end
    if k0 == 0 && lfirst                                  # Saha-Zuber onset (ISUBM 2)
        pe = gabs * cpl * hd / zkl
        dtsub = pe <= 70000.0 ? phi * hd / (455.0 * zkl) : 154.0 * phi / (gabs * cpl)
        tcalo >= ts - dtsub && (k0 = k)
        sv.dsat = tsclad - tcalo - dtsub
        sv.dhsub = cpl * dtsub
    end
    # the caller's RHOL is THMH2O's RHOLAV dummy (the Gauss-averaged liquid
    # density), not the local saturated / re-evaluated RHOL used above
    (; k0, xfl, eps, tcalo, rho, rhol=rholav, rhog, tsclad, kwa, phi, hlv)
end

# ---------------------------------------------------------------------------
# THMROD: rod conduction with a gap (IGAP 0), NDTOT here = THM's NDTOT-1

function thmrod(g::ChanGeom, o::ThmOpts, dtinv, xx0, xx1, qfuel, tsurf, burn; maxit1=o.maxit1, maxit2=o.maxit2)
    nfd = g.nfd; nd = g.ndtot - 1; rad = g.rad
    dar = zeros(nd)
    arci = 0.5 * rad[nfd+1]^2; arce = 0.5 * rad[nd]^2
    for i in 1:nfd-1
        dar[i] = 0.5 * (rad[i+1]^2 - rad[i]^2)
    end
    for i in nfd+2:nd
        dar[i] = 0.5 * (rad[i]^2 - rad[i-1]^2)
    end
    condxa = zeros(nd)
    for i in 1:nd
        if i <= nfd - 1
            condxa[i] = thmccd(xx0[i], o.poros) * dtinv * xx0[i] * dar[i]
        elseif i >= nfd + 2
            condxa[i] = thmgcd(xx0[i]) * dtinv * xx0[i] * dar[i]
        end
    end
    zk = zeros(nd)
    x2 = zeros(nd); x3 = zeros(nd); zf = zeros(2)
    hgap = o.khgap
    itert = 0
    while true
        itert += 1
        itert > maxit1 && error("THMROD: CONVERGENCE FAILURE(1)")
        fill!(zk, 0.0)
        for i in 1:nfd-1
            zk[i] = thmcdi(xx1[i], xx1[i+1], burn, o.poros)
        end
        for i in nfd+1:nd-1
            zk[i] = thmgdi(xx1[i], xx1[i+1])
        end
        zk[nd] = thmgdi(xx1[nd], tsurf)
        T = zeros(nd, nd); b1 = zeros(nd); b2 = zeros(nd)
        c1 = 0.0; c3 = 0.0
        for i in 1:nd
            b1[i] = condxa[i]
            if i <= nfd - 2
                ari = 0.5 * rad[i+1]^2
                c3 = 4.0 * ari * zk[i] / (dar[i] + dar[i+1])
                b1[i] += qfuel * dar[i]
            elseif i == nfd - 1
                ari = 0.5 * rad[i+1]^2
                c3 = 4.0 * ari * zk[i] / dar[i]
                b1[i] += qfuel * dar[i]
            elseif i == nfd
                ravg = 2.0 * rad[nfd] * rad[nfd+1] / (rad[nfd] + rad[nfd+1])
                c3 = ravg * hgap
            elseif i == nfd + 1
                c3 = 4.0 * arci * zk[i] / dar[i+1]
            elseif i <= nd - 1
                ari = 0.5 * rad[i]^2
                c3 = 4.0 * ari * zk[i] / (dar[i] + dar[i+1])
            else
                c3 = 4.0 * arce * zk[i] / dar[i]
                b2[i] += c3
            end
            c2 = c1 + c3
            i > 1 && (T[i, i-1] = -c1)
            if i <= nfd - 1
                T[i, i] = thmccd(xx1[i], o.poros) * dtinv * dar[i]
            elseif i >= nfd + 2
                T[i, i] = thmgcd(xx1[i]) * dtinv * dar[i]
            end
            T[i, i] += c2
            if i < nd
                T[i, i+1] = -c3
                c1 = c3
            end
        end
        zwork = c3
        F = lu(T)
        x2 .= F \ b1; x3 .= F \ b2
        err = 0.0
        for i in 1:nd
            tnew = x2[i] + tsurf * x3[i]
            err = max(err, abs(xx1[i] - tnew))
            xx1[i] = itert <= 20 ? tnew : 0.5 * (tnew + xx1[i])
        end
        zf[1] = zwork * x2[nd]
        zf[2] = zwork * (1.0 - x3[nd])
        (err < o.ermaxt && itert != 1) && break
    end
    tc = 0.5 * (xx1[1] + xx1[2])
    for iterc in 1:maxit2+1
        iterc > maxit2 && error("THMROD: CONVERGENCE FAILURE(2)")
        tcold = tc
        cc1 = thmcdi(xx1[1], tc, burn, o.poros)
        cc2 = thmcdi(tc, xx1[2], burn, o.poros)
        tc = (cc1 * xx1[1] + cc2 * xx1[2]) / (cc1 + cc2)
        itert > 20 && (tc = 0.5 * (tc + tcold))
        (abs(tc - tcold) < o.ermaxt && iterc != 1) && break
    end
    tc1 = 2.0 * xx1[1] - tc
    tc1, x2, x3, zf
end

# ---------------------------------------------------------------------------
# THMDRV: steady state (IPRES 0, IDFM 0)

"""
    thm_steady(g, o, pow, burn, speed, tinlet, pout; tcomb0)

`pow` W per slice (0 = no fuel), `burn` MWd/t per slice, `speed` inlet
velocity m/s, `tcomb0` the initial guess THM: takes from the FMAP's T-FUEL.
"""
function thm_steady(g::ChanGeom, o::ThmOpts, pow, burn, speed, tinlet, pout; tcomb0=fill(900.0, length(pow)))
    nz = length(pow); nd = g.ndtot
    pinlet = pout
    ts = tsat(pinlet)
    tinlet > ts && error("THMDRV: INLET TEMPERATURE GREATER THAN SATURATION")
    a = prop_pT(pinlet, tinlet); rhoin, hinlet = a.rho, a.h
    mflow = speed * rhoin
    hmsup = hinlet
    st = ChanState(zeros(nd, nz), fill(rhoin, nz), fill(rhoin, nz), fill(hinlet, nz), fill(mflow / rhoin, nz),
                   fill(pinlet, nz), zeros(nz), fill(tinlet, nz), zeros(nz), zeros(nz), zeros(nz), zeros(nz),
                   zeros(Int, nz), pout, tinlet, 0, 0.0)
    sv = H2OSave(); k0 = 0
    for k in 1:nz
        pow[k] == 0.0 && continue
        dv = g.sass * g.hz[k]
        powlin = (pow[k] / dv) * g.sass / g.fnfu
        qfuel = pow[k] * g.ffuel / dv
        qcool = pow[k] * g.fcool / dv
        tre = fill(tcomb0[k], nd)
        phi2 = 0.5 * qfuel * g.rad[g.nfd]^2 / g.rad[nd-1]
        phi2 > o.cflux && error("THMDRV: HEAT FLUX $phi2 > CRITICAL $(o.cflux)")
        delth1 = (g.pch / g.acool * phi2 + qcool) * g.hz[k] / mflow
        ent = ntuple(i -> hmsup + (1.0 + XS[i]) / 2.0 * delth1, 4)
        hmsup += delth1
        if k > 1
            st.xfl[k] = st.xfl[k-1]; st.eps[k] = st.eps[k-1]
        end
        r = thmh2o(sv, 0, k, k0, pinlet, mflow, hmsup, ent, g.hd, g.rad[nd-1], (0.0, 0.0),
                   phi2, st.xfl[k], st.eps[k], g.acool, g.pch, g.hz[k])
        k0 = r.k0; st.xfl[k] = r.xfl; st.eps[k] = r.eps; st.kwa[k] = r.kwa
        tre[nd] = r.tsclad
        x = view(tre, 1:nd-1)
        tc1, x2, x3, _ = thmrod(g, o, 0.0, x, x, qfuel, tre[nd], burn[k])
        for k1 in 1:nd-1
            tre[k1] = x2[k1] + tre[nd] * x3[k1]
        end
        st.tcomb[k] = (1.0 - o.wteff) * tc1 + o.wteff * tre[g.nfd]
        st.tcent[k] = tc1
        st.tsurf[k] = tre[g.nfd]
        st.tcool[k] = r.tcalo
        st.dcool[k] = r.rho
        st.dliq[k] = r.rhol
        st.enth[k] = hmsup
        st.temps[:, k] .= tre
        st.pres[k] = pinlet
        st.vel[k] = mflow / st.dcool[k]
    end
    st
end

# ---------------------------------------------------------------------------
# THMTRS: one transient step (IPRES 0, IDFM 0), patches 0005/0006/0009-0015

"""
    thm_transient(g, o, s0, pow, burn, speed, tinlet, pout, dt) -> s1

`s0` the state at the start of the step (THM's MPTHMI), `pow` the new
power (W per slice).  `speed` is the channel's inlet velocity (SPDIN).
"""
function thm_transient(g::ChanGeom, o::ThmOpts, s0::ChanState, pow, burn, speed, tinlet, pout, dt)
    nz = length(pow); nd = g.ndtot
    dtinv = 1.0 / dt
    ts = tsat(pout)
    tinlet > ts && error("THMTRS: INLET TEMPERATURE GREATER THAN SATURATION")
    a = prop_pT(s0.pout, s0.tin); rhoin0, hinle0 = a.rho, a.h
    a = prop_pT(pout, tinlet); rhoinl, hinlet = a.rho, a.h
    mflxin = speed * rhoinl
    dv = g.sass .* g.hz
    powlin = (pow ./ dv) .* g.sass ./ g.fnfu
    qfuel = pow .* g.ffuel ./ dv
    qcool = pow .* g.fcool ./ dv
    dcool0 = s0.dcool; enth0 = s0.enth; temps0 = s0.temps
    dcool = copy(dcool0); vel = copy(s0.vel); pres = copy(s0.pres); enth = copy(enth0)
    dliq = copy(s0.dliq); temps = copy(temps0)
    resm = dcool0 .* vel; resp = copy(pres); resh = copy(enth)
    xfl = zeros(nz); eps = zeros(nz); mflxt = zeros(nz); kwa = zeros(Int, nz)
    dgcool = zeros(nz); phi = zeros(nz)
    tcomb = zeros(nz); tcool = zeros(nz); tsurf = zeros(nz); tcent = zeros(nz)
    kmin = findfirst(!=(0.0), pow)
    kmin === nothing && (kmin = 1)
    wrlx = o.frlx; errprv = 1.0e30
    ncyc = 0; errcyc = 0.0
    err = 0.0
    itercr = 0
    while true
        itercr += 1
        dsave = copy(dcool)
        if itercr > o.maxitc
            if o.cyccap > 0.0 && err < o.cyccap
                ncyc += 1; errcyc = max(errcyc, err)
                break
            end
            error("THMTRS: CONVERGENCE FAILURE IN FLOW CALCULATION")
        end
        sv = H2OSave(); k0 = 0
        for k in kmin:nz
            pow[k] == 0.0 && continue
            tre10 = temps0[1:nd-1, k]
            tre11 = temps[1:nd-1, k]
            tsclad = temps[nd, k]
            tc1, x2, x3, zf = thmrod(g, o, dtinv, tre10, tre11, qfuel[k], tsclad, burn[k])
            phi[k] = (zf[1] - tsclad * zf[2]) / g.rad[nd-1]
            p1 = 0.5 * (dcool0[k] - dcool[k]) * dtinv * g.hz[k]
            if k == kmin
                p1 += 0.5 * (rhoin0 - rhoinl) * dtinv * g.hz[k]
                mflxt[k] = mflxin + p1
            else
                p1 += 0.5 * (dcool0[k-1] - dcool[k-1]) * dtinv * g.hz[k]
                mflxt[k] = mflxt[k-1] + p1
            end
            gtop = mflxt[k]
            gbot = k == kmin ? mflxin : mflxt[k-1]
            # donor-cell energy faces (patch 0012)
            param1 = 0.5 * dcool[k] * dtinv * g.hz[k]
            (gtop >= 0.0 || k == nz) && (param1 += gtop)
            param2 = 0.5 * dcool0[k] * enth0[k] * dtinv * g.hz[k]
            (gtop < 0.0 && k < nz) && (param2 -= gtop * enth[k+1])
            param3 = (qcool[k] + phi[k] * g.pch / g.acool) * g.hz[k]
            local hminf
            if k == kmin
                param2 += 0.5 * (rhoin0 * hinle0 - rhoinl * hinlet) * dtinv * g.hz[k]
                param2 += mflxin * hinlet
                hminf = hinlet
            else
                param2 += 0.5 * (dcool0[k-1] * enth0[k-1] - dcool[k-1] * enth[k-1]) * dtinv * g.hz[k]
                if gbot >= 0.0
                    param2 += gbot * enth[k-1]
                    hminf = enth[k-1]
                else
                    param1 -= gbot
                    hminf = enth[k-1]
                    (gtop < 0.0 && k < nz) && (hminf = enth[k+1])
                end
            end
            enth[k] = (param2 + param3) / param1
            delth = enth[k] - hminf
            ent = ntuple(i -> hminf + (1.0 + XS[i]) / 2.0 * delth, 4)
            if k > 1
                xfl[k] = xfl[k-1]; eps[k] = eps[k-1]
            end
            r = thmh2o(sv, 1, k, k0, pres[k], mflxt[k], enth[k], ent, g.hd, g.rad[nd-1], zf,
                       phi[k], xfl[k], eps[k], g.acool, g.pch, g.hz[k])
            k0 = r.k0; xfl[k] = r.xfl; eps[k] = r.eps; kwa[k] = r.kwa; phi[k] = r.phi
            dcool[k] = r.rho; dliq[k] = r.rhol; dgcool[k] = r.rhog
            o.frlx < 1.0 && (dcool[k] = wrlx * dcool[k] + (1.0 - wrlx) * dsave[k])
            twal = r.tsclad
            for l in 1:nd-1
                temps[l, k] = x2[l] + twal * x3[l]
            end
            temps[nd, k] = twal
            tcomb[k] = (1.0 - o.wteff) * tc1 + o.wteff * temps[g.nfd, k]
            tcool[k] = r.tcalo
            tcent[k] = tc1
            tsurf[k] = temps[g.nfd, k]
        end
        for k in 1:nz
            if eps[k] > 0.0
                rgsat = prop_Tx(tsat(pres[k]), 1.0).rho
                dcool[k] = dliq[k] * (1.0 - eps[k]) + eps[k] * rgsat
            else
                dcool[k] = dliq[k]
            end
            o.frlx < 1.0 && (dcool[k] = wrlx * dcool[k] + (1.0 - wrlx) * dsave[k])
            vel[k] = mflxt[k] / dcool[k]
        end
        errg = 0.0; errp = 0.0; errh = 0.0
        for k in 1:nz
            pow[k] == 0.0 && continue
            errg = max(errg, abs(mflxt[k] - resm[k]) / max(abs(mflxt[k]), abs(mflxin)))
            errp = max(errp, abs(pres[k] - resp[k]) / pres[k])
            errh = max(errh, abs(enth[k] - resh[k]) / enth[k])
            resm[k] = mflxt[k]; resp[k] = pres[k]; resh[k] = enth[k]
        end
        err = max(errg, errp, errh)
        if o.frlx < 1.0 && itercr > 1 && err >= errprv          # patch 0013
            wrlx = max(0.5 * wrlx, o.frlx / 32.0)
        end
        errprv = err
        pinlet = pres[kmin]
        a = prop_pT(pinlet, tinlet); rhoinl, hinlet = a.rho, a.h
        (err < o.ermaxc && itercr > 1) && break
    end
    ChanState(temps, dcool, dliq, enth, vel, pres, tcomb, tcool, tsurf, tcent, xfl, eps, kwa,
              pout, tinlet, ncyc, errcyc)
end

end # module
