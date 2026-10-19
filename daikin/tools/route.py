"""Autoroute the board with Freerouting and fill zones.

Usage: python3.12 route.py <freerouting.jar> [passes]
"""
import os
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import circuit  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HW = os.path.join(ROOT, "hardware")
PCB = os.path.join(HW, circuit.PROJECT + ".kicad_pcb")
BUILD = os.path.join(ROOT, "build")


def main(jar, passes=40):
    os.makedirs(BUILD, exist_ok=True)
    dsn = os.path.join(BUILD, "board.dsn")
    ses = os.path.join(BUILD, "board.ses")
    board = pcbnew.LoadBoard(PCB)
    # remove previous routing (keep the hand-placed EPAD vias, they are locked)
    for t in list(board.GetTracks()):
        if not t.IsLocked():
            board.Remove(t)
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    if os.path.exists(ses):
        os.remove(ses)
    cmd = ["java", "-jar", jar, "-de", dsn, "-do", ses, "-mp", str(passes),
           "--gui.enabled=false", "-mt", "1"]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1500)
    log = (r.stdout + r.stderr).splitlines()
    for line in log[-25:]:
        if "Picked up" not in line:
            print(line)
    if not os.path.exists(ses):
        raise SystemExit("freerouting produced no session file")
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit("SES import failed")
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(PCB)
    print("routed + filled ->", PCB)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40)
