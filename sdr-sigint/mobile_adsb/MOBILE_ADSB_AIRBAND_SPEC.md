# Mobile ADS-B + Airband Transcription System — Build Spec
**Platform:** ZimaBlade (x86, Docker-first)  
**Target:** Portable vehicle/field deployment  
**TLP:** CLEAR

---

## 1. System Overview

Single ZimaBlade node running all services via Docker Compose. Two SDR dongles: one dedicated ADS-B (1090 MHz), one dedicated airband VHF (118–137 MHz). GPS dongle feeds live coordinates to all location-dependent services. All transcription is local via whisper.cpp — no cloud dependencies.

### Physical Inputs
| Input | Hardware | Interface |
|---|---|---|
| ADS-B 1090 MHz | RTL-SDR dongle #1 | USB |
| Airband VHF 118–137 MHz | RTL-SDR dongle #2 | USB |
| GPS | u-blox M8N USB dongle | USB → gpsd |

### Logical Services (all containers unless noted)
```
gpsd (host)
readsb (ADS-B decoder)
tar1090 (radar UI)
freq-manager (Python — GPS → frequency selector)
sdr-hub (airband receiver → audio files)
whisper-worker (whisper.cpp — audio → transcript)
feed-backend (FastAPI — SSE + audio serving)
ui-proxy (Nginx — unified split-screen UI)
```

---

## 2. Architecture Diagram

```
USB GPS dongle
      │
   gpsd (host daemon, port 2947)
      │
      ├──► readsb   (--net-connector gpsd, port 8080)
      │       │
      │    tar1090  (radar iframe, port 8088)
      │
      ├──► freq-manager (Python service)
      │       │  polls gpsd every 30s
      │       │  queries airports.csv (haversine, radius 150km)
      │       │  writes active_freqs.json
      │       │
      │    sdr-hub  (reads active_freqs.json, SDR #2)
      │       │
      │    /data/audio/*.wav  (shared Docker volume)
      │
      ├──► whisper-worker
      │       │  watches /data/audio/ (inotify)
      │       │  runs whisper.cpp on new files
      │       │  writes /data/transcripts/*.json
      │       │
      └──► feed-backend (FastAPI, port 8000)
               │  watches /data/transcripts/
               │  SSE endpoint: /events
               │  serves audio: /audio/<filename>
               │
           ui-proxy (Nginx, port 80)
               │  / → split-screen HTML
               │  /radar → tar1090
               │  /api → feed-backend
               │
           WiFi AP (GL.iNet router or hostapd)
               │
           Client browser (tablet/phone)
```

---

## 3. Directory Structure

```
/opt/airband/
├── docker-compose.yml
├── .env
├── config/
│   ├── airports.csv              # OurAirports data (pre-downloaded)
│   ├── nginx.conf
│   └── whisper-model/            # ggml model files
│       └── ggml-base.en.bin
├── services/
│   ├── freq-manager/
│   │   ├── Dockerfile
│   │   ├── freq_manager.py
│   │   └── requirements.txt
│   ├── whisper-worker/
│   │   ├── Dockerfile
│   │   └── worker.py
│   └── feed-backend/
│       ├── Dockerfile
│       └── main.py
├── ui/
│   └── index.html                # Split-screen UI (single file)
└── data/                         # Docker volume (shared)
    ├── audio/
    ├── transcripts/
    └── gps_state.json            # Written by freq-manager
```

---

## 4. Service Specifications

### 4.1 gpsd (host, not containerized)
- Install: `apt install gpsd gpsd-clients`
- Config `/etc/default/gpsd`:
  ```
  DEVICES="/dev/ttyUSB0"
  GPSD_OPTIONS="-n"
  USBAUTO="true"
  ```
- Verify: `cgps -s` or `gpspipe -w -n 5`
- Exposes: TCP port 2947 (accessible to containers via `host` network or bridge)

---

