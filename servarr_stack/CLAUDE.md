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

## Dutch Audio — Kinder Animatie (2025-03-25)

### Opzet
Releases met Nederlandse audio krijgen voorkeur voor kinder-animatie via een Custom Format + Quality Profile combinatie.

### Custom Format (CF ID 1) — beide apps
- **Naam:** `Dutch/Flemish Audio`
- **Specs:** Language = Dutch (7) OR Flemish (19)
- **Radarr:** `PUT /api/v3/customformat/1` — `X-Api-Key: f0ab335388884239a527bce902574fef`
- **Sonarr:** `PUT /api/v3/customformat/1` — `X-Api-Key: 481ffe1e91ca4d38b6d0fa01f4c7d011`

### Quality Profile (ID 7) — "Animation - Dutch"
| Instelling | Waarde |
|---|---|
| Dutch/Flemish Audio score | +10000 |
| upgradeAllowed | true |
| cutoffFormatScore | 10000 |

> cutoffFormatScore=10000 zorgt dat releases zonder NL audio als "under cutoff" worden beschouwd → Radarr/Sonarr blijft upgraden.

### Op dit profiel (blijft Dutch)
**Radarr (26 films):** Bluey, Shrek 1-4+5, Toy Story 1-4+5, Super Mario, Zootopia 2, SpongeBob, Despicable Me 4, Minions & Monsters, Angry Birds 3, Surf's Up 1+2, Spider-Man Beyond, Star Wars Clone Wars film, en andere Disney/Pixar/kids releases.

**Sonarr (9 series):** Bluey, Star Wars: The Clone Wars, Rebels, Bad Batch, Clone Wars (2003), Young Jedi Adventures, Tales of the Empire, Tales of the Underworld, Maul Shadow Lord.

### Verplaatst naar HD-1080p (profiel 4) — Engels
| App | Titel |
|-----|-------|
| Sonarr | Family Guy, South Park, The Animatrix |
| Radarr | Beavis & Butt-Head Do the Universe, Beavis & Butt-Head Do America, Animal Farm, #TBT Archer/Kingsman, The Animatrix |

### Retroactieve zoekopdracht getriggerd
- Radarr: 31 films gezocht via `POST /api/v3/command {"name":"MoviesSearch","movieIds":[...]}`
- Sonarr: 12 series gezocht via `POST /api/v3/command {"name":"SeriesSearch","seriesId":X}` (per serie)

### Nieuwe kinder-animatie toevoegen
Wijs toe aan profiel **"Animation - Dutch" (ID 7)** in Radarr/Sonarr. Dutch audio releases worden automatisch verkozen boven Engels.

## Gerelateerde projecten
- [[zimaOS/CLAUDE|zimaOS]] — server waarop dit draait
- [[plex_media/CLAUDE|plex_media]] — ontvangt gedownloade content van deze stack
