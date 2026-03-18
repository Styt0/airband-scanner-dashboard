# Airband Scanner Project — Complete Handover

## Hardware & Network
| Item | Detail |
|------|--------|
| Device | Raspberry Pi 4 (4GB), SD card 29GB |
| Hostname | `styto-ebaw` |
| Local IP | `192.168.1.188` |
| Tailscale IP | `100.120.23.59` |
| SSH | `root` / `aXXGTMAL77TK` |
| RTL-SDR dongle | Serial `SDRJUB` — airband scanning |
| RTL-SDR dongle 2 | ADS-B (1090 MHz) — flight tracking |
| Location | Near EBAW (Antwerp Airport, 51.189°N 4.460°E) |

## Architecture Overview
```
RTL-SDR (airband)  ──►  sdr-hub (Docker :8001)  ──►  SQLite DB
                              │                          │
                              │                    transcriber.py
                              │                     (Deepgram + whisper.cpp)
                              │                          │
                              │                    transcript_viewer.py (:8002)
                              │                          │
RTL-SDR (1090MHz)  ──►  ultrafeeder (Docker :8080) ──► aircraft_tracker.py
                         tar1090 map                    (positions DB)
                              │                          │
                         ADS-B feeders              radar map overlay
                         (piaware, fr24, rbfeeder,    in transcript viewer
                          adsbhub)
```

## Docker Containers
| Container | Port | Purpose |
|-----------|------|---------|
| `sdr-hub` | 8001 | Airband scanner web UI, records CU8 IQ files, SQLite DB |
| `ultrafeeder` | 8080 | readsb + tar1090 ADS-B tracker (HTTP 000 over Tailscale, works local) |
| `piaware` | — | FlightAware ADS-B feeder |
| `fr24feed` | — | FlightRadar24 feeder |
| `rbfeeder` | — | RadarBox feeder |
| `adsbhub` | — | ADSBHub feeder |
| `dozzle` | 9999 | Docker log viewer |
| `adsb-setup-proxy` | 80/443 | adsb.im setup proxy |

Config: `/opt/adsb/config/` and `/opt/adsb/.env`

## Custom Services (systemd)

### 1. `deepgram-worker.service` — Transcription Worker
- **File:** `/opt/deepgram-worker/transcriber.py`
- **What:** Polls sdr-hub SQLite for untranscribed AM transmissions, transcribes via Deepgram API (500/day limit), falls back to whisper.cpp
- **Audio pipeline:** CU8 IQ → AM envelope detection → bandpass filter 300–3400 Hz → normalize → WAV → (resample 16kHz for whisper)
- **Deepgram:** nova-3 model, API key `6dea555be134cf89fa4a07284752791b27d444d1`
- **Whisper.cpp:** `/opt/whisper.cpp/build/bin/whisper-cli` with `--suppress-nst` + `--prompt` (ATC context)
- **Models available:** `ggml-small.en.bin` (466MB, preferred), `ggml-base.en.bin` (142MB), `ggml-base.bin` (142MB)
- **Model priority:** small.en > base.en > base (auto-selects best available)
- **Hallucination detection:** Filters out bracketed sound effects like `(drill whirring)`, `[Music]`, etc.
- **No-speech cleanup:** Deletes `.bin` audio files when no speech detected
- **Log:** `/opt/deepgram-worker/transcriber.log`

### 2. `transcript-viewer.service` — Web UI
- **File:** `/opt/deepgram-worker/transcript_viewer.py`
- **Port:** 8002 (accessible locally + Tailscale)
- **Features:**
  - Dark GitHub-style theme
  - Table view: frequency, time, transcript text, audio playback, radar map
  - Badges: DEEPGRAM (blue), WHISPER (purple), PENDING (gray), ERROR (red)
  - Filters: search text, frequency dropdown, speech-only, hide-pending
  - Pagination (50 per page)
  - ATIS highlighting (green background for known ATIS frequencies)
  - Lazy audio loading (CU8→WAV decode on click, not page load)
  - `/audio/<id>` endpoint: serves CU8→WAV decoded audio
  - `/map/<tx_id>` endpoint: SVG radar map showing aircraft positions at transmission time
  - Stats bar: total transcripts, speech count, pending count, disk free, RAM
  - System stats via psutil
- **Threading:** `ThreadingHTTPServer` (handles concurrent browser connections)
- **SQLite:** WAL mode (`PRAGMA journal_mode=WAL`) for concurrent reads during writes
- **iptables:** `ExecStartPre=/sbin/iptables -I INPUT 1 -i tailscale0 -p tcp --dport 8002 -j ACCEPT` (Tailscale ts-input chain DROPs port 8002 otherwise)
- **Log:** `/opt/deepgram-worker/viewer.log`