### 4.2 readsb (ADS-B decoder)
- Image: `ghcr.io/sdr-enthusiasts/docker-readsb-protobuf:latest`
- Replaces dump1090-fa for native gpsd support
- Key environment variables:
  ```env
  READSB_DEVICE_TYPE=rtlsdr
  READSB_RTLSDR_DEVICE=00000001        # serial of SDR #1
  READSB_GAIN=autogain
  READSB_LAT=                          # left empty — sourced from gpsd
  READSB_LON=                          # left empty — sourced from gpsd
  READSB_GPSD_SERVER=172.17.0.1        # host IP from container perspective
  READSB_NET_ENABLE=true
  READSB_NET_BEAST_OUTPUT_PORT=30005
  READSB_NET_RAW_OUTPUT_PORT=30002
  ```
- Ports: 8080 (web), 30005 (beast), 30002 (raw)

---

### 4.3 tar1090 (radar UI)
- Image: `ghcr.io/sdr-enthusiasts/docker-tar1090:latest`
- Consumes readsb beast output
- Environment:
  ```env
  BEASTHOST=readsb
  BEASTPORT=30005
  TAR1090_DEFAULTCENTERLAT=             # dynamically set via freq-manager
  TAR1090_DEFAULTCENTERLON=
  TAR1090_RANGERINGSDISTANCES=50,100,200
  ```
- Port: 8088

---

### 4.4 freq-manager (custom Python service)

**Purpose:** GPS → nearest airports → prioritized frequency list → sdr-hub config

**File: `freq_manager.py`**

```python
"""
Polls gpsd every POLL_INTERVAL seconds.
Queries airports.csv for airports within RADIUS_KM.
Selects top N frequencies by priority and distance.
Writes active_freqs.json for sdr-hub consumption.
Writes gps_state.json for UI and other services.
"""

import json, time, math, csv, socket
from pathlib import Path

POLL_INTERVAL = 30          # seconds
RADIUS_KM = 150
MAX_FREQS = 4               # SDR scan slots
GPSD_HOST = "172.17.0.1"   # host from container
GPSD_PORT = 2947

FREQ_PRIORITY = {
    "ATIS": 1,
    "APP": 2,
    "TWR": 3,
    "GND": 4,
    "DEP": 5,
    "FIS": 6,
    "UNIC": 7,
}

OUTPUT_FREQS = Path("/data/active_freqs.json")
OUTPUT_GPS   = Path("/data/gps_state.json")
AIRPORTS_CSV = Path("/config/airports.csv")

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Returns distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_gps_fix() -> dict | None:
    """Returns {'lat': float, 'lon': float, 'speed': float} or None."""
    try:
        with socket.create_connection((GPSD_HOST, GPSD_PORT), timeout=5) as s:
            s.sendall(b'?WATCH={"enable":true,"json":true}\n')
            buf = ""
            deadline = time.time() + 10
            while time.time() < deadline:
                chunk = s.recv(4096).decode(errors="ignore")
                buf += chunk
                for line in buf.splitlines():
                    try:
                        obj = json.loads(line)
                        if obj.get("class") == "TPV" and obj.get("mode", 0) >= 2:
                            return {"lat": obj["lat"], "lon": obj["lon"], "speed": obj.get("speed", 0)}
                    except json.JSONDecodeError:
                        pass
    except Exception:
        return None

def load_airports(csv_path: Path) -> list[dict]:
    airports = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                airports.append({
                    "icao": row["ident"],
                    "name": row["name"],
                    "lat": float(row["latitude_deg"]),
                    "lon": float(row["longitude_deg"]),
                    "freqs": []  # populated from airport-frequencies.csv join
                })
            except (ValueError, KeyError):
                continue
    return airports

def select_frequencies(lat: float, lon: float, airports: list, freqs_data: list) -> list[dict]:
    # Build airport freq map
    freq_map: dict[str, list] = {}
    for f in freqs_data:
        icao = f["airport_ident"]
        if icao not in freq_map:
            freq_map[icao] = []
        freq_map[icao].append(f)

    candidates = []
    for ap in airports:
        dist = haversine(lat, lon, ap["lat"], ap["lon"])
        if dist > RADIUS_KM:
            continue
        for freq in freq_map.get(ap["icao"], []):
            freq_type = freq.get("type", "").upper()
            priority = FREQ_PRIORITY.get(freq_type, 99)
            try:
                mhz = float(freq["frequency_mhz"])
                if not (118.0 <= mhz <= 137.0):  # VHF airband only
                    continue
            except ValueError:
                continue
            candidates.append({
                "icao": ap["icao"],
                "name": ap["name"],
                "distance_km": round(dist, 1),
                "type": freq_type,
                "mhz": mhz,
                "priority": priority
            })

    candidates.sort(key=lambda x: (x["distance_km"] * 0.5 + x["priority"] * 10))
    return candidates[:MAX_FREQS]

def main():
    airports = load_airports(AIRPORTS_CSV / "airports.csv")
    # Load freq data separately
    freqs_data = []
    with open(AIRPORTS_CSV / "airport-frequencies.csv", newline="", encoding="utf-8") as f:
        freqs_data = list(csv.DictReader(f))

    while True:
        fix = get_gps_fix()
        if fix:
            selected = select_frequencies(fix["lat"], fix["lon"], airports, freqs_data)
            OUTPUT_FREQS.write_text(json.dumps(selected, indent=2))
            OUTPUT_GPS.write_text(json.dumps(fix, indent=2))
            print(f"[freq-manager] GPS fix: {fix['lat']:.4f},{fix['lon']:.4f} → {len(selected)} freqs")
        else:
            print("[freq-manager] No GPS fix")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
```

**Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY freq_manager.py .
CMD ["python", "freq_manager.py"]
```

**requirements.txt:**
```
# no external deps beyond stdlib
```

---

### 4.5 sdr-hub (airband receiver)
- Source: `https://github.com/shajen/sdr-hub`
- Build from source or existing container
- Must watch `/data/active_freqs.json` and reload on change
- Writes audio output to `/data/audio/` as WAV files
- Filename convention (required by whisper-worker): `{ICAO}_{TYPE}_{FREQ_MHZ}_{UNIX_TS}.wav`
- **Integration task:** Add a watcher script or modify sdr-hub config to reload frequencies from `active_freqs.json` on file change (use `inotifywait` wrapper or polling loop)

**Frequency reload wrapper (`freq_watcher.sh`):**
```bash
#!/bin/bash
# Watches active_freqs.json, signals sdr-hub to reload on change
FREQS_FILE="/data/active_freqs.json"
LAST_HASH=""
while true; do
    HASH=$(md5sum "$FREQS_FILE" 2>/dev/null | cut -d' ' -f1)
    if [ "$HASH" != "$LAST_HASH" ]; then
        LAST_HASH="$HASH"
        echo "[freq_watcher] Frequencies changed, reloading sdr-hub"
        # Signal depends on sdr-hub implementation:
        # Option A: kill -SIGHUP <sdr-hub-pid>
        # Option B: write to sdr-hub config and restart service
        pkill -SIGHUP sdr-hub 2>/dev/null || true
    fi
    sleep 15
done
```

---

### 4.6 whisper-worker (local transcription)

**Purpose:** Watches `/data/audio/`, transcribes new WAV files via whisper.cpp, writes JSON transcripts.

**Model:** `ggml-base.en.bin` (recommended for airband — aviation vocabulary, adequate speed on ZimaBlade Celeron)  
**Alternative:** `ggml-tiny.en.bin` for faster throughput at lower accuracy  
**Do NOT use:** multilingual models for airband (English-only models perform better)

