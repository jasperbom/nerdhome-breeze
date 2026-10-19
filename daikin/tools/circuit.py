"""Single source of truth for the daikin-c6 (Nerdhome Breeze voor Daikin) S21 adapter circuit.

Each part: ref -> dict(sym, value, fp, lcsc, mpn, pins={pin_number: net})
Pins not listed are left unconnected (and get a no-connect flag in the schematic
when they are I/O pins).
"""

PROJECT = "daikin-c6"

# Connector J1 pinout (Daikin S21, JST EH 2.5 mm, cable EHR-5 one-to-one):
#   1 Vref 5 V   = NOT connected (reference only, sometimes absent)
#   2 TX of AC   (ESP RX via level shifter, open drain, 5 V)
#   3 RX of AC   (ESP TX via level shifter, open drain, 5 V)
#   4 Vcc 12-15 V (powers the board through the AP63205 buck -> 5 V)
#   5 GND
# Data lines are pulled up to our own 5 V (R3/R4); 2400 baud 8E2.
# GPIO plan (ESP32-C6-MINI-1U):
#   GPIO19 (pin 25) = UART TX to AC, GPIO20 (pin 26) = UART RX from AC
#   GPIO23 (pin 29) = status LED (active high)
#   GPIO9  (pin 23) = BOOT button (strapping, internal pull-up)
#   GPIO8  (pin 22) = strapping, 10k pull-up for reliable download mode
#   GPIO12/13 (pins 17/18) = native USB D-/D+

