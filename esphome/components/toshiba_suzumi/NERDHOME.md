# toshiba_suzumi (Nerdhome-versie)

Deze map is een kopie van de ESPHome-component
[pedobry/esphome_toshiba_suzumi](https://github.com/pedobry/esphome_toshiba_suzumi),
commit `a306be6` (9 juli 2026), onder de GPL-3-licentie (zie `LICENSE`).

## Wijzigingen door Nerdhome (23 oktober 2026)

- Plasmafilter toegevoegd als schakelaar (`plasma:` onder de climate-config). Leest en
  schrijft register `0xC7` met `0x18` = aan en `0x10` = uit, zoals ook
  [florianbrede-ayet/esphome-toshiba-hvac-controller](https://github.com/florianbrede-ayet/esphome-toshiba-hvac-controller)
  doet. De stand wordt bij het opstarten en bij elke poll opgevraagd en alleen gepubliceerd
  als de unit een geldige waarde terugstuurt. Bij een binnenunit zonder plasmafilter blijft
  de schakelaar daardoor op "Onbekend" in Home Assistant.
- Na schakelen wordt het register teruggelezen; de schakelaar verspringt pas als de unit het
  bevestigt.

Gewijzigde bestanden: `climate.py`, `toshiba_climate.h`, `toshiba_climate.cpp`,
`toshiba_climate_mode.h`. Alle toevoegingen zijn in de code gemarkeerd met "Nerdhome".
