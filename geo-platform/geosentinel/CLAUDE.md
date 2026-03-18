# GeoSentinel — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
GeoSentinel is een geospatiale threat-monitoring tool die geo-gecodeerde data (ADS-B vluchten, OSINT feeds, sociale media) combineert om bewegingspatronen en dreigingen te detecteren.

## Stack
- **Python app** met FastAPI backend
- **Docker** op ZimaOS NAS (`192.168.0.237`)
- **Tor proxy** voor anonieme data-ophaling (`socks5://tor:9050`)

## Bestanden
```
main.py          # Hoofdapplicatie / FastAPI entry point
monitor.py       # Monitoring logica
config.py        # Configuratie
utils.py         # Hulpfuncties
requirements.txt # Python dependencies
docker-compose.yml
.env.example     # Template voor secrets
```

## Deploy op ZimaOS
```bash
# Kopieer code naar NAS
scp -r . zimaos:/DATA/AppData/geosentinel/

# Start container
ssh zimaos 'cd /DATA/AppData/geosentinel && docker compose up -d'

# Logs
ssh zimaos 'docker logs geosentinel --tail 50'
```

## Status
- Architecture klaar
- Tor proxy integratie aanwezig
- Needs: deployment op NAS en live testing

## Gerelateerde projecten
- [[zimaOS/CLAUDE|zimaOS]] — server waarop dit draait
- [[osint_researcher/CLAUDE|osint_researcher]] — overlappende OSINT feeds en Tor proxy
- [[map_server/CLAUDE|map_server]] — levert offline kaartdata voor geo-visualisatie
- [[mobile_adsb/CLAUDE|mobile_adsb]] — ADS-B data als geospatiale OSINT feed
- [[terrorism_database/CLAUDE|terrorism_database]] — dreigingsdata als input voor monitoring
