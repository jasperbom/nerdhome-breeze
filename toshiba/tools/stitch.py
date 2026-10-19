"""Add GND stitching vias where they fit, refill zones.

A candidate via is accepted when it keeps >= CLR to every non-GND pad, track and
via on both layers, stays clear of the board edge, is not under the module or
inside a connector's pad area, and lands inside the filled GND pour on both
layers. Run with python3.12 (KiCad).
"""
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import circuit  # noqa: E402
from gen_pcb import OX, OY, W, H, PLACE  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(ROOT, "hardware", circuit.PROJECT + ".kicad_pcb")

VIA_D, VIA_DRILL = 0.6, 0.3
CLR = 0.25          # extra margin over the 0.2 mm zone clearance
EDGE = 0.8
STEP = 1.0


def mm(v):
    return pcbnew.FromMM(v)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def main():
    board = pcbnew.LoadBoard(PCB)
    gnd = board.FindNet("GND")
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    obst = []   # (kind, geometry, half-width)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == "GND":
                continue
            bb = pad.GetBoundingBox()
            obst.append(("box", (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                                 pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))))
        if fp.GetReference() in ("U1",):
            # keep vias out from under the module (only the EPAD vias live there)
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if hasattr(fp, "GetCourtyard") else fp.GetBoundingBox(False)
            obst.append(("keepout", (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                                     pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))))
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            obst.append(("circle", (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)), pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2,
                         t.GetNetname()))
        else:
            if t.GetNetname() == "GND":
                continue
            a, b = t.GetStart(), t.GetEnd()
            obst.append(("seg", (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y), pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)),
                         pcbnew.ToMM(t.GetWidth()) / 2))
    # no stitching vias through the back-side silkscreen text
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.B_SilkS:
            bb = d.GetBoundingBox()
            obst.append(("keepout", (pcbnew.ToMM(bb.GetLeft()) - 0.15, pcbnew.ToMM(bb.GetTop()) - 0.15,
                                     pcbnew.ToMM(bb.GetRight()) + 0.15, pcbnew.ToMM(bb.GetBottom()) + 0.15)))
    # NPTH holes
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                p = pad.GetPosition()
                obst.append(("circle", (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)), pcbnew.ToMM(pad.GetDrillSize().x) / 2, "NPTH"))

    zones = {z.GetLayer(): z for z in board.Zones() if z.GetNetname() == "GND"}
    r = VIA_D / 2
    added = []
    y = OY + EDGE
    while y <= OY + H - EDGE:
        x = OX + EDGE
        while x <= OX + W - EDGE:
            ok = True
            for o in obst:
                kind, g = o[0], o[1]
                if kind in ("box", "keepout"):
                    m = r + (CLR if kind == "box" else 0.1)
                    if g[0] - m < x < g[2] + m and g[1] - m < y < g[3] + m:
                        ok = False
                        break
                elif kind == "circle":
                    d = math.hypot(x - g[0], y - g[1])
                    lim = 1.5 if o[3] == "GND" else r + o[2] + CLR
                    if d < lim:
                        ok = False
                        break
                elif kind == "seg":
                    if seg_dist(x, y, *g) < r + o[2] + CLR:
                        ok = False
                        break
            if ok:
                vp = pcbnew.VECTOR2I(mm(x), mm(y))
                for z in zones.values():
                    if not z.GetFilledPolysList(z.GetLayer()).Contains(vp):
                        ok = False
                        break
            if ok:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                v.SetWidth(mm(VIA_D))
                v.SetDrill(mm(VIA_DRILL))
                v.SetNet(gnd)
                board.Add(v)
                added.append((x, y))
                obst.append(("circle", (x, y), r, "GND"))
            x += STEP
        y += STEP
    filler.Fill(board.Zones())
    board.Save(PCB)
    print("stitching vias added:", len(added))


if __name__ == "__main__":
    main()