### 3. `aircraft-tracker.service` — ADS-B Position Logger
- **File:** `/opt/deepgram-worker/aircraft_tracker.py`
- **What:** Polls `http://127.0.0.1:8080/data/aircraft.json` (tar1090) every 8 seconds, stores aircraft positions within 150km of EBAW
- **DB:** `/opt/deepgram-worker/aircraft.db` (SQLite, WAL mode)
- **Schema:** `positions(id, ts, hex, flight, lat, lon, alt_baro, gs, track, squawk, dist_km)`
- **Retention:** 48 hours (auto-cleanup)
- **Used by:** transcript viewer's `/map/<tx_id>` radar overlay
- **Log:** `/opt/deepgram-worker/aircraft_tracker.log`

## Radar Map Feature
The transcript viewer generates SVG radar maps showing aircraft positions at the time of each transmission:
- **Airports:** EBAW (green, center, 51.189°N 4.460°E) + EBBR (blue, ~32km SSE, 50.901°N 4.484°E)
- **Range rings:** 25/50/75/100 km
- **Aircraft:** Color-coded by altitude (red <3000ft, yellow <10000ft, blue <FL280, gray high)
- **Transmitter guessing:** Uses transcript text to identify which aircraft is likely speaking:
  1. Direct callsign regex match (e.g. "RYR19TJ" in text)
  2. OO-xxx Belgian registration match
  3. Phonetic alphabet decoding (e.g. "Kilo Lima Mike" → KLM)
  4. Proximity fallback (nearest low aircraft on matching frequency)
  5. ATIS frequencies → labeled as ground broadcast
- **Highlighted:** Most likely transmitter shown in gold with glow effect + "likely tx" label

## Key Databases

### sdr-hub DB: `/opt/sdr-hub/data/db.sqlite3`
- `sdr_transmission` — recorded transmissions (id, begin_frequency, end_frequency, begin_date, end_date, data_file, group_id, source)
- `sdr_transcript` — transcriptions (transmission_id, text, confidence, model, error, created_at)
- `sdr_group` — frequency groups/modulation settings
- Audio files: `/opt/sdr-hub/data/public/media/device_3/transmission/YYYY-MM-DD/*.bin` (CU8 IQ format)

### Aircraft DB: `/opt/deepgram-worker/aircraft.db`
- `positions` — aircraft position snapshots every 8s, kept 48h

## Known Frequencies
```
EBAW (Antwerp):  TWR 119.700/120.775  GND 121.900  ATIS 124.200  INFO 119.975
EBBR (Brussels): TWR 118.600/120.780  GND 118.050/121.700  APP 128.800/127.570/129.730
                 ARR 118.250/120.100  DEP 126.630  DELIVERY 121.950
                 ATIS 127.625/117.550  DEP ATIS 121.750  ARR ATIS 132.480
Other:           EMERGENCY 121.500  MIL 130.950  NATO 130.750  EUROCONTROL 132.200
```

## Crontabs
```
# ATIS recordings (every hour)
05 * * * * curl -s 'http://127.0.0.1:8001/api/scheduler/record?freq=127625000&duration=45' > /dev/null
10 * * * * curl -s 'http://127.0.0.1:8001/api/scheduler/record?freq=119975000&duration=45' > /dev/null

# Disk rotation — delete transcribed audio >7 days old
0 3 * * * /usr/bin/python3 /opt/deepgram-worker/disk_rotation.py
```

## Disk Management
- **File:** `/opt/deepgram-worker/disk_rotation.py`
- **What:** Deletes `.bin` audio files older than 7 days that have been transcribed
- **Current rate:** ~149 MB/hour kept (after no-speech deletion, ~69% speech ratio)
- **SD card:** 29GB total, ~17GB free → ~4-5 days runway without rotation
- **With rotation:** Sustainable at 7-day window ≈ ~25GB cycling

## Whisper.cpp Build
- **Location:** `/opt/whisper.cpp/` (git clone, depth 1)
- **Binary:** `/opt/whisper.cpp/build/bin/whisper-cli`
- **Built with:** cmake, Release mode, 4 threads, ARM NEON SIMD
- **Models dir:** `/opt/whisper.cpp/models/`

## Current Issues / Known Problems

### Whisper base model quality
- **Problem:** `ggml-base.bin` hallucinates sound effects like `(drill whirring)`, `[Music]` on noisy AM audio
- **Mitigations applied:**
  - `--suppress-nst` flag prevents sound effect tokens
  - `--prompt` with ATC context primes for aviation english
  - Bandpass filter (300–3400 Hz) on audio before transcription
  - Hallucination regex detector marks bracketed outputs as no-speech
