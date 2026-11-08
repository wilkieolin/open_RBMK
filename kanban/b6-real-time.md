---
id: 42
status: backlog
priority: Normal
blocked_by: []
tags: [tier-b, infra, gpu]
---

# B6: real-time engine

Profile and batch the TH on the GPU; fixed Δt (~10 ms) with sub-cycling in the excursion. Gate: ≥ 1× real
time for the full core through a 7 s AZ-5, with the state exposed for Tier C. Today a loop run takes hours.

**Sources:** `docs/history/TIER_B_WORKPLAN.md` (B6).

## Acceptance Criteria
- Profile of the coupled step; a GPU TH path verified against the CPU Newton path; the real-time gate measured.

## Narrative
- 2026-11-08: Carried over from the retired Tier B workplan. (by @assistant)
