# Servarr Stack — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
Geautomatiseerde media pipeline voor films, series, muziek en e-books.

## Componenten
| Service | Poort | API Key / Login |
|---------|-------|-----------------|
| Radarr | 7878 | via UI: Settings → General |
| Sonarr | 8989 | `481ffe1e91ca4d38b6d0fa01f4c7d011` |
| Lidarr | 8686 | `bcbca9bfcf734a53832f00ac4874679d` |
| Readarr | 8787 | `54ab22bdd59e48a8bd805ecb6b8e1698` |
| Prowlarr | 9696 | `291670267f394566be7fba8093ec60f5` |
| qBittorrent | 8181 | admin / beelinkbee |

## Paden
```
/media/Quick-Storage/media/movies/   → Radarr library
/media/Quick-Storage/media/tv/       → Sonarr library
/media/Quick-Storage/media/music/    → Lidarr library
/media/Quick-Storage/media/books/    → Readarr + Calibre-Web
/media/Quick-Storage/downloads/      → qBittorrent downloads
```

## Compose Locaties
```
/DATA/.casaos/apps/<appnaam>/docker-compose.yml
```

## Readarr Specifiek
- **EOL:** gestopt op 2025-06-27, blijf op `0.3.10-develop`
- **Metadata bron:** `https://api.bookinfo.pro` (NIET api.bookinfo.club — dood)
- **Fix metadata:** `curl -X PUT "http://localhost:8787/api/v1/config/development?apikey=54ab22bdd59e48a8bd805ecb6b8e1698" -H "Content-Type: application/json" -d '{"metadataSource":"https://api.bookinfo.pro"}'`

## Calibre-Web
- **Poort:** 8083 — admin / admin123
- **Library:** `/media/Quick-Storage/media/books/metadata.db`
- **Sync:** Readarr → Calibre-Web via `/DATA/AppData/readarr/config/readarr-to-calibre.sh`
- **Log:** `/DATA/AppData/readarr/config/readarr-calibre.log`

## FileBot Auto-Rename
- **Script:** `/DATA/AppData/filebot/auto-rename.sh`
- **Cron:** elke 15 minuten (styto crontab)
- **Log:** `/DATA/AppData/filebot/auto-rename.log`
- **Plex token:** `WkxszkwNde3kBZTkzrwB`
- **Plex library IDs:** 1=Films(QS), 2=Series, 3=Music, 4=Films(PLEX)

## Prowlarr Tips
- Indexer sync: `POST /api/v1/command` met `{"name":"ApplicationIndexerSync"}`
- Readarr app ID in Prowlarr: 4

## Gerelateerde projecten
- [[zimaOS/CLAUDE|zimaOS]] — server waarop dit draait
- [[plex_media/CLAUDE|plex_media]] — ontvangt gedownloade content van deze stack
