# RESTART.md — Session State

## Last session: 2026-04-03

### What we did
1. **Emergency alert system** — new feature in `transcript_viewer_new.py`:
   - SSE loop: detects 121.5/243.0 MHz (±15 kHz), sets `emerg`+`emerg_detail` in payload
   - Fixed red overlay (`#emergOverlay`) with pulsing animation, auto-dismiss 90s, ACKNOWLEDGE button
   - ADS-B `renderAcList`: checks squawk 7700/7600/7500, triggers overlay + highlights cell red
   - Bell button in topbar requests browser `Notification` permission; fires on alert
   - `_esc()` HTML escape helper added for all AC list values
2. **README.md created** — full feature list, stack table, architecture diagram, deploy instructions, Pi infra, live URLs
3. **Screenshot**: added `screenshot.png` to repo root (monorepo branch) and `docs/screenshot.png` to `airband-scanner` master (standalone repo had path already in README)
4. Deployed to Pi — initial scp failed (Tailscale re-auth timeout), redeployed successfully; service active
5. Pushed to both `airband-scanner-dashboard` (origin, moved from sdr-hub-v2) and `airband-scanner` (scanner remote)

### Current Pi state
- `sdr-hub` container: running
- `transcript-viewer.service`: running on port 8002, new emergency alert code live
- All crons active: disk_rotation (03:00), reboot (04:00), watchdog (*/15)

### GitHub repos
- `Styt0/airband-scanner-dashboard` — primary (origin redirects here from sdr-hub-v2)
- `Styt0/airband-scanner` — standalone, master branch has installer + docs/screenshot.png
- Active branch: `feature/wire-tapper-osint` on both

### Where we stopped
Emergency alerting done. Remaining backlog: hardcoded config (🟡), `portal.py` footer (🟢), `logging.basicConfig()` (🟢), `--dry-run` for archive script (🟢).
