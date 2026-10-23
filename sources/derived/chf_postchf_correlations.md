# CHF and post-CHF heat transfer for the RBMK-1000 channel: sourced correlations

Search of 2026-10-23, for adding a boiling crisis to the transient channel model. Tags are those in
`sources/README.md`. "p." means the PDF page unless it says "printed".

How to read this file:
- **READ** means the equation or number was read in the document named, and the transcription was
  checked against the page image.
- **INFERRED** means I derived it, evaluated it or judged it. It is not in any document.
- *Primary* means the document is the originator's own publication (or a code manual describing that
  code). *Secondary* means it reproduces someone else's correlation.

---

## 1. RBMK-specific CHF / critical power

### 1.1 [D] Dollezhal & Emelyanov 1980, p. 69–70: the RBMK design critical-power formula. Primary, READ

[D] p. 69–70 gives the background:
- The critical power of the channel was derived from bundle CHF tests on rig models and on the
  full-scale channel rig, "at coolant parameters close to the reactor's".
- The design-stage formula was "similar to the one recommended in [12]", with an rms error of
  **8.7 %** against the data then available. [12] is Macbeth R.V., *Burn-out analysis. Part V:
  Examination of published world data for rod bundles*, AEEW-R358, 1964 (bibliography p. 79).
- The same correlation is used in the RBMK core-monitoring programs. In that form,
  N_кр = A − B·t_вх, where A and B are functions of channel flow and separator pressure.
- Refitting the coefficients raised the calculated critical power by 5–7 %.

The formula "recommended at present" (p. 70) is:

```
         4.28·10^6 · d_об^0.83 · (ρw·10^-3)^0.57  +  4.07 · d_об · ρw · Δh
N_кр  =  ----------------------------------------------------------------  · F
              6.64·10^2 · d_об^0.57 · (ρw·10^-3)^0.18  +  39.4 · L
```

| Symbol | Meaning, as printed on p. 70 |
|---|---|
| N_кр | channel critical power, **kW** |
| d_об | 4S/П_об, heated diameter, **m** |
| П_об | heated perimeter of the flow cross-section |
| ρw | mass flux, **kg/(s·m²)** |
| Δh | inlet subcooling, **kcal/kg** |
| L | channel length, **m** |
| F | heat-transfer surface area in the channel, **m²** |

Two things to note about the printed formula:
- The scan prints the exponent of d_об in the numerator as "0,83". It cannot be 0.33: see the
  evaluation below.
- The "ρ_w" in the second numerator term is typeset with a subscript. It is read here as ρw, the mass
  flux.

What the book says about validity and use:
- **Validity range: not stated.**
- There is no pressure term. Inference: it is fitted at the RBMK operating pressure, about 7 MPa.
- p. 70: next, the formula is to account for the axial power non-uniformity. That is expected to add
  another 5–7 %.

Supporting statements in [D]:
- p. 71: the permitted margin K_з ≥ 1 corresponds to a probability of boiling crisis in a channel of
  **0.0013**.
- p. 73, Leningrad-1 at nominal power:
  - most heat-loaded channel 3010 kW;
  - max linear rating 41 kW/m;
  - minimum critical-power margin **1.01**;
  - core flow 42 000 t/h;
  - mean outlet quality 13 %;
  - inlet 270 °C;
  - separator 69 kgf/cm².
- p. 116, p. 170–171: K_з = N_кр,пд/N is computed probabilistically. It uses the variances of the
  power measurement and of the N_кр correlation (eqs 9.1–9.6).
- p. 181, pump trip of two of three MCPs in a loop:
  - in dynamics, K ≥ 1 is kept in channels whose static margin is > 1.35;
  - in channels below 1.35, K < 1 transiently, but the cladding rises for ≤ 20 s to at most
    **370 °C**, then falls to 300 °C (Fig. 9.5).
  - This is the only RBMK statement found on the post-dryout wall superheat in a channel.

**INFERRED: evaluation for the RBMK-1000 channel.**
- Geometry used: 80 mm tube, 18 × 13.6 mm rods, 15 mm central tube. That gives S = 2.235·10⁻³ m²,
  П_об = 0.769 m, d_об = 11.62 mm, L = 7 m, F = 5.38 m².
- Water properties used: h_fg = 1505 kJ/kg at 7 MPa.

| Channel flow | G (kg/m²s) | Δh (kcal/kg) | q_cr = N_кр/F (kW/m²) | N_кр (MW) | implied exit quality at N_кр |
|---|---|---|---|---|---|
| 30 t/h | 3729 | 19.8 (t_in 270 °C) | 667 | 3.59 | 0.23 |
| 30 t/h | 3729 | 3 | 658 | 3.54 | 0.27 |
| 20 t/h | 2486 | 3 | 529 | 2.85 | 0.33 |
| 10 t/h | 1243 | 3 | 364 | 1.96 | 0.46 |

