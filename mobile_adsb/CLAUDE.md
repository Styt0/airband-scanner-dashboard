# Mobile ADS-B / Airband — Claude Code Context

## Project Doel
Mobiele ADS-B ontvangst en airband communicatie monitoring voor veld- en politie-operaties.

## Bestanden
```
MOBILE_ADSB_AIRBAND_SPEC.md   # Volledige specificatie
```

## Kernconcepten
- ADS-B ontvangst op 1090 MHz (vliegtuigpositie)
- Airband communicatie (VHF 118-137 MHz)
- Mobiele setup voor buiten gebruik
- Integratie met ATAK (Android Tactical Assault Kit)

## SDR Hardware
- RTL-SDR voor ontvangst
- Antenne configuratie voor dual-band (ADS-B + Airband)

## Software
- dump1090 / readsb voor ADS-B decoding
- SDR++ of GQRX voor airband monitoring
- TAK server integratie voor positierapportage

## Gerelateerde projecten
- [[geosentinel/CLAUDE|geosentinel]] — ADS-B als geospatiale OSINT feed
- [[osint_researcher/CLAUDE|osint_researcher]] — vluchtdata als OSINT bron
- [[airband_scanner/AIRBAND_PROJECT|airband_scanner]] — RPi airband setup met ADS-B component
- [[ham_scanner/HAM_SCANNER_PLAN|ham_scanner]] — APRS vervangt ADS-B in ham stack
- [[airwave-aggregator/CLAUDE|airwave-aggregator]] — frontend voor frequentie/tracking data
