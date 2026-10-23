# Power-shape diagnostics against INSAG-7's non-uniformity factors (PROGRESS (48)).
#   Kv  volumetric peaking factor: max bundle power / mean bundle power (INSAG-7 p. 196 "Kv
#       volumetric power peaking factor (non-uniformity factor)"; p. 67: Kv = 5.5 in Ref. [28]
#       with the core power ~30x its initial value; p. 121: ~6.0 in all three Models)
#   Kr  radial: max channel power / mean channel power (p. 66: 2.0 at the initial state, Ref. [28])
#   Kz  axial: max plane power / mean plane power (Fig. II-4)
# plus the local power against the INITIAL mean bundle (Kv P/P0; Ref. [28]: 5.5 x 30 = 165), and
# the adiabatic local energy: int p dt per kg of the bundle's fuel, the enthalpy rise each bundle
# would have with no heat removed (the TH-independent part of the fuel's enthalpy).
# pw: bundle powers in FMAP order (ib-1)*nch + ich, all bundles the same fuel mass.
struct ShapeAcc
    nch::Int; nb::Int; pmean0::Float64; mb::Float64; e::Vector{Float64}
end
ShapeAcc(pw0, nch, nb, mb) = ShapeAcc(nch, nb, sum(pw0) / length(pw0), mb, zeros(length(pw0)))
shape_header() = "# t_s P/P0 Kv Kr Kz Kv*P/P0 ich_max ib_max ich_rmax iz_zmax Eadia_max_cal/g ich_e ib_e m_Eadia>{60,100,160,240}_t   (Eadia: int p dt / bundle fuel mass, from AZ-5)"
function shape_line!(a::ShapeAcc, t, dt, pw)
    a.e .+= pw .* (1e3 * dt / a.mb)                       # J/kg (pw kW; rectangle rule at the step end)
    nch, nb = a.nch, a.nb
    pm = sum(pw) / length(pw)
    k = argmax(pw); ib = (k - 1) ÷ nch + 1; ich = k - (ib - 1) * nch
    chp = [sum(pw[(b-1)*nch+i] for b in 1:nb) for i in 1:nch]
    plp = [sum(@view pw[(b-1)*nch+1:b*nch]) for b in 1:nb]
    ke = argmax(a.e); ibe = (ke - 1) ÷ nch + 1
    ms = [count(>=(c * 4184.0), a.e) * a.mb / 1e3 for c in (60, 100, 160, 240)]
    @sprintf("%.4f %.5e %.3f %.3f %.3f %.2f %d %d %d %d %.2f %d %d ", t, pm / a.pmean0, maximum(pw) / pm,
             maximum(chp) / (sum(chp) / nch), maximum(plp) / (sum(plp) / nb), maximum(pw) / a.pmean0, ich, ib,
             argmax(chp), argmax(plp), maximum(a.e) / 4184.0, ke - (ibe - 1) * nch, ibe) *
        join([@sprintf("%.3f", m) for m in ms], " ")
end
