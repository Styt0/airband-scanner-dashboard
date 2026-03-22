# My Brain Is Full — Vault Claude Code Context

## Project Doel
Obsidian kennisbank beheerd door een crew van 10 AI-subagenten via Claude Code. De agents handelen vault-operaties af via natuurlijke taal: notities opslaan, sorteren, zoeken, verbinden, onderhoud, e-mail/kalender, transcriptie, voeding en emotioneel welzijn.

> Server access en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Stack
- **Obsidian** (lokale vault app) + **Claude Code** (agent dispatcher)
- **10 subagenten** gedefinieerd in `.claude/agents/` (auto-geladen bij sessiestart)
- **Syncthing** voor sync tussen ZimaOS en Windows/telefoon
- **Vault locatie Windows:** `C:\Users\Tom\OneDrive\Claude\MyBrainVault\`
- **Vault locatie ZimaOS:** `/DATA/vault/`
- **Docker:** `/DATA/vault-docker/` (vault-maintenance + syncthing containers)
- **Syncthing Web UI:** `http://192.168.0.237:8384`
- **Syncthing API key:** `JSJaRhAgpZkxsY7DjFsxJyHHdnpxJMun`
- **Syncthing server Device ID:** `AFAJ6NV-N2LLHQE-HDAISGV-GZB7MPD-JJJWANP-RPO3UKK-YJ7AZTB-JTX65QZ`

## Vault Structuur
```
MyBrainVault/
├── 00-Inbox/               # Nieuwe notities wachten hier op sortering
├── 01-Projects/            # Actieve projecten
├── 02-Areas/               # Permanente levensgebieden
│   ├── Finance/data/       # Bankexports, analyses (Argenta, PayPal)
│   ├── Health/data/        # Bloedonderzoek, DNA, bariatrie, psychologische tests
│   ├── Health/Fitness/
│   │   └── Garmin/data/    # Garmin exports (CSV + garmindata_extracted/)
│   ├── Learning/data/
│   ├── Personal/data/      # IDs, geboorteaktes, huwelijksaktes, pensioen
│   ├── Side Projects/data/
│   └── Work/data/          # Certificaten, diploma's, CV exports
├── 03-Resources/           # Referentiemateriaal
├── 04-Archives/            # Gearchiveerde notities
├── Meta/
│   ├── agent-messages.md   # Berichtenbord voor inter-agent communicatie
│   ├── docker/             # Docker config voor ZimaOS deployment
│   │   ├── docker-compose.yml
│   │   └── vault-maintenance/
│   │       ├── Dockerfile
│   │       ├── archive-data-dumps.sh
│   │       └── crontab
│   ├── logs/               # Archiveringslog (archive-data-dumps.log)
│   └── scripts/
│       └── archive-data-dumps.sh  # Windows-versie archiveerscript
├── .claude/
│   ├── agents/             # 10 subagenten (auto-geladen)
│   └── references/         # Gedeelde docs die agents lezen
├── CLAUDE.md               # Routing rules + dispatcher logica
└── My-Brain-Is-Full-Crew/  # GitHub repo (voor updates)
```

## De 10 Agents (routering via CLAUDE.md)

| Prioriteit | Agent | Taak |
|---|---|---|
| 1 | **wellness-guide** | Emotioneel welzijn, mindfulness, stress |
| 2 | **food-coach** | Voeding, dieet, boodschappen, maaltijden |
| 3 | **postman** | Gmail + Google Calendar (MCP) |
| 4 | **transcriber** | Audio, opnames, podcasts → notities |
| 5 | **scribe** | Tekst opslaan, ideeën, brainstorm |
| 6 | **seeker** | Zoeken in vault, vragen over notities |
| 7 | **architect** | Vaultstructuur, templates, MOCs, tags |
| 8 | **sorter** | Inbox triage, notities sorteren |
| 9 | **connector** | Links tussen notities, kennisgraaf |
| 10 | **librarian** | Onderhoud, duplicaten, broken links |

