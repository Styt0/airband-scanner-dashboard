# SDR/SIGINT Hub

Centrale hub voor alle SDR (Software Defined Radio) en SIGINT projecten — van hardware scanners tot web-based frequentietools.

## Sub-projecten

### Hardware / Backend
| Project | Beschrijving | Hardware | Locatie |
|---------|-------------|----------|---------|
| `airband-scanner/` | Airband scanner + ADS-B + speech-to-text | RPi 4 + RTL-SDR (EBAW) | [GitHub repo](https://github.com/Styt0/airband-scanner) |
| `airband_scanner/` | RPi airband project handover (specs) | RPi 4 + RTL-SDR | Lokale specs |
| `ham_scanner/` | Ham radio scanner (Reet, BE) | HydraSDR + ZimaBoard | Lokale specs |
| `mobile_adsb/` | Mobiele ADS-B + airband monitoring | RTL-SDR mobiel | Lokale specs |

### Frontend / Web UI
| Project | Beschrijving | Stack | GitHub |
|---------|-------------|-------|--------|
| `airwave-aggregator/` | Frequentie aggregator + kaart | React + Mapbox GL | [repo](https://github.com/Styt0/airwave-aggregator) |
| `sdr-signal-scanner/` | SDR signaalscanner UI + waterfall | React + shadcn/ui | [repo](https://github.com/Styt0/sdr-signal-scanner) |
| `sdr-explorer-hub/` | SDR educatief platform + cursussen | React + shadcn/ui | [repo](https://github.com/Styt0/sdr-explorer-hub) |
| `tuning-maple/` | Frequentie referentie + ISS tracker | React + shadcn/ui | [repo](https://github.com/Styt0/tuning-maple) |

## Architectuur

```
Hardware Layer:
  RTL-SDR dongles → airband-scanner (RPi) → sdr-hub Docker → SQLite
  HydraSDR       → ham_scanner (ZimaBoard) → sdr-hub Docker
  RTL-SDR mobiel → mobile_adsb → ATAK integratie

Data Layer:
  ADS-B (1090 MHz)  → dump1090/readsb → aircraft positions DB
  Airband (118-137)  → speech-to-text (Deepgram/whisper.cpp) → transcripts
  Ham (24-1800 MHz)  → APRS decoder → station tracking

Frontend Layer:
  airwave-aggregator  → frequentiekaart + lijsten (Mapbox)
  sdr-signal-scanner  → waterfall + multi-band monitoring
  tuning-maple        → frequentie referentie + ISS tracker
  sdr-explorer-hub    → educatie + cursusmodules
```

## SDR Hardware Overzicht
- **RTL-SDR (airband-scanner):** 2x dongles — 1x airband (118-137 MHz), 1x ADS-B (1090 MHz)
- **HydraSDR RFOne (ham_scanner):** 24-1800 MHz, 10 MHz bandbreedte
- **RTL-SDR mobiel (mobile_adsb):** Dual-band voor veldoperaties

## Gemeenschappelijke stack (frontends)
React 18 + TypeScript + Vite + shadcn/ui + Tailwind CSS

## Gerelateerde projecten (buiten hub)
- [[geo-platform/map_server/CLAUDE|map_server]] — offline kaartdata voor frequentiekaarten
- [[geo-platform/geosentinel/CLAUDE|geosentinel]] — ADS-B als geospatiale OSINT feed
- [[osint_researcher/CLAUDE|osint_researcher]] — vluchtdata als OSINT bron

## Werken aan een sub-project
```bash
# Hub context
cd "C:\Users\Tom\OneDrive\Claude\projects\sdr-sigint"

# Specifiek frontend repo
cd "C:\Users\Tom\OneDrive\Documents\GitHub\airwave-aggregator"
npm run dev
```
