"""toshiba-c6 enclosure with the outer size of the original Toshiba WRE-T00BJ10 adapter
(56 x 38 x 15 mm), so it clicks into the original wall/unit holder.

Frame (same as KiCad STEP export of the board, shifted in X by XOFF):
  board x 0..24 -> X = bx + XOFF, board y 0..34 -> Y = -by (connector edge at Y = -34)
  PCB bottom at Z = 0, top at Z = 1.6.
The AC connector (J1, CN22 cable) sits in the middle of the 38 mm short side, like the original.
Two parts: base (tray) and lid (snaps over the base with a stepped skirt). No text.
The 42 x 12 mm FPC antenna slides into a slot along the right side of the base (no cable exit, no glue).
Print base flat, lid upside down, no supports.
"""
import os
import cadquery as cq

OUT = os.path.dirname(os.path.abspath(__file__))

# --- outer size of the original adapter -----------------------------------------
OUT_L, OUT_W, OUT_H = 56.0, 38.0, 15.0
R_OUT = 1.5

# --- board / wall stack ----------------------------------------------------------
PCB_W, PCB_H, PCB_T = 24.0, 34.0, 1.6
GAP = 0.25
WALL = 1.6
FLOOR = 1.2
UNDER = 2.0                      # J1 pin tails (~1.5 mm, clip if longer), USB shell tabs (~0.8 mm)
TOP = 1.4
SKIRT, SKIRT_T, FIT = 2.2, 0.8, 0.15

z_base_bot = -UNDER - FLOOR
z_floor_top = -UNDER
z_split = PCB_T
z_lid_top = z_base_bot + OUT_H
z_lid_inner_top = z_lid_top - TOP

# outer box: X centred on 0, connector end at the PCB connector edge
ox0, ox1 = -OUT_W / 2, OUT_W / 2
oy0 = -PCB_H - GAP - WALL
oy1 = oy0 + OUT_L
ix0, ix1 = ox0 + WALL, ox1 - WALL
iy0, iy1 = oy0 + WALL, oy1 - WALL

# J1 housing centre is board x = 17.5; put it as close to the box centre as the wall allows
J1_CX = 17.5
XOFF = max(-J1_CX, ix0 + GAP)


def X(bx): return bx + XOFF
def Y(by): return -by


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def rbox(x0, x1, y0, y1, z0, z1, r):
    w = cq.Workplane("XY").rect(x1 - x0, y1 - y0).extrude(z1 - z0)
    if r > 0:
        w = w.edges("|Z").fillet(r)
    return w.translate(((x0 + x1) / 2, (y0 + y1) / 2, z0))


def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


# --- openings (board coordinates) --------------------------------------------------
USB_X, USB_W = 5.4, 9.6
USB_Z0, USB_Z1 = PCB_T - 0.3, PCB_T + 3.75
J1_X0, J1_X1 = 11.2, 23.8
J1_Z0, J1_Z1 = PCB_T - 0.3, PCB_T + 7.0
ANT_L, ANT_H = 42.0, 12.0        # FPC antenna inside, on the antenna wall in the base
ANT_RIB = 1.4
ANT_SLOT = 0.8
LED, BOOT = (22.6, 9.0), (21.6, 3.6)
LED_D, BOOT_D, HOLE_CHAMFER = 3.2, 3.0, 0.5
VENT_W, VENT_PITCH = 1.2, 2.6


def front_cut(bx0, bx1, z0, z1):
    return box(X(bx0), X(bx1), oy0 - 1, iy0 + 0.6, z0, z1)


def cutters():
    # USB-C is only used for the first flash (lid off); later updates go OTA,
    # so the wall in front of it stays closed (also: never USB while on the AC)
    return front_cut(J1_X0, J1_X1, J1_Z0, J1_Z1)


# ---------------------------------------------------------------------------- base
def make_base():
    base = rbox(ox0, ox1, oy0, oy1, z_base_bot, z_split, R_OUT)
    base = base.cut(box(ix0, ix1, iy0, iy1, z_floor_top, z_split + 1))
    step_out = rbox(ox0, ox1, oy0, oy1, z_split - SKIRT, z_split + 1, R_OUT)
    step_in = rbox(ox0 + SKIRT_T + FIT, ox1 - SKIRT_T - FIT, oy0 + SKIRT_T + FIT, oy1 - SKIRT_T - FIT,
                   z_split - SKIRT - 1, z_split + 2, 0.8)
    base = base.cut(step_out.cut(step_in))
    # PCB supports (corners + long-side middles), clear of the THT tails
    s = 1.8
    for (bx0, bx1, by0, by1) in [(0, s, 0, s), (PCB_W - s, PCB_W, 0, s),
                                 (0, s, PCB_H - s, PCB_H), (PCB_W - s, PCB_W, PCB_H - s, PCB_H),
                                 (0, 1.4, 14, 19), (PCB_W - 1.4, PCB_W, 14, 19)]:
        base = base.union(box(X(bx0), X(bx1), Y(by1), Y(by0), z_floor_top, 0))
    # locating posts on the two free PCB edges (right edge and antenna edge), up to PCB top
    p = 1.4
    for (x0, x1, y0, y1) in [(X(PCB_W) + GAP, X(PCB_W) + GAP + p, Y(6), Y(2)),
                             (X(PCB_W) + GAP, X(PCB_W) + GAP + p, Y(30), Y(26)),
                             (X(2), X(6), Y(0) + GAP, Y(0) + GAP + p),
                             (X(18), X(22), Y(0) + GAP, Y(0) + GAP + p)]:
        base = base.union(box(x0, x1, y0, y1, z_floor_top, z_split - 0.05))
    # snap bumps on both long sides
    for y in (oy0 + 12, oy1 - 12):
        for x in (ox0 + SKIRT_T + FIT, ox1 - SKIRT_T - FIT):
            bump = (cq.Workplane("XZ").center(x, z_split - SKIRT / 2).circle(0.45).extrude(-8)
                    .translate((0, y - 4, 0)))
            base = base.union(bump)
    # antenna slot: the 42 x 12 mm FPC antenna slides (from the top, lid off) into a 0.8 mm slot
    # between the right long wall and a comb of 12 mm high fingers. The coax is soldered in the
    # middle of the antenna, so the comb leaves the centre 13 mm open for it.
    # The antenna ends up ~10 mm beside the PCB edge, never above or below the copper.
    ay1 = iy1 - 1.0
    ay0 = ay1 - ANT_L - 1.0
    rib_top = z_lid_inner_top - 0.3
    rx1 = ix1 - ANT_SLOT
    rx0 = rx1 - ANT_RIB
    L = ay1 - ay0
    for (f0, f1) in ((0.0, 6.0), (11.0, 15.0), (L - 15.0, L - 11.0), (L - 6.0, L)):
        base = base.union(box(rx0, rx1, ay0 + f0, ay0 + f1, z_floor_top, rib_top))
    # end stops (low, below the lid) close the slot at both ends and tie the comb to the wall
    for y0 in (ay0 - 1.2, ay1):
        base = base.union(box(rx0, ix1, y0, y0 + 1.2, z_floor_top, z_split))
    return base.cut(cutters())


