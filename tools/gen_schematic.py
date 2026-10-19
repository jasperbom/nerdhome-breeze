"""Generate hardware/toshiba-c6.kicad_sch from circuit.py.

Every connected pin gets a short wire stub ending in a net label (or a power
symbol for GND / +3V3). Connectivity therefore only depends on pin positions,
which are read from the KiCad 9 symbol libraries.
"""
import copy
import math
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, dump, find, find1, Sym  # noqa: E402
import circuit  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "hardware", circuit.PROJECT + ".kicad_sch")
LIBDIR = "/usr/share/kicad/symbols/"
ROOT_UUID = "6f1c2c1e-5b8e-4a5e-9d3f-2a7c0c6e0001"   # fixed so PCB paths stay stable
GRID = 1.27


def nid(seed):
    """Deterministic UUID so regenerating keeps the PCB<->schematic links."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "toshiba-c6/" + seed))


_libcache = {}


def libsym(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        _libcache[lib] = parse(open(LIBDIR + lib + ".kicad_sym").read())
    t = _libcache[lib]
    for s in find(t, "symbol"):
        if s[1] == name:
            ext = find1(s, "extends")
            if not ext:
                out = copy.deepcopy(s)
            else:
                base = libsym(lib + ":" + ext[1])
                base_name = base[1].split(":")[-1]
                out = copy.deepcopy(base)
                # replace properties with the derived ones
                out = [x for x in out if not (isinstance(x, list) and x and x[0] == "property")]
                props = [copy.deepcopy(p) for p in find(s, "property")]
                head, rest = out[:2], out[2:]
                out = head + props + rest
                for sub in find(out, "symbol"):
                    sub[1] = name + sub[1][len(base_name):]
            out[1] = lib_id
            return out
    raise KeyError(lib_id)


def pins_of(sym):
    res = []

    def walk(n):
        for x in n:
            if isinstance(x, list) and x:
                if x[0] == "pin":
                    at = find1(x, "at")
                    res.append(dict(num=str(find1(x, "number")[1]), name=str(find1(x, "name")[1]),
                                    etype=str(x[1]), x=float(at[1]), y=float(at[2]),
                                    a=float(at[3]) if len(at) > 3 else 0.0))
                else:
                    walk(x)
    walk(sym)
    return res


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def eff(size=1.27, justify=None, hide=False):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e


def prop(name, value, x, y, hide=False, justify=None, size=1.27):
    return [Sym("property"), name, value, [Sym("at"), x, y, 0], eff(size, justify, hide)]


items = []          # top-level schematic items
used_libs = {}      # lib_id -> embedded symbol
pin_uuid_seed = 0


def place_symbol(ref, lib_id, x, y, value, fp="", ds="~", extra=None, rot=0, ref_xy=None, val_xy=None,
                 power=False, just=None):
    sym = libsym(lib_id)
    used_libs[lib_id] = sym
    node = [Sym("symbol"), [Sym("lib_id"), lib_id], [Sym("at"), x, y, rot], [Sym("unit"), 1],
            [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("no" if power else "yes")],
            [Sym("on_board"), Sym("no" if power else "yes")], [Sym("dnp"), Sym("no")],
            [Sym("uuid"), nid("sym/" + ref)]]
    rx, ry = ref_xy if ref_xy else (x, y - 3.81)
    vx, vy = val_xy if val_xy else (x, y + 3.81)
    node.append(prop("Reference", ref, rx, ry, hide=power, justify=just))
    node.append(prop("Value", value, vx, vy, justify=just))
    node.append(prop("Footprint", fp, x, y, hide=True))
    node.append(prop("Datasheet", ds, x, y, hide=True))
    node.append(prop("Description", "", x, y, hide=True))
    for k, v in (extra or {}).items():
        node.append(prop(k, v, x, y, hide=True))
    for p in pins_of(sym):
        node.append([Sym("pin"), p["num"], [Sym("uuid"), nid("pin/%s/%s" % (ref, p["num"]))]])
    node.append([Sym("instances"), [Sym("project"), circuit.PROJECT,
                                    [Sym("path"), "/" + ROOT_UUID, [Sym("reference"), ref], [Sym("unit"), 1]]]])
    items.append(node)
    return sym


def wire(x1, y1, x2, y2):
    items.append([Sym("wire"), [Sym("pts"), [Sym("xy"), x1, y1], [Sym("xy"), x2, y2]],
                  [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                  [Sym("uuid"), nid("w/%s/%s/%s/%s" % (x1, y1, x2, y2))]])


def label(net, x, y, direction):
    ang = {"R": 0, "U": 90, "L": 180, "D": 270}[direction]
    just = ["left", "bottom"] if direction in ("R", "U") else ["right", "bottom"]
    items.append([Sym("label"), net, [Sym("at"), x, y, ang], [Sym("fields_autoplaced"), Sym("yes")],
                  eff(1.27, just), [Sym("uuid"), nid("lbl/%s/%s/%s" % (net, x, y))]])


_pwr_n = [0]


def power_symbol(net, x, y, direction):
    lib_id = {"GND": "power:GND", "+3V3": "power:+3V3"}[net]
    # GND graphic points down at rot 0, +3V3 graphic points up at rot 0 (rotation is CCW)
    if net == "GND":
        rot = {"D": 0, "R": 90, "U": 180, "L": 270}[direction]
    else:
        rot = {"U": 0, "L": 90, "D": 180, "R": 270}[direction]
    _pwr_n[0] += 1
    ref = "#PWR%03d" % _pwr_n[0]
    dx, dy = {"D": (0, 3.81), "U": (0, -3.81), "L": (-3.81, 0), "R": (3.81, 0)}[direction]
    place_symbol(ref, lib_id, x, y, net, rot=rot, power=True, ref_xy=(x, y), val_xy=(x + dx, y + dy))


def global_label(net, x, y, direction):
    ang = {"R": 0, "U": 90, "L": 180, "D": 270}[direction]
    just = ["left"] if direction in ("R", "U") else ["right"]
    items.append([Sym("global_label"), net, [Sym("shape"), Sym("passive")], [Sym("at"), x, y, ang],
                  [Sym("fields_autoplaced"), Sym("yes")], eff(1.27, just),
                  [Sym("uuid"), nid("glbl/%s/%s/%s" % (net, x, y))],
                  [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [Sym("at"), x, y, 0],
                   eff(1.27, just, hide=True)]])


def no_connect(x, y):
    items.append([Sym("no_connect"), [Sym("at"), x, y], [Sym("uuid"), nid("nc/%s/%s" % (x, y))]])


def note(txt, x, y, size=1.5):
    items.append([Sym("text"), txt, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), x, y, 0],
                  eff(size, ["left", "top"]), [Sym("uuid"), nid("txt/%s/%s" % (x, y))]])


def outward(a):
    """Lib pin angle -> schematic direction pointing away from the symbol body."""
    a = int(round(a)) % 360
    return {0: "L", 90: "D", 180: "R", 270: "U"}[a]


STUB = 2.54


def auto_fields(lib_id, x, y):
    """Reference/Value positions that do not overlap the symbol body."""
    name = lib_id.split(":")[1]
    if name in ("R", "C"):
        return (x + 2.54, y - 1.27), (x + 2.54, y + 1.27), ["left"]
    if name in ("D_Schottky", "LED"):
        return (x, y - 3.175), (x, y + 3.175), None
    if name in ("AO3400A",):
        return (x + 5.08, y - 1.27), (x + 5.08, y + 1.27), ["left"]
    if name.startswith("AP2112K"):
        return (x, y - 6.35), (x, y + 10.16), None
    if name == "Conn_01x05":
        return (x - 1.27, y - 8.89), (x - 1.27, y + 10.16), None
    if name == "SW_Push":
        return (x, y - 3.81), (x, y + 2.54), None
    return (x, y - 3.81), (x, y + 3.81), None


def add_part(ref, x, y, ref_xy=None, val_xy=None, pwr_labels=False, stub=None, just=None):
    p = circuit.PARTS[ref]
    extra = {"LCSC": p["lcsc"], "MPN": p["mpn"]}
    a_ref, a_val, a_just = auto_fields(p["sym"], x, y)
    sym = place_symbol(ref, p["sym"], x, y, p["value"], fp=p["fp"], extra=extra,
                       ref_xy=ref_xy or a_ref, val_xy=val_xy or a_val,
                       just=just if (ref_xy or val_xy) else a_just)
    stub_len = stub or STUB
    done = set()
    for pin in pins_of(sym):
        px, py = snap(x + pin["x"]), snap(y - pin["y"])
        net = p["pins"].get(pin["num"])
        if net is None:
            if pin["etype"] not in ("no_connect",) and (px, py) not in done:
                no_connect(px, py)
                done.add((px, py))
            continue
        if (px, py) in done:
            continue
        done.add((px, py))
        d = outward(pin["a"])
        dx, dy = {"L": (-stub_len, 0), "R": (stub_len, 0), "U": (0, -stub_len), "D": (0, stub_len)}[d]
        ex, ey = snap(px + dx), snap(py + dy)
        wire(px, py, ex, ey)
        if net in ("GND", "+3V3") and pwr_labels:
            global_label(net, ex, ey, d)
        elif net in ("GND", "+3V3"):
            power_symbol(net, ex, ey, d)
        else:
            label(net, ex, ey, d)


def pwr_flag(net, x, y):
    ref = "#FLG%02d" % (len([i for i in items if i[0] == "symbol"]) + 1)
    place_symbol(ref, "power:PWR_FLAG", x, y, "PWR_FLAG", power=True, ref_xy=(x, y - 5), val_xy=(x, y - 3.81))
    wire(x, y, x, y + STUB)
    if net in ("GND", "+3V3"):
        power_symbol(net, x, y + STUB, "D")
    else:
        label(net, x, y + STUB, "D")


def build():
    # ---------------- layout (A3, mm) ----------------
    note("Toshiba RAS (Shorai/Seiya/Haori...) wifi-port adapter - ESP32-C6 + ESPHome\n"
         "Replaces the Toshiba wifi module on indoor-unit connector CN22 (5 V UART 9600 8E1).",
         20.32, 15.24, 2.0)

    # Connector + level shifters (left)
    note("Toshiba CN22 cable (JST PA 2.0 mm)\n1 blue = AC RX   2 pink = GND   3 black = +5 V\n"
         "4 white = AC TX   5 pink = do NOT connect", 20.32, 35.56)
    add_part("J1", 45.72, 63.5, pwr_labels=True, stub=5.08)
    note("5 V <-> 3.3 V level shifters (MOSFET, 9600 baud)", 76.2, 35.56)
    add_part("Q1", 101.6, 55.88)
    add_part("R3", 119.38, 50.8)
    add_part("R5", 81.28, 50.8)
    add_part("Q2", 101.6, 86.36)
    add_part("R4", 119.38, 81.28)
    add_part("R6", 81.28, 81.28)

    # Power (bottom left)
    note("Power: AC 5 V or USB 5 V via Schottky OR (no back-feed), 3.3 V / 600 mA LDO", 20.32, 119.38)
    add_part("D1", 38.1, 139.7)
    add_part("D2", 38.1, 160.02)
    add_part("C1", 63.5, 157.48)
    add_part("U2", 88.9, 147.32)
    add_part("C4", 116.84, 157.48)
    pwr_flag("VSYS", 63.5, 132.08)
    pwr_flag("GND", 50.8, 177.8)

    # MCU (centre)
    note("ESP32-C6-MINI-1U (U.FL antenna)\nGPIO19 = TX to AC, GPIO20 = RX from AC\n"
         "GPIO23 = status LED, GPIO9 = BOOT, GPIO12/13 = USB", 172.72, 35.56)
    add_part("U1", 195.58, 101.6, ref_xy=(200.66, 71.12), val_xy=(200.66, 73.66), just=["left"])
    add_part("C2", 147.32, 71.12)
    add_part("C3", 162.56, 71.12)
    add_part("R1", 147.32, 101.6)
    add_part("C5", 160.02, 121.92)
    add_part("R2", 157.48, 147.32)
    add_part("SW1", 157.48, 165.1)
    add_part("R7", 241.3, 147.32)
    add_part("D3", 241.3, 165.1)

    # USB (right)
    note("USB-C: flashing + bench power only.\nDo NOT plug in USB while the board is connected\n"
         "to the air conditioner (AC logic ground may not be isolated).", 287.02, 35.56)
    add_part("J2", 304.8, 106.68, ref_xy=(304.8, 76.2), val_xy=(304.8, 78.74))
    add_part("R8", 345.44, 99.06)
    add_part("R9", 358.14, 99.06)

    lib_symbols = [Sym("lib_symbols")] + [used_libs[k] for k in sorted(used_libs)]
    sch = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"],
           [Sym("generator_version"), "9.0"], [Sym("uuid"), ROOT_UUID], [Sym("paper"), "A3"],
           [Sym("title_block"), [Sym("title"), "Toshiba AC wifi-port adapter (ESP32-C6)"],
            [Sym("date"), "2026-10-13"], [Sym("rev"), "1.0"],
            [Sym("company"), "Jasper Bom"],
            [Sym("comment"), 1, "UART 9600 8E1 @ 5 V on CN22; ESPHome toshiba_suzumi / toshiba_controller"],
            [Sym("comment"), 2, "JLCPCB assembly: LCSC numbers in symbol fields"]],
           lib_symbols]
    sch += items
    sch.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
    sch.append([Sym("embedded_fonts"), Sym("no")])
    with open(OUT, "w") as f:
        f.write(dump(sch) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    build()
