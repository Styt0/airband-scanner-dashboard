# Network & Security — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
Netwerk-brede ad-blocking en beveiligde externe toegang.

## Componenten
| Service | Poort | Beschrijving |
|---------|-------|--------------|
| AdGuard Home | 3001 (UI), 53 (DNS) | DNS filter & ad-blocker |
| Tailscale | — | Mesh VPN voor remote access |

## AdGuard Beheer
```bash
# Status
ssh zimaos 'docker ps | grep adguard'

# Logs
ssh zimaos 'docker logs adguard --tail 50'

# Restart
ssh zimaos 'cd /DATA/.casaos/apps/adguard-home && docker compose restart'
```

## Open Taken
- [ ] AdGuard: controleer blocklist statistieken (Dashboard)
- [ ] Tailscale: verificeer server is "Online" in admin console
