# Terrorism Knowledge Database — Claude Code Context

## Project Doel
Kennisdatabank over Belgische inlichtingendiensten, dreigingslandschap en extremisme-dossiers. Gehost als MkDocs wiki op ZimaOS.

> Server access en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Stack
- **MkDocs** met Material theme
- **Poort:** 3070 op ZimaOS (`http://192.168.0.237:3070`)
- **FreshRSS** voor RSS monitoring van dreigingsfeeds

## Bestanden in dit project
```
memory-claude.md          # Hoofdkennisdatabank — DGJ/FGP/dreigingsanalyse (v9.0)
database-claude.md        # P/CVE-beleid België/Vlaanderen (v1.0)
monitoring_protocol_v3.md # Actueel monitoringprotocol (gebruik DEZE versie)
monitoring_protocol.md    # Verouderd (zie v3)
PROGRESS.md               # Status van project
docs/                     # Bronbestanden voor wiki
  terrorism_db_main.md    # Hoofddocument
  Casussen.md             # Dossier S4B, Krugergroep, etc.
  Diensten.md             # Structuur inlichtingendiensten
  Geopolitiek.md          # Geopolitieke context
  Juridisch.md            # Strafrecht terrorism
  full_wiki.md            # Volledige wiki export
```

## Beheer op ZimaOS
```bash
# Wiki bekijken
# http://192.168.0.237:3070

# Restart wiki container
ssh zimaos 'cd /DATA/.casaos/apps/mkdocs && docker compose restart'

# FreshRSS refresh
ssh zimaos 'docker exec freshrss php /var/www/FreshRSS/app/actualize_script.php'

# FreshRSS logs
ssh zimaos 'docker logs freshrss --tail 50'
```

## Scope
- **Primaire focus:** DGJ/FGP structuur + dreigingslandschap België
- **Secundaire focus:** OCAD, VSSE, ADIV, Federaal Parket, S4B-ecosysteem
- **Classificatie:** TLP:CLEAR — alle data is publiek

## Monitoring OPML
```
rsshub_feeds.opml           # RSSHub bridges voor moeilijk bereikbare bronnen
terrorisme_feeds_v2.opml    # Actuele feeds (gebruik DEZE versie)
terrorisme_feeds.opml       # Verouderd
```

## Open Taken (zie memory-claude.md → PENDING VERIFICATIE)
- FP-persbericht juli 2017 "terreurcel wapens + uniformen"
- Vonnis weduwe Feisal Yamoun (Faiza H.)
- Namen leiders/leden Way of Life
- Exacte datum Krugergroep home invasion
