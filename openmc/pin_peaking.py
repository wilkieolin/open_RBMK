"""Rod-to-rod power peaking inside the 18-rod RBMK bundle (A8 fuel enthalpy).

    python pin_peaking.py

THM: models a channel as one average rod, so the fuel enthalpy A8 reads is a
bundle average.  The 220 cal/g criterion (INSAG-7 p. 67) is a property of the
hottest ROD.  The bundle's 6 inner and 12 outer rods are separate materials
here (MIX 6 / MIX 7), so the outer-rod peaking factor is

    f_out = (P_outer / 12) / (P_total / 18)

from a kappa-fission tally by material.  Evaluated on the depleted isotopics
of deplete_void.py (depl_gb10_ed, the burnup scale DRAGON uses) at 10 MWd/kg,
and on fresh fuel, each at the 01:23 coolant density (0.72) and at the most
voided density the A8 runs reach (0.15).  Writes pin_peaking.json.
"""
import json
import os

import openmc
import openmc.deplete

import deplete_void as D
from rbmk_cell import make_model


def run(dca, depleted, tag):
    model = make_model(dca=dca, particles=50_000, batches=250, inactive=50,
                       graphite_tsl="c_Graphite_10p")
    if depleted is not None:
        newmats = []
        for mat in model.materials:
            if mat.id in D.VOL:
                dm = depleted[mat.id]
                dm.volume = D.VOL[mat.id]
                dm.temperature = mat.temperature
                newmats.append(dm)
            else:
                newmats.append(mat)
        model.materials = openmc.Materials(newmats)
    fuel = [m for m in model.materials if m.id in (6, 7)]
    t = openmc.Tally(name="ringpower")
    t.filters = [openmc.MaterialFilter(fuel)]
    t.scores = ["kappa-fission"]
    model.tallies = openmc.Tallies([t])
    d = os.path.join("pin_peaking_runs", tag)
    os.makedirs(d, exist_ok=True)
    sp = model.run(cwd=d, threads=int(os.environ.get("RBMK_THREADS", "8")), output=False)
    with openmc.StatePoint(sp) as s:
        tl = s.get_tally(name="ringpower")
        v = tl.mean.ravel(); e = tl.std_dev.ravel()
        ids = [b for b in tl.filters[0].bins]
        k = s.keff.nominal_value
    p = dict(zip(ids, v)); pe = dict(zip(ids, e))
    tot = p[6] + p[7]
    f_out = (p[7] / 12) / (tot / 18)
    f_in = (p[6] / 6) / (tot / 18)
    # relative standard error of f_out, first order
    rel = ((pe[7] / p[7]) ** 2 + (pe[6] / tot) ** 2 + (pe[7] / tot) ** 2) ** 0.5
    r = dict(case=tag, dca=dca, k=k, f_out=f_out, f_in=f_in, f_out_rel_sd=rel)
    print(r, flush=True)
    return r


if __name__ == "__main__":
    depl = os.environ.get("RBMK_DEPLDIR", "depl_gb10_ed")
    marks = D.substeps()[1]
    res = openmc.deplete.Results(os.path.join(depl, "depletion_results.h5"))
    idx = dict(zip(D.BU_GRID, marks))[10.0]
    dep = {m.id: m for m in res.export_to_materials(idx, path=os.path.join(depl, "materials.xml"))}
    out = []
    for dca in (0.72, 0.15):
        out.append(run(dca, dep, f"bu10_d{dca:g}"))
        out.append(run(dca, None, f"bu0_d{dca:g}"))
    json.dump(out, open("pin_peaking.json", "w"), indent=1)
