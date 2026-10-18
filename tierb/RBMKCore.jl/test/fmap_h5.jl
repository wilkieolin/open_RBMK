# FMAP (LCM ASCII export, DONJON) -> HDF5 with the per-bundle PARAM values
# (T-FUEL, D-COOL, ...), bottom bundle first as the fuel element scan order.
#   julia --project=. test/fmap_h5.jl fmap0.asc fmap0.h5
using HDF5

# records: (level, name, type, n, lines); type 1 int, 2 real, 3 char, 0/10 dir/list
function records(path)
    L = readlines(path); out = []; i = 1
    while i <= length(L)
        if startswith(L[i], "->") && i < length(L)
            h = parse.(Int, split(L[i])[2:5])
            name, j = h[2] == 0 ? ("", i + 1) : (strip(L[i+1]), i + 2)      # list items are unnamed
            while j <= length(L) && !startswith(L[j], "->"); j += 1; end
            push!(out, (h[1], name, h[3], h[4], L[(h[2] == 0 ? i + 1 : i + 2):j-1])); i = j
        else
            i += 1
        end
    end
    out
end

reals(lines) = [parse(Float64, replace(t, r"(\d)([+-]\d{2,3})$" => s"\1E\2")) for l in lines for t in split(l)]

function main(src, dst)
    recs = records(src); pname = nothing
    h5open(dst, "w") do h
        for (lev, name, typ, n, lines) in recs
            if name == "P-NAME"
                pname = strip(lines[end])
            elseif name == "P-VALUE" && pname !== nothing && typ == 2
                v = reals(lines); @assert length(v) == n
                h[pname] = v; println(pname, ": ", n, " values, ", extrema(v)); pname = nothing
            end
        end
        attributes(h)["source"] = abspath(src)
    end
end

main(ARGS[1], ARGS[2])
