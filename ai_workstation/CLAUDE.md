# AI Workstation — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
Lokale en cloud-gebaseerde AI tools voor onderzoek en automatisering op ZimaOS.

## Componenten
| Service | Poort | Beschrijving |
|---------|-------|--------------|
| Open WebUI | 3050 | Primaire AI interface |
| Ollama | 11434 | Lokale LLM runner |
| Faster-Whisper | 10300 | Speech-to-text |

## Gemini API in Open WebUI
```
Base URL: https://generativelanguage.googleapis.com/v1beta/openai
```
- User-Agent impersonation actief voor scrapers

## Beheer
```bash
# Open WebUI updaten
ssh zimaos 'cd /DATA/.casaos/apps/open-webui && docker compose pull && docker compose up -d'

# Ollama model toevoegen
ssh zimaos 'docker exec ollama ollama pull <model>'

# Beschikbare modellen
ssh zimaos 'docker exec ollama ollama list'
```

## Open Taken
- [ ] Open WebUI updaten naar nieuwste versie (Ollama tag)
- [ ] Gemini connectivity testen in Open WebUI
- [ ] CPU/RAM gebruik monitoren bij lokale modellen
