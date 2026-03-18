# Broodautomaat Hub

Crowdsourced broodautomaat locator platform — twee frontend varianten die hetzelfde concept implementeren.

## Sub-projecten

| Project | Naam | Kaart | Extra features | GitHub |
|---------|------|-------|----------------|--------|
| `breadbot-locator/` | BroodBot | Leaflet | Gamificatie (badges, leaderboard), Capacitor mobiel | [repo](https://github.com/Styt0/breadbot-locator) |
| `broodautomaat-ervaring/` | BroodSpot | Mapbox GL | Import functionaliteit, gebruikersprofielen | [repo](https://github.com/Styt0/broodautomaat-ervaring) |

## Gemeenschappelijke stack
React 18 + TypeScript + Vite + shadcn/ui + Tailwind CSS

## Verschil
- **BroodBot (Leaflet):** Open source kaart, geen API key nodig, Capacitor voor native mobiel
- **BroodSpot (Mapbox):** Rijkere kaart styling, import features, gebruikersprofielen

## Consolidatie mogelijkheden
- Beide projecten delen dezelfde use case en tech stack
- Overweeg: features samenvoegen in één definitieve app
- Best-of-both: Mapbox kaart + gamificatie + Capacitor mobiel + import + profielen

## Werken aan een sub-project
```bash
# BroodBot (Leaflet)
cd "C:\Users\Tom\OneDrive\Documents\GitHub\breadbot-locator"
npm run dev

# BroodSpot (Mapbox)
cd "C:\Users\Tom\OneDrive\Documents\GitHub\broodautomaat-ervaring"
npm run dev
```
