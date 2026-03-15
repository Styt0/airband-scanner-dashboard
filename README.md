# Airband Scanner

**See & hear planes near you.** A self-hosted airband radio scanner with automatic speech-to-text transcription and live radar maps.

![screenshot](docs/screenshot.png)

## What It Does

1. **Scans airband frequencies** (118–137 MHz AM) using an RTL-SDR dongle and records transmissions
2. **Transcribes speech** using Deepgram (cloud, 500 free/day) or whisper.cpp (local, unlimited)
3. **Tracks aircraft** via ADS-B and shows a radar map overlay for each transmission
4. **Identifies who's talking** by matching callsigns in transcripts to nearby aircraft positions
5. **Web UI** to browse transcripts, play audio, and view radar maps

## Hardware Required

| Item | Required | Notes |
|------|----------|-------|
| Raspberry Pi 4 (4GB+) | Yes | Also works on x86_64 Linux |
| RTL-SDR dongle | Yes | For airband scanning (118–137 MHz) |
| Second RTL-SDR | Optional | For ADS-B tracking (1090 MHz) — enables radar maps |
| Antenna | Yes | Airband antenna tuned for ~130 MHz |

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USER/airband-scanner/main/install.sh | sudo bash
```

Or clone and run:
```bash
git clone https://github.com/YOUR_USER/airband-scanner.git
cd airband-scanner
sudo bash install.sh
```

The installer will ask for:
- **Your coordinates** (latitude/longitude)
- **Station name** (e.g. your nearest airport ICAO code)
- **Deepgram API key** (optional — get a free one at [console.deepgram.com](https://console.deepgram.com))
- **tar1090 URL** (if you have ADS-B tracking set up)
- **Whisper model size** (base.en or small.en)

## What Gets Installed

| Component | Description |
|-----------|-------------|
| [sdr-hub](https://github.com/shajen/rtl-sdr-scanner-cpp) (Docker) | Airband scanner — records AM transmissions to SQLite |
| Transcriber | Auto-transcribes recordings via Deepgram + whisper.cpp |
| Aircraft Tracker | Polls tar1090 for ADS-B aircraft positions every 8s |
| Web Viewer (`:8002`) | Browse transcripts, play audio, view radar maps |
| Disk Rotation | Deletes old audio files (default 7 days) via cron |

## Architecture

```
RTL-SDR (airband)  ──>  sdr-hub (Docker :8001)  ──>  SQLite DB
                              |                          |
                              |                    transcriber
                              |                    (Deepgram + whisper.cpp)
                              |                          |
RTL-SDR (1090 MHz) ──>  tar1090 (Docker :8080)    web viewer (:8002)
                              |                    - transcripts table
                         aircraft_tracker    ----> - audio playback
                         (position logger)         - SVG radar maps
                                                   - callsign matching
```

## Features

### Transcript Viewer
- Dark theme, mobile-friendly
- Search, filter by frequency, speech-only mode
- Model badges (DEEPGRAM / WHISPER / PENDING)
- Lazy audio playback (CU8 → WAV on click)

### Radar Map Overlay
- SVG map centered on your station with range rings (25/50/75/100 km)
- Aircraft color-coded by altitude (red = low, yellow = mid, blue = high)
- **Automatic transmitter identification:**
  - Regex callsign matching (e.g. "RYR19TJ" in transcript)
  - Phonetic alphabet decoding ("Kilo Lima Mike" → KLM)
  - Registration matching (e.g. "OO-BET")
  - Proximity-based fallback (nearest low aircraft)
- Gold highlight with glow effect on most likely transmitter

### Transcription
- **Deepgram nova-3** (cloud) — fast, high quality, 500 free/day
- **whisper.cpp** (local) — unlimited, runs on Pi4 (base: ~20s/clip, small: ~60s/clip)
- Automatic fallback: Deepgram first, whisper.cpp when limit reached
- Audio preprocessing: bandpass filter (300–3400 Hz voice band)
- Hallucination detection (filters out fake sound effects)
- `--suppress-nst` flag blocks non-speech tokens

## Configuration

Config file: `/opt/airband/config.env`

```bash
STATION_LAT=51.189          # Your latitude
STATION_LON=4.460           # Your longitude
STATION_NAME=MYSTATION      # Your station name
DEEPGRAM_KEY=               # Deepgram API key (optional)
WHISPER_MODEL=base.en       # base.en or small.en
TAR1090_URL=http://127.0.0.1:8080/data/aircraft.json
AIRCRAFT_RANGE_KM=150       # Radar range in km
RETENTION_DAYS=7            # Days to keep audio files
DAILY_DG_LIMIT=500          # Deepgram daily limit
```

### Custom Frequencies

Add known frequencies to the viewer via environment variable:
```bash
KNOWN_FREQS_CSV=119.700:MY TWR,121.900:MY GND,127.625:MY ATIS
```

### ATIS Frequencies

Tell the transmitter guesser which frequencies are ATIS (ground broadcast, not aircraft):
```bash
ATIS_FREQS=127.625,124.200,119.975
```

## Service Management

```bash
# Status
systemctl status airband-transcriber airband-viewer airband-tracker

# Restart
sudo systemctl restart airband-transcriber

# Logs
tail -f /opt/airband/transcriber.log
tail -f /opt/airband/viewer.log
journalctl -u airband-transcriber -f

# DB queries
sqlite3 /opt/sdr-hub/data/db.sqlite3 "SELECT model, COUNT(*) FROM sdr_transcript GROUP BY model"
```

## Uninstall

```bash
sudo bash install.sh --uninstall
```

## How the Audio Works

sdr-hub records raw IQ data in CU8 format (unsigned 8-bit I/Q samples). The transcriber and viewer convert this to audio:

1. **AM envelope detection** — `magnitude = sqrt((I-127.5)^2 + (Q-127.5)^2)`
2. **DC removal** — subtract mean
3. **Bandpass filter** — 2nd-order Butterworth biquad cascade (300–3400 Hz)
4. **Normalize** to 90% of int16 range
5. **Resample** to 16 kHz for whisper.cpp (linear interpolation)

## Requirements

- Debian/Raspbian 12+ (bookworm) or Ubuntu 22.04+
- Python 3.9+
- Docker
- cmake, git (installed automatically)
- ~1 GB free disk for whisper model
- ~150 MB/hour for audio storage (with speech ratio ~70%)

## Credits

- [sdr-hub](https://github.com/shajen/rtl-sdr-scanner-cpp) by shajen — RTL-SDR scanner
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by ggerganov — local speech-to-text
- [Deepgram](https://deepgram.com) — cloud speech-to-text API
- [tar1090](https://github.com/wiedehopf/tar1090) — ADS-B web interface

## License

MIT
