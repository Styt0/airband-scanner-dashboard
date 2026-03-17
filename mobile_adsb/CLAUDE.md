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

## Gerelateerde Projecten
- GeoSentinel (geospatiale monitoring): zie `../geosentinel/CLAUDE.md`
- OSINT Researcher: zie `../osint_researcher/CLAUDE.md`
