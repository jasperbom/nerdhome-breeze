"""Work out JLCPCB CPL rotation corrections by aligning each KiCad footprint's
pads onto the EasyEDA footprint JLC uses for the chosen LCSC part.

Uses the rigid-alignment solver from Bouni/kicad-jlcpcb-tools (jlcfootprint).
Writes build/jlc_rotations.json: {ref: {"correction": deg, "residual": mm, ...}}

Run with python3.12 (needs pcbnew).
"""
import json
import os
import sys
import time
import urllib.request

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, "/home/claude/Bouni/kicad-jlcpcb-tools")
import circuit  # noqa: E402
from jlcfootprint.solver import solve_transform  # noqa: E402
from jlcfootprint.geometry import ccw_correction  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(ROOT, "hardware", circuit.PROJECT + ".kicad_pcb")
CACHE = os.path.join(ROOT, "build", "easyeda_cache")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def easyeda(lcsc):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, lcsc + ".json")
    if not os.path.exists(path):
        req = urllib.request.Request(
            "https://easyeda.com/api/products/%s/components?version=6.4.19.5" % lcsc,
            headers={"User-Agent": UA, "Accept": "application/json", "Referer": "https://easyeda.com/"})
        data = urllib.request.urlopen(req, timeout=30).read()
        open(path, "wb").write(data)
        time.sleep(0.5)
    return json.load(open(path))


def jlc_pads(lcsc):
    d = easyeda(lcsc)["result"]["packageDetail"]
    ds = d["dataStr"]
    hx, hy = float(ds["head"]["x"]), float(ds["head"]["y"])
    acc = {}
    for s in ds["shape"]:
        if not s.startswith("PAD~"):
            continue
        f = s.split("~")
        num = f[8]
        if not num:
            continue
        x, y = (float(f[2]) - hx) * 0.254, (float(f[3]) - hy) * 0.254
        acc.setdefault(num, []).append((x, y))
    return d.get("title", ""), {k: (sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v))
                                for k, v in acc.items()}


def jlc_cathode(lcsc):
    """Pin number that EasyEDA's symbol calls the cathode (K or -), if any."""
    d = easyeda(lcsc)["result"]
    for sh in d["dataStr"]["shape"]:
        if sh.startswith("P~"):
            parts = sh.split("^^")
            num = parts[0].split("~")[3]
            names = [seg.split("~")[4] for seg in parts[1:]
                     if len(seg.split("~")) > 4 and seg.split("~")[0] in ("0", "1")]
            if names and names[0].strip().upper() in ("K", "-", "CATHODE", "C"):
                return num
    return None


def kicad_pads(fp):
    acc = {}
    for pad in fp.Pads():
        if not pad.GetNumber() or pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            continue
        p = pad.GetFPRelativePosition()
        acc.setdefault(pad.GetNumber(), []).append((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)))
    return {k: (sum(q[0] for q in v) / len(v), sum(q[1] for q in v) / len(v)) for k, v in acc.items()}


def main():
    board = pcbnew.LoadBoard(PCB)
    out = {}
    seen = {}
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        lcsc = circuit.PARTS[ref]["lcsc"]
        key = (lcsc, str(fp.GetFPID().GetLibItemName()))
        if key not in seen:
            title, jp = jlc_pads(lcsc)
            kp = kicad_pads(fp)
            note = ""
            if ref.startswith("D") and len(kp) == 2:
                # KiCad diode/LED footprints: pad 1 = cathode. Match by function, not number.
                k = jlc_cathode(lcsc)
                if k and k != "1":
                    kp = {k: kp["1"], ("1" if k == "2" else "2"): kp["2"]}
                    note = "cathode is EasyEDA pin %s" % k
            r = solve_transform(kp, jp)
            seen[key] = dict(correction=ccw_correction(r.rotation_deg), raw=round(r.rotation_deg_raw, 2),
                             residual=round(r.residual, 3), matched=r.matched_pad_count,
                             kicad_pads=len(kp), jlc_pads=len(jp), mirrored=r.is_mirrored,
                             flag=r.quality_flag, easyeda_footprint=title, note=note)
        out[ref] = dict(seen[key], lcsc=lcsc, footprint=key[1])
        print("%-4s %-10s %-45s corr=%3d raw=%7.2f resid=%.3f matched=%d/%d %s" % (
            ref, lcsc, key[1][:45], out[ref]["correction"], out[ref]["raw"], out[ref]["residual"],
            out[ref]["matched"], out[ref]["kicad_pads"], out[ref]["flag"] + " " + out[ref]["note"]))
    json.dump(out, open(os.path.join(ROOT, "build", "jlc_rotations.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
