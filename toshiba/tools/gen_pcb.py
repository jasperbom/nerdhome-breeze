"""Build hardware/toshiba-c6.kicad_pcb (placement, outline, zones) from the
schematic netlist. Run with KiCad's python (python3.12).

Usage: python3.12 gen_pcb.py <netlist.net>
"""
import os
import re
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import circuit  # noqa: E402
from gen_schematic import nid  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HW = os.path.join(ROOT, "hardware")
PCB = os.path.join(HW, circuit.PROJECT + ".kicad_pcb")
KFP = "/usr/share/kicad/footprints"

OX, OY = 100.0, 100.0        # board origin on the page
W, H = 24.0, 34.0            # board size (mm)
R_CORNER = 1.0

# ref: (x, y, rotation_deg) in board-local mm, y down, rotation CCW
PLACE = {
    "U1": (12.0, 7.6, 0),
    "J1": (13.5, 25.8, 0),       # pin 1 position; cable opening at bottom edge
    "J2": (5.4, 30.35, 0),       # USB-C, opening at bottom edge
    # left column
    "C2": (2.0, 3.6, 90),
    "C3": (4.2, 5.3, 90),
    "R1": (2.0, 8.0, 90),
    "C5": (4.2, 9.4, 90),
    # power
    "U2": (7.0, 16.5, 0),
    "C4": (10.0, 15.4, 90),
    "C1": (4.0, 19.8, 90),
    "D2": (1.9, 19.6, 270),
    "D1": (8.8, 20.6, 0),
    "R8": (3.0, 23.6, 180),
    "R9": (8.4, 22.4, 0),
    # level shifters
    "Q1": (13.4, 16.0, 0),
    "Q2": (18.4, 16.0, 0),
    "R5": (12.3, 18.7, 0),
    "R3": (15.0, 18.7, 0),
    "R6": (17.3, 18.7, 0),
    "R4": (20.0, 18.7, 0),
    "R2": (15.8, 14.6, 90),
    # right column
    "SW1": (21.6, 3.6, 90),
    "R7": (20.4, 8.2, 0),
    "D3": (22.6, 9.0, 90),
}


# GND escapes placed before routing: (ref, pad, via_x, via_y) in board-local mm.
# Without these the autorouter tends to box in a few GND pads with signal traces.
PRE_VIAS = [
    ("U2", "2", 4.65, 16.5),      # LDO GND (middle pin between VIN and EN)
    ("C4", "2", 11.1, 14.4),      # LDO output cap GND
    ("U1", "50", 18.95, 1.65),    # module top-right GND corner pad
    ("U1", "51", 18.95, 13.55),   # module bottom-right GND corner pad
    ("C3", "2", 4.2, 3.8),        # decoupling cap GND, short path to the plane
    ("R8", "2", 1.3, 23.6),       # CC1 pull-down
]
# extra locked GND tracks: (ref, pad, x, y) -> straight track from pad to point
PRE_TRACKS = [
    ("J2", "A12", 9.72, 26.6),    # USB-C GND pins to the shell's through-hole tabs
    ("J2", "A1", 1.08, 26.6),
]


# back-side silkscreen: (text, y, size)
BACK_TEXT = [               # rows chosen to stay clear of the module's EPAD vias (y 5.6/7.6/9.6)
    ("toshiba-c6 v1.0", 2.3, 1.0),
    ("by Jasper Bom", 3.9, 0.8),
    ("ESP32-C6 / ESPHome", 6.6, 0.8),
    ("CN22 1=RX 2=GND 3=5V 4=TX", 8.6, 0.8),
    ("GPIO19=TX GPIO20=RX 8E1", 10.6, 0.8),
    ("NO USB WHILE ON THE AC", 12.2, 0.8),
    ("SW1 = BOOT  D3 = LED", 13.8, 0.8),
]


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def read_netlist(path):
    t = open(path).read()
    t = t[t.find("(nets"):]
    padnet = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)', t, re.S):
        for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
            padnet[(ref, pin)] = m.group(1)
    return padnet


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(HW, lib + ".pretty") if lib == circuit.PROJECT else os.path.join(KFP, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("footprint not found: " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def add_outline(board):
    """Rounded-rectangle Edge.Cuts."""
    r = R_CORNER

    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(x1, y1))
        s.SetEnd(pt(x2, y2))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.05))
        board.Add(s)

    def arc(cx, cy, sx, sy, ang):
        a = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        a.SetCenter(pt(cx, cy))
        a.SetStart(pt(sx, sy))
        a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
        a.SetLayer(pcbnew.Edge_Cuts)
        a.SetWidth(mm(0.05))
        board.Add(a)

    seg(r, 0, W - r, 0)
    seg(W, r, W, H - r)
    seg(W - r, H, r, H)
    seg(0, H - r, 0, r)
    arc(W - r, r, W - r, 0, 90)
    arc(W - r, H - r, W, H - r, 90)
    arc(r, H - r, r, H, 90)
    arc(r, r, 0, r, 90)


