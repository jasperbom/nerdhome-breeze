"""Connect GND pads that the pour could not reach: short 0.3 mm track to a new
GND via. Pads come from a DRC report (unconnected_items). Run with python3.12.

Usage: python3.12 fix_gnd.py <drc.rpt>
"""
import math
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import circuit  # noqa: E402
from stitch import seg_dist  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(ROOT, "hardware", circuit.PROJECT + ".kicad_pcb")
CLR = 0.22
VIA_R = 0.3
TRK_W = 0.3


def mm(v):
    return pcbnew.FromMM(v)


def to_mm(p):
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


def obstacles(board):
    obs = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == "GND" and pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                continue
            bb = pad.GetBoundingBox()
            obs.append(("box", (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                                pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())), pad))
    for t in board.GetTracks():
        if t.GetNetname() == "GND":
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            x, y = to_mm(t.GetPosition())
            obs.append(("seg", (x, y, x, y, pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2), t))
        else:
            a, b = to_mm(t.GetStart()), to_mm(t.GetEnd())
            obs.append(("seg", (a[0], a[1], b[0], b[1], pcbnew.ToMM(t.GetWidth()) / 2), t))
    return obs


def box_dist(px, py, b):
    dx = max(b[0] - px, 0, px - b[2])
    dy = max(b[1] - py, 0, py - b[3])
    return math.hypot(dx, dy)


def seg_box_clear(ax, ay, bx, by, half, b):
    # sample the segment; boxes are small so 0.05 mm steps are plenty
    n = max(2, int(math.hypot(bx - ax, by - ay) / 0.05))
    for i in range(n + 1):
        t = i / n
        if box_dist(ax + t * (bx - ax), ay + t * (by - ay), b) < half + CLR:
            return False
    return True


def seg_seg_clear(ax, ay, bx, by, half, s):
    n = max(2, int(math.hypot(bx - ax, by - ay) / 0.05))
    for i in range(n + 1):
        t = i / n
        if seg_dist(ax + t * (bx - ax), ay + t * (by - ay), s[0], s[1], s[2], s[3]) < half + s[4] + CLR:
            return False
    return True


def stranded_pads(board):
    """GND SMD pads sitting in a top-layer pour island that has no via and no
    through-hole pad (so the island never reaches the bottom plane)."""
    out = set()
    vias = [t.GetPosition() for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND"]
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == "GND"]
    for z in board.Zones():
        if z.GetNetname() != "GND" or z.GetLayer() != pcbnew.F_Cu:
            continue
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(polys.OutlineCount()):
            ol = polys.Outline(i)
            if any(ol.PointInside(v) for v in vias):
                continue
            inside = [p for p in pads if p.IsOnLayer(pcbnew.F_Cu) and ol.PointInside(p.GetPosition())]
            if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in inside):
                continue
            # one escape per island is enough
            if inside:
                p = inside[0]
                out.add((p.GetNumber(), p.GetParentFootprint().GetReference()))
    return out


def main(rpt):
    board = pcbnew.LoadBoard(PCB)
    gnd = board.FindNet("GND")
    txt = open(rpt).read()
    targets = set(re.findall(r"Pad (\S+) \[GND\] of (\S+) on", txt))
    if os.environ.get("STRANDED"):
        targets |= stranded_pads(board)
    edge = board.GetBoardEdgesBoundingBox()
    ex0, ey0 = pcbnew.ToMM(edge.GetLeft()) + 0.6, pcbnew.ToMM(edge.GetTop()) + 0.6
    ex1, ey1 = pcbnew.ToMM(edge.GetRight()) - 0.6, pcbnew.ToMM(edge.GetBottom()) - 0.6
    u1 = board.FindFootprintByReference("U1").GetBoundingBox(False)
    mod = (pcbnew.ToMM(u1.GetLeft()), pcbnew.ToMM(u1.GetTop()), pcbnew.ToMM(u1.GetRight()), pcbnew.ToMM(u1.GetBottom()))
    gvias = [to_mm(t.GetPosition()) for t in board.GetTracks()
             if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND"]
    obs = obstacles(board)
    bfill = [z.GetFilledPolysList(pcbnew.B_Cu) for z in board.Zones()
             if z.GetNetname() == "GND" and z.GetLayer() == pcbnew.B_Cu]

    def on_bottom_plane(vx, vy):
        pts = [(vx, vy)] + [(vx + 0.31 * math.cos(a), vy + 0.31 * math.sin(a))
                            for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
        return all(any(f.Contains(pcbnew.VECTOR2I(mm(x), mm(y))) for f in bfill) for x, y in pts)

    for num, ref in sorted(targets):
        fp = board.FindFootprintByReference(ref)
        pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
        px, py = to_mm(pad.GetPosition())
        best = None
        for rad in (0.9, 1.1, 1.3, 1.6, 2.0, 2.5):
            for k in range(24):
                a = 2 * math.pi * k / 24
                vx, vy = px + rad * math.cos(a), py + rad * math.sin(a)
                if not (ex0 < vx < ex1 and ey0 < vy < ey1):
                    continue
                if ref != "U1" and mod[0] - 0.4 < vx < mod[2] + 0.4 and mod[1] - 0.4 < vy < mod[3] + 0.4:
                    continue
                if ref == "U1" and mod[0] + 0.3 < vx < mod[2] - 0.3 and mod[1] + 0.3 < vy < mod[3] - 0.3:
                    continue
                if any(math.hypot(vx - gx, vy - gy) < 0.9 for gx, gy in gvias):
                    continue
                if not on_bottom_plane(vx, vy):
                    continue
                ok = True
                for kind, g, item in obs:
                    if item is pad:
                        continue
                    if kind == "box":
                        if box_dist(vx, vy, g) < VIA_R + CLR or not seg_box_clear(px, py, vx, vy, TRK_W / 2, g):
                            ok = False
                            break
                    else:
                        if seg_dist(vx, vy, g[0], g[1], g[2], g[3]) < VIA_R + g[4] + CLR or \
                                not seg_seg_clear(px, py, vx, vy, TRK_W / 2, g):
                            ok = False
                            break
                if ok:
                    best = (vx, vy)
                    break
            if best:
                break
        if not best:
            print("no spot for", ref, num)
            continue
        vx, vy = best
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pcbnew.VECTOR2I(mm(px), mm(py)))
        tr.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
        tr.SetWidth(mm(TRK_W))
        tr.SetLayer(pad.GetPrincipalLayer())
        tr.SetNet(gnd)
        board.Add(tr)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(gnd)
        board.Add(v)
        gvias.append((vx, vy))
        print("connected %s.%s via (%.2f, %.2f)" % (ref, num, vx - 100, vy - 100))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)


if __name__ == "__main__":
    main(sys.argv[1])
