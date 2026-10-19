"""3D-printable enclosure for the toshiba-c6 board (CadQuery).

Frame = KiCad STEP export with --user-origin 100x100mm:
  board spans X 0..24, Y -34..0 (board y=0 edge is Y=0, connector edge is Y=-34),
  PCB bottom at Z=0, top at Z=1.6.

Two parts:
  base: tray with corner/side supports, PCB sits on them, cut-outs for J1/J2 below PCB top
  lid:  snaps over the base with a stepped skirt; openings for J1 (Toshiba CN22 cable),
        USB-C, antenna cable notch, LED window and BOOT pin-hole.
Print both parts flat side down, no supports needed (lid printed upside down).
"""
import os
import cadquery as cq

OUT = os.path.dirname(os.path.abspath(__file__))

# --- board / parts -------------------------------------------------------
PCB_W, PCB_H, PCB_T = 24.0, 34.0, 1.6
GAP = 0.25                      # clearance PCB edge -> wall
WALL = 1.6
FLOOR = 1.2
UNDER = 2.0                     # free space below PCB: J1 pin tails (~1.5 mm, clip if longer) and USB shell tabs (~0.8 mm)
ABOVE = 8.0                     # free space above PCB (JST PA housing ~6.5 mm)
TOP = 1.4                       # lid top thickness
SKIRT = 2.2                     # lid skirt overlap down over the base
SKIRT_T = 0.8                   # skirt thickness
FIT = 0.15                      # clearance skirt <-> base step

# board-coordinates (x right, y down from board top edge) -> model frame
def X(bx): return bx
def Y(by): return -by

# --- derived ---------------------------------------------------------------
ix0, ix1 = -GAP, PCB_W + GAP                     # inner cavity
iy0, iy1 = -PCB_H - GAP, GAP
ox0, ox1 = ix0 - WALL, ix1 + WALL                # outer
oy0, oy1 = iy0 - WALL, iy1 + WALL
z_floor_top = -UNDER                             # PCB bottom at 0
z_base_bot = z_floor_top - FLOOR
z_split = PCB_T                                  # base top = PCB top surface
z_lid_inner_top = PCB_T + ABOVE
z_lid_top = z_lid_inner_top + TOP
OW, OH = ox1 - ox0, oy1 - oy0
CX, CY = (ox0 + ox1) / 2, (oy0 + oy1) / 2


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def rbox(x0, x1, y0, y1, z0, z1, r):
    w = cq.Workplane("XY").rect(x1 - x0, y1 - y0).extrude(z1 - z0)
    if r > 0:
        w = w.edges("|Z").fillet(r)
    return w.translate(((x0 + x1) / 2, (y0 + y1) / 2, z0))


def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


# ---------------------------------------------------------------- cut-outs
# connector edge is Y = -34 (board y = 34)
def front_cut(bx0, bx1, z0, z1):
    """through-cut in the connector-side wall (Y = oy0 side)."""
    return box(bx0, bx1, oy0 - 1, iy0 + 0.6, z0, z1)


USB_X, USB_W = 5.4, 9.6                     # receptacle 8.94 wide
USB_Z0, USB_Z1 = PCB_T - 0.3, PCB_T + 3.75  # receptacle 3.26 high
J1_X0, J1_X1 = 11.2, 23.95                  # JST PA housing x 11.5..23.5
J1_Z0, J1_Z1 = PCB_T - 0.3, PCB_T + 7.0

ANT_X = 7.1                                  # U.FL on the module, board (7.1, 2.25)
ANT_W = 2.2                                  # slot for 1.13 mm / 0.81 mm IPEX coax
LED = (22.6, 9.0)
BOOT = (21.6, 3.6)
LED_D, BOOT_D = 3.2, 3.0       # >= 3 mm: small holes close up on the first layer (elephant foot)
HOLE_CHAMFER = 0.5             # 45deg chamfer on the outside (= bed side when printing)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TXT_DEPTH = 0.6
VENT_W, VENT_PITCH = 1.2, 2.6  # ventilation slots
LABEL = False                  # engraved text on the lid (unreadable in FDM at this size)


def cutters():
    c = front_cut(USB_X - USB_W / 2, USB_X + USB_W / 2, USB_Z0, USB_Z1)
    c = c.union(front_cut(J1_X0, J1_X1, J1_Z0, J1_Z1))
    return c


# ------------------------------------------------------------------- base
def make_base():
    outer = rbox(ox0, ox1, oy0, oy1, z_base_bot, z_split, 1.5)
    cav = box(ix0, ix1, iy0, iy1, z_floor_top, z_split + 1)
    base = outer.cut(cav)
    # stepped top: outer part of the wall removed over SKIRT height so the lid skirt slides over it
    step_out = rbox(ox0, ox1, oy0, oy1, z_split - SKIRT, z_split + 1, 1.5)
    step_in = rbox(ox0 + SKIRT_T + FIT, ox1 - SKIRT_T - FIT, oy0 + SKIRT_T + FIT, oy1 - SKIRT_T - FIT,
                   z_split - SKIRT - 1, z_split + 2, 0.8)
    base = base.cut(step_out.cut(step_in))
    # PCB supports (pads under board corners and long-side middles), clear of THT tails
    sup = []
    s = 1.8
    for (bx0, bx1, by0, by1) in [(0, s, 0, s), (PCB_W - s, PCB_W, 0, s),
                                 (0, s, PCB_H - s, PCB_H), (PCB_W - s, PCB_W, PCB_H - s, PCB_H),
                                 (0, 1.4, 14, 19), (PCB_W - 1.4, PCB_W, 14, 19)]:
        sup.append(box(X(bx0) - GAP, X(bx1), Y(by1), Y(by0) + (GAP if by0 == 0 else 0), z_floor_top, 0))
    for p in sup:
        base = base.union(p)
    # ventilation slots in the floor (cool air in at the bottom)
    for i in range(5):
        x = 6.8 + i * VENT_PITCH
        base = base.cut(box(x - VENT_W / 2, x + VENT_W / 2, Y(24.0), Y(12.0), z_base_bot - 1, z_floor_top + 0.5))
    # snap bumps on the long sides of the base step (lid has matching grooves)
    for y in (-8.0, -26.0):
        for x, sx in ((ox0 + SKIRT_T + FIT, -1), (ox1 - SKIRT_T - FIT, 1)):
            bump = cq.Workplane("XZ").center(x, z_split - SKIRT / 2).circle(0.45).extrude(-6).translate((0, y - 3, 0))
            base = base.union(bump)
    base = base.cut(cutters())
    return base


