# BROODnodig! — Broodautomaat Hub

Crowdsourced broodautomaat locator platform. **BROODnodig!** is de definitieve merged app (basis: broodautomaat-ervaring + features uit breadbot-locator).

**Repo:** `C:\Users\dell oem\OneDrive\Documents\GitHub\broodautomaat-ervaring`
**GitHub:** https://github.com/Styt0/broodautomaat-ervaring

## Status: Merged

De twee originele projecten zijn samengevoegd:
- **broodautomaat-ervaring** (BroodSpot) = basis (Mapbox, import, profiel, Supabase-ready)
- **breadbot-locator** (BroodBot) = geporteerde features (gamificatie, foto upload, comments, achievement toasts, leaderboard)

## Stack
React 18 + TypeScript + Vite + shadcn/ui + Tailwind CSS + Mapbox GL

## Features (merged)
- Mapbox kaart met status-gekleurde markers
- Dispenser toevoegen / status updaten / importeren (JSON)
- Foto upload bij automaten
- Reacties/comments systeem
- Gamificatie: punten, levels, badges, leaderboard, achievement toasts
- Gebruikersprofiel met favorieten + badges + ranglijst
- 11 echte Belgische broodautomaten als seed data

## Routes
- `/` — Homepage (hero + recent bijgewerkt)
- `/map` — Kaartweergave + sidebar
- `/add` — Automaat toevoegen
- `/profile` — Profiel + favorieten + badges + leaderboard
- `/import` — JSON import

## Werken aan dit project
```bash
cd "C:\Users\dell oem\OneDrive\Documents\GitHub\broodautomaat-ervaring"
npm run dev
```

## Archief
- `breadbot-locator/` — Originele BroodBot (Leaflet + Capacitor). Features geport, repo bewaard als referentie.

## Gerelateerde projecten
- [[geo-platform/map_server/CLAUDE|map_server]] — offline kaartdata als Mapbox fallback
