# Light-water properties as THM: sees them: freesteam (IAPWS-IF97) through
# the same four entry points FREESTEAM.f90 binds (THMSAT, THMSAP, THMPT,
# THMTX), from the vendored C sources (deps/build_freesteam.sh).  CPU only:
# the GPU TH (B6) will carry its own tables, verified against these.
#
# THM: works in REAL*4; these are Float64, so parity is to ~1e-7 relative.

module Water

export tsat, psat, prop_pT, prop_Tx

const LIB = normpath(joinpath(@__DIR__, "..", "..", "build", "libfreesteam.so"))

"""Saturation temperature (K) at pressure p (Pa)."""
tsat(p) = ccall((:freesteam_region4_Tsat_p, LIB), Cdouble, (Cdouble,), p)
"""Saturation pressure (Pa) at temperature T (K)."""
psat(T) = ccall((:freesteam_region4_psat_T, LIB), Cdouble, (Cdouble,), T)

for (fn, sym) in ((:_pT, :free_pT), (:_Tx, :free_Tx))
    @eval function $fn(a::Float64, b::Float64)
        rho = Ref(0.0); h = Ref(0.0); k = Ref(0.0); mu = Ref(0.0); cp = Ref(0.0)
        ccall(($(QuoteNode(sym)), LIB), Cvoid,
              (Ref{Cdouble}, Ref{Cdouble}, Ref{Cdouble}, Ref{Cdouble}, Ref{Cdouble}, Ref{Cdouble}, Ref{Cdouble}),
              a, b, rho, h, k, mu, cp)
        (rho=rho[], h=h[], k=k[], mu=mu[], cp=cp[])
    end
end
"""(rho, h, k, mu, cp) at (p, T): THMPT."""
prop_pT(p, T) = _pT(Float64(p), Float64(T))
"""(rho, h, k, mu, cp) at (T, x) on saturation: THMTX."""
prop_Tx(T, x) = _Tx(Float64(T), Float64(x))

end # module