**File: `worker.py`**
```python
"""
Watches /data/audio/ for new .wav files.
Runs whisper.cpp binary (must be compiled into container).
Writes transcript to /data/transcripts/{stem}.json
"""

import subprocess, json, time, os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

AUDIO_DIR      = Path("/data/audio")
TRANSCRIPT_DIR = Path("/data/transcripts")
WHISPER_BIN    = "/app/whisper.cpp/main"
MODEL_PATH     = "/config/whisper-model/ggml-base.en.bin"

TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

class AudioHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".wav":
            return
        time.sleep(0.5)  # let write complete
        self.transcribe(path)

    def transcribe(self, wav_path: Path):
        print(f"[whisper-worker] Transcribing {wav_path.name}")
        try:
            result = subprocess.run(
                [
                    WHISPER_BIN,
                    "-m", MODEL_PATH,
                    "-f", str(wav_path),
                    "--output-json",
                    "--output-file", str(TRANSCRIPT_DIR / wav_path.stem),
                    "--no-prints",
                    "--language", "en",
                    "--threads", "4",
                ],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                # Enrich transcript JSON with metadata from filename
                meta = parse_filename(wav_path.name)
                transcript_path = TRANSCRIPT_DIR / f"{wav_path.stem}.json"
                if transcript_path.exists():
                    data = json.loads(transcript_path.read_text())
                    data["meta"] = meta
                    data["audio_file"] = wav_path.name
                    data["timestamp_unix"] = meta.get("ts", int(time.time()))
                    transcript_path.write_text(json.dumps(data, indent=2))
                    print(f"[whisper-worker] Done: {wav_path.stem}")
            else:
                print(f"[whisper-worker] Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"[whisper-worker] Timeout on {wav_path.name}")

def parse_filename(name: str) -> dict:
    """
    Expected format: {ICAO}_{TYPE}_{FREQ_MHZ}_{UNIX_TS}.wav
    Example: EBAW_ATIS_126450_1710000000.wav
    """
    try:
        stem = Path(name).stem
        parts = stem.split("_")
        return {
            "icao": parts[0],
            "type": parts[1],
            "freq_mhz": float(parts[2]) / 1000,
            "ts": int(parts[3])
        }
    except Exception:
        return {}

if __name__ == "__main__":
    handler = AudioHandler()
    observer = Observer()
    observer.schedule(handler, str(AUDIO_DIR), recursive=False)
    observer.start()
    print(f"[whisper-worker] Watching {AUDIO_DIR}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

**Dockerfile:**
```dockerfile
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    build-essential cmake git python3 python3-pip \
    libsdl2-dev ffmpeg && rm -rf /var/lib/apt/lists/*

# Build whisper.cpp
WORKDIR /app
RUN git clone https://github.com/ggerganov/whisper.cpp.git
WORKDIR /app/whisper.cpp
RUN cmake -B build -DWHISPER_NO_AVX512=ON && cmake --build build -j$(nproc)
RUN cp build/bin/main /app/whisper.cpp/main

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt
COPY worker.py .

CMD ["python3", "worker.py"]
```

**requirements.txt:**
```
watchdog==4.0.0
```

---

### 4.7 feed-backend (FastAPI)

**Purpose:** SSE endpoint for live transcript feed. Audio file serving. GPS state endpoint.

**File: `main.py`**
```python
"""
FastAPI backend.
GET /events         → SSE stream of new transcripts
GET /audio/{file}   → serve WAV file
GET /gps            → current GPS fix
GET /freqs          → current active frequencies
"""

import asyncio, json, time
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import deque

app = FastAPI()

TRANSCRIPT_DIR = Path("/data/transcripts")
AUDIO_DIR      = Path("/data/audio")
GPS_STATE      = Path("/data/gps_state.json")
ACTIVE_FREQS   = Path("/data/active_freqs.json")

# In-memory event queue (last 200 entries)
event_queue: deque = deque(maxlen=200)
subscribers: list[asyncio.Queue] = []

class TranscriptHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".json"):
            return
        time.sleep(0.2)
        try:
            data = json.loads(Path(event.src_path).read_text())
            event_queue.append(data)
            for q in subscribers:
                q.put_nowait(data)
        except Exception as e:
            print(f"[feed-backend] Error reading transcript: {e}")

observer = Observer()
observer.schedule(TranscriptHandler(), str(TRANSCRIPT_DIR), recursive=False)
observer.start()

@app.get("/events")
async def sse_events():
    q: asyncio.Queue = asyncio.Queue()
    subscribers.append(q)

    async def generator():
        # Send backlog (last 50)
        for entry in list(event_queue)[-50:]:
            yield f"data: {json.dumps(entry)}\n\n"
        try:
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {json.dumps(item)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            subscribers.remove(q)

    return StreamingResponse(generator(), media_type="text/event-stream")

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    path = AUDIO_DIR / filename
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="audio/wav")

@app.get("/gps")
async def gps():
    if GPS_STATE.exists():
        return JSONResponse(json.loads(GPS_STATE.read_text()))
    return JSONResponse({"error": "no fix"}, status_code=503)

@app.get("/freqs")
async def freqs():
    if ACTIVE_FREQS.exists():
        return JSONResponse(json.loads(ACTIVE_FREQS.read_text()))
    return JSONResponse([])
```

**Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn watchdog
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 4.8 ui-proxy (Nginx + split-screen UI)

**nginx.conf:**
```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        index index.html;
    }

    location /radar/ {
        proxy_pass http://tar1090:8088/;
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://feed-backend:8000/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

**ui/index.html** — single-file split-screen:
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AirWatch Mobile</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0a0a0f; color: #e0e0e0; font-family: 'Courier New', monospace; height: 100vh; display: flex; flex-direction: column; }
  #header { background: #111; border-bottom: 1px solid #333; padding: 6px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; }
  #gps-status { color: #4af; }
  #split { display: flex; flex: 1; overflow: hidden; }
  #radar-pane { flex: 1; border-right: 1px solid #333; }
  #radar-pane iframe { width: 100%; height: 100%; border: none; }
  #feed-pane { width: 380px; display: flex; flex-direction: column; overflow: hidden; }
  #feed-header { background: #111; padding: 8px 12px; font-size: 11px; color: #888; border-bottom: 1px solid #222; }
  #feed { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 6px; }
  .entry { background: #111; border: 1px solid #222; border-left: 3px solid #4af; border-radius: 4px; padding: 8px 10px; }
  .entry.ATIS { border-left-color: #fa4; }
  .entry.TWR  { border-left-color: #4f8; }
  .entry.APP  { border-left-color: #f4f; }
  .entry.GND  { border-left-color: #fa8; }
  .entry-meta { display: flex; justify-content: space-between; font-size: 10px; color: #666; margin-bottom: 4px; }
  .entry-icao { color: #4af; font-weight: bold; }
  .entry-type { color: #fa4; }
  .entry-freq { color: #888; }
  .entry-text { font-size: 12px; line-height: 1.5; color: #ccc; margin-bottom: 6px; }
  .play-btn { background: #1a2a3a; border: 1px solid #4af; color: #4af; padding: 3px 10px; border-radius: 3px; cursor: pointer; font-size: 11px; }
  .play-btn:hover { background: #4af; color: #000; }
  .play-btn.playing { background: #4af; color: #000; }
  #freq-bar { background: #111; border-top: 1px solid #222; padding: 6px 12px; font-size: 10px; color: #555; display: flex; gap: 12px; flex-wrap: wrap; }
  .freq-chip { background: #1a1a2e; border: 1px solid #333; border-radius: 3px; padding: 2px 8px; }
  .freq-chip.active { border-color: #4af; color: #4af; }
</style>
</head>
<body>
<div id="header">
  <span>▶ AIRWATCH MOBILE</span>
  <span id="gps-status">GPS: acquiring...</span>
  <span id="entry-count">0 transmissions</span>
</div>
<div id="split">
  <div id="radar-pane">
    <iframe src="/radar/" title="ADS-B Radar"></iframe>
  </div>
  <div id="feed-pane">
    <div id="feed-header">AIRBAND FEED — live transcription</div>
    <div id="feed"></div>
    <div id="freq-bar">monitoring: <span id="freq-chips">—</span></div>
  </div>
</div>

<script>
const feed = document.getElementById('feed');
let count = 0;

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toTimeString().slice(0, 8);
}

function getText(data) {
  if (data.transcription) return data.transcription;
  if (data.text) return data.text;
  if (data.segments && data.segments.length) return data.segments.map(s => s.text).join(' ').trim();
  return '[no transcription]';
}

function addEntry(data) {
  const meta = data.meta || {};
  const text = getText(data);
  if (!text || text === '[no transcription]') return;

  const el = document.createElement('div');
  const type = (meta.type || 'UNK').toUpperCase();
  el.className = `entry ${type}`;

  const audioFile = data.audio_file || '';
  const ts = meta.ts || data.timestamp_unix || Math.floor(Date.now()/1000);

  el.innerHTML = `
    <div class="entry-meta">
      <span>
        <span class="entry-icao">${meta.icao || '???'}</span>
        <span class="entry-type"> ${type}</span>
        <span class="entry-freq"> ${meta.freq_mhz ? meta.freq_mhz.toFixed(3) + ' MHz' : ''}</span>
      </span>
      <span>${formatTime(ts)}</span>
    </div>
    <div class="entry-text">${text}</div>
    ${audioFile ? `<button class="play-btn" onclick="playAudio(this, '${audioFile}')">▶ play</button>` : ''}
  `;

  feed.prepend(el);
  count++;
  document.getElementById('entry-count').textContent = `${count} transmissions`;

  // Keep feed to 100 entries
  while (feed.children.length > 100) feed.removeChild(feed.lastChild);
}

let currentAudio = null;
function playAudio(btn, file) {
  if (currentAudio) {
    currentAudio.pause();
    document.querySelectorAll('.play-btn.playing').forEach(b => { b.textContent = '▶ play'; b.classList.remove('playing'); });
  }
  const audio = new Audio(`/api/audio/${file}`);
  currentAudio = audio;
  btn.textContent = '■ stop';
  btn.classList.add('playing');
  audio.play();
  audio.onended = () => { btn.textContent = '▶ play'; btn.classList.remove('playing'); };
}

// SSE connection
function connectSSE() {
  const es = new EventSource('/api/events');
  es.onmessage = e => {
    try { addEntry(JSON.parse(e.data)); } catch {}
  };
  es.onerror = () => { setTimeout(connectSSE, 3000); es.close(); };
}
connectSSE();

// GPS status polling
async function pollGPS() {
  try {
    const r = await fetch('/api/gps');
    if (r.ok) {
      const d = await r.json();
      document.getElementById('gps-status').textContent =
        `GPS: ${d.lat.toFixed(4)}, ${d.lon.toFixed(4)} | ${(d.speed * 3.6).toFixed(0)} km/h`;
      document.getElementById('gps-status').style.color = '#4f8';
    }
  } catch {}
}

// Frequency bar polling
async function pollFreqs() {
  try {
    const r = await fetch('/api/freqs');
    if (r.ok) {
      const freqs = await r.json();
      const chips = document.getElementById('freq-chips');
      if (freqs.length) {
        chips.innerHTML = freqs.map(f =>
          `<span class="freq-chip active" title="${f.name}">${f.icao} ${f.type} ${f.mhz.toFixed(3)}</span>`
        ).join('');
      }
    }
  } catch {}
}

setInterval(pollGPS, 15000);
setInterval(pollFreqs, 30000);
pollGPS();
pollFreqs();
</script>
</body>
</html>
```

---

## 5. docker-compose.yml

```yaml
version: "3.9"

volumes:
  data:

networks:
  airband:

services:

  readsb:
    image: ghcr.io/sdr-enthusiasts/docker-readsb-protobuf:latest
    container_name: readsb
    restart: unless-stopped
    devices:
      - /dev/bus/usb:/dev/bus/usb
    environment:
      READSB_DEVICE_TYPE: rtlsdr
      READSB_RTLSDR_DEVICE: "00000001"   # SDR #1 serial
      READSB_GAIN: autogain
      READSB_NET_ENABLE: "true"
      READSB_NET_BEAST_OUTPUT_PORT: "30005"
      READSB_NET_RAW_OUTPUT_PORT: "30002"
      READSB_GPSD_SERVER: "172.17.0.1"
      READSB_GPSD_PORT: "2947"
    ports:
      - "8080:8080"
      - "30005:30005"
      - "30002:30002"
    networks:
      - airband

  tar1090:
    image: ghcr.io/sdr-enthusiasts/docker-tar1090:latest
    container_name: tar1090
    restart: unless-stopped
    environment:
      BEASTHOST: readsb
      BEASTPORT: "30005"
    ports:
      - "8088:80"
    networks:
      - airband
    depends_on:
      - readsb

  freq-manager:
    build: ./services/freq-manager
    container_name: freq-manager
    restart: unless-stopped
    volumes:
      - data:/data
      - ./config:/config:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - airband

  sdr-hub:
    build:
      context: .
      dockerfile: ./services/sdr-hub/Dockerfile   # existing build
    container_name: sdr-hub
    restart: unless-stopped
    devices:
      - /dev/bus/usb:/dev/bus/usb
    volumes:
      - data:/data
    environment:
      SDR_SERIAL: "00000002"                        # SDR #2 serial
      AUDIO_OUTPUT_DIR: /data/audio
      FREQS_CONFIG: /data/active_freqs.json
    networks:
      - airband
    depends_on:
      - freq-manager

  whisper-worker:
    build: ./services/whisper-worker
    container_name: whisper-worker
    restart: unless-stopped
    volumes:
      - data:/data
      - ./config:/config:ro
    networks:
      - airband

  feed-backend:
    build: ./services/feed-backend
    container_name: feed-backend
    restart: unless-stopped
    volumes:
      - data:/data
    ports:
      - "8000:8000"
    networks:
      - airband

  ui-proxy:
    image: nginx:alpine
    container_name: ui-proxy
    restart: unless-stopped
    volumes:
      - ./ui:/usr/share/nginx/html:ro
      - ./config/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    ports:
      - "80:80"
    networks:
      - airband
    depends_on:
      - feed-backend
      - tar1090
```

---

## 6. SDR Dongle Identification & Assignment

Before deployment, fix USB serial numbers so Docker device mapping is deterministic:

```bash
# List dongles
rtl_test -t

# Set serial on SDR #1 (ADS-B)
rtl_eeprom -d 0 -s 00000001

# Set serial on SDR #2 (airband)
rtl_eeprom -d 1 -s 00000002

# Verify
rtl_test -d 00000001
rtl_test -d 00000002
```

---

## 7. OurAirports Data Setup

```bash
mkdir -p /opt/airband/config/airports.csv
cd /opt/airband/config/airports.csv

# Download
wget https://davidmegginson.github.io/ourairports-data/airports.csv
wget https://davidmegginson.github.io/ourairports-data/airport-frequencies.csv

# Optional: pre-filter to BE/NL/DE/FR/LU to reduce memory
awk -F',' 'NR==1 || $9 ~ /^"(BE|NL|DE|FR|LU|GB)"/' airports.csv > airports_eur.csv
```

---

## 8. Whisper Model Download

```bash
cd /opt/airband/config/whisper-model

# Base English (recommended — ~150MB)
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

# Tiny English (faster, lower accuracy)
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin
```

---

## 9. Autostart on Boot (ZimaBlade)

```bash
# /etc/systemd/system/airband.service
[Unit]
Description=AirWatch Mobile Stack
After=network.target gpsd.service

[Service]
Type=simple
WorkingDirectory=/opt/airband
ExecStartPre=/usr/bin/docker compose pull --quiet
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable airband.service
```

---

## 10. Known Constraints & Open Items

| Item | Status | Notes |
|---|---|---|
| sdr-hub freq reload API | **OPEN** | Needs verification — may require fork/wrapper |
| whisper.cpp AVX support | **OPEN** | ZimaBlade Celeron N3450 — disable AVX512, test AVX2 |
| Single SDR airband | **CONSTRAINT** | One frequency at a time; scan-modus not yet implemented |
| GPS cold start latency | **KNOWN** | First fix may take 30–60s; services must handle no-fix gracefully |
| Audio file naming | **REQUIRED** | sdr-hub must be configured/patched to output `{ICAO}_{TYPE}_{FREQ}_{TS}.wav` |
| Deepgram | **REMOVED** | All transcription via local whisper.cpp only |
| Multi-freq scanning | **FUTURE** | Requires squelch detection + freq hopping logic in sdr-hub wrapper |

---

## 11. Build Order for Claude Code

```
1. Setup gpsd on host → verify with gpspipe
2. Build freq-manager → test with mock GPS coords (EBAW, EBBR)
3. Integrate readsb with gpsd → verify radar centering
4. Build whisper-worker → test with sample airband WAV
5. Build feed-backend → test SSE with manual JSON drop
6. Integrate sdr-hub → verify audio file output naming
7. Build ui-proxy + index.html → full stack test
8. docker-compose full stack → integration test
9. Autostart systemd → reboot test
```

---

*Spec version: 1.0 | Platform: ZimaBlade x86 | No cloud dependencies*
