# Claude Projects — Centrale Hub

`C:\Users\Tom\OneDrive\Claude\projects\`

Centrale locatie voor alle Claude Code projectcontexten. Elke map = één project met een `CLAUDE.md` die de context, regels en status bevat.

## Structuur

```
projects/
├── README.md
│
│── Thematische Hubs (geconsolideerd)
├── sdr-sigint/                    # SDR/SIGINT Hub — 8 sub-projecten
│   ├── CLAUDE.md                  # Hub overzicht + architectuur
│   ├── airband-scanner/           # RPi airband scanner + ADS-B + STT
│   ├── airband_scanner/           # RPi airband specs (handover doc)
│   ├── airwave-aggregator/        # Frequentie aggregator (React + Mapbox)
│   ├── ham_scanner/               # Ham radio scanner (ZimaBoard)
│   ├── mobile_adsb/               # Mobiele ADS-B + airband
│   ├── sdr-explorer-hub/          # SDR educatief platform
│   ├── sdr-signal-scanner/        # SDR signaalscanner UI
│   └── tuning-maple/              # Frequentie referentie + ISS tracker
│
├── geo-platform/                  # Geo Platform Hub — 2 sub-projecten
│   ├── CLAUDE.md                  # Hub overzicht
│   ├── map_server/                # OSM Tile Server België/BeNeLux
│   └── geosentinel/               # Geospatiale threat monitoring
│
├── broodautomaat/                 # Broodautomaat Hub — 2 sub-projecten
│   ├── CLAUDE.md                  # Hub overzicht
│   ├── breadbot-locator/          # BroodBot (Leaflet + Capacitor)
│   └── broodautomaat-ervaring/    # BroodSpot (Mapbox + profielen)
│
│── ZimaOS & NAS Services
├── zimaOS/                        # ZimaOS homeserver (192.168.0.237) — hoofdproject
├── ai_workstation/                # Open WebUI / Ollama / Whisper
├── servarr_stack/                 # Media automation (Radarr/Sonarr/etc.)
├── network_security/              # AdGuard Home / Tailscale
├── offline_services/              # Kiwix / RetroArch
├── plex_media/                    # Plex / Overseerr / Downtify
│
│── Intelligence & OSINT
├── terrorism_database/            # Kennisdatabank dreigingsanalyse België
├── osint_researcher/              # OSINT pipeline (Open WebUI + Tor)
├── maghreb-watchtower/            # Maghreb monitoring (React) — thema: intelligence
├── osint-hub-collective/          # OSINT research hub (React) — thema: OSINT
│
│── Situational Awareness
├── astro-command-dashboard/       # TangoSierra.One dashboard (React)
│
│── Standalone
└── bushcraft-weekend-planner/     # Bushcraft evenementen (React)
```

> **GitHub repos:** Hub-entry hier bevat alleen context + link. CLAUDE.md voor coding staat IN de repo zelf: `OneDrive\Documents\GitHub\<naam>\CLAUDE.md`

## Thema Toewijzing

| Thema | Projecten | Status |
|-------|-----------|--------|
| **SDR/SIGINT** | airband-scanner, airband_scanner, airwave-aggregator, ham_scanner, mobile_adsb, sdr-explorer-hub, sdr-signal-scanner, tuning-maple | Geconsolideerd in `sdr-sigint/` |
| **Geo Platform** | map_server, geosentinel | Geconsolideerd in `geo-platform/` |
| **Broodautomaat** | breadbot-locator, broodautomaat-ervaring | Geconsolideerd in `broodautomaat/` |
| **Intelligence** | terrorism_database, maghreb-watchtower | Apart (user keuze) |
| **OSINT** | osint_researcher, osint-hub-collective | Apart (user keuze) |
| **Sit. Awareness** | astro-command-dashboard | Cross-thema dashboard |
| **NAS Services** | zimaOS, ai_workstation, servarr_stack, network_security, offline_services, plex_media | ZimaOS infra |
| **Standalone** | bushcraft-weekend-planner | Geen overlap |

## Workflow — Zo werkt het

### Starten met een project
```bash
# Hub-project (bv. SDR hub overzicht)
cd "C:\Users\Tom\OneDrive\Claude\projects\sdr-sigint"
claude

# Sub-project binnen hub
cd "C:\Users\Tom\OneDrive\Claude\projects\sdr-sigint\airwave-aggregator"
claude

# Standalone project
cd "C:\Users\Tom\OneDrive\Claude\projects\terrorism_database"
claude
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
