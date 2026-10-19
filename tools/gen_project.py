"""Write hardware/toshiba-c6.kicad_pro with JLCPCB-friendly rules and net classes."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import circuit  # noqa: E402
from gen_schematic import ROOT_UUID  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "hardware", circuit.PROJECT + ".kicad_pro")


def netclass(name, track, clearance=0.15, via_d=0.6, via_drill=0.3, prio=0):
    return {
        "bus_width": 12, "clearance": clearance, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
        "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": prio,
        "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": track,
        "via_diameter": via_d, "via_drill": via_drill, "wire_width": 6,
    }


pro = {
    "board": {
        "3dviewer": {"background_bottom": "#ffffff", "background_top": "#ffffff"},
        "design_settings": {
            "defaults": {
                "board_outline_line_width": 0.05, "copper_line_width": 0.2, "copper_text_size_h": 1.0,
                "copper_text_size_v": 1.0, "copper_text_thickness": 0.15, "other_line_width": 0.1,
                "silk_line_width": 0.12, "silk_text_size_h": 0.8, "silk_text_size_v": 0.8,
                "silk_text_thickness": 0.12,
                "pads": {"drill": 0.8, "height": 1.35, "width": 1.35},
                "zones": {"min_clearance": 0.2},
            },
            "rules": {
                "max_error": 0.005,
                "min_clearance": 0.127,
                "min_connection": 0.0,
                "min_copper_edge_clearance": 0.3,
                "min_hole_clearance": 0.25,
                "min_hole_to_hole": 0.25,
                "min_microvia_diameter": 0.2,
                "min_microvia_drill": 0.1,
                "min_resolved_spokes": 1,
                "min_silk_clearance": 0.0,
                "min_text_height": 0.6,
                "min_text_thickness": 0.08,
                "min_through_hole_diameter": 0.3,
                "min_track_width": 0.127,
                "min_via_annular_width": 0.1,
                "min_via_diameter": 0.45,
                "solder_mask_to_copper_clearance": 0.0,
                "use_height_for_length_calcs": True,
            },
            "rule_severities": {
                "silk_over_copper": "warning", "silk_overlap": "warning", "silk_edge_clearance": "warning",
                "lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                "text_height": "warning", "text_thickness": "warning",
            },
            "track_widths": [0.0, 0.2, 0.3, 0.5],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
        },
        "layer_presets": [],
        "viewports": [],
    },
    "boards": [],
    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    "meta": {"filename": circuit.PROJECT + ".kicad_pro", "version": 3},
    "net_settings": {
        "classes": [
            netclass("Default", 0.2),
            netclass("Power", 0.4, prio=1),
            netclass("USB", 0.2, prio=2),
        ],
        "meta": {"version": 4},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": (
            [{"netclass": "Power", "pattern": n} for n in ("GND", "+3V3", "/VSYS", "/5V_AC", "/VBUS")]
            + [{"netclass": "USB", "pattern": "/USB_D*"}]
        ),
    },
    "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
    "schematic": {
        "annotation": {"method": 0, "sort_order": 0},
        "drawing": {"default_line_thickness": 6.0, "default_text_size": 50.0, "label_size_ratio": 0.375,
                    "pin_symbol_size": 25.0, "text_offset_ratio": 0.15},
        "legacy_lib_dir": "", "legacy_lib_list": [],
        "meta": {"version": 1},
        "net_format_name": "", "page_layout_descr_file": "", "plot_directory": "",
        "spice_adjust_passive_values": False, "spice_external_command": "spice \"%I\"",
        "subpart_first_id": 65, "subpart_id_separator": 0,
    },
    "sheets": [[ROOT_UUID, "Root"]],
    "text_variables": {},
}

with open(OUT, "w") as f:
    json.dump(pro, f, indent=2)
print("wrote", OUT)
