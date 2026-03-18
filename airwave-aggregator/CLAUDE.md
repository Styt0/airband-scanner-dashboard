# airwave-aggregator

Radio frequentie aggregator — toont frequenties op kaart en in lijsten.

## Stack
React 18 + TypeScript + Vite + shadcn/ui + Tailwind CSS + Mapbox GL

## Structuur
- `src/components/ui/` = standaard shadcn/ui — NOOIT volledig lezen, Claude kent deze
- `src/components/` = project componenten (zie lijst hieronder)
- `src/pages/` = 3 pagina's: Index, NotFound, SignalIdentificationPage
- `src/hooks/` = custom hooks
- `src/lib/utils.ts` = cn() helper

## Routes (App.tsx)
- `/` → Index
- `/signal-identification` → SignalIdentificationPage
- `*` → NotFound

## Project componenten
- `FrequencyTable.tsx` — frequentie tabel weergave
- `FrequencyItem.tsx` — enkel frequentie item
- `FrequencyTabs.tsx` — tab navigatie tussen frequentie categorieën
- `FrequencyHeader.tsx` — header met filters
- `CategoryFilter.tsx` — filter op categorie
- `FavoriteFrequencies.tsx` — favoriete frequenties
- `LocationSelector.tsx` — locatie kiezen
- `MapView.tsx` — Mapbox kaartweergave
- `MapContext.tsx` — map state context
- `ActivityIndicator.tsx` — actief/inactief indicator
- `AirportFrequencyItem.tsx` — luchthaven frequentie item
- `AprsItem.tsx` — APRS (Amateur radio) item
- `SignalIdentification.tsx` — signaal herkenning
- `frequency-dialog/` — dialog voor frequentie toevoegen
- `map/` — kaart sub-componenten (FrequencyMarkers, UserLocationMarker, EmptyMapState)

## Hooks
- `useFrequencyData.tsx` — data ophalen en beheren
- `useFavoriteManager.tsx` — favorieten opslaan
- `useLocationManager.tsx` — GPS/locatie beheer
- `use-toast.ts` — notificaties
- `use-mobile.tsx` — responsive check

## Externe dependencies (key)
- `mapbox-gl` + `@types/mapbox-gl` — kaart
- `@tanstack/react-query` — data fetching
- `react-hook-form` + `zod` — forms
- `uuid` — unieke IDs voor frequenties
- `lucide-react` — iconen

## Conventies
- Tailwind classes, geen inline styles
- `cn()` uit `@/lib/utils` voor conditionele classes
- Functionele componenten + hooks only
- Imports via `@/` alias (geconfigureerd in vite.config)

## Veelgebruikte imports
```ts
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useQuery } from '@tanstack/react-query'
import { Map } from 'lucide-react'
```

## Wat NIET doen
- `src/components/ui/` niet aanpassen
- Geen nieuwe packages zonder te vragen
- Geen class components

## Gerelateerde projecten
- [[airband_scanner/AIRBAND_PROJECT|airband_scanner]] — RPi backend scanner waarvan dit de frontend is
- [[map_server/CLAUDE|map_server]] — offline kaartdata voor Mapbox fallback
- [[mobile_adsb/CLAUDE|mobile_adsb]] — verwante frequentie/ADS-B tracking stack
- [[ham_scanner/HAM_SCANNER_PLAN|ham_scanner]] — verwante SDR scanner (ham frequenties)
