# OSINT Researcher — Claude Code Context

> ZimaOS sub-project. Server access, credentials en Docker commando's: zie `../zimaOS/CLAUDE.md`

## Project Doel
Geautomatiseerde OSINT pipeline voor onderzoek via open bronnen. Gebaseerd op David Kyazze's fasemodel (Fasen 0-6).

## Stack
- **Open WebUI** (Port 3050) als AI interface
- **Gemini API** voor LLM reasoning
- **Tor Proxy** (`socks5://tor:9050`) voor anonieme scraping
- **Python tool** (`tor_search_tool.py`) voor geautomatiseerde zoekopdrachten

## Pipeline Fases
0. Taak-definitie
1. Bron-identificatie
2. Data-ophaling (via Tor)
3. Extractie & normalisatie
4. AI-analyse (Gemini/Ollama)
5. Rapportage
6. Archivering

## Bestanden
```
tor_search_tool.py   # Tor-gebaseerde zoektool
```

## Gemini API Configuratie (in Open WebUI)
```
Base URL: https://generativelanguage.googleapis.com/v1beta/openai
Model: gemini-1.5-pro (of gemini-2.0-flash)
```

## Status
- Architecture klaar
- Tool beschikbaar
- Needs: "Tool" integratie in Open WebUI voor automatische scraping pipeline

## Gerelateerde projecten
- [[zimaOS/CLAUDE|zimaOS]] — server waarop dit draait
- [[ai_workstation/CLAUDE|ai_workstation]] — levert AI-modellen voor analyse
- [[geosentinel/CLAUDE|geosentinel]] — overlappende geo-monitoring functionaliteit
- [[terrorism_database/CLAUDE|terrorism_database]] — OSINT output voedt kennisdatabank
