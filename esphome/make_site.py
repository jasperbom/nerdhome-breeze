"""Nerdhome Breeze: collect the compiled factory firmware into a GitHub Pages site.

Writes <out>/index.html (ESP Web Tools installer) and <out>/firmware/<variant>/ with
  breeze-toshiba.factory.bin   full image for the web installer (offset 0)
  breeze-toshiba.ota.bin       app image for OTA updates from Home Assistant
  manifest.json            ESP Web Tools manifest + ESPHome http_request OTA block
"""
import argparse
import glob
import hashlib
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def find(build_dir, *names):
    for n in names:
        hits = sorted(glob.glob(os.path.join(build_dir, "**", n), recursive=True), key=os.path.getmtime)
        if hits:
            return hits[-1]
    raise SystemExit("not found in %s: %s" % (build_dir, ", ".join(names)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-dir", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--summary", default="")
    ap.add_argument("--release-url", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--variant", default="toshiba")
    a = ap.parse_args()

    factory = find(a.build_dir, "firmware.factory.bin")
    ota = find(a.build_dir, "firmware.ota.bin", "firmware.bin")
    fw = os.path.join(a.out, "firmware", a.variant)
    os.makedirs(fw, exist_ok=True)
    shutil.copy(factory, os.path.join(fw, "breeze-%s.factory.bin" % a.variant))
    shutil.copy(ota, os.path.join(fw, "breeze-%s.ota.bin" % a.variant))
    md5 = hashlib.md5(open(ota, "rb").read()).hexdigest()

    manifest = {
        "name": "Nerdhome Breeze voor %s" % a.variant.capitalize(),
        "version": a.version,
        "home_assistant_domain": "esphome",
        "new_install_prompt_erase": True,
        "builds": [{
            "chipFamily": "ESP32-C6",
            "parts": [{"path": "breeze-%s.factory.bin" % a.variant, "offset": 0}],
            "ota": {"path": "breeze-%s.ota.bin" % a.variant, "md5": md5,
                    "summary": a.summary, "release_url": a.release_url},
        }],
    }
    json.dump(manifest, open(os.path.join(fw, "manifest.json"), "w"), indent=2)
    shutil.copy(os.path.join(HERE, "site", "index.html"), os.path.join(a.out, "index.html"))
    open(os.path.join(a.out, ".nojekyll"), "w").close()
    print("site ready: version %s, factory %s, ota %s (md5 %s)" % (a.version, factory, ota, md5))


if __name__ == "__main__":
    main()
