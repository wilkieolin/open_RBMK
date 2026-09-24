"""
beta_eff -- independent delayed-neutron fraction for the RBMK cell.

WHY
Every dollar figure this project has quoted rests on beta = 0.0048, which was
assumed, not computed (PROGRESS.md, "Open geometry questions").  It matters
twice over: the void worth in dollars is rho/beta, and beta FALLS with burnup
as Pu-239 (beta ~ 0.0021) displaces U-235 (beta ~ 0.0065), so the same rho
buys more dollars at discharge than at loading.

METHOD
The prompt-vs-total method:  beta_eff = 1 - k_prompt / k_total, where k_prompt
is the same eigenvalue problem with delayed neutron production switched off
(settings.create_delayed_neutrons = False).  This is the standard Monte Carlo
estimator and needs no adjoint.

STATISTICS
beta_eff is ~5e-3, so the two k values differ in the third decimal place.  The
uncertainty on beta_eff is roughly sqrt(2)*sigma_k/k, so sigma_k = 2e-5 gives
~0.6 % on beta.  That is why the particle counts here are much larger than for
a plain k-inf run; anything cheaper produces a number whose error bar is a
large fraction of the answer, which is how 0.0048 would get "confirmed" by
accident.

Run:  python beta_eff.py <dca> <outdir_prefix> [particles] [batches]
"""
import os
import sys

import openmc

from rbmk_cell import make_model


def run(dca, delayed, outdir, particles, batches, inactive, seed=1):
    model = make_model(dca=dca, particles=particles, batches=batches,
                       inactive=inactive, seed=seed)
    model.settings.create_delayed_neutrons = delayed
    sp = model.run(cwd=outdir, threads=18, output=False)
    with openmc.StatePoint(sp) as s:
        return s.keff.nominal_value, s.keff.std_dev


def main():
    dca = float(sys.argv[1]) if len(sys.argv) > 1 else 0.72
    prefix = sys.argv[2] if len(sys.argv) > 2 else "beta"
    parts = int(sys.argv[3]) if len(sys.argv) > 3 else 200_000
    bat = int(sys.argv[4]) if len(sys.argv) > 4 else 220

    out = {}
    for tag, delayed in (("total", True), ("prompt", False)):
        d = f"{prefix}_{tag}_d{dca}"
        os.makedirs(d, exist_ok=True)
        # same seed for both runs: the two eigenvalues are then correlated,
        # and much of the statistical error cancels in the ratio
        out[tag] = run(dca, delayed, d, parts, bat, 40, seed=1)
        print(f"  k_{tag:<6s} = {out[tag][0]:.6f} +/- {out[tag][1]:.6f}",
              flush=True)

    kt, st = out["total"]
    kp, sp_ = out["prompt"]
    beta = 1.0 - kp / kt
    # correlated runs make this an upper bound on the true uncertainty
    sig = (kp / kt) * ((sp_ / kp) ** 2 + (st / kt) ** 2) ** 0.5
    print(f"\nBETARESULT dca={dca} beta_eff={beta:.6f} +/- {sig:.6f} "
          f"({beta / 0.0048:.3f} x the assumed 0.0048)")


if __name__ == "__main__":
    main()