PARTS = {
    "U1": dict(sym="RF_Module:ESP32-C6-MINI-1", value="ESP32-C6-MINI-1U-H4",
               fp="daikin-c6:ESP32-C6-MINI-1U", lcsc="C20627095", mpn="ESP32-C6-MINI-1U-H4",
               pins={"3": "+3V3", "8": "EN", "17": "USB_D-", "18": "USB_D+",
                     "22": "IO8", "23": "BOOT", "25": "ESP_TX", "26": "ESP_RX", "29": "LED",
                     **{str(p): "GND" for p in [1, 2, 11, 14] + list(range(36, 54))}}),
    "U2": dict(sym="Regulator_Linear:AP2112K-3.3", value="AP2112K-3.3",
               fp="Package_TO_SOT_SMD:SOT-23-5", lcsc="C51118", mpn="AP2112K-3.3TRG1",
               pins={"1": "VSYS", "2": "GND", "3": "VSYS", "5": "+3V3"}),
    "J1": dict(sym="Connector_Generic:Conn_01x05", value="Daikin S21 (JST EH)",
               fp="Connector_JST:JST_EH_S5B-EH_1x05_P2.50mm_Horizontal", lcsc="C265103",
               mpn="S5B-EH(LF)(SN)",
               pins={"2": "AC_TX", "3": "AC_RX", "4": "VIN_AC", "5": "GND"}),
    # 12-15 V from the S21 port -> 5 V (AP63205, 1.1 MHz, datasheet table 3: 4.7 uH, 10 uF, 2x22 uF, 100 nF)
    "U3": dict(sym="Regulator_Switching:AP63205WU", value="AP63205WU-7",
               fp="Package_TO_SOT_SMD:TSOT-23-6", lcsc="C2071056", mpn="AP63205WU-7",
               pins={"1": "5V_BUCK", "3": "VIN_AC", "4": "GND", "5": "SW", "6": "BST"}),
    "L1": dict(sym="Device:L", value="4.7uH", fp="Inductor_SMD:L_Cenker_CKCS4030", lcsc="C354587",
               mpn="CKCS4030-4.7uH/M", pins={"1": "SW", "2": "5V_BUCK"}),
    "C6": dict(sym="Device:C", value="10uF 50V", fp="Capacitor_SMD:C_1206_3216Metric", lcsc="C13585",
               mpn="CL31A106KBHNNNE", pins={"1": "VIN_AC", "2": "GND"}),
    "C7": dict(sym="Device:C", value="22uF", fp="Capacitor_SMD:C_0805_2012Metric", lcsc="C45783",
               mpn="CL21A226MAQNNNE", pins={"1": "5V_BUCK", "2": "GND"}),
    "C8": dict(sym="Device:C", value="22uF", fp="Capacitor_SMD:C_0805_2012Metric", lcsc="C45783",
               mpn="CL21A226MAQNNNE", pins={"1": "5V_BUCK", "2": "GND"}),
    "C9": dict(sym="Device:C", value="100nF", fp="Capacitor_SMD:C_0402_1005Metric", lcsc="C1525",
               mpn="CL05B104KO5NNNC", pins={"1": "BST", "2": "SW"}),
    "J2": dict(sym="Connector:USB_C_Receptacle_USB2.0_16P", value="USB-C",
               fp="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", lcsc="C165948",
               mpn="TYPE-C-31-M-12",
               pins={"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
                     "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
                     "A5": "CC1", "B5": "CC2",
                     "A6": "USB_D+", "B6": "USB_D+", "A7": "USB_D-", "B7": "USB_D-"}),
    "D1": dict(sym="Device:D_Schottky", value="B5819W",
               fp="Diode_SMD:D_SOD-123", lcsc="C8598", mpn="B5819W SL",
               pins={"1": "VSYS", "2": "5V_BUCK"}),
    "D2": dict(sym="Device:D_Schottky", value="B5819W",
               fp="Diode_SMD:D_SOD-123", lcsc="C8598", mpn="B5819W SL",
               pins={"1": "VSYS", "2": "VBUS"}),
    "D3": dict(sym="Device:LED", value="Red",
               fp="LED_SMD:LED_0603_1608Metric", lcsc="C2286", mpn="KT-0603R",
               pins={"1": "GND", "2": "LED_A"}),
    "Q1": dict(sym="Transistor_FET:AO3400A", value="AO3400A",
               fp="Package_TO_SOT_SMD:SOT-23", lcsc="C20917", mpn="AO3400A",
               pins={"1": "+3V3", "2": "ESP_TX", "3": "AC_RX"}),
    "Q2": dict(sym="Transistor_FET:AO3400A", value="AO3400A",
               fp="Package_TO_SOT_SMD:SOT-23", lcsc="C20917", mpn="AO3400A",
               pins={"1": "+3V3", "2": "ESP_RX", "3": "AC_TX"}),
    "SW1": dict(sym="Switch:SW_Push", value="BOOT",
                fp="Button_Switch_SMD:SW_SPST_TS-1088-xR020", lcsc="C455280", mpn="TS-1088R-02026",
                pins={"1": "BOOT", "2": "GND"}),
    "R1": dict(sym="Device:R", value="10k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25744",
               mpn="0402WGF1002TCE", pins={"1": "+3V3", "2": "EN"}),
    "R2": dict(sym="Device:R", value="10k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25744",
               mpn="0402WGF1002TCE", pins={"1": "+3V3", "2": "IO8"}),
    "R3": dict(sym="Device:R", value="10k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25744",
               mpn="0402WGF1002TCE", pins={"1": "5V_BUCK", "2": "AC_RX"}),
    "R4": dict(sym="Device:R", value="10k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25744",
               mpn="0402WGF1002TCE", pins={"1": "5V_BUCK", "2": "AC_TX"}),
    "R5": dict(sym="Device:R", value="10k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25744",
               mpn="0402WGF1002TCE", pins={"1": "+3V3", "2": "ESP_TX"}),
    "R6": dict(sym="Device:R", value="10k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25744",
               mpn="0402WGF1002TCE", pins={"1": "+3V3", "2": "ESP_RX"}),
    "R7": dict(sym="Device:R", value="1k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C11702",
               mpn="0402WGF1001TCE", pins={"1": "LED", "2": "LED_A"}),
    "R8": dict(sym="Device:R", value="5.1k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25905",
               mpn="0402WGF5101TCE", pins={"1": "CC1", "2": "GND"}),
    "R9": dict(sym="Device:R", value="5.1k", fp="Resistor_SMD:R_0402_1005Metric", lcsc="C25905",
               mpn="0402WGF5101TCE", pins={"1": "CC2", "2": "GND"}),
    "C1": dict(sym="Device:C", value="10uF", fp="Capacitor_SMD:C_0603_1608Metric", lcsc="C19702",
               mpn="CL10A106KP8NNNC", pins={"1": "VSYS", "2": "GND"}),
    "C2": dict(sym="Device:C", value="22uF", fp="Capacitor_SMD:C_0805_2012Metric", lcsc="C45783",
               mpn="CL21A226MAQNNNE", pins={"1": "+3V3", "2": "GND"}),
    "C3": dict(sym="Device:C", value="100nF", fp="Capacitor_SMD:C_0402_1005Metric", lcsc="C1525",
               mpn="CL05B104KO5NNNC", pins={"1": "+3V3", "2": "GND"}),
    "C4": dict(sym="Device:C", value="1uF", fp="Capacitor_SMD:C_0402_1005Metric", lcsc="C52923",
               mpn="CL05A105KA5NQNC", pins={"1": "+3V3", "2": "GND"}),
    "C5": dict(sym="Device:C", value="1uF", fp="Capacitor_SMD:C_0402_1005Metric", lcsc="C52923",
               mpn="CL05A105KA5NQNC", pins={"1": "EN", "2": "GND"}),
}

POWER_NETS = {"VSYS", "5V_BUCK", "VIN_AC", "VBUS", "+3V3", "GND"}


def nets():
    out = {}
    for ref, p in PARTS.items():
        for pin, net in p["pins"].items():
            out.setdefault(net, []).append((ref, pin))
    return out


if __name__ == "__main__":
    for n, nodes in sorted(nets().items()):
        print(n, len(nodes), nodes if len(nodes) < 12 else str(len(nodes)) + " nodes")