## Docker op ZimaOS (server-side operaties)

```bash
# Status bekijken
ssh zimaos 'docker ps --filter name=vault-maintenance --filter name=syncthing'

# Logs archive script
ssh zimaos 'cat /DATA/vault/Meta/logs/archive-data-dumps.log | tail -20'

# Containers herstarten
ssh zimaos 'cd /DATA/vault-docker && docker compose restart'

# Rebuild na Dockerfile wijziging
ssh zimaos 'cd /DATA/vault-docker && docker compose up -d --build'
```

## Archive Script
- **Werking:** bestanden ouder dan 7 dagen in `data/` mappen → `data/archive/`
- **Trigger:** dagelijks 02:23 (ZimaOS container-cron + Windows Task Scheduler)
- **Windows taak:** `VaultArchiveDataDumps` (schtasks)
- **Log:** `Meta/logs/archive-data-dumps.log`
- **Dekt:** alle 10 `data/` mappen in `02-Areas/`

## Data Mappen Status (2026-03-22)

| Map | Bestanden | Inhoud |
|---|---|---|
| `Health/data/` | 80+ | Bloedonderzoek, DNA, bariatrie, psych tests |
| `Personal/data/` | 28 | IDs, aktes, pensioen, scheiding-dossier |
| `Work/data/` | 16 | Certificaten (CEPOL, OSINT, Drone), diploma's |
| `Finance/data/` | 16 | Argenta exports, PayPal, financiële analyses |
| `Health/Fitness/Garmin/data/` | 5 CSV + extracted/ | Garmin Connect export verwerkt → zie Garmin Health Overview.md |

## Garmin Gezondheidsdata (verwerkt 2026-03-22)
- **Bron:** Garmin Connect export (Jan 2025), uitgepakt in `garmindata_extracted/`
- **Overzichtsnotitie:** `02-Areas/Health/Fitness/Garmin/Garmin Health Overview.md`
- **Key findings:** VO2 Max piek 49 (dec 2023), huidig 45-46 (Excellent), RHR 50-53 bpm
- **Garmin op ZimaOS:** aparte `garmin-fetch-data` + `garmin-influxdb` + `grafana` stack (al aanwezig)

## MCP Servers (postman agent)
- **Gmail** + **Google Calendar** via `.mcp.json` in vaultroot
- Mails/events → notities in vault via postman agent

## Sessie Update — 2026-03-22

### Vault opgezet op ZimaOS
- 4.343 bestanden gekopieerd naar `/DATA/vault/` via SFTP
- `vault-maintenance` container actief (Alpine + cron, dagelijks archiveren)
- `syncthing` container actief, vault folder geconfigureerd
- `VaultArchiveDataDumps` Windows Task Scheduler job aangemaakt

### Data map audit + fixes
- Garmin CSV bestanden verplaatst van `Health/data/` → `Health/Fitness/Garmin/data/`
- `Diploma secundair.pdf` duplicaat verwijderd uit `Work/data/`
- MyCareer bestanden geconsolideerd in `Work/data/` (juni 2024 kopieën verwijderd uit `Personal/data/`)
- Garmin zip uitgepakt + verwerkt → `Garmin Health Overview.md`

### Open Taken
- [ ] Syncthing koppelen aan Windows PC (Device ID server: `AFAJ6NV-...`)
- [ ] Syncthing koppelen aan telefoon (Syncthing Android app)
- [ ] 3 Garmin subfolders in `Health/data/` evalueren (`fit garmin/`, `garmindata/`, `garmindatanec2023/`) — mogelijk verplaatsen naar `Garmin/data/`
- [ ] 6 ongeïdentificeerde PDFs in `Personal/data/` identificeren

## Gerelateerde Projecten
- [[zimaOS/CLAUDE|zimaOS]] — server waarop vault en Docker containers draaien
- [[ai_workstation/CLAUDE|ai_workstation]] — Ollama/Whisper (transcriber agent kan hiervan gebruik maken)
