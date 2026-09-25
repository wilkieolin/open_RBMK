"""
Where does the void reactivity actually come from?

DRAGON and OpenMC agree the RBMK cell's void coefficient is positive but
disagree by ~4x at full void (+222 vs +887 pcm, with hydrogen treatment and
nuclear data already matched).  k-inf is production over absorption, so
decomposing absorption by nuclide and energy range, at nominal and at full
void, localises the disagreement to a specific reaction rather than leaving
it as a bulk k-inf difference.

Energy cut is 0.625 eV, the same one the DRAGON deck uses in EDI: COND.

Run:  python rates.py <dca> <outdir> [particles] [batches]
"""
import os
import sys
import openmc
from rbmk_cell import make_model

THERMAL = 0.625
FAST    = 1.0e5
NUCS = ["U235", "U238", "O16", "H1", "C12", "Zr90", "Zr91", "Zr92",
        "Zr94", "Zr96", "Nb93", "He4"]
RANGE = {0: "thermal", 1: "epitherm", 2: "fast"}


def build(dca, particles, batches, inactive):
    # RBMK_GRAPHITE_TSL=c_Graphite_10p puts OpenMC on DRAGON's own graphite
    # scattering law (method-gap hypothesis H1); default is unchanged.
    model = make_model(dca=dca, particles=particles, batches=batches,
                       inactive=inactive,
                       graphite_tsl=os.environ.get("RBMK_GRAPHITE_TSL", "c_Graphite"))
    efilter = openmc.EnergyFilter([0.0, THERMAL, FAST, 2.0e7])

    t_nuc = openmc.Tally(name="by nuclide")
    t_nuc.filters = [efilter]
    t_nuc.nuclides = NUCS
    t_nuc.scores = ["absorption", "fission", "nu-fission"]

    t_tot = openmc.Tally(name="totals")
    t_tot.filters = [efilter]
    t_tot.scores = ["absorption", "nu-fission", "flux"]

    model.tallies = openmc.Tallies([t_nuc, t_tot])
    model.settings.output = {"tallies": False}
    return model


def main():
    dca = float(sys.argv[1]); out = sys.argv[2]
    parts = int(sys.argv[3]) if len(sys.argv) > 3 else 40_000
    bat   = int(sys.argv[4]) if len(sys.argv) > 4 else 160
    model = build(dca, parts, bat, 40)
    sp_path = model.run(cwd=out, threads=int(os.environ.get("RBMK_THREADS", os.cpu_count())), output=False)

    with openmc.StatePoint(sp_path) as sp:
        k = sp.keff
        dn = sp.get_tally(name="by nuclide").get_pandas_dataframe()
        dt = sp.get_tally(name="totals").get_pandas_dataframe()

    tot_abs = dt[dt.score == "absorption"]["mean"].sum()
    nuf     = dt[dt.score == "nu-fission"]["mean"].sum()
    flux    = dt[dt.score == "flux"]["mean"].values

    print(f"@@ dca {dca}")
    print(f"@@ kinf {k.nominal_value:.6f} {k.std_dev:.6f}")
    print(f"@@ totabs {tot_abs:.8f}")
    print(f"@@ nufis {nuf:.8f}")
    print(f"@@ kcheck {nuf/tot_abs:.6f}")
    for i, nm in RANGE.items():
        print(f"@@ fluxfrac {nm} {flux[i]/flux.sum():.6f}")
    for nuc in NUCS:
        sub = dn[(dn.nuclide == nuc) & (dn.score == "absorption")]
        for i, (_, r) in enumerate(sub.iterrows()):
            if r["mean"] > 0:
                print(f"@@ abs {nuc} {RANGE.get(i,i)} {r['mean']:.8f} "
                      f"{100*r['mean']/tot_abs:.4f}")
    for nuc in ("U235", "U238"):
        sub = dn[(dn.nuclide == nuc) & (dn.score == "nu-fission")]
        tot = sub["mean"].sum()
        if tot > 0:
            print(f"@@ nufis_nuc {nuc} {tot:.8f} {100*tot/nuf:.4f}")


if __name__ == "__main__":
    main()
