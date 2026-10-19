"""Generate the project footprint library daikin-c6.pretty."""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, dump, find, find1, Sym  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "hardware", "daikin-c6.pretty")
KFP = "/usr/share/kicad/footprints"


def u():
    return [Sym("uuid"), str(uuid.uuid4())]


def line(x1, y1, x2, y2, layer, w):
    return [Sym("fp_line"), [Sym("start"), x1, y1], [Sym("end"), x2, y2],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]],
            [Sym("layer"), layer], u()]


def rect(x1, y1, x2, y2, layer, w):
    return [line(x1, y1, x2, y1, layer, w), line(x2, y1, x2, y2, layer, w),
            line(x2, y2, x1, y2, layer, w), line(x1, y2, x1, y1, layer, w)]


def circle(cx, cy, r, layer, w, fill=False):
    return [Sym("fp_circle"), [Sym("center"), cx, cy], [Sym("end"), cx + r, cy],
            [Sym("stroke"), [Sym("width"), w], [Sym("type"), Sym("solid")]],
            [Sym("fill"), Sym("yes" if fill else "no")], [Sym("layer"), layer], u()]


def text(kind, value, x, y, layer, size=1.0, thick=0.15, hide=False):
    eff = [Sym("effects"), [Sym("font"), [Sym("size"), size, size], [Sym("thickness"), thick]]]
    if kind in ("Reference", "Value"):
        node = [Sym("property"), kind, value, [Sym("at"), x, y, 0], [Sym("layer"), layer]]
        if hide:
            node.append([Sym("hide"), Sym("yes")])
        node += [u(), eff]
        return node
    return [Sym("fp_text"), Sym("user"), value, [Sym("at"), x, y, 0], [Sym("layer"), layer], u(), eff]


def footprint(name, descr, tags, attr, body):
    fp = [Sym("footprint"), name, [Sym("version"), 20241229], [Sym("generator"), "pcbnew"],
          [Sym("generator_version"), "9.0"], [Sym("layer"), "F.Cu"],
          [Sym("descr"), descr], [Sym("tags"), tags], [Sym("attr")] + [Sym(a) for a in attr]]
    fp += body
    return fp


def esp32_c6_mini_1u():
    """Same land pattern as ESP32-C6-MINI-1 (datasheet fig. 11-1 / 11-2), but the
    body is only 12.5 mm long (U.FL connector instead of PCB antenna), so no
    antenna keepout is needed."""
    src = parse(open(os.path.join(KFP, "RF_Module.pretty", "ESP32-C6-MINI-1.kicad_mod")).read())
    pads = find(src, "pad")
    # body: x -6.6..6.6, y -6.9..5.6 (bottom edge 5.6 from pad-array centre, 12.5 long)
    x0, x1, y0, y1 = -6.6, 6.6, -6.9, 5.6
    body = [text("Reference", "REF**", 0, -8.2, "F.SilkS"),
            text("Value", "ESP32-C6-MINI-1U", 0, 7.0, "F.Fab"),
            text("user", "${REFERENCE}", 0, 0, "F.Fab")]
    # fab outline with pin-1 chamfer
    body += [line(x0, y0, x1, y0, "F.Fab", 0.1), line(x1, y0, x1, y1, "F.Fab", 0.1),
             line(x1, y1, x0 + 1.0, y1, "F.Fab", 0.1), line(x0 + 1.0, y1, x0, y1 - 1.0, "F.Fab", 0.1),
             line(x0, y1 - 1.0, x0, y0, "F.Fab", 0.1)]
    # U.FL connector position (top view): 1.70 mm from left edge, 1.55 mm from top edge
    ux, uy = x0 + 1.70, y0 + 1.55
    body.append(circle(ux, uy, 0.75, "F.Fab", 0.1))
    body.append(text("user", "U.FL", ux + 2.1, uy, "F.Fab", size=0.6, thick=0.1))
    # silkscreen just outside the body, leaving the pad rows free
    s = 0.12
    sx0, sx1, sy0, sy1 = x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15
    body += [line(sx0, sy0, sx1, sy0, "F.SilkS", s),
             line(sx0, sy0, sx0, -5.6, "F.SilkS", s), line(sx1, sy0, sx1, -5.6, "F.SilkS", s),
             line(sx0, sy1, -5.6, sy1, "F.SilkS", s), line(sx1, sy1, 5.6, sy1, "F.SilkS", s),
             line(sx0, sy1, sx0, 5.2, "F.SilkS", s), line(sx1, sy1, sx1, 5.2, "F.SilkS", s)]
    # pin-1 marker (left of pin 1)
    body.append([Sym("fp_poly"), [Sym("pts"), [Sym("xy"), -7.1, -4], [Sym("xy"), -7.45, -3.75],
                                  [Sym("xy"), -7.45, -4.25], [Sym("xy"), -7.1, -4]],
                 [Sym("stroke"), [Sym("width"), 0.12], [Sym("type"), Sym("solid")]],
                 [Sym("fill"), Sym("yes")], [Sym("layer"), "F.SilkS"], u()])
    body += rect(x0 - 0.25, y0 - 0.25, x1 + 0.25, y1 + 0.25, "F.CrtYd", 0.05)
    # keep the original pads untouched (incl. 3x3 EPAD and corner GND pads)
    for p in pads:
        # drop the per-pad uuid and give a fresh one
        p[:] = [x for x in p if not (isinstance(x, list) and x and x[0] == "uuid")] + [u()]
    body += pads
    body.append([Sym("model"), "${KIPRJMOD}/3dmodels/ESP32-C6-MINI-1U.step",
                 [Sym("offset"), [Sym("xyz"), -6.75, 1.5, -8.389]],
                 [Sym("scale"), [Sym("xyz"), 1, 1, 1]],
                 [Sym("rotate"), [Sym("xyz"), -90, 0, 0]]])
    return footprint("ESP32-C6-MINI-1U",
                     "ESP32-C6-MINI-1U(-H4/-N4) module with U.FL connector, 13.2x12.5 mm, "
                     "land pattern per Espressif datasheet v1.5 fig. 11-2",
                     "ESP32-C6 MINI-1U U.FL external antenna", ["smd"], body)


