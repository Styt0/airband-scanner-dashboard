# ZimaOS Homeserver — Claude Code Context

## Server Toegang
- **IP:** 192.168.0.237
- **SSH:** `ssh zimaos` (key-based, geen wachtwoord nodig)
- **SSH key:** `C:/Users/Tom/.ssh/zimaos`
- **User:** styto (member van docker groep — docker zonder sudo)
- **ZimaOS login:** styto / beelinkbee
- **Sudo:** `echo beelinkbee | sudo -S <command>`

## Snelle Docker commando's via SSH
```bash
ssh zimaos 'docker ps'
ssh zimaos 'docker restart <naam>'
ssh zimaos 'docker logs <naam> --tail 50'
ssh zimaos 'cd /var/lib/casaos/apps/<naam> && docker compose up -d'
ssh zimaos 'docker compose -f /var/lib/casaos/apps/<naam>/docker-compose.yml pull && docker compose -f /var/lib/casaos/apps/<naam>/docker-compose.yml up -d'
```

## Servarr Stack — Poorten & API Keys
| Service      | Poort | API Key / Login                      |
|--------------|-------|--------------------------------------|
| Sonarr       | 8989  | `481ffe1e91ca4d38b6d0fa01f4c7d011`   |
| Radarr       | 7878  | (via Radarr UI: Settings → General)  |
| Lidarr       | 8686  | `bcbca9bfcf734a53832f00ac4874679d`   |
| Readarr      | 8787  | `54ab22bdd59e48a8bd805ecb6b8e1698`   |
| Prowlarr     | 9696  | `291670267f394566be7fba8093ec60f5`   |
| Overseerr    | 5055  | (via Overseerr UI)                   |
| qBittorrent  | 8181  | user: admin / pass: beelinkbee       |
| Plex         | 32400 | (via Plex UI)                        |
| Calibre-Web  | 8083  | user: admin / pass: admin123         |

## Directory Structuur
```
/media/Quick-Storage/
├── media/
│   ├── movies/        → Radarr library
│   ├── tv/            → Sonarr library
│   ├── music/         → Lidarr library
│   └── books/         → Readarr library + Calibre-Web bibliotheek
│       └── metadata.db → Calibre library database
└── downloads/         → qBittorrent download map (alle *arr apps)

/DATA/AppData/<appnaam>/config/  → Config per app
/var/lib/casaos/apps/<appnaam>/docker-compose.yml  → ZimaOS compose files
/DATA/AppData/readarr/config/readarr-to-calibre.sh  → Sync script (Readarr → Calibre-Web)
/DATA/AppData/readarr/config/readarr-calibre.log    → Log van sync acties
```

## ZimaOS App Beheer
- App configs: `/var/lib/casaos/apps/<naam>/docker-compose.yml`
- Starten: `ssh zimaos 'cd /var/lib/casaos/apps/<naam> && docker compose up -d'`
- Stoppen: `ssh zimaos 'docker stop <naam>'`
- Logs: `ssh zimaos 'docker logs <naam> --tail 100'`

## Servarr API gebruiken (voorbeeld Sonarr)
```bash
curl -s "http://192.168.0.237:8989/api/v3/system/status" -H "X-Api-Key: 481ffe1e91ca4d38b6d0fa01f4c7d011"
```
- Lidarr/Readarr v0.x gebruiken `X-Api-Key` header NIET — gebruik `?apikey=<key>` query param
- Sonarr/Radarr/Prowlarr gebruiken `X-Api-Key` header

## Calibre-Web Setup
- **Container:** `linuxserver/calibre-web:0.6.24` met `DOCKER_MODS: ghcr.io/linuxserver/mods:universal-calibre`
- **Library path (in container):** `/books` → `/media/Quick-Storage/media/books/` op host
- **Config (in container):** `/config` → `/DATA/AppData/calibre-web/config/`
- **Calibre-Web config DB:** `/DATA/AppData/calibre-web/config/app.db`
- **Calibre library DB:** `/media/Quick-Storage/media/books/metadata.db`
- **Uploads ingeschakeld via:** `sqlite3 /DATA/AppData/calibre-web/config/app.db "UPDATE settings SET config_uploading=1"`

