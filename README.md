# Nerdhome Breeze

Lokale wifi-adapters voor airco's, met ESPHome in Home Assistant. Geen cloud, geen app: het printje gaat op de service- of wifi-aansluiting van de binnenunit en praat rechtstreeks met de airco.

| Variant | Aansluiting | Print | Firmware |
|---|---|---|---|
| **Breeze voor Toshiba** | CN22 (wifi-poort, 5 V, 9600 8E1) | [`toshiba/`](toshiba/README.md), 24 × 34 mm | [`esphome/breeze-toshiba.yaml`](esphome/breeze-toshiba.yaml) |
| **Breeze voor Daikin** | S21 (12–15 V, 2400 8E2) | [`daikin/`](daikin/README.md), 28 × 42 mm | [`esphome/breeze-daikin.yaml`](esphome/breeze-daikin.yaml) |

Beide printjes gebruiken een ESP32-C6-MINI-1U (wifi 6, U.FL-antenne), USB-C voor de eerste keer flashen en MOSFET-niveau-omzetters naar de 5 V-logica van de airco.

**Status:** beide printjes zijn revisie 1.0 en nog niet in hardware getest.

## Firmware

De ESPHome-config staat in [`esphome/`](esphome/) en wordt op twee manieren gebruikt.

**1. Eigen config per binnenunit (voor ESPHome-gebruikers)**
`breeze-<merk>.yaml` bevat alles wat voor elke unit van dat merk gelijk is. Elke unit krijgt in de ESPHome Builder een kleine eigen yaml (voorbeelden: [`toshiba-woonkamer.yaml`](esphome/toshiba-woonkamer.yaml), [`daikin-voorbeeld.yaml`](esphome/daikin-voorbeeld.yaml)) met alleen naam, API-sleutel en wifi. De rest komt via `packages:` van GitHub (`refresh: 1d`).

1. Zet de waarden uit [`esphome/secrets.yaml.example`](esphome/secrets.yaml.example) in de `secrets.yaml` van de ESPHome Builder, met per unit een eigen API-sleutel (`openssl rand -base64 32`).
2. Maak per unit een kopie van het voorbeeld en pas `name`, `friendly_name` en de naam van de API-sleutel aan.
3. Eerste keer via USB-C flashen (deksel eraf, print los van de airco; niet herkend? houd BOOT ingedrukt bij het insteken). Daarna gaan updates via wifi.

**2. Kant-en-klare firmware (voor klanten, zonder compileren)**
GitHub Actions bouwt `breeze-<merk>.factory.yaml` bij elke wijziging in `esphome/` en elke 1e van de maand met de nieuwste ESPHome, en publiceert op GitHub Pages:

- Webinstaller: https://jasperbom.github.io/nerdhome-breeze/ (Chrome/Edge, via USB, wifi meteen instellen via Improv)
- Update-kanalen: `…/firmware/toshiba/manifest.json` en `…/firmware/daikin/manifest.json`

Units met deze firmware krijgen in Home Assistant een update-entiteit *Firmware*; elke nieuwe build verschijnt daar als update. Met *Take control* in de ESPHome Builder stap je over op route 1.

## Licenties

De firmware gebruikt de ESPHome-componenten [esphome_toshiba_suzumi](https://github.com/pedobry/esphome_toshiba_suzumi) en [esphome-daikin-s21](https://github.com/asund/esphome-daikin-s21), beide GPL-3. Wie gecompileerde firmware verspreidt, moet de broncode beschikbaar stellen; dat gebeurt hier: de config staat in deze repository en de componenten worden bij het bouwen van GitHub gehaald. Merknamen worden alleen beschrijvend gebruikt ("voor Toshiba", "voor Daikin"); dit product is niet van of goedgekeurd door Toshiba of Daikin.
