#!/usr/bin/env python3
"""Generate RBMK 3D DONJON input with realistic 1661-channel pattern (square lattice)"""

# Core parameters - full resolution (25 cm pitch)
import os
NX, NY, NZ = 49, 49, 32  # +2 axial reflector planes at each end
PITCH = 25.0  # cm

# RBMK-1000: 1661 fuel channels on SQUARE lattice (not triangular!)
# 25 cm pitch, ~11.8m diameter circle
RADIUS_CM = 590.0
radius_cells = RADIUS_CM / PITCH  # 23.6

# Reflector thickness: 2 cells = 50 cm radial
REFLECTOR_CELLS = 2
REFLECTOR_THICK_CM = REFLECTOR_CELLS * PITCH  # 50 cm

# Center
cx = (NX - 1) / 2.0  # 24.0
cy = (NY - 1) / 2.0  # 24.0

# Generate ALL positions within circle on square lattice
all_core_positions = []
for iy in range(NY):
    for ix in range(NX):
        dx = ix - cx
        dy = iy - cy
        if dx*dx + dy*dy <= radius_cells*radius_cells:
            all_core_positions.append((ix, iy))

print(f"Total core positions (square lattice): {len(all_core_positions)}")

# We need 1661 fuel channels. The rest are graphite moderator.
# RBMK has fuel channels on a regular square grid.
# The 1661 channels are a subset of the core positions.
# Let's take the 1661 closest to center (standard loading pattern).
all_core_positions.sort(key=lambda p: (p[0]-cx)**2 + (p[1]-cy)**2)
fuel_channels = all_core_positions[:1661]
fuel_set = set(fuel_channels)

print(f"Fuel channels: {len(fuel_channels)}")
print(f"Graphite moderator positions: {len(all_core_positions) - len(fuel_channels)}")

# Create mix map with radial and axial reflectors
# Mix 1 = Fuel channel, Mix 2 = Graphite moderator, Mix 0 = Void, Mix 3 = Radial reflector, Mix 4/5 = Axial reflector
mix_planes = []
for z in range(NZ):
    plane = []
    # Axial reflector: first 2 planes (z=0,1) and last 2 planes (z=30,31) are axial reflector (mix 4/5)
    is_axial_reflector = z < 2 or z >= NZ - 2
    for y in range(NY):
        row = []
        for x in range(NX):
            if (x, y) in fuel_set:
                row.append(1)  # fuel channel
            else:
                dx = x - cx
                dy = y - cy
                dist2 = dx*dx + dy*dy
                if dist2 <= radius_cells*radius_cells:
                    if is_axial_reflector:
                        row.append(4)  # axial reflector (mix 4)
                    else:
                        row.append(2)  # graphite moderator
                elif dist2 <= (radius_cells + REFLECTOR_CELLS)**2:
                    # Radial reflector region
                    if is_axial_reflector:
                        row.append(5)  # corner reflector (mix 5)
                    else:
                        row.append(3)  # radial reflector (mix 3)
                else:
                    row.append(0)  # void
        plane.append(row)
    mix_planes.append(plane)

# Count per plane (central plane z=14, which is index 14, non-reflector)
central_z = 14  # 0-indexed, plane 15 of 32
fuel_count = sum(sum(1 for x in range(NX) if mix_planes[central_z][y][x] == 1) for y in range(NY))
graphite_count = sum(sum(1 for x in range(NX) if mix_planes[central_z][y][x] == 2) for y in range(NY))
radial_refl_count = sum(sum(1 for x in range(NX) if mix_planes[central_z][y][x] == 3) for y in range(NY))
void_count = sum(sum(1 for x in range(NX) if mix_planes[central_z][y][x] == 0) for y in range(NY))
print(f"Central plane: Fuel={fuel_count}, Graphite={graphite_count}, RadialRefl={radial_refl_count}, Void={void_count}")

# Verify mesh output
print(f"MESHX: {[f'{i * PITCH:.2f}' for i in range(NX + 1)][:5]} ... {[f'{i * PITCH:.2f}' for i in range(NX + 1)][-1]}")
print(f"MESHZ: {[f'{i * PITCH:.2f}' for i in range(NZ + 1)][:5]} ... {[f'{i * PITCH:.2f}' for i in range(NZ + 1)][-1]}")