### Calibre 9.4 schema fix (eenmalig toegepast)
Calibre 9.4 (via DOCKER_MODS) mist `isbn` en `flags` kolommen die Calibre-Web 0.6.24 verwacht:
```sql
-- Uitvoeren in: docker exec calibre-web sqlite3 /books/metadata.db
ALTER TABLE books ADD COLUMN isbn TEXT NOT NULL DEFAULT "";
ALTER TABLE books ADD COLUMN flags INTEGER NOT NULL DEFAULT 1;
```

### Readarr → Calibre-Web sync
- Script: `/DATA/AppData/readarr/config/readarr-to-calibre.sh` (in container: `/config/readarr-to-calibre.sh`)
- Readarr Custom Script notification (id:1): trigger op `onReleaseImport` + `onUpgrade`
- Log: `/DATA/AppData/readarr/config/readarr-calibre.log`
- Script voert `docker exec calibre-web calibredb add <filepath> --library-path /books` uit

## Readarr Metadata Setup
- **Metadata bron:** `https://api.bookinfo.pro` (NIET de default `api.bookinfo.club` — die is dood sinds 2025, NXDOMAIN)
- **Fix toepassen:** `curl -s -X PUT "http://localhost:8787/api/v1/config/development?apikey=54ab22bdd59e48a8bd805ecb6b8e1698" -H "Content-Type: application/json" -d '{"metadataSource":"https://api.bookinfo.pro"}'`
- **Readarr is EOL:** Project officieel gestopt op 2025-06-27; `linuxserver/readarr:develop` heeft geen amd64 manifest meer — bij 0.3.10-develop blijven
- **Zoeken werkt niet?** Controleer altijd eerst: `curl -s "http://localhost:8787/api/v1/config/development?apikey=54ab22bdd59e48a8bd805ecb6b8e1698" | python3 -c "import sys,json; print(json.load(sys.stdin).get('metadataSource'))"`

## Prowlarr Tips
- **Indexer sync naar Readarr/Sonarr/Radarr:** `POST /api/v1/command` met `{"name":"ApplicationIndexerSync"}` — NIET `/api/v1/application/<id>/sync` (geeft 405)
- **Readarr app ID in Prowlarr:** 4 (fullSync, syncCategories: 7000/7010/7020/7030/7050/3030)
- **EBookBay:** toegevoegd als ID=23; `ebb.la` heeft SSL cert mismatch → Prowlarr cert validatie staat op disabled
- **Book search test:** `curl -s "http://localhost:9696/api/v1/search?query=dune&categories=7000&type=search&apikey=291670267f394566be7fba8093ec60f5" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d), 'results')"`

## Bekende Issues (opgelost)
- Readarr docker-compose had template vars `$PUID/$PGID/$TZ/$AppID` → vervangen door echte waarden
- Readarr image: `linuxserver/readarr:0.3.10-develop` (geen latest/develop tag beschikbaar voor amd64)
- Lidarr had `TZ=Europe/London` → gecorrigeerd naar `Europe/Brussels`
- Calibre-Web docker-compose had dezelfde template var bug → zelfde fix toegepast
- PUID=1000, PGID=1000, TZ=Europe/Brussels voor alle containers
- **ZimaOS patroon:** Apps geïnstalleerd via CasaOS store hebben `$PUID/$PGID/$TZ/$AppID` nooit vervangen → altijd controleren bij crashende containers!

## Overige Services
| Service              | Poort | Beschrijving                        |
|----------------------|-------|-------------------------------------|
| OpenStreetMap        | 8085  | Tile server België (raster tiles)   |
| Kiwix                | 8080  | Offline Wikipedia (EN, no-pics)     |
| AdGuard Home         | 3001  | DNS adblocker                       |
| Ollama               | 11434 | LLM inference                       |
| Open WebUI           | 3050  | Ollama web interface                |
| Faster Whisper       | 10300 | Speech-to-text                      |
| RetroArch Web        | 8183  | Retro gaming                        |
| Downtify             | 8582  | Spotify downloader                  |
| MiniDLNA             | 8200  | DLNA media server (750 audio, 1475 video) |

