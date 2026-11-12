#!/bin/bash
# Card #47 run 1 (copied from the session scratchpad; paths are that session's): members K, VA, CA, one at a time from the Fig. 11 nominal.
# DONJON steps run sequentially here; each newton B4 is launched in the background as soon as its dump exists.
cd /home/wilkie/code/RBMK
SP=/tmp/claude-1000/-home-wilkie-code-RBMK/14e22cf9-6e1b-4020-9553-0798a9bf74a9/scratchpad/scan
D=/home/wilkie/code/RBMK/sources/derived
G=$D/insag7_fig_II9_t0_axburn_fit_cB.txt
clean(){ for v in $(env | grep ^U4_ | cut -d= -f1); do unset $v; done; }
memok(){ until [ $(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo) -ge 25 ]; do echo "waiting for memory"; sleep 120; done; }

member(){  # $1 tag  $2 extra U4_ env (space-separated)  $3 description for headers
  local tag=$1 extra="$2" desc="$3"
  local F=$D/insag7_fig_II9_t0_axburn_fit_f11$tag.txt PC=$D/a8_fit_pchan_f11$tag.txt
  echo "=== member $tag: $extra   $(date +%T)"
  if [ ! -f $F ]; then
    ( clean; export U4_CPSB=1 U4_VOIDB=1 U4_RODTYPE=fig11 $extra
      python3 tools/a8_axinvert.py $SP/fit_$tag 8 6 $G ) || { echo "FAIL fit $tag"; return 1; }
    [ -f $SP/fit_$tag/g_best.txt ] || { echo "FAIL fit $tag: no g_best"; return 1; }
    local best=$(grep " rms " $SP/fit_$tag/log.txt | awk '{for(i=1;i<=NF;i++){if($i=="rms")r=$(i+1); if($i=="k")k=$(i+1)}; print r, k}' | sort -n | head -1)
    local st=$(grep "^start" $SP/fit_$tag/log.txt | tail -1 | awk '{for(i=1;i<=NF;i++) if($i=="rms") print $(i+1)}')
    local ns=$(grep -c " rms " $SP/fit_$tag/log.txt)
    { echo "# B5 threshold scan (card #47, member $tag): the Fig. II-9 t=0 inversion on the re-typed map with $desc (U4_RODTYPE=fig11, U4_CPSB=1 U4_VOIDB=1 unless overridden: $extra)."
      echo "# tools/a8_axinvert.py, N=6, start from insag7_fig_II9_t0_axburn_fit_cB.txt (rms $st on this build); rms ${best% *}, k ${best#* }, $ns solves. Bottom bundle first."
      cat $SP/fit_$tag/g_best.txt; } > $F
    echo "fit $tag: rms/k $best"
  fi
  # POWER-CHAN of the fitted static state
  local N=$(cd decks/Donjon/data && clean && env U4_DEV=1 U4_RODS=wat U4_PBUND=1 U4_CPSB=1 U4_VOIDB=1 U4_RODTYPE=fig11 $extra U4_AXBURN=file:$F python3 gen_rbmk_unit4.py | head -1 | sed 's/.*wrote decks\/Donjon\/data\///')
  tools/link_decks.sh >/dev/null
  rm -f 5.1/Donjon/Linux_aarch64/$N.result
  (cd 5.1/Donjon && ./rdonjon $N >/dev/null 2>&1)
  local RES=5.1/Donjon/Linux_aarch64/$N.result
  [ -f $RES ] || { echo "FAIL static $tag"; return 1; }
  echo "static $tag: $(grep -o 'KEFF *[0-9.]*e[-+][0-9]*' $RES | tail -1)"
  { echo "# Channel powers (kW, channel order) of the static device-model core in the INSAG-7 Fig. II-9 fitted state,"
    echo "# card #47 member $tag ($desc): U4_DEV=1 U4_RODS=wat U4_RODTYPE=fig11 U4_CPSB=1 U4_VOIDB=1 overridden by: $extra,"
    echo "# U4_AXBURN=file: $(basename $F). From its POWER-CHAN block; U4_FLOW=prop uses only the ratios."
    awk "/CONTENT OF BLOCK 'POWER-CHAN/{p=1;print;next} p&&/CONTENT OF BLOCK|DRVUTL|LEAVING/{exit} p" $RES; } > $PC
  # band-B deck and dump
  local S=$(cd decks/Donjon/data && clean && . /tmp/claude-1000/-home-wilkie-code-RBMK/14e22cf9-6e1b-4020-9553-0798a9bf74a9/scratchpad/p44/envB.sh && env U4_RODTYPE=fig11 $extra U4_PCHAN=$PC U4_AXBURN=file:$F python3 gen_rbmk_unit4.py | head -1 | sed 's/.*wrote decks\/Donjon\/data\///; s/\.don.*//')
  echo "STEM $tag $S"
  ( clean; python3 tools/tierb_kinref.py $S --dual --t0only ) > $SP/t0_$tag.log 2>&1
  [ -f tierb/xs/${S}_tbd0/fmap0.asc ] || { echo "FAIL t0 $tag"; return 1; }
  memok
  ( cd tierb/RBMKCore.jl && clean && JULIA_CUDA_HARD_MEMORY_LIMIT=8GiB B4_TH=newton B4_CLAMP=1 setsid nohup julia --project=. -t 5 test/b4_coupled.jl $S /home/wilkie/code/RBMK/tierb/xs/${S}_tbd0 700 0.01 > $SP/b4_$tag.log 2>&1 & echo $! > $SP/pid_$tag )
  echo "newton $tag launched pid $(cat $SP/pid_$tag)  $(date +%T)"
  # static AZ-5 ramp of the member (Karpan's was run in #44)
  if [ "$tag" != kv ]; then
    ( clean; export U4_CPSB=1 U4_VOIDB=1 A8_USP=0 U4_RODTYPE=fig11 $extra U4_AXBURN=file:$F; python3 tools/a8_ramp.py 0 10 25 40 80 160 240 280 ) > $SP/ramp_$tag.log 2>&1
    echo "ramp $tag:"; cat $SP/ramp_$tag.log
  fi
}

member kv "U4_RODDEPTH=$D/karpan_vk_fig3_roddepth.txt" "Karpan VK Fig. 3 rod depths"
member vA "U4_VOIDB=0" "void-worth bracket A (DRAGON void worth, no OpenMC correction)"
member cA "U4_CPSB=0" "CPS-worth bracket A (DRAGON CPS worths, no OpenMC correction)"
echo "=== DONJON part done $(date +%T)"
