SDR-Hub Transcript Viewer V2.0
Backed up: 2026-03-28 14:01

Files:
  transcript_viewer_new.py  — Production server (deployed to Pi at 192.168.1.188:/opt/deepgram-worker/transcript_viewer.py)
  mockup_v2.html            — Static HTML design mockup

Deployment:
  Service: transcript-viewer.service (port 8002)
  Pi: 192.168.1.188  user: root
  DB: /opt/sdr-hub/data/db.sqlite3

Key features:
  - Deep dark CSS grid layout (1fr 360px / 1fr 196px)
  - Inline radar SVG (EBAW + EBBR + live aircraft positions from tar1090)
  - Pill filter for freq types (TWR/APP/GND/ATIS/EMERG)
  - Analytics strip: freq bars, donut, 24h sparkline, KPI cards
  - Aircraft list with altitude colouring and distance sort
  - Audio playback, per-TX radar modal
