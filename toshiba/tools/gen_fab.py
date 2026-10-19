"""JLCPCB BOM + CPL from the routed board. Run with python3.12 after jlc_rotations.py.

CPL convention (same as Bouni/kicad-jlcpcb-tools): position = centre of the
soldered pads' bounding box, Y negated, rotation = KiCad rotation + the
correction found by aligning KiCad pads onto JLC's EasyEDA footprint.
"""
import csv
import json
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import circuit  # noqa: E402
from gen_pcb import OX, OY  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(ROOT, "hardware", circuit.PROJECT + ".kicad_pcb")
OUT = os.path.join(ROOT, "production")


def pad_centre(fp):
    pads = [p for p in fp.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    bb = pads[0].GetBoundingBox()
    for p in pads[1:]:
        bb.Merge(p.GetBoundingBox())
    c = bb.GetCenter()
    return pcbnew.ToMM(c.x) - OX, pcbnew.ToMM(c.y) - OY


def main():
    os.makedirs(OUT, exist_ok=True)
    rot = json.load(open(os.path.join(ROOT, "build", "jlc_rotations.json")))
    board = pcbnew.LoadBoard(PCB)
    rows = []
    for fp in sorted(board.GetFootprints(), key=lambda f: (f.GetReference()[0], int(''.join(c for c in f.GetReference() if c.isdigit()) or 0))):
        ref = fp.GetReference()
        x, y = pad_centre(fp)
        r = (fp.GetOrientationDegrees() + rot[ref]["correction"]) % 360
        rows.append([ref, fp.GetValue(), str(fp.GetFPID().GetLibItemName()),
                     "%.4f" % x, "%.4f" % (-y), "%g" % r, "top"])
    with open(os.path.join(OUT, circuit.PROJECT + "_cpl_jlcpcb.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
        w.writerows(rows)

    groups = {}
    for ref, p in circuit.PARTS.items():
        key = (p["lcsc"], p["value"], p["fp"].split(":")[1], p["mpn"])
        groups.setdefault(key, []).append(ref)

    def refkey(r):
        return (r.rstrip("0123456789"), int(''.join(c for c in r if c.isdigit())))

    with open(os.path.join(OUT, circuit.PROJECT + "_bom_jlcpcb.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Quantity", "MPN"])
        for (lcsc, value, fpn, mpn), refs in sorted(groups.items(), key=lambda kv: refkey(sorted(kv[1], key=refkey)[0])):
            refs = sorted(refs, key=refkey)
            w.writerow([value, ",".join(refs), fpn, lcsc, len(refs), mpn])
    print("BOM groups:", len(groups), "| CPL rows:", len(rows))


if __name__ == "__main__":
    main()