# -------------------------------------------------------------------- lid
def make_lid():
    shell = rbox(ox0, ox1, oy0, oy1, z_split - SKIRT, z_lid_top, 1.5)
    inner = rbox(ox0 + SKIRT_T, ox1 - SKIRT_T, oy0 + SKIRT_T, oy1 - SKIRT_T, z_split - SKIRT - 1, z_split, 0.8)
    cav = box(ix0, ix1, iy0, iy1, z_split - 1, z_lid_inner_top)
    lid = shell.cut(inner).cut(cav)
    # grooves for the snap bumps
    for y in (-8.0, -26.0):
        for x in (ox0 + SKIRT_T, ox1 - SKIRT_T):
            g = cq.Workplane("XZ").center(x, z_split - SKIRT / 2).circle(0.55).extrude(-6.4).translate((0, y - 3.2, 0))
            lid = lid.cut(g)
    # hold-down pins onto free PCB corners (top-left / top-right) and onto the USB-C shell
    for (bx, by, zbot) in [(0.9, 0.9, PCB_T + 0.1), (23.1, 0.9, PCB_T + 0.1)]:
        lid = lid.union(cyl(X(bx), Y(by), zbot, z_lid_inner_top + 0.1, 1.4))
    lid = lid.union(box(X(2.5), X(8.3), Y(32.5), Y(28.0), PCB_T + 3.26 + 0.15, z_lid_inner_top + 0.1))
    # openings
    lid = lid.cut(cutters())
    # antenna cable notch in the top (board y=0) wall, open towards the skirt edge
    ant_top = PCB_T + 5.0
    lid = lid.cut(box(ANT_X - ANT_W / 2, ANT_X + ANT_W / 2, iy1 - 0.6, oy1 + 1, z_split - SKIRT - 1, ant_top))
    lid = lid.cut(cq.Workplane("XZ").center(ANT_X, ant_top).circle(ANT_W / 2).extrude(-(WALL + 3))
                  .translate((0, iy1 - 0.6, 0)))
    # LED window and BOOT pin-hole, chamfered on the outside against elephant foot
    for (bx, by), d in ((LED, LED_D), (BOOT, BOOT_D)):
        lid = lid.cut(cyl(X(bx), Y(by), z_lid_inner_top - 1, z_lid_top + 1, d))
        cone = cq.Solid.makeCone(d / 2, d / 2 + HOLE_CHAMFER + 0.3, HOLE_CHAMFER + 0.3,
                                 pnt=cq.Vector(X(bx), Y(by), z_lid_top - HOLE_CHAMFER))
        lid = lid.cut(cq.Workplane("XY").add(cone))
    # ventilation slots high in both long side walls (warm air out at the top)
    z0, z1 = PCB_T + 2.0, z_lid_inner_top - 1.0
    for i in range(5):
        y = Y(13.0 + i * VENT_PITCH)
        for xa, xb in ((ox0 - 1, ix0 + 0.5), (ix1 - 0.5, ox1 + 1)):
            lid = lid.cut(box(xa, xb, y - VENT_W / 2, y + VENT_W / 2, z0, z1))
    # engraved label along the long side (reads bottom-to-top), bold font, left of the LED/BOOT holes
    L = OH - 5.0
    try:
        if not LABEL:
            return lid
        for s, x, size in (("toshiba-c6", 6.2, 7.0), ("by Jasper Bom", 13.2, 5.6)):
            def mk(sz):
                return (cq.Workplane("XY").workplane(offset=z_lid_top)
                        .text(s, sz, -TXT_DEPTH, combine=False, halign="center", valign="center", fontPath=FONT))
            t = mk(size)
            k = min(1.0, L / t.val().BoundingBox().xlen)
            t = mk(size * k).rotate((0, 0, 0), (0, 0, 1), 90).translate((x, CY, 0))
            bb = t.val().BoundingBox()
            print("label %-14s %.1f long x %.1f high, x %.1f..%.1f" % (s, bb.ylen, bb.xlen, bb.xmin, bb.xmax))
            lid = lid.cut(t)
    except Exception as e:  # font problems should never break the build
        print("label skipped:", e)
    return lid


if __name__ == "__main__":
    base = make_base()
    lid = make_lid()
    cq.exporters.export(base, os.path.join(OUT, "toshiba-c6_base.step"))
    cq.exporters.export(lid, os.path.join(OUT, "toshiba-c6_lid.step"))
    # STL: lid flipped so it prints top-down without supports
    cq.exporters.export(base.translate((0, 0, -z_base_bot)), os.path.join(OUT, "toshiba-c6_base.stl"),
                        tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, z_lid_top)),
                        os.path.join(OUT, "toshiba-c6_lid.stl"), tolerance=0.02, angularTolerance=0.1)
    print("outer size: %.1f x %.1f x %.1f mm" % (OW, OH, z_lid_top - z_base_bot))
