# Offline Services — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
Toegang tot kennis en entertainment zonder internet.

## Componenten
| Service | Poort | Beschrijving |
|---------|-------|--------------|
| Kiwix | 8080 | Offline Wikipedia/StackOverflow |
| RetroArch | 8183 | Web-based retro gaming emulator |

## Kiwix
- **ZIM locatie:** `/media/Quick-Storage/kiwix/zim/`
- **ZIM bestand:** `wikipedia_en_all_nopic_2025-12.zim` (48GB, dec 2025)
- **Update script:** `/media/Quick-Storage/kiwix/kiwix-update.sh` (cron: 1e vd maand, 04:00)
- **Update log:** `/media/Quick-Storage/kiwix/kiwix-update.log`

### Nieuw ZIM toevoegen
```bash
# Zet ZIM in juiste map
scp nieuw-bestand.zim zimaos:/media/Quick-Storage/kiwix/zim/
# Herstart container
ssh zimaos 'cd /DATA/.casaos/apps/big-bear-kiwix-serve && docker compose restart'
```

## Open Taken
- [ ] Kiwix update log controleren op succesvolle maandelijkse downloads
- [ ] RetroArch: test of games laden zonder lag
