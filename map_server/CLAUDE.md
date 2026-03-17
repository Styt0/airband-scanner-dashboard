# OSM Tile Server — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
Offline OpenStreetMap tile server voor België (en evt. BeNeLux) op ZimaOS.

## Stack
- **Container:** `overv/openstreetmap-tile-server:2.3.0`
- **Tile URL:** `http://192.168.0.237:8085/tile/{z}/{x}/{y}.png`
- **Compose:** `/media/Quick-Storage/osm/docker-compose.yml` (NIET via CasaOS)

## Paden op NAS
```
/media/Quick-Storage/osm/data/           # PostgreSQL + styles + PBF
/media/Quick-Storage/osm/data/database/postgres/  # 22GB na BE import
/media/Quick-Storage/osm/data/tiles/     # Tile cache (.meta formaat)
```

## PBF Bestanden
```
/media/Quick-Storage/osm/belgium-latest.osm.pbf
/media/Quick-Storage/osm/netherlands-latest.osm.pbf   (1.3GB, klaar voor import)
/media/Quick-Storage/osm/luxembourg-latest.osm.pbf    (44MB, klaar voor import)
```

## Beheer Commando's
```bash
# Start/stop tile server
ssh zimaos 'docker compose -f /media/Quick-Storage/osm/docker-compose.yml up -d'
ssh zimaos 'docker compose -f /media/Quick-Storage/osm/docker-compose.yml down'

# Append import (NL of LU)
ssh zimaos 'docker exec openstreetmap-tile-server osm2pgsql --append --slim -G --hstore \
  --tag-transform-script /data/style/openstreetmap-carto.lua \
  -S /data/style/openstreetmap-carto.style \
  -d gis /data/<file>.osm.pbf'

# osmium (in container)
ssh zimaos 'docker exec openstreetmap-tile-server osmium ...'
```

## Status
- België volledig geïmporteerd (22GB PostgreSQL)
- osm2pgsql voor NL/LU klaar (PBF's aanwezig)

## Open Taken
- [ ] België opnieuw importeren na reset (PBF beschikbaar)
- [ ] CPU resource limit instellen op container
- [ ] NL toevoegen na België import
- [ ] LU toevoegen na NL
