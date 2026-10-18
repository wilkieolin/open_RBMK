include("b3b_lines_setup.jl")
println("-- power x20 over 1 s, header and drum held")
dt = 0.01
for n in 1:150
    f = n <= 100 ? 1 + 19 * n / 100 : 20.0
    t = @elapsed (global s = col_step_newton(g, o, s, pow .* f, bu, L, Av, ph, pd, tin, dt))
    n % 10 == 0 && @printf("t %.2f  P x%4.1f  Gin %7.1f  G_out %8.1f  x_out %.3f  eps_out %.3f  ptop %.2f  TFmax %.0f  its %d sub %d (%.1f ms)\n",
                           n * dt, f, s.Gin, s.G[30], s.xfl[30], s.eps[30], s.ptop / KGF, maximum(s.tcomb), s.sweeps, s.substeps, 1e3t)
end
println("-- header falls 3 kgf/cm2 over 2 s (a pump coastdown), power held x20")
for n in 1:200
    phn = ph - 3KGF * min(n / 200, 1.0)
    global s = col_step_newton(g, o, s, pow .* 20, bu, L, Av, phn, pd, tin, dt)
    n % 20 == 0 && @printf("t %.2f  ph-pd %.2f kgf/cm2  Gin %7.1f  G_out %8.1f  x_out %.3f  TFmax %.0f\n",
                           1.5 + n * dt, (phn - pd) / KGF, s.Gin, s.G[30], s.xfl[30], maximum(s.tcomb))
end
