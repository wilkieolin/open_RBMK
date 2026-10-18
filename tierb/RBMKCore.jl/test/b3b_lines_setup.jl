# B3b-2 mechanics: one channel between a group header and its drum.
# Geometry entries marked PLACEHOLDER are gaps in sources/derived/b3b_loop_data.md:
# this test exercises the solver, it is not a result.
using RBMKCore.Channel, RBMKCore.Column, RBMKCore.Column.Lines, RBMKCore.IF97, Printf
const KGF = 0.0980665e6
g = chan_geom(fill(0.25, 32), 0.0625; pitch=0.017639, nfuel=18, rc=0.00575, rig=0.00585, rgg=0.00679, nfd=15, ndtot=20)
o = ThmOpts(cflux=1.8e6, khgap=2800.0, maxit1=100, maxit2=100, ermaxt=0.05)
pow = zeros(32); pow[3:30] .= 0.2e6 / 28 .* (π / 2 .* sin.(range(0.06, π - 0.06; length=28)))   # 0.2 MW channel (~01:23 mean x1.6)
bu = fill(10000.0, 32)
tin = 559.6204; pd = 7.384407e6                   # the A7 deck INLET; drum pressure unsourced (gap 6)
L = ChanLines(Ach=18 * g.acool / 3,
              Ain=π * 0.025^2, Din=0.050, Lin=25.0, dzin=5.0,          # [D] p.60 57x3.5; L, dz PLACEHOLDER
              xi_valve=6.2 / 7.7,                                       # [D] Table 3.1, valve fully open
              Aout=π * 0.034^2, Dout=0.068, Lout=30.0, dzout=18.0,      # [D] p.60 76x4; L, dz PLACEHOLDER
              Kout=2.0, eps_bundle=(18 * 6.79^2 + 7.5^2) / 40.0^2, sourced=false)
speed = 3.5; rhoin = prop_pT97(pd, tin).rho; Gin = speed * rhoin
st = thm_steady(g, o, pow, bu, speed, tin, pd)
c0 = col_from_steady(st, g, speed, tin, pd)
ph = pd + 12.7KGF                                  # header - drum: [D] p. 50 nominal
Av, dpv, s = valve_area(g, o, c0, pow, bu, L, ph, pd, tin, Gin)
@printf("steady: Gin %.0f kg/m2/s (W %.2f kg/s = %.1f t/h), exit quality %.3f, valve dp %.2f kgf/cm2, throat %.2f cm2\n",
        Gin, Gin * L.Ach, Gin * L.Ach * 3.6, s.xfl[30], dpv / KGF, Av * 1e4)
@printf("column dp (bottom to top) %.2f kgf/cm2\n", (s.p[3] - s.ptop) / KGF)