- **Problem:** With suppress-nst, base model generates fake coherent text instead (e.g. "I'm going to go to the next one")
- **Next step:** Try `ggml-small.en.bin` (already downloaded, 466MB) — should be significantly better at noisy audio but ~3x slower (~60-90s per clip on Pi4)
- **To switch model:** It auto-selects best available. small.en is already preferred. Just restart: `systemctl restart deepgram-worker`

### Deepgram daily limit
- 500 transcriptions/day with nova-3 (free tier)
- Resets midnight UTC (~01:00 CET)
- After limit: falls back to whisper.cpp

### Tailscale access
- Port 8001 (Docker sdr-hub): accessible via FORWARD chain
- Port 8002 (host transcript-viewer): needs iptables rule (added via ExecStartPre)
- Port 8080 (Docker ultrafeeder/tar1090): returns HTTP 000 over Tailscale (Docker networking issue, works locally)

### Disk space
- SD card will fill up without disk_rotation.py running
- Consider USB HDD for long-term storage if needed

## File Locations Summary
```
/opt/deepgram-worker/
├── transcriber.py          # Main transcription worker (v2, bandpass+suppress-nst)
├── transcriber.log         # Worker log
├── transcript_viewer.py    # Web UI server (port 8002)
├── viewer.log              # Viewer log
├── aircraft_tracker.py     # tar1090 position poller
├── aircraft_tracker.log    # Tracker log
├── aircraft.db             # Aircraft positions SQLite
├── disk_rotation.py        # 7-day audio cleanup cron

/opt/whisper.cpp/
├── build/bin/whisper-cli   # Whisper binary
├── models/
│   ├── ggml-small.en.bin   # 466MB — best quality (preferred)
│   ├── ggml-base.en.bin    # 142MB — english-only base
│   └── ggml-base.bin       # 142MB — multilingual base

/opt/sdr-hub/
├── data/db.sqlite3                     # Main database
├── data/public/media/device_3/         # Audio recordings (CU8 IQ)

/etc/systemd/system/
├── deepgram-worker.service
├── transcript-viewer.service
├── aircraft-tracker.service
```

## Quick Commands
```bash
# SSH
ssh root@192.168.1.188  # password: aXXGTMAL77TK

# Service management
systemctl status deepgram-worker transcript-viewer aircraft-tracker
systemctl restart deepgram-worker
journalctl -u deepgram-worker -f

# Logs
tail -f /opt/deepgram-worker/transcriber.log
tail -f /opt/deepgram-worker/viewer.log

# DB queries
sqlite3 /opt/sdr-hub/data/db.sqlite3 "SELECT COUNT(*) FROM sdr_transmission"
sqlite3 /opt/sdr-hub/data/db.sqlite3 "SELECT model, COUNT(*) FROM sdr_transcript GROUP BY model"
sqlite3 /opt/sdr-hub/data/db.sqlite3 "SELECT t.id, tr.model, substr(tr.text,1,80) FROM sdr_transmission t JOIN sdr_transcript tr ON tr.transmission_id=t.id WHERE tr.text!='' ORDER BY t.id DESC LIMIT 10"

# Disk
df -h /opt
du -sh /opt/sdr-hub/data/public/media/

# Docker
docker ps
docker logs sdr-hub --tail 20

# Web UIs
# Transcript viewer: http://192.168.1.188:8002 or http://100.120.23.59:8002
# sdr-hub scanner:   http://192.168.1.188:8001
# tar1090 map:       http://192.168.1.188:8080
# Dozzle logs:       http://192.168.1.188:9999
```

## Audio Format: CU8 IQ
- Raw unsigned 8-bit I/Q samples (interleaved: I0, Q0, I1, Q1, ...)
- Center value 127.5, range 0-255
- Sample rate = `end_frequency - begin_frequency` (typically 25000 or 32000 Hz)
- AM demodulation: envelope = sqrt((I-127.5)^2 + (Q-127.5)^2)
- Voice bandpass: 300-3400 Hz (2nd-order Butterworth biquad cascade)
- Whisper requires 16kHz mono WAV (linear interpolation resample)

## Transcript Viewer API Endpoints
```
GET /              → HTML page with transcript table
GET /audio/<id>    → WAV audio for transmission id (CU8→WAV on-the-fly)
GET /map/<id>      → SVG radar map with aircraft positions at transmission time
GET /favicon.ico   → 204 No Content
```
