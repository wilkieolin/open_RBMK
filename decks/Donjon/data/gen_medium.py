#!/usr/bin/env python3
import os
import math

PITCH = 0.25
CORE_RADIUS = 3.875  # ~15*0.25/2 = 1.875, but let's use 3.875 for 31 cells diameter
N_RINGS = int(CORE_RADIUS / PITCH) + 1
NX = NY = 2 * N_RINGS + 1
NZ = 14

def generate_channel_map(nx, ny, core_radius, pitch):
    cx = cy = nx // 2
    r_max = core_radius / pitch
    r_refl = r_max + 2
    map_2d = [[0]*ny for _ in range(nx)]
    n_fuel = n_refl = 0
    for i in range(nx):
        for j in range(ny):
            dx = i - cx
            dy = j - cy
            r = math.sqrt(dx*dx + dy*dy)
            if r <= r_max:
                map_2d[i][j] = 1
                n_fuel += 1
            elif r <= r_refl:
                map_2d[i][j] = 2
                n_refl += 1
    return map_2d, n_fuel, n_refl

channel_map, n_fuel, n_refl = generate_channel_map(NX, NY, CORE_RADIUS, PITCH)
print(f"Grid: {NX}x{NY}, Fuel: {n_fuel}, Reflector: {n_refl}")

# Output goes next to this script, which is decks/Donjon/data -- the
# canonical copy.  tools/link_decks.sh symlinks it into 5.1/Donjon/data,
# so DONJON sees the new deck without a second copy existing.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rbmk_half_test.don')
with open(OUT, 'w') as f:
    f.write(f"""* DONJON5 RBMK Half-Size Test - {NX}x{NY}x{NZ}
* IAEA-3D XS test

LINKED_LIST RBMK RBMK_2 MACRO MACRO2 TRACK SYSTEM FLUX MATEX LMAP POWER FLMAP ;
MODULE GEO: MAC: TRIVAT: TRIVAA: FLUD: USPLIT: MACINI: RESINI: FLPOW: GREP: END: ;
REAL Keff ;
PROCEDURE assertS ;

*==============================================================
* GEOMETRY
*==============================================================
RBMK := GEO: :: CAR3D {NX} {NY} {NZ}
          EDIT 2
          X- VOID  X+ VOID 
          Y- VOID  Y+ VOID 
          Z- VOID  Z+ VOID 
          
          MIX
""")
    for plane in range(1, NZ + 1):
        f.write(f"PLANE {plane}\n")
        for j in range(NY):
            row = ' '.join(str(channel_map[i][j]) for i in range(NX))
            f.write(f"          {row}\n")
    
    def fmt_mesh(vals, per_line=15):
        lines = []
        for i in range(0, len(vals), per_line):
            lines.append(' '.join(vals[i:i+per_line]))
        return '\n          '.join(lines)
    
    mesh_x = [f"{i*PITCH:.2f}" for i in range(NX + 1)]
    mesh_y = [f"{i*PITCH:.2f}" for i in range(NY + 1)]
    mesh_z = [f"{i*PITCH:.2f}" for i in range(NZ + 1)]
    
    f.write(f"""
          MESHX {fmt_mesh(mesh_x)}
          MESHY {fmt_mesh(mesh_y)}
          MESHZ {fmt_mesh(mesh_z)}
          ;

*==============================================================
* MACROLIB: IAEA-3D pattern
*==============================================================
MACRO := MAC: ::
  EDIT 2 NGRO 2 NMIX 2 NIFI 1
  READ INPUT
* Mix 1: Fuel (IAEA fuel)
  MIX     1
      DIFFX  1.500E+00  4.000E-01
      TOTAL  3.000E-02  8.000E-02
     NUSIGF  0.000E+00  1.350E-01
   H-FACTOR  0.000E+00  1.350E-01
       SCAT  1 1 0.0  2 2 0.0  2.00E-02
* Mix 2: Reflector (IAEA reflector)
  MIX     2
      DIFFX  2.000E+00  3.000E-01
      TOTAL  4.000E-02  1.000E-02
     NUSIGF  0.000E+00  0.000E+00
   H-FACTOR  0.000E+00  0.000E+00
       SCAT  1 1 0.0  2 2 0.0  4.00E-02
  ;

*==============================================================
* FUEL MAP
*==============================================================
RBMK_2 MATEX := USPLIT: RBMK :: EDIT 1
  NGRP 2 MAXR 100000 NMIX 2
  NREFL 1 RMIX 2
  NFUEL 1 FMIX 1
  ;

*==============================================================
* MACINI
*==============================================================
MACRO2 MATEX := MACINI: MATEX MACRO :: EDIT 1 ;

*==============================================================
* TRACKING
*==============================================================
TRACK := TRIVAT: RBMK_2 ::
      TITLE 'RBMK HALF TEST'
      EDIT 1 MAXR 100000 DUAL 3 3 ;

*==============================================================
* ASSEMBLY
*==============================================================
SYSTEM := TRIVAA: MACRO2 TRACK ::
      EDIT 1 ;

*==============================================================
* FLUX
*==============================================================
FLUX := FLUD: SYSTEM TRACK ::
      EDIT 2 ADI 5 EXTE 1.0E-7 1000 ;

*==============================================================
* POWER
*==============================================================
POWER := FLPOW: FLUX TRACK MATEX MACRO2
  :: EDIT 10 PTOT 1600.0  PRINT ALL ;

*==============================================================
* CHECK
*==============================================================
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>Keff<< ;
ECHO "Keff=" Keff ;
assertS FLUX :: 'K-EFFECTIVE' 1 1.005 ;

ECHO "Half-size test completed" ;
END: ;

QUIT .
""")
    print("Generated rbmk_half_test.don")
