# B6: the pure-Julia IF97 (GPU-capable) against freesteam itself (Water.jl,
# the library THM: calls), over the range THM: can see at RBMK pressures.
using RBMKCore.Water, RBMKCore.IF97, Printf
worst = Dict{Symbol,Float64}()
upd(k, a, b) = (worst[k] = max(get(worst, k, 0.0), abs(a - b) / abs(b)))
for p in range(5.0e6, 9.0e6; length=41)
    upd(:tsat, tsat97(p), tsat(p))
    for T in range(280.0, 1500.0; length=244)
        a = prop_pT97(p, T); b = prop_pT(p, T)
        for f in (:rho, :h, :k, :mu, :cp)
            upd(Symbol("pT_", f), getfield(a, f), getfield(b, f))
        end
    end
end
for T in range(500.0, 620.0; length=121)
    upd(:psat, psat97(T), psat(T))
    for x in (0.0, 1.0)
        a = prop_Tx97(T, x); b = prop_Tx(T, x)
        for f in (:rho, :h, :k, :mu, :cp)
            upd(Symbol("Tx", Int(x), "_", f), getfield(a, f), getfield(b, f))
        end
    end
end
for k in sort(collect(keys(worst)))
    @printf("%-10s worst rel %.2e\n", k, worst[k])
end
@assert maximum(values(worst)) < 1e-12 "IF97 port disagrees with freesteam"
println("IF97 = freesteam to < 1e-12 everywhere tested")
