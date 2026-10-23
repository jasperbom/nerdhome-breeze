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

## Wijzigingen door Nerdhome, tweede ronde (23 oktober 2026)

- **Actie (hvac_action):** het climate-entity meldt nu of de unit echt koelt, verwarmt,
  ontvochtigt, alleen ventileert, stilstaat of uit is. Dat komt uit de compressorbelasting
  in de ODU-statusberichten die de unit elke minuut uit zichzelf stuurt (ook als hij uit
  staat). Belasting 0 betekent *inactief*. Is er drie minuten geen ODU-status geweest
  (units die hem niet sturen), dan volgt de actie de gekozen stand, zoals voorheen.
  Tijdens de zelfreiniging na het uitzetten is de actie *ventilator*.
- **Wifi-lampje als schakelaar** (`wifi_led:`), in plaats van alleen de vaste optie
  `disable_wifi_led`. De unit heeft geen leesbaar register voor het lampje, dus de stand
  wordt in flash onthouden en bij het opstarten opnieuw verstuurd.
- **Typenummers** (`idu_model`, `idu_serial`, `idu_software`, `odu_model`, `odu_serial`,
  `odu_software`): de unit stuurt uit zichzelf, ongeveer elke 4 à 5 minuten, een bericht van 114 bytes (type
  `0xE0`) met vaste, met NUL opgevulde ASCII-velden voor binnen- en buitendeel: typenummer
  (21), serienummer (13), datumcode (9) en softwareversie (7). Zie `parse_unit_info_`.
- **Grenscontroles:** een antwoord op het energieregister dat korter is dan de volledige
  uurtabel (units zonder energiemeter), of een ODU/IDU-bericht met een onverwachte lengte,
  wordt genegeerd in plaats van buiten het bericht te lezen.

Gewijzigde bestanden: `climate.py`, `toshiba_climate.h`, `toshiba_climate.cpp`,
`toshiba_climate_mode.h`. Alle toevoegingen zijn in de code gemarkeerd met "Nerdhome".