def add_zone(board, net, layer, inset=0.0, prio=0):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(net.GetNetCode())
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(0.2))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((inset, inset), (W - inset, inset), (W - inset, H - inset), (inset, H - inset)):
        ol.Append(mm(OX + x), mm(OY + y))
    board.Add(z)
    return z


def add_edge_keepouts(board, w=0.45):
    """Track/via keepout strips along the board edge so the autorouter keeps the
    JLCPCB copper-to-edge clearance (it only knows the default clearance)."""
    for x0, y0, x1, y1 in ((0, 0, W, w), (0, H - w, W, H), (0, 0, w, H), (W - w, 0, W, H)):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu)
        ls.AddLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(mm(OX + x), mm(OY + y))
        z.SetZoneName("edge_keepout")
        board.Add(z)


def add_text(board, text, x, y, size=0.8, layer=pcbnew.F_SilkS, rot=0, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(max(0.1, size * 0.15)))
    t.SetTextAngleDegrees(rot)
    if mirror:
        t.SetMirrored(True)
    board.Add(t)
    return t


def build(netlist_path):
    padnet = read_netlist(netlist_path)
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)

    nets = {}
    for name in sorted(set(padnet.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    for ref, part in circuit.PARTS.items():
        fp = load_fp(part["fp"])
        fp.SetReference(ref)
        fp.SetValue(part["value"])
        for k in ("LCSC", "MPN"):
            f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldId(), k)
            f.SetText(part[k.lower()])
            f.SetVisible(False)
            f.SetLayer(pcbnew.F_Fab)
            fp.AddField(f)
        fp.SetPath(pcbnew.KIID_PATH("/" + nid("sym/" + ref)))
        fp.SetSheetname("Root")
        fp.SetSheetfile(circuit.PROJECT + ".kicad_sch")
        x, y, rot = PLACE[ref]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            n = padnet.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(nets[n])
        # tiny board: references live on the fab layer (assembly drawing), not on silk
        r = fp.Reference()
        r.SetLayer(pcbnew.F_Fab if not fp.IsFlipped() else pcbnew.B_Fab)
        r.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
        r.SetTextThickness(mm(0.1))
        r.SetPosition(fp.GetPosition())
        r.SetVisible(False)               # the fab layer already carries ${REFERENCE}
        fp.Value().SetVisible(False)      # values clutter a 24 mm board; see BOM
        board.Add(fp)
        # connector silk lines that would sit on/over the board edge are dropped
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() == pcbnew.F_SilkS and isinstance(item, pcbnew.PCB_SHAPE):
                bb = item.GetBoundingBox()
                if pcbnew.ToMM(bb.GetBottom()) > OY + H - 0.25 or pcbnew.ToMM(bb.GetTop()) < OY + 0.25:
                    fp.Remove(item)

    add_outline(board)
    add_edge_keepouts(board)
    gnd = nets["GND"]
    add_zone(board, gnd, pcbnew.F_Cu)
    add_zone(board, gnd, pcbnew.B_Cu)

    # thermal / ground vias in the module EPAD (centre + 4 corners of the 3x3 pad array)
    ux, uy, _ = PLACE["U1"]
    for dx, dy in ((0, 0), (-1.975, -1.975), (1.975, -1.975), (-1.975, 1.975), (1.975, 1.975)):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pt(ux + dx, uy + dy))
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(gnd)
        v.SetLocked(True)
        board.Add(v)

    for ref, num, vx, vy in PRE_VIAS:
        fp = board.FindFootprintByReference(ref)
        pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
        assert pad.GetNetname() == "GND", (ref, num, pad.GetNetname())
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pad.GetPosition())
        tr.SetEnd(pt(vx, vy))
        tr.SetWidth(mm(0.3))
        tr.SetLayer(pcbnew.F_Cu)
        tr.SetNet(gnd)
        tr.SetLocked(True)
        board.Add(tr)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pt(vx, vy))
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(gnd)
        v.SetLocked(True)
        board.Add(v)

    for ref, num, x, y in PRE_TRACKS:
        fp = board.FindFootprintByReference(ref)
        pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
        assert pad.GetNetname() == "GND", (ref, num, pad.GetNetname())
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pad.GetPosition())
        tr.SetEnd(pt(x, y))
        tr.SetWidth(mm(0.3))
        tr.SetLayer(pcbnew.F_Cu)
        tr.SetNet(gnd)
        tr.SetLocked(True)
        board.Add(tr)

    # silkscreen labels
    bs = pcbnew.B_SilkS
    for text, y, size in BACK_TEXT:
        add_text(board, text, 12.0, y, size, layer=bs, mirror=True)

    board.Save(PCB)
    # board.Save() rewrites the .kicad_pro with defaults -> restore our rules / net classes
    subprocess.run([sys.executable.replace("python3.12", "python3"), os.path.join(os.path.dirname(__file__), "gen_project.py")],
                   check=True)
    print("saved", PCB)


if __name__ == "__main__":
    build(sys.argv[1])
