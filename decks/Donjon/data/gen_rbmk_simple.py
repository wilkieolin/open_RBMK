#!/usr/bin/env python3
"""Generate RBMK 3D DONJON input matching IAEA format exactly"""

# Core parameters - coarse mesh
import os
NX, NY, NZ = 25, 25, 14
PITCH = 0.50  # meters

# Create cylindrical mask: central region = fuel (mix=1), outer = reflector (mix=2)
radius_fuel = 9.0  # fuel radius in cells
cx, cy = (NX - 1) / 2, (NY - 1) / 2

# Generate mix planes: 14 Z-planes
mix_planes = []
for z in range(NZ):
    plane = []
    for y in range(NY):
        row = []
        for x in range(NX):
            dx = x - cx
            dy = y - cy
            if dx*dx + dy*dy <= radius_fuel*radius_fuel:
                row.append(1)  # fuel
            else:
                row.append(2)  # reflector
        plane.append(row)
    mix_planes.append(plane)

# Write DONJON input matching IAEA format exactly
# Output goes next to this script, which is decks/Donjon/data -- the
# canonical copy.  tools/link_decks.sh symlinks it into 5.1/Donjon/data,
# so DONJON sees the new deck without a second copy existing.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rbmk_core_3d_simple.don')
with open(OUT, 'w') as f:
    f.write("""* DONJON5 RBMK-1000 3D Core Model - Simple two-region (no RESINI/FLPOW)
LINKED_LIST RBMK RBMK_2 MACRO MACRO2 TRACK SYSTEM FLUX MATEX ;
MODULE GEO: MAC: TRIVAT: TRIVAA: FLUD: USPLIT: MACINI: GREP: END: ;
REAL Keff ;
PROCEDURE assertS ;

*==============================================================
* GEOMETRY: Initial GEO with explicit fuel (mix=1) / reflector (mix=2)
*==============================================================
RBMK := GEO: :: CAR3D {} {} {}
          EDIT 2
          X- VOID  X+ VOID 
          Y- VOID  Y+ VOID 
          Z- VOID  Z+ VOID 
          MIX 
""".format(NX, NY, NZ))

    # Write all Z planes - PLANE at column 1, data rows at column 1
    for z in range(NZ):
        f.write("PLANE {}\n".format(z + 1))
        for y in range(NY):
            row_str = " ".join(str(mix_planes[z][y][x]) for x in range(NX))
            f.write(row_str + "\n")

    # Mesh - MESHX at column 10 (indented), continuation lines at column 10
    f.write("          MESHX")
    for i in range(NX + 1):
        if i % 10 == 0 and i > 0:
            f.write("\n          ")
        f.write(" {:.1f}".format(i * PITCH))
    f.write("\n")
    
    f.write("          MESHY")
    for i in range(NY + 1):
        if i % 10 == 0 and i > 0:
            f.write("\n          ")
        f.write(" {:.1f}".format(i * PITCH))
    f.write("\n")
    
    f.write("          MESHZ")
    for i in range(NZ + 1):
        if i % 10 == 0 and i > 0:
            f.write("\n          ")
        f.write(" {:.1f}".format(i * PITCH))
    f.write("\n          ;\n\n")

    # Rest of input
    f.write("""*==============================================================
* MACROLIB: IAEA 2-group XS (NMIX=2)
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
* TRACKING: 3D transport (TRIVAT)
*==============================================================
TRACK := TRIVAT: RBMK_2 ::
      TITLE 'RBMK-1000 3D CORE'
      EDIT 1 MAXR 100000 DUAL 3 3 ;

*==============================================================
* ASSEMBLY: System matrices
*==============================================================
SYSTEM := TRIVAA: MACRO2 TRACK ::
      EDIT 1 ;

*==============================================================
* FLUX: 3D k-eigenvalue solution
*==============================================================
FLUX := FLUD: SYSTEM TRACK ::
      EDIT 2 EXTE 1.0E-7 1000 ;

*==============================================================
* CHECK: k-effective
*==============================================================
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>Keff<< ;
ECHO "Keff=" Keff ;
assertS FLUX :: 'K-EFFECTIVE' 1 1.005 ;

ECHO "RBMK 3D core test completed" ;
END: ;
QUIT .
""")

print("Generated rbmk_core_3d_simple.don with {} Z-planes".format(NZ))
fuel_count = sum(sum(1 for x in range(NX) if mix_planes[z][y][x] == 1) 
                 for z in range(NZ) for y in range(NY))
refl_count = sum(sum(1 for x in range(NX) if mix_planes[z][y][x] == 2) 
                 for z in range(NZ) for y in range(NY))
print("Fuel cells (mix=1): {}".format(fuel_count))
print("Reflector cells (mix=2): {}".format(refl_count))