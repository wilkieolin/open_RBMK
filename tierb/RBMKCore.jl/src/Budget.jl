# Memory budget for device allocations.  The GB10 has ~110 GB of unified
# memory shared by CPU and GPU; exceeding it pages to disk and locks the
# machine.  Every device allocation in this package goes through `alloc`,
# which checks the running total against an explicit cap before allocating.

const BUDGET_BYTES = Ref{Int}(8 * 2^30)      # default cap: 8 GiB per process
const USED_BYTES = Ref{Int}(0)

"""
    set_budget!(bytes)

Set the per-process device allocation cap.  Raise it explicitly, with the
analysis that justifies it, for batched ensembles.
"""
set_budget!(bytes::Integer) = (BUDGET_BYTES[] = Int(bytes); nothing)

"""
    reserve!(bytes, what)

Account for `bytes` of device memory, or throw if the cap would be exceeded.
"""
function reserve!(bytes::Integer, what::AbstractString)
    new = USED_BYTES[] + Int(bytes)
    new <= BUDGET_BYTES[] || error("memory budget: $what needs $(bytes ÷ 2^20) MiB, " *
                                   "$(USED_BYTES[] ÷ 2^20) MiB in use, cap $(BUDGET_BYTES[] ÷ 2^20) MiB")
    USED_BYTES[] = new
    nothing
end

release!(bytes::Integer) = (USED_BYTES[] = max(0, USED_BYTES[] - Int(bytes)); nothing)