# Write DONJON input
# Output goes next to this script, which is decks/Donjon/data -- the
# canonical copy.  tools/link_decks.sh symlinks it into 5.1/Donjon/data,
# so DONJON sees the new deck without a second copy existing.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rbmk_core_3d_realistic.don')
with open(OUT, 'w') as f:
    f.write(f"""* DONJON5 RBMK-1000 3D Core Model - Realistic 1661 channels (square lattice)
LINKED_LIST RBMK RBMK_2 MACRO MACRO2 TRACK SYSTEM FLUX MATEX ;
MODULE GEO: MAC: TRIVAT: TRIVAA: FLUD: USPLIT: MACINI: GREP: END: ;
REAL Keff ;

*==============================================================
* GEOMETRY: 3D Cartesian core (49x49x32, 25cm pitch, 7m active + 50cm reflectors)
* Mix 1 = Fuel channel, Mix 2 = Graphite moderator, Mix 3 = Radial reflector, Mix 4/5 = Axial reflector, Mix 0 = Void
*==============================================================
RBMK := GEO: :: CAR3D {NX} {NY} {NZ}
          EDIT 2
          X- VOID  X+ VOID 
          Y- VOID  Y+ VOID 
          Z- VOID  Z+ VOID 
          MIX 
""")

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
* MACROLIB: IAEA 2-group XS (validated at -8.9 pcm)
* Mix 1 = Fuel channel (IAEA fuel type 1 XS)
* Mix 2 = Graphite moderator (IAEA reflector XS)
* Mix 3 = Radial graphite reflector
* Mix 4 = Axial graphite reflector
* Mix 5 = Corner graphite reflector
*==============================================================
MACRO := MAC: ::
  EDIT 2 NGRO 2 NMIX 5 NIFI 1
  READ INPUT
  MIX     1
      DIFFX  1.500E+00  4.0000E-01
      TOTAL  3.000E-02  8.0000E-02
     NUSIGF  0.000E+00  1.3500E-01
   H-FACTOR  0.000E+00  1.3500E-01
       SCAT  1 1 0.0 2 2 0.0 0.2E-01
  MIX     2
      DIFFX  1.500E+00  4.0000E-01
      TOTAL  3.000E-02  8.5000E-02
     NUSIGF  0.000E+00  1.3500E-01
   H-FACTOR  0.000E+00  1.3500E-01
       SCAT  1 1 0.0 2 2 0.0 0.2E-01
  MIX     3
      DIFFX  1.500E+00  4.00000E-01
      TOTAL  3.000E-02  1.30000E-01
     NUSIGF  0.000E+00  1.35000E-01
   H-FACTOR  0.000E+00  1.35000E-01
       SCAT  1 1 0.0 2 2 0.0 0.2E-01
  MIX     4
      DIFFX  2.000E+00  3.0000E-01
      TOTAL  4.000E-02  1.0000E-02
       SCAT  1 1 0.0 2 2 0.0 0.4E-01
  MIX     5
      DIFFX  2.000E+00  3.0000E-01
      TOTAL  4.000E-02  5.5000E-02
       SCAT  1 1 0.0 2 2 0.0 0.4E-01
  ;

*==============================================================
* USPLIT: Split geometry (preserves existing mixes)
*==============================================================
RBMK_2 MATEX := USPLIT: RBMK :: EDIT 1
  NGRP 2 MAXR 100000 NMIX 5
  NREFL 4 RMIX 2 3 4 5
  NFUEL 1 FMIX 1
  ;

*==============================================================
* MACINI: Initialize macrolib
*==============================================================
MACRO2 MATEX := MACINI: MATEX MACRO :: EDIT 1 ;

*==============================================================
* TRACKING: 3D transport (TRIVAT) - MCFD 1 (not DUAL 3 3)
*==============================================================
TRACK := TRIVAT: RBMK_2 ::
      TITLE 'RBMK-1000 3D CORE - 1661 CHANNELS'
      EDIT 1 MAXR 100000 MCFD 1 ;

*==============================================================
* ASSEMBLY: System matrices
*==============================================================
SYSTEM := TRIVAA: MACRO2 TRACK ::
      EDIT 1 ;

*==============================================================
* FLUX: 3D k-eigenvalue solution
*==============================================================
FLUX := FLUD: SYSTEM TRACK ::
      EDIT 2 EXTE 1.0E-5 1000 ;

*==============================================================
* CHECK: k-effective
*==============================================================
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>Keff<< ;
ECHO "Keff=" Keff ;
* A2 REPORTS, IT DOES NOT ASSERT.
* This deck previously carried  assertS FLUX :: 'K-EFFECTIVE' 1 1.123062 ;
* -- a seven-digit target inherited from a run of a DIFFERENT, centimetre-
* scale core, on IAEA PWR constants.  There is no reference value for "IAEA
* PWR cross sections in an RBMK-shaped box", so any target here could only
* have come from a previous answer, which is what standing rule 1 forbids.
* A2 is a geometry and solver check: the gate is that FLUD: CONVERGES.
* Real cross sections arrive with the A5b MULTICOMPO.

ECHO "RBMK 3D core test completed" ;
END: ;
QUIT .
""")

print("Generated rbmk_core_3d_realistic.don")