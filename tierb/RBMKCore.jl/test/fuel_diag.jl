# Fuel and cladding state against failure criteria (PROGRESS (47)), per step of a coupled run.
#   fuel enthalpy  H(T) = int_298^T cp dT with THM's own UO2 cp (Channel.thmccd: the model's
#                  temperatures and this enthalpy are consistent), pellet-averaged over the
#                  equal-area rings, per axial cell (bundle-average; the OpenMC pin peaking
#                  1.02-1.05 is NOT applied).  All thresholds are peak radial-average enthalpy:
#     120 cal/g  dispersal of irradiated fuel by PCMI failure, burnup > 40 MWd/kgU, not VVER-type
#                Zr-Nb ([NEA10] Ch. 7; a lower bound only: Unit 4 averaged ~10 MWd/kgU)
#     160        Zr-1%Nb cladding ballooning failure, lower boundary, fresh and irradiated, pulse
#                widths to 950 ms, no pulse-width effect ([HOZ] Sec. 2.3, IGR/BIGR/GIDRA)
#     193        Vitanza/KAERI correlations at 10 MWd/kgU, 10 um oxide ([HOZ] eqs 4, 5)
#     220        "begin to disintegrate" (INSAG-7 p. 67, NSRR fresh fuel)
#     240, 270   fresh-rod fragmentation, 1005-1130 J/g; IGR VVER: clad failure = fragmentation
#                at 1130 ([NEA10] Table 12)
#     285, 325   molten-fuel expulsion, violent FCI and pressure pulses, 1190-1360 J/g ([NEA10]
#                Sec. 7.1.2; INSAG-7: 285 "rupture", 320 "explode and disperse")
#   cladding       max over the cladding nodes; 700 C (operational mechanical integrity) and
#                  1200 C (design-basis limit), TECDOC-722 Table 1 (Smolensk-3)
#   mass           nfuel x pi rc^2 x hz x (1 - poros) 10970 kg/m3 (= 10420; [ALM98] 10400)
const CALG = 4184.0
const H_THR = (120.0, 160.0, 193.0, 220.0, 240.0, 270.0, 285.0, 325.0)   # cal/g
const TCLAD_THR = (700.0 + 273.15, 1200.0 + 273.15)        # K
_fuo2(T) = 193.238T + 325.7294T^2 / 2000 - 312.0042T^3 / 3e6 + 116.8224T^4 / 4e9 - 9.7535T^5 / 5e12 + 2.6441e6 / T
h_uo2(T) = _fuo2(T) - _fuo2(298.15)                        # J/kg

"""items: an iterable of (geometry, column state, fuel planes).  Returns a NamedTuple."""
function fuel_diag(items; poros=0.05)
    Tcl = 0.0; Hmax = 0.0; mtot = 0.0
    mH = zeros(length(H_THR)); mT = zeros(length(TCLAD_THR))
    for (g, s, planes) in items
        nfd = g.nfd; nd = g.ndtot; rc = g.rad[nfd]
        for k in planes
            m = g.fnfu * pi * rc^2 * g.hz[k] * (1 - poros) * 10970.0
            hs = [h_uo2(s.temps[i, k]) for i in 1:nfd]
            h = sum(0.5 * (hs[i] + hs[i+1]) for i in 1:nfd-1) / (nfd - 1)      # equal-area rings
            tc = maximum(s.temps[i, k] for i in nfd+1:nd)
            mtot += m; Hmax = max(Hmax, h); Tcl = max(Tcl, tc)
            for (j, thr) in enumerate(H_THR); h >= thr * CALG && (mH[j] += m); end
            for (j, thr) in enumerate(TCLAD_THR); tc >= thr && (mT[j] += m); end
        end
    end
    (; Tcl, Hmax=Hmax / CALG, mtot, mH, mT)
end
fuel_header() = "# t_s Tclad_max_C m_clad>700C_t m_clad>1200C_t Hmax_cal/g " *
                join(["m_H>$(Int(t))_t" for t in H_THR], " ") * "   (bundle-average enthalpy; total fuel mass in line 2)"
fuel_line(t, d) = @sprintf("%.4f %.1f %.4f %.4f %.2f ", t, d.Tcl - 273.15, d.mT[1] / 1e3, d.mT[2] / 1e3, d.Hmax) *
                  join([@sprintf("%.4f", m / 1e3) for m in d.mH], " ")
