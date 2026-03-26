# Geo Platform Hub

Geospatiale services — offline kaartserver en threat monitoring met geo-data.

> Beide draaien op ZimaOS NAS (192.168.0.237). Server access: zie `../zimaOS/CLAUDE.md`

## Sub-projecten

| Project | Beschrijving | Stack | Status |
|---------|-------------|-------|--------|
| `map_server/` | OSM Tile Server België/BeNeLux | Docker (overv/openstreetmap-tile-server) | BE geimporteerd (22GB) |
| `geosentinel/` | Geospatiale threat monitoring | Python + FastAPI + Docker + Tor | Architecture klaar, needs deploy |

## Architectuur

```
map_server (OSM tiles)
  ├── PostgreSQL (22GB België data)
  ├── Tile URL: http://192.168.0.237:8085/tile/{z}/{x}/{y}.png
  └── PBF bestanden klaar voor NL + LU import

geosentinel (monitoring)
  ├── FastAPI backend
  ├── Tor proxy (socks5://tor:9050)
  ├── Input: ADS-B vluchten, OSINT feeds, sociale media
  └── Output: bewegingspatronen + dreigingsdetectie
```

## Relatie tussen sub-projecten
- **map_server** levert offline kaartdata aan **geosentinel** voor geo-visualisatie
- Beide draaien als Docker containers op dezelfde NAS
- map_server wordt ook gebruikt door SDR/SIGINT frontends (airwave-aggregator, mobile_adsb)

## Gerelateerde projecten (buiten hub)
- [[zimaOS/CLAUDE|zimaOS]] — server waarop beide draaien
- [[sdr-sigint/airwave-aggregator/CLAUDE|airwave-aggregator]] — gebruikt tile server voor frequentiekaart
- [[sdr-sigint/mobile_adsb/CLAUDE|mobile_adsb]] — ADS-B data als input voor geosentinel
- [[osint_researcher/CLAUDE|osint_researcher]] — OSINT feeds als input voor geosentinel
- [[terrorism_database/CLAUDE|terrorism_database]] — dreigingsdata als input voor monitoring

## Werken aan een sub-project
```bash
cd "C:\Users\dell oem\OneDrive\Claude\projects\geo-platform"
```
