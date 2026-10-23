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

### Wat Breeze voor Toshiba in Home Assistant zet

- Het airco-entity (standen, temperatuur, ventilator, zwenken verticaal én horizontaal) en het vermogensniveau.
- **Actie**: of de unit echt koelt, verwarmt, ontvochtigt, ventileert of stilstaat (*inactief*), op basis van de compressor in het buitendeel.
- **Presets**: Eco, Boost (Hi POWER), Silent 1 en 2, Slapen, Comfort, Fireplace 1 en 2. Vorstbeveiliging (8 °C) en de vloerstand staan bewust uit.
- **Lamellen verticaal**: vaste stand (boven t/m onder) of zwenken.
- **Plasmafilter** aan/uit. Heeft de binnenunit geen plasmafilter, dan meldt hij nooit een stand en blijft de schakelaar op *Onbekend*.
- **Zelfreiniging**: aan zolang de unit zich na koelen of drogen droogblaast (ca. 30 minuten, ventilator laag, airco staat op uit).
- **Wifi-lampje** op de binnenunit aan/uit; de stand wordt onthouden.
- **Ruimtetemperatuur**: de unit meldt hele graden, elke minuut opgevraagd en afgevlakt met een glijdend gemiddelde over 10 minuten.
- **Buitentemperatuur** van de buitenunit (alleen als het buitendeel aan staat).
- **Energie vandaag** (kWh) uit de eigen meter van de unit en een geschat **Vermogen** (W), op modellen met energiemeting. De unit krijgt daarvoor de klok van Home Assistant.
- **Draaiuren** (totaal) en **Draaiuren sinds onderhoud**, met een instelbaar **Onderhoudsinterval** (standaard 250 uur), een melding **Onderhoud nodig** en een knop **Onderhoud uitgevoerd** die de teller op nul zet. Een uur telt mee zodra de unit aan staat, in elke stand.
- **Diagnose, standaard verborgen**: compressorbelasting en -stroom, pers- en zuiggastemperatuur, warmtewisselaar buiten en binnen (TC, TCJ) en ventilatortoerental. Deze komen uit statusberichten die niet elk model stuurt; zet ze in Home Assistant aan als je unit ze levert.
- **Van de Breeze zelf**: chiptemperatuur, IP-adres, wifi-netwerk, wifi-signaal, ESPHome-versie en uptime.

Wat een unit niet ondersteunt (bijvoorbeeld horizontale lamellen of een preset), negeert hij. Losse ESPHome-entiteiten kunnen in Home Assistant niet op *Niet beschikbaar* staan; dat kan alleen het hele apparaat.

## Licenties

De firmware gebruikt de ESPHome-componenten [esphome_toshiba_suzumi](https://github.com/pedobry/esphome_toshiba_suzumi) en [esphome-daikin-s21](https://github.com/asund/esphome-daikin-s21), beide GPL-3. Wie gecompileerde firmware verspreidt, moet de broncode beschikbaar stellen; dat gebeurt hier: de config staat in deze repository en de componenten worden bij het bouwen van GitHub gehaald. De Toshiba-component staat als aangepaste kopie (met plasmafilter) in [`esphome/components/toshiba_suzumi/`](esphome/components/toshiba_suzumi/NERDHOME.md), met de oorspronkelijke GPL-3-licentie en een overzicht van de wijzigingen. Merknamen worden alleen beschrijvend gebruikt ("voor Toshiba", "voor Daikin"); dit product is niet van of goedgekeurd door Toshiba of Daikin.
