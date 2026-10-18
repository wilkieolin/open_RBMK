# Reader for DONJON LCM objects exported as SEQ_ASCII (the `X_A := X ;`
# dumps the Tier B reference decks write).  Each record is a header line
#   ->  level  namelen  type  length  <-
# then the name (absent for an unnamed list item, namelen 0), then the data:
# type 1 integers, 2 reals, 3 characters (int codes then the text line),
# 0/10 a directory / list.

module LcmAscii

export lcm_read, lcm_get, lcm_params

struct Rec
    level::Int
    name::String
    typ::Int
    n::Int
    lines::Vector{String}
end

function lcm_read(path)
    L = readlines(path); out = Rec[]; i = 1
    while i <= length(L)
        if startswith(L[i], "->") && i < length(L)
            h = parse.(Int, split(L[i])[2:5])
            name, j = h[2] == 0 ? ("", i + 1) : (String(strip(L[i+1])), i + 2)
            d0 = j
            while j <= length(L) && !startswith(L[j], "->"); j += 1; end
            push!(out, Rec(h[1], name, h[3], h[4], L[d0:j-1])); i = j
        else
            i += 1
        end
    end
    out
end

_real(t) = parse(Float64, replace(t, r"(\d)([+-]\d{2,3})$" => s"\1E\2"))
function data(r::Rec)
    r.typ == 1 && return [parse(Int, t) for l in r.lines for t in split(l)]
    r.typ == 2 && return [_real(t) for l in r.lines for t in split(l)]
    r.typ == 3 && return String(strip(r.lines[end]))
    nothing
end

"""The `nth` record called `name` (at any level), decoded."""
function lcm_get(recs, name; nth=1)
    c = 0
    for r in recs
        if r.name == name
            c += 1
            c == nth && return data(r)
        end
    end
    error("record $name (#$nth) not found")
end

"""The FMAP PARAM list as P-NAME => P-VALUE."""
function lcm_params(recs)
    out = Dict{String,Any}(); pname = nothing
    for r in recs
        if r.name == "P-NAME"
            pname = data(r)
        elseif r.name == "P-VALUE" && pname !== nothing
            out[pname] = data(r); pname = nothing
        end
    end
    out
end

end # module
