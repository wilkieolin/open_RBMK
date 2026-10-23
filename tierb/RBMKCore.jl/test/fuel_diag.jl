# Fuel and cladding state against failure criteria (PROGRESS (47)), per step of a coupled run.
#   fuel enthalpy  H(T) = int_298^T cp dT with THM's own UO2 cp (Channel.thmccd: the model's
#                  temperatures and this enthalpy are consistent), pellet-averaged over the
#                  equal-area rings, per axial cell (bundle-average; the OpenMC pin peaking
#                  1.02-1.05 is NOT applied)
#   thresholds     220 cal/g "begin to disintegrate", 285 "rupture", 320 "explode and disperse"
#                  (INSAG-7 p. 67, citing NSRR fresh-fuel pulse tests); 100 and 150 cal/g as
#                  the lower irradiated-fuel bracket (to be sourced)
#   cladding       max over the cladding nodes; 700 C (operational mechanical integrity) and
#                  1200 C (design-basis limit), TECDOC-722 Table 1 (Smolensk-3)
#   mass           nfuel x pi rc^2 x hz x (1 - poros) 10970 kg/m3 (= 10420; [ALM98] 10400)
const CALG = 4184.0
const H_THR = (100.0, 150.0, 220.0, 285.0, 320.0)          # cal/g
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
