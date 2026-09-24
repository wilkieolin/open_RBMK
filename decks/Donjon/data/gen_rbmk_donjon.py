#!/usr/bin/env python3
"""
import os
Generate DONJON5 input for RBMK-1000 3D core model.
1661 channels, 25 cm pitch, cylindrical core ~11.8 m diameter.
"""

import math

# Core parameters
PITCH = 0.25  # 25 cm = 0.25 m
CORE_RADIUS = 5.9  # ~11.8 m diameter / 2
N_RINGS = int(CORE_RADIUS / PITCH) + 1  # grid half-size
NX = NY = 2 * N_RINGS + 1
NZ = 28  # 7 m active / 0.25 m = 28 planes

# Generate cylindrical channel pattern
def generate_channel_map(nx, ny, core_radius, pitch):
    """Return 2D array: 1=fuel channel, 2=graphite reflector, 0=void"""
    cx = cy = nx // 2
    r_max = core_radius / pitch
    r_reflector = r_max + 2  # 2 cells of reflector
    map_2d = [[0]*ny for _ in range(nx)]
    n_fuel = 0
    n_refl = 0
    for i in range(nx):
        for j in range(ny):
            dx = i - cx
            dy = j - cy
            r = math.sqrt(dx*dx + dy*dy)
            if r <= r_max:
                map_2d[i][j] = 1  # fuel channel
                n_fuel += 1
            elif r <= r_reflector:
                map_2d[i][j] = 2  # graphite reflector
                n_refl += 1
    return map_2d, n_fuel, n_refl

channel_map, n_fuel, n_refl = generate_channel_map(NX, NY, CORE_RADIUS, PITCH)
print(f"Grid: {NX}x{NY}, Fuel channels: {n_fuel}, Reflector: {n_refl}")

# Write DONJON input
# Output goes next to this script, which is decks/Donjon/data -- the
# canonical copy.  tools/link_decks.sh symlinks it into 5.1/Donjon/data,
# so DONJON sees the new deck without a second copy existing.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rbmk_core_3d.don')
with open(OUT, 'w') as f:
    f.write("""* DONJON5 RBMK-1000 3D Core Model (Generated)
* 1661 fuel channels, 25 cm pitch, 7 m active height

LINKED_LIST RBMK RBMK_2 MACRO MACRO2 TRACK SYSTEM FLUX MATEX FLMAP POWER ;
MODULE GEO: MAC: TRIVAT: TRIVAA: FLUD: USPLIT: MACINI: RESINI: FLPOW: GREP: END: ;
REAL Keff ;
PROCEDURE assertS ;

*==============================================================
* GEOMETRY: 3D Cartesian core
*==============================================================
RBMK := GEO: :: CAR3D """ + f"{NX} {NY} {NZ}" + """
          EDIT 2
          X- VOID  X+ VOID 
          Y- VOID  Y+ VOID 
          Z- VOID  Z+ VOID 
          
          MIX
""")
    
    # Write planes: bottom reflector (plane 1), active (planes 2-27), top reflector (plane 28)
    for plane in range(1, NZ + 1):
        f.write(f"          PLANE {plane}\n")
        for j in range(NY):
            row = ' '.join(str(channel_map[i][j]) for i in range(NX))
            f.write(f"{row}\n")
    
    # Mesh - split into multiple lines to avoid overflow
    def format_mesh(values, per_line=15):
        lines = []
        for i in range(0, len(values), per_line):
            chunk = values[i:i+per_line]
            lines.append(' '.join(chunk))
        return '\n          '.join(lines)
    
    mesh_x_vals = [f"{i*PITCH:.2f}" for i in range(NX + 1)]
    mesh_y_vals = [f"{i*PITCH:.2f}" for i in range(NY + 1)]
    mesh_z_vals = [f"{i*PITCH:.2f}" for i in range(NZ + 1)]
    
    f.write(f"""
          MESHX {format_mesh(mesh_x_vals)}
          MESHY {format_mesh(mesh_y_vals)}
          MESHZ {format_mesh(mesh_z_vals)}
          ;
""")
    
    # Macrolib
    f.write("""
*==============================================================
* MACROLIB: 2-group XS - IAEA-3D pattern for RBMK
* Mix 1 = Fuel channel (homogenized, similar to IAEA fuel)
* Mix 2 = Graphite reflector (with absorption like IAEA reflector)
*==============================================================
MACRO := MAC: ::
  EDIT 2 NGRO 2 NMIX 2 NIFI 1
  READ INPUT
* Mix 1: Homogenized RBMK fuel channel
  MIX     1
      DIFFX  1.500E+00  4.000E-01
      TOTAL  3.000E-02  1.000E-01
     NUSIGF  0.000E+00  1.350E-01
   H-FACTOR  0.000E+00  1.350E-01
       SCAT  1 1 0.0  2 2 0.0  2.00E-02
* Mix 2: Graphite reflector (with absorption for diffusion model)
  MIX     2
      DIFFX  2.000E+00  3.000E-01
      TOTAL  4.000E-02  1.000E-02
     NUSIGF  0.000E+00  0.000E+00
   H-FACTOR  0.000E+00  0.000E-00
       SCAT  1 1 0.0  2 2 0.0  4.00E-02
  ;

*==============================================================
* FUEL MAP: Define channel locations
*==============================================================
RBMK_2 MATEX := USPLIT: RBMK :: EDIT 1
  NGRP 2 MAXR 100000 NMIX 2
  NREFL 1 RMIX 2
  NFUEL 1 FMIX 1
  ;

*==============================================================
* MACINI: Initialize macrolib for each unique mixture
*==============================================================
MACRO2 MATEX := MACINI: MATEX MACRO :: EDIT 1 ;

*==============================================================
* RESINI: Create fuel map for FLPOW
*==============================================================
FLMAP MATEX := RESINI: MATEX :: 
      ::: GEO: CAR3D """ + f"{NX} {NY} {NZ}" + """
                EDIT  0
                X- VOID      X+ VOID
                Y- VOID      Y+ VOID
                Z- VOID      Z+ VOID
MIX
""")
    
    # Write planes for FLMAP (same as channel_map but with 0 for reflector)
    for plane in range(1, NZ + 1):
        f.write(f"PLANE {plane}\n")
        for j in range(NY):
            row = ' '.join(str(channel_map[i][j] if channel_map[i][j] == 1 else 0) for i in range(NX))
            f.write(f"{row}\n")
    
    f.write(f"""
                MESHX {format_mesh(mesh_x_vals)}
                MESHY {format_mesh(mesh_y_vals)}
                MESHZ {format_mesh(mesh_z_vals)}
                ;
""")

    f.write("""
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
* POWER: Power distribution (3200 MWth)
*==============================================================
POWER := FLPOW: FLMAP FLUX TRACK MATEX MACRO2
  :: EDIT 10 PTOT 3200.0  PRINT ALL ;

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

print(f"Generated {OUT}")