## OpenStreetMap Tile Server
- **Container:** `overv/openstreetmap-tile-server:2.3.0`
- **Tile URL:** `http://192.168.0.237:8085/tile/{z}/{x}/{y}.png`
- **Demo pagina:** `http://192.168.0.237:8085/`
- **Data:** `/media/Quick-Storage/osm/data/` (PostgreSQL 14 + PostGIS + stijlen + PBF)
- **PostgreSQL data op host:** `/media/Quick-Storage/osm/data/database/postgres/` (22GB na BE import)
- **Tiles cache:** `/media/Quick-Storage/osm/data/tiles/`
- **Compose:** `/media/Quick-Storage/osm/docker-compose.yml` (NIET via CasaOS)
- **Beheer:** `docker compose -f /media/Quick-Storage/osm/docker-compose.yml up/down`
- **Dataset:** België OSM volledig geïmporteerd (142.704 road rows in planet_osm_roads)
- **osmium:** beschikbaar INSIDE container op `/usr/bin/osmium` v1.14.0 — gebruik `docker exec openstreetmap-tile-server osmium ...`
- **osm2pgsql append:** `docker exec openstreetmap-tile-server osm2pgsql --append --slim -G --hstore --tag-transform-script /data/style/openstreetmap-carto.lua -S /data/style/openstreetmap-carto.style -d gis /data/<file>.osm.pbf`
- **PBF bestanden** moeten in `/media/Quick-Storage/osm/data/` staan zodat ze in container zichtbaar zijn als `/data/`

### OSM TODO (in uitvoering)
- [x] België geïmporteerd (647MB PBF → 22GB PostgreSQL)
- [ ] **Nederland toevoegen** — PBF gedownload: `/media/Quick-Storage/osm/netherlands-latest.osm.pbf` (1.3GB) — verplaats naar `/data/`, append met osm2pgsql
- [ ] **Luxembourg toevoegen** — PBF gedownload: `/media/Quick-Storage/osm/luxembourg-latest.osm.pbf` (44MB)
- [ ] **Europa lowres** — download `europe-latest.osm.pbf` (31GB van geofabrik), filter met osmium naar motorways/trunk/primary + cities + rivers, append
- [ ] **Wereld superlow** (optioneel) — planet.osm.pbf (85GB), filter naar coastlines + capitals + country borders → ~1-3GB gefilterd, ~10GB PostgreSQL

### OSM bekende issues (opgelost)
- Volume was fout: `/var/lib/postgresql/12/main` → PostgreSQL gebruikt `/data/database/postgres/` (via `/data` volume)
- `/data/style/` en `/data/database/` en `/data/tiles/` moeten bestaan vóór import
- Import: `docker run --rm -e DOWNLOAD_PBF=... -v /media/Quick-Storage/osm/data:/data -v /media/Quick-Storage/osm/tiles:/var/lib/mod_tile overv/openstreetmap-tile-server:2.3.0 import`
- Tiles opgeslagen als `.meta` bestanden (mod_tile formaat), niet als losse .png
- Eerste tile-render duurt ~30s; daarna gecached en razendsnel (<20ms)
- ZimaOS heeft GEEN apt/apk/snap → osmium alleen via container beschikbaar

## Kiwix Setup
- **Container:** `ghcr.io/kiwix/kiwix-serve:3.7.0-2`
- **ZIM locatie:** `/media/Quick-Storage/kiwix/zim/` (op Quick-Storage, /DATA had onvoldoende ruimte)
- **ZIM bestand:** `wikipedia_en_all_nopic_2025-12.zim` (48GB, dec 2025)
- **Download log:** `/media/Quick-Storage/kiwix/wget-wiki.log`
- **Compose:** `/var/lib/casaos/apps/big-bear-kiwix-serve/docker-compose.yml`
- **Nieuw ZIM toevoegen:** Zet het in `/media/Quick-Storage/kiwix/zim/` en update compose `command:` of herstart

### Kiwix bekende issue (opgelost)
- Container crashte door lege `/data` dir (geen ZIM bestanden) → `*.zim` glob faalt op lege map
- Oorspronkelijke volume `/DATA/AppData/.../zim` had geen ruimte (5.5GB vrij, ZIM is 48GB)
- Fix: volume verplaatst naar Quick-Storage, compose bijgewerkt met `command: "*.zim"`

## Readarr Quality Profile
- **eBook profiel (id=1) toegestane formats:** Unknown Text, PDF, MOBI, EPUB, AZW3 (PDF + Unknown Text waren uitgeschakeld — fix toegepast)
- Comics/graphic novels komen binnen als CBZ/CBR → worden als "Unknown Text" geclassificeerd → moet aanstaan
- **Downloads werken niet?** Check: zijn er auteurs/boeken gemonitord? Trigger manual search: `POST /api/v1/command` met `{"name":"AuthorSearch","authorId":<id>}`

