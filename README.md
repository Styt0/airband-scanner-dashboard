# Claude Projects — Centrale Hub

`C:\Users\Tom\OneDrive\Claude\projects\`

Centrale locatie voor alle Claude Code projectcontexten. Elke map = één project met een `CLAUDE.md` die de context, regels en status bevat.

## Structuur

```
projects/
├── README.md
│
│── ZimaOS & NAS services
├── zimaOS/                    # ZimaOS homeserver (192.168.0.237) — hoofdproject
├── geosentinel/               # Geospatiale threat monitoring (Python/Docker)
├── terrorism_database/        # Kennisdatabank dreigingsanalyse België
├── osint_researcher/          # OSINT pipeline (Open WebUI + Tor)
├── ai_workstation/            # Open WebUI / Ollama / Whisper
├── map_server/                # OSM Tile Server België
├── servarr_stack/             # Media automation (Radarr/Sonarr/etc.)
├── network_security/          # AdGuard Home / Tailscale
├── offline_services/          # Kiwix / RetroArch
├── plex_media/                # Plex / Overseerr / Downtify
├── mobile_adsb/               # Mobiele ADS-B / Airband monitoring
│
│── GitHub repos  (code in OneDrive\Documents\GitHub\<naam>)
├── airband-scanner/           # RPi airband scanner + ADS-B + speech-to-text
├── airwave-aggregator/        # Frequentie aggregator (React + Mapbox)
├── astro-command-dashboard/   # Mission control dashboard (React)
├── breadbot-locator/          # Broodautomaat locator (React + Leaflet)
├── broodautomaat-ervaring/    # Broodautomaat platform (React + Mapbox)
├── bushcraft-weekend-planner/ # Bushcraft evenementen (React)
├── maghreb-watchtower/        # Maghreb nieuwsmonitoring (React)
├── osint-hub-collective/      # OSINT hub (React)
├── sdr-signal-scanner/        # SDR signaalscanner UI (React)
└── tuning-maple/              # Radio frequentie referentie (React)
```

> **GitHub repos:** Hub-entry hier bevat alleen context + link. CLAUDE.md voor coding staat IN de repo zelf: `OneDrive\Documents\GitHub\<naam>\CLAUDE.md`

## Workflow — Zo werkt het

### Starten met een project
```bash
cd "C:\Users\Tom\OneDrive\Claude\projects\<project>"
claude  # Claude leest automatisch CLAUDE.md
```

### Na een werksessie — wijzigingen opslaan
```bash
cd "C:\Users\Tom\OneDrive\Claude\projects"
git add <project>/CLAUDE.md
git commit -m "<project>: kort beschrijving van wat er veranderde"
```

### Nieuw project toevoegen
1. Maak map aan: `mkdir C:\Users\Tom\OneDrive\Claude\projects\<naam>`
2. Maak `CLAUDE.md` met context
3. Commit: `git add <naam>/ && git commit -m "<naam>: initial project context"`

## Versiegeschiedenis bekijken
```bash
cd "C:\Users\Tom\OneDrive\Claude\projects"
git log --oneline                          # Alle commits
git log --oneline -- zimaOS/CLAUDE.md     # Enkel zimaOS
git diff HEAD~1 zimaOS/CLAUDE.md          # Wat veranderde in laatste commit
git show HEAD:zimaOS/CLAUDE.md            # Vorige versie bekijken
```

## Regels
- **Elke betekenisvolle wijziging = git commit** (geen dump van alle sessies tegelijk)
- **Commit message** = `<project>: wat veranderde` (bv. `zimaOS: Plex mounts gecorrigeerd`)
- **NAS CLAUDE.md is leidend** voor zimaOS — update `/DATA/CLAUDE.md` via SSH als die wijzigt
- **Sub-projecten** refereren naar `../zimaOS/CLAUDE.md` voor server access details

## NAS CLAUDE.md synchroniseren
Wanneer de zimaOS CLAUDE.md geüpdated wordt:
```bash
# Van NAS naar OneDrive kopiëren
ssh zimaos 'cat /DATA/CLAUDE.md' > "C:\Users\Tom\AppData\Local\Temp\NAS_CLAUDE.md"
copy "C:\Users\Tom\AppData\Local\Temp\NAS_CLAUDE.md" "C:\Users\Tom\OneDrive\Claude\projects\zimaOS\CLAUDE.md"
cd "C:\Users\Tom\OneDrive\Claude\projects"
git add zimaOS/CLAUDE.md && git commit -m "zimaOS: sync CLAUDE.md van NAS"

# Van OneDrive naar NAS kopiëren (na lokale wijziging)
scp "C:\Users\Tom\OneDrive\Claude\projects\zimaOS\CLAUDE.md" zimaos:/DATA/CLAUDE.md
```
