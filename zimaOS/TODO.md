# ZimaOS Server Tasks (Migrated from Claude Sessions)

## 🔄 In Progress
- [ ] **Terrorisme Kennisdatabank (Open Source)**
  - Status: Gelaagd monitoringprotocol (v3.0) en initiële feitelijke database opgezet op ZimaOS.
  - Volgende stap: RSS-aggregator (bijv. FreshRSS) installeren op server voor Tier 1 automatisering.
- [ ] **Fleshing out OSINT Researcher**
  - Status: Architectuur opgezet (Open WebUI + Gemini API + Tor).
  - Sub-tasks:
    - [ ] "Model File" aanmaken in Open WebUI met Phase 0-6 logic.
    - [ ] Tor-enabled Python Tools (Functions) implementeren voor anoniem scrapen.
    - [ ] GeoSentinel data koppelen aan de agent via API/Files.
    - [ ] Gemini 1.5 Pro/Flash configureren voor deep reasoning.
- [ ] **OSM BeNeLux importeren (BE + NL + LU)**
  - Status: Import (osm2pgsql) is bezig. Ways (~1.2M) worden verwerkt.
  - Volgende stap: Database indexatie en overschakelen naar `run` mode.
- [ ] **Install GeoSentinel (Geospatial Monitoring & OSINT)**
  - Status: Basis structuur gereed. Wacht op TomTom API key.

## ✅ Completed
- [x] **Plex /plex-tv sectie aanmaken + series migratie** (814GB OK)
- [x] **Open WebUI installatie** (Running op poort 3050)
- [x] **Server Health Check & Disk Maintenance**
- [x] **Cron script voor Kiwix: Wiki updates geautomatiseerd**

## ⏳ Pending
- [ ] **Download Europe PBF (31GB) + filter with osmium**
- [ ] **Append filtered Europe to tile server DB**

