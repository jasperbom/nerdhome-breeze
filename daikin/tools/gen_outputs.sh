#!/usr/bin/env bash
# Manufacturing + documentation outputs from the routed board.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3.12
export KICAD9_3DMODEL_DIR=${KICAD9_3DMODEL_DIR:-/usr/share/kicad/3dmodels}

$PY tools/jlc_rotations.py
$PY tools/gen_fab.py

rm -rf build/gerbers && mkdir -p build/gerbers production docs
kicad-cli pcb export gerbers -l F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  --subtract-soldermask -o build/gerbers/ hardware/daikin-c6.kicad_pcb >/dev/null
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th \
  -o build/gerbers/ hardware/daikin-c6.kicad_pcb >/dev/null
rm -f production/daikin-c6_gerbers_jlcpcb.zip
(cd build/gerbers && zip -q ../../production/daikin-c6_gerbers_jlcpcb.zip ./*)

kicad-cli sch export pdf -o docs/daikin-c6_schematic.pdf hardware/daikin-c6.kicad_sch >/dev/null
kicad-cli pcb export pdf --mode-single -l F.Fab,Edge.Cuts,F.Silkscreen --sketch-pads-on-fab-layers \
  --include-border-title -o docs/daikin-c6_assembly.pdf hardware/daikin-c6.kicad_pcb >/dev/null

R="xvfb-run -a kicad-cli pcb render --background opaque --quality high"
$R --rotate "-40,0,-25" --perspective --zoom 0.9 -w 1400 -h 1150 -o docs/render_iso.png hardware/daikin-c6.kicad_pcb >/dev/null
$R --side top -w 1000 -h 1300 -o docs/render_top.png hardware/daikin-c6.kicad_pcb >/dev/null
$R --side bottom -w 1000 -h 1300 -o docs/render_bottom.png hardware/daikin-c6.kicad_pcb >/dev/null
ls -la production docs
