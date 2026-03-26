# wire-tapper

Wireless OSINT & Signal Intelligence Platform — passieve detectie van Wi-Fi, Bluetooth, CCTV, IoT, voertuigen, headphones, smart TVs en celmasten.

**GitHub:** https://github.com/h9zdev/WireTapper
**Web UI:** http://192.168.0.237:8484/map-w

## Installatie
- Gedeployed als Docker container op zimaOS (192.168.0.237)
- Poort: **8484** (intern 8080, Kiwix gebruikt al 8080)
- Compose: `/DATA/.casaos/apps/wire-tapper/docker-compose.yml`

## ZimaOS Docker commando's (let op: speciale syntax vereist)

```bash
# docker compose werkt NIET — gebruik de volledige plugin path
DOCKER_BUILDKIT=0 DOCKER_CONFIG=/tmp/.docker /usr/lib/docker/cli-plugins/docker-compose \
  -f /DATA/.casaos/apps/wire-tapper/docker-compose.yml up -d

# Logs bekijken
ssh zimaos 'docker logs wire-tapper 2>&1'

# Stoppen
ssh zimaos 'docker stop wire-tapper'

# Opnieuw bouwen na update
ssh zimaos 'DOCKER_BUILDKIT=0 DOCKER_CONFIG=/tmp/.docker /usr/lib/docker/cli-plugins/docker-compose \
  -f /DATA/.casaos/apps/wire-tapper/docker-compose.yml up --build -d'
```

## API Keys instellen
Kopieer `.env.example` naar `.env` op de server en vul de keys in:

```bash
ssh zimaos 'cp /DATA/.casaos/apps/wire-tapper/.env.example /DATA/.casaos/apps/wire-tapper/.env'
# Daarna editen en container herstarten
```

Benodigde keys (aanvragen bij de respectieve diensten):
| Dienst | URL | Gebruik |
|--------|-----|---------|
| Wigle.net | https://wigle.net/account | Wi-Fi netwerk mapping |
| wpa-sec | https://wpa-sec.stanev.org | WPA credential leaks |
| OpenCellID | https://opencellid.org | Celmasten database |
| Shodan | https://account.shodan.io | IoT device search (Premium!) |

## ZimaOS Docker quirks
- `docker build -t` en `docker compose` werken NIET via SSH — altijd volledige plugin path gebruiken
- `DOCKER_BUILDKIT=0` is vereist (buildx heeft geen schrijfrechten op /DATA/.docker)
- `DOCKER_CONFIG=/tmp/.docker` vermijdt permission errors op /DATA/.docker/config.json
- sudo gebruiken voor mkdir/cp maar NIET voor docker (styto is lid van docker groep)

## Gerelateerde projecten
- [[zimaOS/CLAUDE|zimaOS]] — homeserver context en SSH toegang
- [[osint_researcher/CLAUDE|osint_researcher]] — OSINT pipeline
- [[osint-hub-collective/CLAUDE|osint-hub-collective]] — OSINT frontend