The numbers are consistent with the sources:
- N_кр ≈ 3.6 MW against [D] p. 73's 3.01 MW maximum channel at minimum margin 1.01. K_з includes
  the statistical allowance, so it is not N_кр/N.
- [ADE98] Fig. 2b: measured RBMK-1000 assembly-model CHF of 0.5–0.9 MW/m² at 7–9 MPa and
  2000–2500 kg/m²s.
- The critical (dryout) exit quality comes out at **x ≈ 0.23–0.28 at nominal flow**. Within the
  Macbeth form this is the RBMK dryout quality that PROGRESS (47) lists as unsourced.

With d^0.33 instead of d^0.83, q_cr would be about 6 MW/m², which is inconsistent with all of the
above. So the reading 0.83 stands.

**INFERRED: a units inconsistency in the subcooling term.**
- In a Macbeth inlet-conditions form q = (A + ¼·d·G·Δh)/(C + L), the subcooling coefficient must
  satisfy the energy balance as L → ∞. That limit is N → G·S·Δh.
- With [D]'s units (kW, Δh in kcal/kg), this requires the coefficient to be 39.4 × 4.1868/4 =
  **41.2**, not 4.07.
- Either the book has a misprint (40.7?), or the term is defined differently.
- The effect is small for Unit 4: the inlet was nearly saturated before the accident, Δh ≈ 0–5 kcal/kg.
  At 30 t/h and Δh = 3 kcal/kg, the two readings differ by 2 % in N_кр.
- At Δh = 20 kcal/kg they differ by 14 %. Use 4.07 as printed and carry 41.2 as a sensitivity.

**INFERRED: the local-conditions form for a transient code.**
- Take the self-consistent coefficient (41.2) and uniform heating. The inlet form is then exactly
  equivalent to a linear local CHF–quality relation:
  ```
  q_cr(x, G) = [ 4.28·10^6 · d^0.83 · (G/1000)^0.57  −  9.85 · d · G · h_fg · x ] / [ 6.64·10^2 · d^0.57 · (G/1000)^0.18 ]
  ```
  with q in kW/m², G in kg/m²s, h_fg in kJ/kg, d in m. 9.85 = 39.4/4.
- At G = 3729 it gives q_cr = 656 kW/m² at x = 0.28, and q_cr = 0 at x ≈ 0.35.
- This is the Macbeth "local conditions" form that [JAS03] eq 17 quotes in general terms.
- Low-quality caveat: as x → 0 it extrapolates to about 3.4 MW/m². The Macbeth form is a dryout
  (annular-flow) correlation, so do not use it for x ≲ 0.05–0.1 or for subcooled DNB. Use the LUT
  there (§2).

### 1.2 Osmachkin correlation (RBMK-1000 / RBMK-1500 lower assembly). Secondary [JAS03] §3.6.1, p. 66–69, eqs 17–30, READ but not implementable as printed

[JAS03] attributes it to Osmachkin V.S., Seminar TF-74, Moscow, 1974 (its ref [140]). It describes
it as "the modification of the Macbeth formula … used also for the RBMK-1000 type reactor CHF
analysis".

As printed (eq 18):
```
         2.899 · (0.94 − 0.286 · x_cr · We^(1/5))
q_cr = ------------------------------------------ · r ρ' g d_th (g a)^(1/3) (Pr')^(1/3) (Re)^(1/5)
         1 + (1/3.54) · (1/Φ'(z)) · ∫0^z Φ(z) dz

x_cr = 1 − 0.86 · exp(−19/√We)        (19)
We   = (ρw)² / (ρ' σ)                  (20)
Φ(z) = Φ0 · sin(π(z+δ)/H)              (21)
Pr'  = ν'/a                            (29)
Re   = ρw d_th / μ'                    (30)
```

Definitions given in [JAS03]:
- r: latent heat, kJ/kg
- ρ': water density
- a: "temperature coefficient of conductivity", i.e. thermal diffusivity
- Φ: linear heat rate, W/m
- δ: extrapolation length, ≈ 0.8 m
- H: extrapolated core height
- Eqs 22–28 define Φ0 from reactor power and peaking factors.

Range (p. 68): **p = 6.5–8.0 MPa, ρw = 1000–4000 kg/m²s, t_in = 220–270 °C**.

**INFERRED: why it cannot be used as printed.**
- We in eq 20 is not dimensionless: it has units of 1/m, so a length factor is missing.
- The group r ρ' g d_th (g a)^(1/3) is not W/m². The group r ρ'(g a)^(1/3) would be.
- Φ'(z) is never defined. [VTT03] p. 23 states that "the standard Osmachkin correlation results in
  zero value" for uniform axial power, which fits Φ' being a derivative. The modification KTH used
  for that case is not given.
