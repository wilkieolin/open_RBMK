#!/usr/bin/env python3
"""Generate RBMK 3D DONJON transient input with realistic 1661-channel pattern"""

# Core parameters
import os
NX, NY, NZ = 49, 49, 28
PITCH = 0.25  # meters
radius_m = 5.9
radius_cells = radius_m / PITCH  # 23.6
cx = (NX - 1) / 2.0  # 24.0
cy = (NY - 1) / 2.0  # 24.0

# Generate fuel channel positions
all_core_positions = []
for iy in range(NY):
    for ix in range(NX):
        dx = ix - cx
        dy = iy - cy
        if dx*dx + dy*dy <= radius_cells*radius_cells:
            all_core_positions.append((ix, iy))

all_core_positions.sort(key=lambda p: (p[0]-cx)**2 + (p[1]-cy)**2)
fuel_channels = all_core_positions[:1661]
fuel_set = set(fuel_channels)

# Create mix map for all planes
mix_planes = []
for z in range(NZ):
    plane = []
    for y in range(NY):
        row = []
        for x in range(NX):
            if (x, y) in fuel_set:
                row.append(1)  # fuel channel
            else:
                dx = x - cx
                dy = y - cy
                if dx*dx + dy*dy <= radius_cells*radius_cells:
                    row.append(2)  # graphite
                else:
                    row.append(0)  # void
        plane.append(row)
    mix_planes.append(plane)

# Write DONJON input
# Output goes next to this script, which is decks/Donjon/data -- the
# canonical copy.  tools/link_decks.sh symlinks it into 5.1/Donjon/data,
# so DONJON sees the new deck without a second copy existing.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rbmk_transient_full.don')
with open(OUT, 'w') as f:
    f.write("""*==============================================================
* RBMK-1000 3D Transient - Realistic 1661 channels
* Uses KINSOL for transient (avoids FLPOW/RESINI conflict)
*==============================================================
LINKED_LIST RBMK RBMK_2 MACRO MACRO2 TRACK SYSTEM FLUX0 KINET KINET_0 MATEX ;
MODULE GEO: MAC: TRIVAT: TRIVAA: FLUD: USPLIT: MACINI: INIKIN: KINSOL: GREP: END: ;
REAL Keff Powf ;
PROCEDURE assertS ;

*==============================================================
* GEOMETRY: 3D Cartesian core (49x49x28, 25cm pitch, 7m active)
* Mix 1 = Fuel channel, Mix 2 = Graphite, Mix 0 = Void
*==============================================================
RBMK := GEO: :: CAR3D {} {} {}
          EDIT 2
          X- VOID  X+ VOID 
          Y- VOID  Y+ VOID 
          Z- VOID  Z+ VOID 
          MIX 
""".format(NX, NY, NZ))

    for z in range(NZ):
        f.write(f"PLANE {z + 1}\n")
        for y in range(NY):
            row_str = " ".join(str(mix_planes[z][y][x]) for x in range(NX))
            f.write(row_str + "\n")

    f.write("          MESHX")
    for i in range(NX + 1):
        if i % 10 == 0 and i > 0:
            f.write("\n          ")
        f.write(f" {i * PITCH:.2f}")
    f.write("\n")
    
    f.write("          MESHY")
    for i in range(NY + 1):
        if i % 10 == 0 and i > 0:
            f.write("\n          ")
        f.write(f" {i * PITCH:.2f}")
    f.write("\n")
    
    f.write("          MESHZ")
    for i in range(NZ + 1):
        if i % 10 == 0 and i > 0:
            f.write("\n          ")
        f.write(f" {i * PITCH:.2f}")
    f.write("\n          ;\n\n")

    f.write("""*==============================================================
* MACRO: 2-group XS (IAEA benchmark validated)
*==============================================================
MACRO := MAC: ::
  EDIT 2 NGRO 2 NMIX 2 NIFI 1
  READ INPUT
  MIX     1
      DIFFX  1.500E+00  4.000E-01
      TOTAL  3.012E-02  8.000E-02
     NUSIGF  0.000E+00  1.350E-01
   H-FACTOR  0.000E+00  1.350E-01
       SCAT  1 1 0.0  2 2 0.0  2.00E-02
  MIX     2
      DIFFX  2.000E+00  3.000E-01
      TOTAL  4.000E-02  1.000E-02
     NUSIGF  0.000E+00  0.000E+00
   H-FACTOR  0.000E+00  0.000E+00
       SCAT  1 1 0.0  2 2 0.0  4.00E-02
  ;

*==============================================================
* USPLIT: Split geometry (preserves existing mixes)
*==============================================================
RBMK_2 MATEX := USPLIT: RBMK :: EDIT 1
  NGRP 2 MAXR 100000 NMIX 2
  NREFL 1 RMIX 2
  NFUEL 1 FMIX 1
  ;

*==============================================================
* MACINI: Initialize macrolib
*==============================================================
MACRO2 MATEX := MACINI: MATEX MACRO :: EDIT 1 ;

*==============================================================
* TRACKING: 3D transport (TRIVAT) for kinetics
*==============================================================
TRACK := TRIVAT: RBMK_2 ::
  TITLE 'RBMK-1000 3D TRIVAC TRACKING'
  EDIT 1 MAXR 100000 DUAL 3 3
  ;

*==============================================================
* TRIVAA: System with kinetics (UNIT required for kinetics)
*==============================================================
SYSTEM := TRIVAA: MACRO2 TRACK ::
  EDIT 1
  UNIT
  ;

*==============================================================
* FLUD: Direct flux (steady-state initialization)
*==============================================================
FLUX0 := FLUD: SYSTEM TRACK ::
  EDIT 2 EXTE 1.0E-7 1000 ;
GREP: FLUX0 :: GETVAL 'K-EFFECTIVE' 1 >>Keff<< ;
ECHO "Initial Keff=" Keff ;
assertS FLUX0 :: 'K-EFFECTIVE' 1 1.005 ;

*==============================================================
* INIKIN: Initialize kinetics parameters
*==============================================================
KINET_0 := INIKIN: MACRO2 TRACK SYSTEM FLUX0 ::
  EDIT 1
  NORM POWER-INI 3200.0
  ;

*==============================================================
* KINSOL: Transient flux solver
*==============================================================
KINET := KINSOL: KINET_0 MACRO2 TRACK SYSTEM MACRO2 SYSTEM ::
  EDIT 1
  DELTA 0.1
  SCHEME FLUX CRANK
  PREC EXPON
  ;

* Output
GREP: KINET :: GETVAL 'E-POW' 1 >>Powf<< ;
ECHO "Final Power (MW)=" Powf ;
GREP: KINET :: GETVAL 'K-EFFECTIVE' 1 >>Keff<< ;
ECHO "Final Keff=" Keff ;

END: ;
QUIT .
""")

print("Generated rbmk_transient_full.don")