## Open Taken (volgende sessie)
- **OSM tile server:** NL + LU appenden, Europa lowres downloaden/filteren/appenden (zie OSM TODO)
- **Readarr → Calibre-Web:** sync script werkt voor test-event, maar controleer of echte boekdownloads ook doorkomen (log: `/DATA/AppData/readarr/config/readarr-calibre.log`)
- **Home Assistant:** toegang krijgen via SSH of web UI op lokaal netwerk, alles inventariseren
- **Grafana dashboard:** visueel interessant huisdashboard bouwen met HA-data (sensors, energie, aanwezigheid, etc.)

## Home Assistant (TODO — nog niet onderzocht)
- Waarschijnlijk op lokaal netwerk, IP onbekend — scan met `ssh zimaos "nmap -sn 192.168.0.0/24"` of check router
- Doel: Grafana dashboard met huisstatus (sensors, energie, klimaat, aanwezigheid)
- HA heeft een REST API + WebSocket API + long-lived access tokens
- Grafana kan via `grafana-plugin-datasource-infinity` of InfluxDB/Prometheus HA integratie

---
## Sessie Update — 2026-03-10

### Storage Cleanup
- **Ollama models verwijderd** (`/DATA/AppData/ollama/models/`) — geen gebruik, 8.8GB vrijgekomen
- **PLEX $RECYCLE.BIN leeggemaakt** — 169GB vrijgekomen op `/media/PLEX`
- **OSM osm2pgsql gekilled** — liep al 5 dagen (NL import nooit afgerond), alle OSM data getruncate
- **/DATA:** 96% → 76% | **PLEX drive:** 73% → 70%

### OSM Status (RESET)
- Alle planet_osm_* tabellen getruncate + VACUUM FULL uitgevoerd
- **TODO: België opnieuw importeren** (was ~22GB PostgreSQL)
- NL/LU/Europa import geannuleerd — te zwaar voor server, enkel België houden
- osm2pgsql limiet: zet CPU limit op container zodat servarr stack prioriteit houdt

### Plex Docker-Compose Gecorrigeerd
- **Config:** `/DATA/.casaos/apps/plex/docker-compose.yml`
- `/dev/dvb` verwijderd (bestaat niet op deze server)
- Duplicate mounts gefixed (waren 2x `/tv` en 2x `/movies`)
- Nieuwe mounts toegevoegd voor PLEX WD drive:

| Container pad | Host pad |
|---------------|----------|
| `/tv` | `/media/Quick-Storage/media/tv` |
| `/movies` | `/media/Quick-Storage/media/movies` |
| `/music` | `/media/Quick-Storage/media/music` |
| `/books` | `/media/Quick-Storage/media/books` |
| `/downloads` | `/media/Quick-Storage/downloads` |
| `/plex-tv` | `/media/PLEX/Media/TV Shows` |
| `/plex-movies` | `/media/PLEX/Media/Movies` |
| `/plex-music` | `/media/PLEX/Media/Music` |
| `/plex-books` | `/media/PLEX/Media/Books` |
| `/plex-calibre` | `/media/PLEX/Media/Calibre` |

### Storage Overzicht (actueel)
| Locatie | Grootte | Gebruik | Inhoud |
|---------|---------|---------|--------|
| `/media/PLEX` (sda1) | 3.6TB | ~70% | 383 films, Music, Books, Calibre |
| `/media/Quick-Storage` (nvme RAID0) | 1.8TB | ~60% | 148 TV shows, 30 films, music, downloads, osm, kiwix |
| `/DATA` (mmcblk0p8) | 46GB | ~76% | AppData, configs |

### ⚠️ Correctie bestaande docs
- App configs zitten op **`/DATA/.casaos/apps/<naam>/`** (NIET `/var/lib/casaos/apps/<naam>/`)
- Docker beheer: `cd /DATA/.casaos/apps/<naam> && sudo docker compose up -d`
- Docker config permission error `/DATA/.docker/config.json` → WARNING maar geen probleem, alles werkt

