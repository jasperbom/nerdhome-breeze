#!/usr/bin/env bash
# Full board build: schematic -> netlist -> placement -> autoroute -> GND stitching -> DRC
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3.12
JAR=build/freerouting-2.1.0.jar
PASSES=${PASSES:-40}

python3 tools/gen_footprints.py
python3 tools/gen_schematic.py
python3 tools/gen_project.py
kicad-cli sch erc --severity-all --exit-code-violations -o build/erc.rpt hardware/toshiba-c6.kicad_sch
kicad-cli sch export netlist --format kicadsexpr -o build/toshiba-c6.net hardware/toshiba-c6.kicad_sch
python3 tools/check_netlist.py build/toshiba-c6.net
$PY tools/gen_pcb.py build/toshiba-c6.net
$PY tools/route.py "$JAR" "$PASSES"
$PY tools/stitch.py
(cd hardware && kicad-cli pcb drc --severity-all --schematic-parity -o ../build/drc_pre.rpt toshiba-c6.kicad_pcb >/dev/null) || true
$PY tools/fix_gnd.py build/drc_pre.rpt
(cd hardware && kicad-cli pcb drc --severity-all --schematic-parity -o ../build/drc.rpt toshiba-c6.kicad_pcb >/dev/null) || true
grep -E "^\*\* Found" build/drc.rpt