- The primary (TF-74 proceedings) was not found.
- If d_th is the missing length in We, eq 19 gives x_cr = 0.275 at G = 3729 kg/m²s, 7 MPa
  (σ = 0.0175 N/m, ρ' = 740 kg/m³). That agrees with §1.1's 0.23–0.28. **This is suggestive only.**

### 1.3 RRC KI correlation (RBMK-1500 upper assembly with twisting intensifiers). Secondary [JAS03] §3.6.2, p. 70, eq 31, READ

```
q_CHF = 2.23 − 2.05 · x      [MW/m²],  x = average outlet quality of the channel
```

Validity: inlet p 6.37–8.14 MPa; ρw 1300–3520 kg/m²s; t_in 210–270 °C; **x 0.325–0.76**;
q″ 0.49–1.61 MW/m². It is fitted to 2.0 m and 7.0 m assemblies, uniform and non-uniform.

**Not applicable to Unit 4** (inference): RBMK-1000 assemblies have no intensifier grids.

### 1.4 Khabenski correlation (RBMK and VVER bundles, low flow 0–300 kg/m²s). Secondary [JAS03] §3.6.3, p. 70–71, eqs 32–34, READ

```
Smolin–Polyakov (1967):  q_cr = 0.65 · A(p) · (ρw)^0.2 · (1 − x)^1.2               (32)
A(p) = 1.3 − 4.36·10^-2 p   (p ≥ 3 MPa);  1.16 (1.0 ≤ p < 3 MPa);  1.16 p^0.15 (p < 1.0 MPa)
Khabenski et al. (1998):  q_cr = (1 − ρw/300) · q_cr^T + (ρw/150) · A(p) · (1 − x)^1.2  (33)
q_cr^T = 6.75·10^-9 · h ρ_v^0.5 / H · [σ g (ρ_l − ρ_v)]^0.25                        (34)
```

[JAS03] gives no units for q_cr or p in eqs 32–33, and h and H in eq 34 are not defined there.

[VTT03] p. 23: it is good only up to about 1100 kg/m²s.

Primary: Khabenski V.B. et al., Nucl. Eng. Des. 183 (1998) 249–259. Paywalled; not obtained.

### 1.5 Assessments at 7 MPa ([JAS03] §3.7, Table 7, p. 77; [VTT03] p. 23). READ

Single-tube CHF:
- KTH tests: 7 m tubes, D = 10 and 14.9 mm.
- EREC E-108 tests: 7 m, 10 mm, flow reduction at constant power.
- At 7 MPa, CHF was best predicted by **Bowring, Osmachkin and RRC KI**. EPRI predicts CHF too
  early; W-3 under-predicts.

Post-CHF at 7 MPa (E-108):
- transition boiling: **Condie–Bengston** best;
- film boiling: **Groeneveld 5.7 and Groeneveld–Delorme** best.

Subchannel model of the RRC KI KS rig, which was full-scale: 18 rods, 7 m, 80 mm tube, up to 6 MW,
p ≤ 10.8 MPa ([JAS03] p. 64–65). [VTT03] p. 22–23: "EPRI CHF correlation … provides satisfactory
agreement for the CHF for the multichannel fuel bundle model … recommended when performing
RBMK-1000 thermal hydraulic analysis". Bowring also agreed for the RBMK-1500 upper assemblies.

**The EPRI, Bowring, Condie–Bengston, Groeneveld 5.7 and Groeneveld–Delorme equations are not in
any document obtained.** They are therefore unsourced here.

### 1.6 [ADE98] RDIPE assembly tests. Primary, READ (no equation)

- p. 39 (printed): axial power non-uniformity K_z = 1.38 had **no influence** on the critical loads.
  A heated length of 1.23 m gave **twice** the critical load of 7 m. "A new correlation was
  proposed" (Fig. 2), but its equation is not given.
- p. 41 (printed), Fig. 2a/2b:
  - RBMK-1500 assembly model (p 7.0–9.5 MPa, ρw 1000–3000): q_cr falls roughly linearly from about
    1.6 MW/m² at x ≈ 0.15 to about 0.6 MW/m² at x ≈ 0.65.
  - RBMK-1000 assembly model (p 7–9 MPa, ρw 2000–2500): measured 0.5–0.9 MW/m².
  - The curve's ±3σ band is drawn.
  - These are read off the plots, not tabulated.
- printed p. 43–44: Fig. 4 and 5 compare rig and in-pile dryout (Leningrad NPP) data. They are not digitised.

### 1.7 [TD722] Smolensk-3. Primary, READ (functional form only)

- p. 52 (printed 54): K = N_кр·K_δ/N_факт, with N_кр = f(G, P, T_вх) and K_δ a statistical
  correction. The correlation itself is not given. The fraction is OCR-garbled; the variable list is
  clear.
- p. 137, Fig. 39, loss of station power: minimum margin 1.03 at 3 s.
- p. 9 and p. 69: a "new correlation" for channel critical power, linking power, flow and fuel
  temperature, was under development in 1995. Not given.

---

## 2. Fallback: CHF look-up tables with bundle factors

### 2.1 [TD1203] IAEA-TECDOC-1203 (2001). Primary for the method, READ

**Tube table.** The recommended tube method is the **1995 AECL–IPPE CHF LUT** (Groeneveld et al.
1996), described on printed p. 30 (p. 38) and given in full in **App. II**:
- printed p. 175–182, p. 183–190;
- kW/m² as a function of P, G and X;
- **the table pages are images**, so they must be digitised;
- this is the openly published LUT.

**Bundle method**, eq 3.6, printed p. 31:
`CHF_bundle = CHF_table × K1 × K2 × K3 × K4 × K5 × K6 × K7 × K8`.

Table 3.3 (printed p. 33, p. 41), READ from the image:

| Factor | Form |
|---|---|
| K1, diameter | 2 ≤ D_hy ≤ 25 mm: K1 = (0.008/D_hy)^(1/2); D_hy > 25 mm: K1 = 0.57 |
| K2, bundle geometry | K2 = min[1, (0.5 + 2δ/d) · exp(−0.5 x^(1/3))]. δ = rod gap, d = rod diameter. "Tentative" |
| K3, mid-plane spacer (37-element bundle) | K3 = 1 + A exp(−B L_sp/D_hy), A = 1.5 K_L^0.5 (G/1000)^0.2, B = 0.10. K_L = spacer pressure-loss coefficient |
| K4, heated length (L/D_hy ≥ 5) | K4 = exp[(D_hy/L) exp(2α_h)], α_h = Xρ_f/[Xρ_f + (1−X)ρ_g]. Text p. 34: K4 = 1 when K3 is used |
| K5, axial flux | X ≤ 0: 1.0; X > 0: q_loc/q_BLA. q_BLA is eqs 3.11–3.12 |
| K6, radial/circumferential flux | X > 0: q(z)_avg/q(z)_max; X ≤ 0: 1.0 |
| K7, orientation | 1 − exp(−(T1/3)^0.5) (horizontal only) |
| K8, vertical low flow | G < −400 or X ≪ 0: 1; −400 < G < 0: interpolate to CHF_G=0,X=0·(1−α_hom)·C1 |

**IPPE WWER bundle LUT** (App. III, printed p. 183–189, text and tables):
- triangular lattice, D_he = 9.36 mm, p/d = 1.4, 0.1–20 MPa, 50–5000 kg/m²s, X −0.5 to 0.9;
- corrections K1 = (9.36/D_he)^(1/3), K2(p/d), K3 = 0.95 + 0.6 exp(−0.01 L_h/D_he), and
  K4 (spacer).
- Inference: the RBMK assembly is two concentric rings, not a triangular lattice. Use for comparison
  only.

**Film-boiling tables:**
- AECL fully developed film-boiling HTC LUT (Leung 1997 version), **App. IV**, printed p. 190–240,
  kW/m²K, 8 mm tube. Text p. 87: "rms error 6.73 % in surface temperature".
- IPPE film-boiling table, **App. V**, printed p. 241–270.

### 2.2 [R5V4] RELAP5/MOD3: the CHF actually used by RELAP5. Primary for the code, READ (printed p. 4-87 to 4-89)

- "MOD3 uses the **1986 AECL-UO** Critical Heat Flux Lookup Table". The table spans 15 P from 0.1 to
  20 MPa, 14 G from 0 to 7500, and 21 X from −0.5 to 1.0.
- CHF = CHF_table · chfmul, with chfmul = k1·k2·k3·k4·k5·k6·k8 (eqs 4.2-32/33). Table 4.2-8:
  - k1 = (0.008/D_h)^0.33 for D_h < 0.016 m, otherwise (0.008/0.016)^0.33;
  - k2 = min[0.8, 0.8 exp(−0.5 X^(1/3))] for rod bundles;
  - k3 = 1 + A exp(−B L_sp/D_h), A = 1.5 K_loss^0.5 (0.001 G)^0.2, B = 0.1;
  - k4 = exp{(D_h/L) exp(2 alp)};
  - k5 = q_local/q_BLA;
  - k6 is orientation; k7 is vertical low flow; k8 is pressure out of range.
- Note: the RELAP5 k1 exponent (0.33) and k2 form differ from [TD1203] Table 3.3.
- [JAS03] p. 70: RELAP5/MOD3.3 uses the tabular CHF by default, with an optional PG-CHF set from NRI
  Řež.

### 2.3 [CTF23] CTF. Primary for the code, READ (p. 184, printed p. 170)

- q″_chf = q″_LUT · ∏ K_i, i = 1…8 (eq 562).
- Range p 0.1–21 MPa, G 0–8000 kg/m²s, x_e −0.5 to 0.9, D_h 3–25 mm.
- Stored as a 15 × 21 × 23 array. Out-of-range inputs are clipped to the boundary.

### 2.4 The 2006 Groeneveld LUT

- **Primary:** Nucl. Eng. Des. 237 (2007) 1909–1922. Paywalled; not obtained. A university-course
  copy that came up in search needs a login and was not used.
- The **data base used to build it** is public as NUREG/KM-0011
  (https://www.nrc.gov/docs/ML1902/ML19029B306.pdf). nrc.gov answers scripted downloads with a
  JavaScript bot challenge, so it was not fetched. A browser can get it.
- **A table is downloadable only as a third-party transcription:** [GRO06T].
  - It has 24 pressures (0.1, 0.3, 0.5, 1–21 MPa) × 21 G (0–8000) × 23 X (−0.5 to 1.0), in kW/m².
  - The grid is from the repository's `Groeneveld_LUT.m`.
  - CTF stores 15 pressures, so the two grids differ.
  - Not verified against the primary.

**INFERRED: a check against [D].**
- [GRO06T] at 7 MPa, 3500 kg/m²s, X = 0.25 gives 2188 kW/m².
- × K1 = (8/11.62)^0.5 = 0.83 gives 1816 kW/m².
- × K2 (outer-ring gap: pitch 62·sin 15° = 16.05 mm, δ/d = 0.18, K2 = 0.63) gives ≈ **1140 kW/m²**.
- [D]'s formula gives ≈ 650 kW/m² at that quality, consistent with [ADE98] Fig. 2b's
  0.5–0.9 MW/m².
- So the tube LUT with the generic K1·K2 over-predicts RBMK bundle CHF by ~1.7× in the dryout
  region. The K6 (radial peaking between the rings) and spacer factors needed to close the gap are
  not sourced for RBMK.

### 2.5 Russian skeleton tables (Kirillov/Bobkov)

- The 1995 LUT in [TD1203] App. II is the joint AECL–IPPE table (printed p. 30), so the IPPE tube
  data are already merged into it.
- The IPPE bundle table is App. III.
- The separate Russian "skeleton tables" (Kirillov, Bobkov, *Справочник по теплогидравлическим
  расчётам*) were not found in open form.

---

## 3. Transient CHF under fast power ramps

What the documents say (READ):
- **[TD1203] §3.7.3, printed p. 42.**
  - Flow transients with decay constant C1 > 10 s have no noticeable effect.
  - For C1 ≤ 1 s, "It is generally assumed that the CHF is enhanced during fast transients but no
    reliable predictions are available. The assumption that CHF_transient = CHF_steady state for the
    same instantaneous local flow conditions is frequently made."
  - Power transients: use a "Lagrangian" boiling-length-average approach in annular flow. BLA handles
    flux spikes of 2–3× the average.
  - §3.8(5): "relatively little is known of the effect of fast flow and power transients on CHF".
- **[NEA10] §5.2.2.1, Table 8, p. 78.** These are the PATRICIA electrically heated tube tests; the
  primary is Bessiron, JNST 44 (2007) 211, paywalled.

  | Condition | Heating rate | CHF, steady → transient | Critical wall temperature | Film-boiling flux, steady → transient |
  |---|---|---|---|---|
  | PWR: 15 MPa, 553 K, 4 m/s | 2200–4900 K/s | 3 → **4–6 MW/m²** | 630 → 670 K | 3 → 1–2 MW/m² |
  | NSRR: 0.1 MPa, stagnant | 6000–12000 K/s | 1 → 12 MW/m² | | |

- **[NEA10] §6.2.1, p. 89–93.**
  - In RIA, whether a boiling crisis occurs depends on energy deposition, subcooling, pellet–clad gap
    and oxide.
  - Film boiling lasts 2–15 s in NSRR.
  - The quench temperature is largely unaffected by flow and rises with subcooling and with oxide
    thickness.
- **[FUJ81] p. 201.** NSRR, 0.1 MPa, 1.0 m/s, 190 cal/g:
  - "DNB occurred about 20 ms after peak power"; film boiling then lasted ~3 s.
  - "heat transferred to the coolant before DNB was estimated to be less than 2 % of the total heat
    loss till the time of maximum cladding temperature".
  - Higher flow velocity (0.3–1.8 m/s) and subcooling raise the film-boiling HTC (abstract).
- **[LEE21] p. 13–15.** Exponential-period correlations, all at about 0.1 MPa:
  - Sakurai, pool: q″_tr = q″_st(1 + 0.21 τ^−0.5) saturated (eq 6), and q″_st(1 + 0.023 τ^−0.7)
    subcooled (eq 7). The units of τ are not stated on that page.
  - Hata, flow: Bo = [steady correlation] × [1 + A{τu/√(σ/g(ρ_l−ρ_g))}^B], with A = 11.4,
    B = −0.6 (eq 10, Table 3).
- **IGR/BIGR ([HOZ], [NEA10]):** no CHF or clad-to-coolant data were found in these documents.
  **SPERT, CABRI water loop:** not obtained.

INFERRED:
- At RBMK pressure, the only quantitative enhancement found is PATRICIA's factor of ~1.3–2 at
  2000–5000 K/s.
- In the AZ-5 excursion, local heat flux reaches tens of × nominal (nominal ≈ 0.4–0.6 MW/m²). That
  exceeds any CHF in §1–2, even with ×2 enhancement.
- So whether a boiling crisis occurs is **insensitive** to the transient-enhancement question. Only its
  timing, by tens of ms, is affected.
- Following [TD1203], implement CHF_tr = CHF_ss with no enhancement. Carry a ×2 multiplier as the
  sensitivity bound.
- [FUJ81] implies that in a fast pulse almost all heat leaves the clad after DNB, i.e. through film
  boiling. The post-CHF model therefore matters more than the CHF model.

---

## 4. Post-CHF heat transfer

### 4.1 RELAP5 set [R5V4]. Primary for the code, READ (printed p. 4-78 to 4-87)

**Transition boiling: Chen.**
- Basis (eq 4.2-16): q_tb = A_f q_f + h_g(T_w − T_g)(1 − A_f).
- As coded (eq 4.2-19): **q_tb = q_CHF · A_f · M_f + h_g (T_w − T_g)(1 − A_f M_f)**.
- A_f = exp[−λ (T_w − T_spt)^0.5], with λ = max(λ1, λ2):
  - λ1 = C1 − C2 G/10⁵;
  - λ2 = C3 G/10⁵, **G in lbm/hr-ft²**;
  - C1 = 2.4 C2;
  - C2 = 0.05/(1 − α_g^40) + 0.075 α_g;
  - C3 = 0.2 C2.
- α_g is limited to ≤ 0.999 (eq 4.2-20).
- "The minimum of 15 K and (T_w − T_spt)^1/2 is used" in A_f.
- h_g comes from DITTUS with gas properties, ramped linearly between α_g = 0 and 0.5.
- Database: 4167 points, mean deviation 16 % (Table 4.2-6). It includes Era, 6.89–7.28 MPa,
  1098–3024 kg/m²s.

**Film boiling, conduction part: Bromley–Berenson** (eq 4.2-25):
```
h_fspt = 0.62 · [ g ρ_g k_g² (ρ_f − ρ_g) h'_fg C_pg / ( L (T_w − T_spt) Pr_g ) ]^0.25 · M_a
L = 2π [σ / (g(ρ_f − ρ_g))]^0.5                       (4.2-24)
h'_fg = h_fg + 0.5 C_pg (T_w − T_spt)                 (4.2-23)
T_film = (T_w + T_spt)/2                              (4.2-22)
```
- M_a, the void-fraction factor, is 1 for α_g ≤ 0.2, 0 at α_g = 0.999, and 0.0108 at 0.95, with "a
  spline fit" between. **The spline itself is not given.**
- Sudo–Murao subcooling: h_fspt ← h_fspt[1 + 0.025 max(T_spt − T_f, 0.01)] (eq 4.2-26).
- Plus convection to vapour (DITTUS, ramped to zero as α → 0) and Sun's radiation model:
  ε_wall = 0.9, ε_vapour = 0.02, liquid ≤ 0.75 (p. 4-87).
- Post-CHF flux = max(transition, film) (p. 4-82 and 4-87). RELAP5/MOD3 therefore has **no explicit
  T_min** outside reflood.

### 4.2 CTF set [CTF23]. Primary for the code, READ

**Minimum film-boiling temperature** (p. 159–160, printed p. 145–146; °F and psi):
```
T_hn = 705.44 − 4.722e-2 (P_crit − P) + 2.3907e-5 (P_crit − P)² − 5.8193e-9 (P_crit − P)³     (466)
T_min,hn = T_hn + (T_hn − T_l) [(kρC_p)_l / (kρC_p)_w]^1/2                                     (467)
T_min,henry = T_B + 0.42 (T_B − T_l) { [(kρC_p)_l/(kρC_p)_w]^1/2 [H_fg / (C_pw (T_B − T_sat))] }^0.6   (468)
T_B = T_sat + 0.127 (ρ_v H_fg / k_v) [g(ρ_f−ρ_g)/(ρ_f+ρ_g)]^2/3 [g_c σ/(g(ρ_f−ρ_g))]^1/2 [μ_v/(g(ρ_f−ρ_g))]^1/3   (469)
T_min = max{ min[1158, max(T_min,hn, T_min,henry)],  900 if α_v < 0.8 / 700 if α_v ≥ 0.8 }        (470)
```
P_crit = 3203.6 psi.

**Transition boiling: Bjornard–Griffith interpolation** (p. 189, printed p. 175):
- q″_trans = F_w R_d q″_chf + (1 − F_w) q″_min (eq 587);
- F_w = [(T_w − T_min)/(T_chf − T_min)]² (eq 588);
- R_d = min(1, max(0, 400(α_l − 0.0025))) (eq 589);
- q″_mfb = h_ℓ(T_mfb − T_ℓ) + h_b(T_mfb − T_f) + h_v(T_mfb − T_v) (eq 590).

IAFB in CTF uses "the modified Bromley correlation" (p. 187). Its CTF form was not transcribed here.

### 4.3 Groeneveld–Stewart (1982) T_MFB. Secondary [DUA18], eqs 2-11 to 2-13, p. 39–40, READ

```
P ≤ 9 MPa, x ≤ 0:  T_MFB = 284.7 + 44.1 P − 3.72 P² − [(h_l − h_l,sat)/h_fg] · 10^4/(2.82 + 1.22 P)
P ≤ 9 MPa, x ≥ 0:  T_MFB,sat = 284.7 + 44.1 P − 3.72 P²
P ≥ 9 MPa:         T_MFB = ΔT_MFB(9 MPa) · (P_crit − P)/(P_crit − 9) + T_sat
```

What [DUA18] says about it (p. 39):
- data from 2–9 MPa, 100–2700 kg/m²s, x −0.15 to 0.15, 8.93 mm tube, hot-patch technique;
- it is used in TRACE V5.840;
- [DUA18] notes only three points above 1000 kg/m²s, so the "no mass flux effect" conclusion is weak.

Units are not printed at the equations. The INFERRED reading is °C and MPa: at 7 MPa that gives
T_MFB = 411 °C, which is 125 K above T_sat. The primary (Groeneveld & Stewart, Proc. 7th IHTC 1982)
was not obtained.

### 4.4 [TD1203] Ch. 4 recommendations. Primary review, READ

- **Modified Bromley, pool** (eq 4.13, printed p. 88):
  α_FB = 0.62 [ (λ_v³ ρ_v (ρ_ℓ−ρ_v) r g / (ΔT_s μ_v)) · (1/2π) √(g(ρ_ℓ−ρ_v)/σ) ]^(1/4).
- **Radiation**, added to convection, α = α_conv + α_rad (eq 4.14):
  - IAFB, wall to liquid (eq 4.15, printed p. 90):
    α_rad = 5.67·10⁻⁸ (T_w+T_s)(T_w²+T_s²) / [1/ε_w + 1/(ε_ℓ √(φ−1)) − 1]. Printed this way; φ is not
    defined on the page, so this looks like a typesetting fault.
  - DFFB (eq 4.16, printed p. 91): α_rad = 5.67·10⁻⁸ (T_w+T_s)(T_w²+T_s²) / [1/ε_w + 1/ε_v − 1].
- **Steam convection.**
  - Miropolskiy (eq 4.17): Nu_v = 0.028 Re_v^0.8 Pr_v^0.4 (ρ_w/ρ_v)^1.15, with Re_v = G X D/μ_v.
    Valid for P 4–22 MPa, G 0.4–2 Mg/m²s, ρ_w/ρ_v 0.5–0.9, Re 10⁵–2·10⁶.
  - Colburn (eq 4.18): Nu_v = 0.023 Re_v^0.8 Pr_v^0.4 (T_va/T_w)^0.5.
- §4.5.2: the film-boiling LUT is "the more promising approach". For DFFB at high G (> ~3 Mg/m²s)
  the equilibrium single-phase steam equations apply. No validated IAFB method exists.
- **§4.7(9): "No final recommendation for any specific prediction method for film boiling has been
  made".**
- §4.7(8): transients can destabilise IAFB. "Increases in heat transfer coefficient of 10–40 times
  have been recorded due to small pressure pulses or by passing through shock waves". This is
  relevant to the Unit 4 pressure spikes (inference).

### 4.5 What RBMK codes used

- [JAS03] Table 7: for RBMK-1500 at 7 MPa, VIPRE-02 used Condie–Bengston transition boiling and
  Groeneveld 5.7 / Groeneveld–Delorme film boiling. RELAP5/MOD3.3 used its standard set (§4.1).
- No document obtained says which post-CHF set ATHLET or RELAP5-3D used for Ignalina.

### 4.6 Zr–steam oxidation and E110. READ

- **Baker–Just** ([BJ62] abstract, p. 10): **w² = 33.3·10⁶ · t · exp(−45 500/RT)**.
  w = mg Zr reacted per cm², t in s, R in cal/mol·K.
- **Cathcart–Pawel**, Zircaloy-4 ([CP77] Summary p. vii, p. 9). These are parabolic constants,
  δ²/2 = K dK/dt:
  - oxide: δ_φ²/2 = 0.01126 exp(−35 890/RT) cm²/s, 1000–1500 °C;
  - alpha: 0.7615 exp(−48 140/RT) cm²/s, 900–1500 °C;
  - Xi: 0.3412 exp(−41 700/RT) cm²/s;
  - total O: δ_τ²/2 = 0.1811 exp(−39 940/RT) (g/cm²)²/s, 1000–1500 °C;
  - "not valid below ~1000 °C".
- **E110 embrittlement time limit** ([HOZ] eq 6): τ = 2·10⁻⁴ · exp(17 500/(t+273)) s, t in °C.
  Zircaloy-4: 10⁻⁴ exp(20 000/(t+273)).
- [HOZ] §3.2: E110 becomes brittle at much lower oxidation than Zircaloy-4. INFERRED: Zircaloy-4
  kinetics applied to E110 is an assumption.
- **E110 burst criteria (ballooning strain/temperature): not found.**

---

## 5. Recommendation (INFERRED)

**CHF onset: [D] p. 70, in local form (§1.1).**
- It is the RBMK-1000 designer's own correlation, fitted to full-scale 18-rod, 7 m channel data at
  operating conditions, with rms 8.7 % for its predecessor.
- It gives the right magnitude against [ADE98] and [D] p. 73.
- Use: q_cr(x, G) = [4.28·10⁶ d^0.83 (G/1000)^0.57 − 9.85 d G h_fg x] / [6.64·10² d^0.57 (G/1000)^0.18],
  with q in kW/m², d = 0.01162 m and h_fg in kJ/kg. Apply it per axial node with the local
  equilibrium quality.
- Valid in the dryout regime. Inference: roughly x > 0.1 and G 1000–4000 kg/m²s, using Osmachkin's
  range as a proxy, since [D] gives none. Pressure is about 7 MPa.
- Below x ≈ 0.1 and in subcooled flow, take **min**(that, the LUT value).
- The LUT branch is [GRO06T] × K1 × K2 × K5 per [TD1203] Table 3.3, with K3 = 1 because the RBMK
  spacer loss coefficient is unsourced. Alternatively use the [TD1203] App. II 1995 table, once
  digitised.
- Sensitivities to carry:
  - the 4.07 vs 41.2 subcooling coefficient;
  - transient enhancement ×1 vs ×2 (§3);
  - LUT-only CHF, which is +70 % in dryout.

**Post-CHF:** the RELAP5/MOD3 set [R5V4] (§4.1). It is the only complete, consistently documented
set obtained:
- Chen transition boiling with q_CHF from the CHF model above;
- Bromley–Berenson conduction film boiling with Sudo–Murao subcooling;
- DITTUS vapour convection;
- radiation from [TD1203] eqs 4.15/4.16 with the RELAP5 emissivities;
- post-CHF flux = max(transition, film).

That set has no T_min. If quench/rewet matters after the pulse, add **Groeneveld–Stewart T_MFB**
([DUA18], secondary) as the transition/film boundary, and use [CTF23] eq 470 as the cross-check.
INFERRED: at 7 MPa, Groeneveld–Stewart gives 411 °C and CTF gives ≥ 482 °C (the 900 °F floor).

For DFFB at high quality, Miropolskiy (eq 4.17) is the steam-convection asymptote. RELAP5's DITTUS
is the alternative.

Oxidation: Cathcart–Pawel above 1000 °C and Baker–Just as the conservative bound. Both were measured
on Zircaloy (inference: not on E110).

## 6. Still unsourced or unverified

1. **The validity range of [D]'s formula**, and whether the "4.07" subcooling coefficient is a
   misprint. The original NIKIET/RRC KI report behind [D] p. 70 was not found.
2. **The Osmachkin primary** (TF-74, Moscow 1974). The [JAS03] transcription is dimensionally
   inconsistent (§1.2), and the KTH uniform-power modification is not given.
3. **The 2006 LUT primary** (NED 237, 1909) and **NUREG/KM-0011**. Both are blocked or paywalled
   from here; NUREG/KM-0011 is public and can be fetched in a browser. [GRO06T] is unverified.
4. **The 1995 LUT in [TD1203] App. II is images**, not digitised.
5. **RBMK spacer-grid pressure-loss coefficient** (for K3), and the radial power split between the
   inner (6) and outer (12) rings (for K6).
6. **EPRI, Bowring, Condie–Bengston, Groeneveld 5.7/5.9, Groeneveld–Delorme**: no document obtained
   gives these equations. [JAS03] only reports their performance at 7 MPa.
7. **The RELAP5 M_a void-fraction spline** (only anchor points given). **The Chen q_f mechanistic
   term** (only its coded replacement q_CHF is used).
8. **The Groeneveld–Stewart primary** (1982 IHTC). The units in [DUA18] are inferred.
9. **Transient CHF at ~7 MPa for ~1 s ramps**: only PATRICIA (15 MPa, ×1.3–2) via [NEA10]. The
   Bessiron JNST papers are paywalled. No SPERT, CABRI-water-loop or IGR/BIGR clad-to-coolant data
   were obtained.
10. **What ATHLET and RELAP5-3D used for Ignalina** (LEI papers). The ResearchGate/ScienceDirect
    copies are not open.
11. **E110 burst (ballooning) criteria**, and **E110 oxidation kinetics**.
12. **[GRO03T] film-boiling LUT**: grid and units are not documented in the file. The primary is
    paywalled. [TD1203] App. IV (open, images) is the older version.
