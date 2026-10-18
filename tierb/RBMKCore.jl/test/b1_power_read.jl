function power_bund(result)
    L = readlines(result)
    i = findlast(l -> occursin("CONTENT OF BLOCK 'POWER-BUND", l), L)
    v = Float64[]
    for l in L[i+1:end]
        t = split(l)
        isempty(t) && (isempty(v) ? continue : break)
        x = tryparse.(Float64, t)
        any(isnothing, x) && break
        append!(v, x)
    end
    v
end

const RES = joinpath(@__DIR__, "..", "..", "..", "5.1", "Donjon", "Linux_aarch64")
