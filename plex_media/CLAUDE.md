# Plex & Media Delivery — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
Media streaming en content request beheer.

## Componenten
| Service | Poort | Beschrijving |
|---------|-------|--------------|
| Plex | 32400 | Media server |
| Overseerr | 5055 | Content requests |
| Downtify | 8582 | Spotify downloader |

## Plex Token & Library IDs
- **Token:** `WkxszkwNde3kBZTkzrwB`
- **Library IDs:** 1=Films(QS), 2=Series, 3=Music, 4=Films(PLEX)

## Plex Mounts
| Container | Host |
|-----------|------|
| `/tv` | `/media/Quick-Storage/media/tv` |
| `/movies` | `/media/Quick-Storage/media/movies` |
| `/plex-tv` | `/media/PLEX/Media/TV Shows` |
| `/plex-movies` | `/media/PLEX/Media/Movies` |
| `/plex-music` | `/media/PLEX/Media/Music` |
| `/plex-books` | `/media/PLEX/Media/Books` |

## Handige Commando's
```bash
# Handmatige library refresh
ssh zimaos 'curl -s "http://localhost:32400/library/sections/all/refresh?X-Plex-Token=WkxszkwNde3kBZTkzrwB"'

# Plex status
ssh zimaos 'docker ps | grep plex'

# Compose pad
# /DATA/.casaos/apps/plex/docker-compose.yml
```

## Open Taken
- [ ] PLEX WD drive libraries toevoegen in Plex UI (/plex-tv, /plex-movies, etc.)
- [ ] Overseerr sync verificeren (requests → Radarr/Sonarr)
- [ ] Remote access checken buiten lokaal netwerk
