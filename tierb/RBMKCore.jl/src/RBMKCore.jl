"""
    RBMKCore

Tier B: a GPU-resident RBMK-1000 core engine (2-group diffusion, 6 delayed
groups, 1-D channel thermal-hydraulics), verified against the Tier A DONJON
reference runs.  See TIER_B_WORKPLAN.md.
"""
module RBMKCore

include("Budget.jl")
include("XS.jl")
include("Diffusion.jl")
include("Mixed.jl")
include("Core.jl")
include("Kinetics.jl")
include("DualKinetics.jl")
include("GPUDual.jl")
include("LcmAscii.jl")
include("Water.jl")
include("IF97.jl")
include("Channel.jl")
include("Column.jl")
include("Loop.jl")

end