### Open Taken (bijgewerkt)
- **OSM:** België opnieuw importeren (PBF beschikbaar op `/media/Quick-Storage/osm/`)
- **OSM:** CPU resource limit instellen op container
- **Plex:** PLEX WD drive libraries toevoegen in Plex UI (`/plex-tv`, `/plex-movies`, etc.)
- **Readarr → Calibre-Web:** sync verificeren
- **Home Assistant:** inventariseren

## FileBot Setup (2026-03-10)
- **Container:** jlesage/filebot:latest
- **Web UI:** http://192.168.0.237:5800
- **Config:** /DATA/AppData/filebot/config/
- **License:** PX74512168 (lifetime, geldig tot 2075)
- **Rename script:** /DATA/AppData/filebot/rename-media.sh
- **Compose:** /DATA/.casaos/apps/filebot/docker-compose.yml
- **Filebot executable in container:** /opt/filebot/filebot
- **Action flag:** gebruik --action move (niet rename)

### Rename commando's
```bash
# Dry-run TV
docker exec filebot /opt/filebot/filebot -rename "/storage/tv" --db TheTVDB --format "{n}/{'Season '+s}/{n} - {s00e00} - {t}" --action test --conflict skip -non-strict

# Rename TV
docker exec filebot /opt/filebot/filebot -rename "/storage/tv" --db TheTVDB --format "{n}/{'Season '+s}/{n} - {s00e00} - {t}" --action move --conflict skip -non-strict

# Rename Films
docker exec filebot /opt/filebot/filebot -rename "/storage/movies" "/storage/plex-movies" --db TheMovieDB --format "{n.colon(' -')} ({y})" --action move --conflict skip -non-strict
```

## FileBot Auto-Rename (2026-03-10)
- **Script:** /DATA/AppData/filebot/auto-rename.sh
- **Cron:** elke 15 minuten automatisch (styto crontab)
- **Log:** /DATA/AppData/filebot/auto-rename.log
- **Plex token:** WkxszkwNde3kBZTkzrwB
- **Plex library IDs:** 1=Films(QS), 2=Series, 3=Music, 4=Films(PLEX)

### Handmatige Plex refresh
```bash
curl -s 'http://localhost:32400/library/sections/all/refresh?X-Plex-Token=WkxszkwNde3kBZTkzrwB'
```

### Cron beheren
```bash
crontab -l          # bekijken
crontab -e          # aanpassen
```

## FileBot Setup (2026-03-10)
- **Container:** jlesage/filebot:latest
- **Web UI:** http://192.168.0.237:5800
- **Config:** /DATA/AppData/filebot/config/
- **License:** PX74512168 (lifetime, geldig tot 2075)
- **Rename script:** /DATA/AppData/filebot/rename-media.sh
- **Compose:** /DATA/.casaos/apps/filebot/docker-compose.yml
- **Filebot executable:** /opt/filebot/filebot (gebruik dit in docker exec!)
- **Action flag:** gebruik --action move (niet rename — bestaat niet)

### Gemounte volumes
| Container | Host |
|-----------|------|
| /storage/tv | /media/Quick-Storage/media/tv |
| /storage/movies | /media/Quick-Storage/media/movies |
| /storage/plex-tv | /media/PLEX/Media/TV Shows |
| /storage/plex-movies | /media/PLEX/Media/Movies |
| /storage/plex-music | /media/PLEX/Media/Music |
| /storage/plex-books | /media/PLEX/Media/Books |
| /storage/downloads | /media/Quick-Storage/downloads |

### Rename commando's


## Gerelateerde projecten
- [[ai_workstation/CLAUDE|ai_workstation]] — lokale AI-modellen (OpenWebUI, Ollama) op deze server
- [[geosentinel/CLAUDE|geosentinel]] — geospatiale threat-monitoring, draait op deze server
- [[map_server/CLAUDE|map_server]] — offline OSM tile server, draait op deze server
- [[network_security/CLAUDE|network_security]] — AdGuard DNS + Tailscale, draait op deze server
- [[offline_services/CLAUDE|offline_services]] — Kiwix + RetroArch, draait op deze server
- [[osint_researcher/CLAUDE|osint_researcher]] — OSINT pipeline, draait op deze server
- [[plex_media/CLAUDE|plex_media]] — Plex media server, draait op deze server
- [[servarr_stack/CLAUDE|servarr_stack]] — media automation stack, draait op deze server
- [[terrorism_database/CLAUDE|terrorism_database]] — MkDocs kennisdatabank, draait op deze server