def jst_pa_s05b_pask_2():
    """JST PA side-entry header S05B-PASK-2 (pin row at y=0, housing opening towards +y).
    Geometry taken from the produced florianbrede-ayet controller board; drill enlarged
    slightly (0.71 -> 0.80 mm) for tolerance."""
    n, pitch = 5, 2.0
    body = [text("Reference", "REF**", 4.0, -4.6, "F.SilkS"),
            text("Value", "S05B-PASK-2", 4.0, 9.3, "F.Fab"),
            text("user", "${REFERENCE}", 4.0, 4.5, "F.Fab")]
    fx0, fx1, fy0, fy1 = -2.0, 10.0, -3.5, 8.2
    body += rect(fx0, fy0, fx1, fy1, "F.Fab", 0.1)
    body.append(text("user", "cable entry", 4.0, 7.3, "F.Fab", size=0.6, thick=0.1))
    sx0, sx1, sy0, sy1 = fx0 - 0.12, fx1 + 0.12, fy0 - 0.12, fy1 + 0.12
    s = 0.12
    body += [line(sx0, sy0, sx1, sy0, "F.SilkS", s), line(sx0, sy1, sx1, sy1, "F.SilkS", s),
             line(sx0, sy0, sx0, 1.2, "F.SilkS", s), line(sx0, 3.0, sx0, sy1, "F.SilkS", s),
             line(sx1, sy0, sx1, 1.2, "F.SilkS", s), line(sx1, 3.0, sx1, sy1, "F.SilkS", s)]
    # pin-1 marker
    body.append([Sym("fp_poly"), [Sym("pts"), [Sym("xy"), 0, -1.25], [Sym("xy"), -0.4, -1.85],
                                  [Sym("xy"), 0.4, -1.85], [Sym("xy"), 0, -1.25]],
                 [Sym("stroke"), [Sym("width"), 0.12], [Sym("type"), Sym("solid")]],
                 [Sym("fill"), Sym("yes")], [Sym("layer"), "F.SilkS"], u()])
    body += rect(fx0 - 0.3, fy0 - 0.3, fx1 + 0.3, fy1 + 0.3, "F.CrtYd", 0.05)
    for i in range(n):
        shape = "rect" if i == 0 else "circle"
        body.append([Sym("pad"), str(i + 1), Sym("thru_hole"), Sym(shape), [Sym("at"), i * pitch, 0],
                     [Sym("size"), 1.35, 1.35], [Sym("drill"), 0.8],
                     [Sym("layers"), "*.Cu", "*.Mask"], [Sym("remove_unused_layers"), Sym("no")], u()])
    for x in (-1.5, 9.5):
        body.append([Sym("pad"), "", Sym("np_thru_hole"), Sym("circle"), [Sym("at"), x, 2.1],
                     [Sym("size"), 1.1, 1.1], [Sym("drill"), 1.1],
                     [Sym("layers"), "*.Cu", "*.Mask"], u()])
    return footprint("JST_PA_S05B-PASK-2_1x05_P2.00mm_Horizontal",
                     "JST PA series connector, S05B-PASK-2 (LCSC C489718), 2.00mm pitch, side entry, "
                     "through hole. Mates with the Toshiba CN22 wifi-module cable.",
                     "connector JST PA side entry Toshiba CN22", ["through_hole"], body)


def main():
    os.makedirs(OUT, exist_ok=True)
    for fp in (esp32_c6_mini_1u(),):
        path = os.path.join(OUT, fp[1] + ".kicad_mod")
        with open(path, "w") as f:
            f.write(dump(fp) + "\n")
        print("wrote", path)


if __name__ == "__main__":
    main()