# ----------------------------------------------------------------------------- lid
def make_lid():
    shell = rbox(ox0, ox1, oy0, oy1, z_split - SKIRT, z_lid_top, R_OUT)
    inner = rbox(ox0 + SKIRT_T, ox1 - SKIRT_T, oy0 + SKIRT_T, oy1 - SKIRT_T, z_split - SKIRT - 1, z_split, 0.8)
    lid = shell.cut(inner).cut(box(ix0, ix1, iy0, iy1, z_split - 1, z_lid_inner_top))
    for y in (oy0 + 12, oy1 - 12):
        for x in (ox0 + SKIRT_T, ox1 - SKIRT_T):
            g = (cq.Workplane("XZ").center(x, z_split - SKIRT / 2).circle(0.55).extrude(-8.4)
                 .translate((0, y - 4.2, 0)))
            lid = lid.cut(g)
    # hold-down pins on the free PCB corners and a pad on the USB-C shell
    for (bx, by) in [(0.9, 0.9), (23.1, 0.9)]:
        lid = lid.union(cyl(X(bx), Y(by), PCB_T + 0.1, z_lid_inner_top + 0.1, 1.4))
    lid = lid.union(box(X(2.5), X(8.3), Y(32.5), Y(28.0), PCB_T + 3.26 + 0.15, z_lid_inner_top + 0.1))
    lid = lid.cut(cutters())
    # LED window and BOOT pin-hole, chamfered on the outside (bed side when printing)
    for (bx, by), d in ((LED, LED_D), (BOOT, BOOT_D)):
        lid = lid.cut(cyl(X(bx), Y(by), z_lid_inner_top - 1, z_lid_top + 1, d))
        cone = cq.Solid.makeCone(d / 2, d / 2 + HOLE_CHAMFER + 0.3, HOLE_CHAMFER + 0.3,
                                 pnt=cq.Vector(X(bx), Y(by), z_lid_top - HOLE_CHAMFER))
        lid = lid.cut(cq.Workplane("XY").add(cone))
    # ventilation slots high in the left long wall (right wall carries the antenna)
    z0, z1 = PCB_T + 2.0, z_lid_inner_top - 1.0
    for i in range(14):
        y = Y(-12.0 + i * VENT_PITCH)
        lid = lid.cut(box(ox0 - 1, ix0 + 0.5, y - VENT_W / 2, y + VENT_W / 2, z0, z1))
    return lid


def fit_check(base, lid):
    import os.path
    pcb = cq.importers.importStep(os.path.join(OUT, "..", "build", "pcb.step")).translate((XOFF, 0, 0))
    j1 = box(X(11.5), X(23.5), -34.0, -22.3, 1.6, 8.6)
    parts = pcb.union(j1)
    for name, sh in (("base", base), ("lid", lid)):
        v = sh.val().intersect(parts.val()).Volume()
        print("overlap %s/pcb: %.4f mm3" % (name, v))
    print("overlap base/lid: %.4f mm3" % base.val().intersect(lid.val()).Volume())


if __name__ == "__main__":
    base, lid = make_base(), make_lid()
    fit_check(base, lid)
    cq.exporters.export(base, os.path.join(OUT, "toshiba-c6_mount_base.step"))
    cq.exporters.export(lid, os.path.join(OUT, "toshiba-c6_mount_lid.step"))
    cq.exporters.export(base.translate((0, 0, -z_base_bot)), os.path.join(OUT, "toshiba-c6_mount_base.stl"),
                        tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, z_lid_top)),
                        os.path.join(OUT, "toshiba-c6_mount_lid.stl"), tolerance=0.02, angularTolerance=0.1)
    print("outer: %.1f x %.1f x %.1f mm, J1 centre offset from box centre: %.2f mm"
          % (OUT_W, OUT_L, z_lid_top - z_base_bot, X(J1_CX)))
