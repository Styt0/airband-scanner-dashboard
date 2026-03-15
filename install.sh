#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Airband Scanner — See & Hear Planes Near You                              ║
# ║  One-script installer for Raspberry Pi + RTL-SDR                           ║
# ║                                                                            ║
# ║  What it does:                                                             ║
# ║    1. sdr-hub (Docker) — scans airband AM frequencies, records audio       ║
# ║    2. Transcriber — speech-to-text via Deepgram + whisper.cpp fallback     ║
# ║    3. Aircraft tracker — logs ADS-B positions from tar1090                 ║
# ║    4. Web viewer (:8002) — browse transcripts, play audio, radar maps      ║
# ║                                                                            ║
# ║  Requirements:                                                             ║
# ║    • Raspberry Pi 4 (4GB+) with Debian/Raspbian 12 (bookworm)             ║
# ║    • RTL-SDR dongle for airband scanning                                   ║
# ║    • (Optional) Second RTL-SDR for ADS-B + ultrafeeder/tar1090            ║
# ║    • (Optional) Deepgram API key for cloud transcription                   ║
# ║                                                                            ║
# ║  Usage:                                                                    ║
# ║    curl -sSL https://raw.githubusercontent.com/YOU/airband-scanner/main/install.sh | sudo bash  ║
# ║    — or —                                                                  ║
# ║    sudo bash install.sh                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    echo '    _    _      _                     _   ____'
    echo '   / \  (_)_ __| |__   __ _ _ __   __| | / ___|  ___ __ _ _ __  _ __   ___ _ __'
    echo '  / _ \ | |  __| |_ \ / _` |  _ \ / _` | \___ \ / __/ _` |  _ \|  _ \ / _ \  __|'
    echo ' / ___ \| | |  | |_) | (_| | | | | (_| |  ___) | (_| (_| | | | | | | |  __/ |'
    echo '/_/   \_\_|_|  |_.__/ \__,_|_| |_|\__,_| |____/ \___\__,_|_| |_|_| |_|\___|_|'
    echo -e "${NC}"
    echo -e "${BOLD}See & Hear Planes Near You${NC}"
    echo ""
}

info()  { echo -e "${GREEN}[*]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
err()   { echo -e "${RED}[✗]${NC} $*"; }
ask()   { echo -en "${BLUE}[?]${NC} $* "; }

banner

# ── Preflight checks ────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    err "Please run as root: sudo bash install.sh"
    exit 1
fi

ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "armv7l" && "$ARCH" != "x86_64" ]]; then
    err "Unsupported architecture: $ARCH (need aarch64, armv7l, or x86_64)"
    exit 1
fi

info "Architecture: $ARCH"
info "OS: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')"

# ── Configuration ────────────────────────────────────────────────────────────
INSTALL_DIR="/opt/airband"
SDR_HUB_DIR="/opt/sdr-hub"
WHISPER_DIR="/opt/whisper.cpp"
VIEWER_PORT=8002
SDR_HUB_PORT=8001

CONFIG_FILE="$INSTALL_DIR/config.env"

# Defaults (user can override)
STATION_LAT=""
STATION_LON=""
STATION_NAME=""
DEEPGRAM_KEY=""
WHISPER_MODEL="base.en"
TAR1090_URL="http://127.0.0.1:8080/data/aircraft.json"
AIRCRAFT_RANGE_KM=150
RETENTION_DAYS=7
DAILY_DG_LIMIT=500

# Load existing config if upgrading
if [[ -f "$CONFIG_FILE" ]]; then
    info "Found existing config at $CONFIG_FILE"
    source "$CONFIG_FILE"
fi

echo ""
echo -e "${BOLD}── Station Configuration ──${NC}"
echo ""

# Station location
if [[ -z "$STATION_LAT" ]]; then
    ask "Your latitude (e.g. 51.189 for Antwerp):"
    read -r STATION_LAT
fi
if [[ -z "$STATION_LON" ]]; then
    ask "Your longitude (e.g. 4.460 for Antwerp):"
    read -r STATION_LON
fi
if [[ -z "$STATION_NAME" ]]; then
    ask "Station name (e.g. EBAW, KJFK, EGLL — or press Enter to skip):"
    read -r STATION_NAME
    STATION_NAME="${STATION_NAME:-MYSTATION}"
fi

# Deepgram (optional)
if [[ -z "$DEEPGRAM_KEY" ]]; then
    echo ""
    echo -e "  ${CYAN}Deepgram provides high-quality cloud transcription (500 free/day).${NC}"
    echo -e "  ${CYAN}Without it, only local whisper.cpp is used (slower but free/unlimited).${NC}"
    echo -e "  ${CYAN}Get a free key at: https://console.deepgram.com${NC}"
    echo ""
    ask "Deepgram API key (or press Enter to skip):"
    read -r DEEPGRAM_KEY
fi

# tar1090 URL
echo ""
echo -e "  ${CYAN}If you have tar1090/ultrafeeder running for ADS-B, the radar map${NC}"
echo -e "  ${CYAN}overlay will show aircraft positions alongside transcripts.${NC}"
echo ""
ask "tar1090 aircraft.json URL [$TAR1090_URL]:"
read -r input_tar1090
TAR1090_URL="${input_tar1090:-$TAR1090_URL}"

# Whisper model
echo ""
echo -e "  ${CYAN}Whisper model sizes (local speech-to-text, runs on Pi):${NC}"
echo -e "  ${CYAN}  base.en  — 148 MB, ~20s/clip  (faster, decent quality)${NC}"
echo -e "  ${CYAN}  small.en — 466 MB, ~60s/clip  (better quality, slower)${NC}"
echo ""
ask "Whisper model [base.en / small.en] ($WHISPER_MODEL):"
read -r input_model
WHISPER_MODEL="${input_model:-$WHISPER_MODEL}"

echo ""
info "Configuration:"
info "  Location:  $STATION_LAT, $STATION_LON ($STATION_NAME)"
info "  Deepgram:  ${DEEPGRAM_KEY:+configured}${DEEPGRAM_KEY:-skipped (whisper-only)}"
info "  tar1090:   $TAR1090_URL"
info "  Whisper:   $WHISPER_MODEL"
echo ""

ask "Continue with installation? [Y/n]:"
read -r confirm
if [[ "${confirm,,}" == "n" ]]; then
    echo "Aborted."
    exit 0
fi

# ── Install system dependencies ──────────────────────────────────────────────
info "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip cmake git curl wget docker.io >/dev/null 2>&1

# Ensure Docker is running
systemctl enable --now docker >/dev/null 2>&1 || true

# Python packages
pip3 install --quiet --break-system-packages requests psutil 2>/dev/null || \
pip3 install --quiet requests psutil 2>/dev/null || true

info "Dependencies installed"

# ── Create directories ───────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR" "$SDR_HUB_DIR/data" "$WHISPER_DIR"

# ── Save configuration ──────────────────────────────────────────────────────
cat > "$CONFIG_FILE" << ENVEOF
# Airband Scanner configuration — generated $(date -Iseconds)
STATION_LAT=$STATION_LAT
STATION_LON=$STATION_LON
STATION_NAME=$STATION_NAME
DEEPGRAM_KEY=$DEEPGRAM_KEY
WHISPER_MODEL=$WHISPER_MODEL
TAR1090_URL=$TAR1090_URL
AIRCRAFT_RANGE_KM=$AIRCRAFT_RANGE_KM
RETENTION_DAYS=$RETENTION_DAYS
DAILY_DG_LIMIT=$DAILY_DG_LIMIT
ENVEOF
chmod 600 "$CONFIG_FILE"
info "Config saved to $CONFIG_FILE"

# ── Deploy sdr-hub (Docker) ─────────────────────────────────────────────────
info "Starting sdr-hub container..."
if docker ps -a --format '{{.Names}}' | grep -q '^sdr-hub$'; then
    info "sdr-hub container already exists — skipping"
else
    docker run -d \
        --name sdr-hub \
        --restart unless-stopped \
        -p "${SDR_HUB_PORT}:80" \
        -v "${SDR_HUB_DIR}/data:/app/data" \
        -v "${SDR_HUB_DIR}/log:/var/log/sdr" \
        --device /dev/bus/usb \
        shajen/sdr-hub
    info "sdr-hub started on port $SDR_HUB_PORT"
    echo ""
    warn "IMPORTANT: Open http://$(hostname -I | awk '{print $1}'):${SDR_HUB_PORT} in your browser"
    warn "and configure sdr-hub with your RTL-SDR device + airband frequencies."
    warn "The installer will continue setting up the transcription stack."
    echo ""
fi

# ── Write transcriber.py ────────────────────────────────────────────────────
info "Writing transcription worker..."
cat > "$INSTALL_DIR/transcriber.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Airband transcriber — Deepgram primary, whisper.cpp fallback.
Bandpass filter, suppress-nst, ATC prompt, hallucination detector.
"""
import array, datetime, io, logging, math, os, re, sqlite3, struct, subprocess, time, wave

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Config (from environment / defaults) ─────────────────────────────────────
DEEPGRAM_API_KEY  = os.environ.get('DEEPGRAM_KEY', '')
DB_PATH           = os.environ.get('DB_PATH', '/opt/sdr-hub/data/db.sqlite3')
DATA_ROOT         = os.environ.get('DATA_ROOT', '/opt/sdr-hub/data/public/media')
LOG_FILE          = os.environ.get('LOG_FILE', '/opt/airband/transcriber.log')
WHISPER_CLI       = os.environ.get('WHISPER_CLI', '/opt/whisper.cpp/build/bin/whisper-cli')
MAX_DAILY         = int(os.environ.get('DAILY_DG_LIMIT', '500'))
MIN_DURATION_S    = float(os.environ.get('MIN_DURATION_S', '2.0'))
POLL_INTERVAL_S   = 10
DEEPGRAM_URL      = 'https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&language=en&punctuate=true'

# Whisper model priority: small.en > base.en > base
WHISPER_MODELS = [
    '/opt/whisper.cpp/models/ggml-small.en.bin',
    '/opt/whisper.cpp/models/ggml-base.en.bin',
    '/opt/whisper.cpp/models/ggml-base.bin',
]

WHISPER_PROMPT = (
    "Air traffic control radio communication. "
    "Callsigns, runway numbers, flight levels, altitudes, headings, QNH, squawk codes."
)

HALLUCINATION_RE = re.compile(
    r'^\s*([\[\(][^\]\)]+[\]\)]\s*)+$', re.IGNORECASE
)
HALLUCINATION_PHRASES = {
    'thank you', 'thanks for watching', 'subscribe',
    'like and subscribe', 'please subscribe',
    'thank you for watching', 'bye',
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(LOG_FILE)]
)
log = logging.getLogger('transcriber')


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    return conn


def count_today(conn):
    today = datetime.date.today().isoformat()
    row = conn.execute(
        "SELECT COUNT(*) FROM sdr_transcript WHERE created_at >= ? AND model LIKE 'nova%'",
        (today,)
    ).fetchone()
    return row[0] if row else 0


def whisper_model():
    for m in WHISPER_MODELS:
        if os.path.exists(m):
            return m
    return None


def whisper_ready():
    return os.path.exists(WHISPER_CLI) and whisper_model() is not None


def whisper_model_label(path):
    return os.path.basename(path).replace('ggml-', 'whisper-').replace('.bin', '')


def _biquad(samples, b0, b1, b2, a1, a2):
    x1 = x2 = y1 = y2 = 0.0
    out = [0.0] * len(samples)
    for i, s in enumerate(samples):
        y = b0 * s + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, s
        y2, y1 = y1, y
        out[i] = y
    return out


def bandpass_voice(samples, sr, lo=300.0, hi=3400.0):
    w = math.tan(math.pi * lo / sr)
    n = 1.0 / (1.0 + math.sqrt(2.0) * w + w * w)
    b0, b1, b2 = n, -2.0 * n, n
    a1 = 2.0 * (w * w - 1.0) * n
    a2 = (1.0 - math.sqrt(2.0) * w + w * w) * n
    samples = _biquad(samples, b0, b1, b2, a1, a2)
    w = math.tan(math.pi * hi / sr)
    n = 1.0 / (1.0 + math.sqrt(2.0) * w + w * w)
    b0 = w * w * n
    b1 = 2.0 * b0
    b2 = b0
    a1 = 2.0 * (w * w - 1.0) * n
    a2 = (1.0 - math.sqrt(2.0) * w + w * w) * n
    return _biquad(samples, b0, b1, b2, a1, a2)


def decode_cu8_to_wav(filepath, sample_rate):
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
        iq = array.array('B', raw)
        n = len(iq) // 2
        if n == 0:
            return None
        envelope = [math.sqrt((iq[2*i] - 127.5)**2 + (iq[2*i+1] - 127.5)**2) for i in range(n)]
        mean = sum(envelope) / n
        envelope = [v - mean for v in envelope]
        envelope = bandpass_voice(envelope, sample_rate)
        peak = max(abs(v) for v in envelope) or 1.0
        scale = 29000.0 / peak
        samples = struct.pack(
            f"<{n}h",
            *[max(-32768, min(32767, int(v * scale))) for v in envelope]
        )
        buf = io.BytesIO()
        with wave.open(buf, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(samples)
        return buf.getvalue()
    except Exception as e:
        log.error('Audio decode error: %s', e)
        return None


def resample_wav_16k(wav_bytes, src_rate):
    if src_rate == 16000:
        return wav_bytes
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, 'r') as wf:
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    src = struct.unpack(f"<{n_frames}h", raw)
    ratio = 16000.0 / src_rate
    new_n = int(n_frames * ratio)
    out = [0] * new_n
    for i in range(new_n):
        pos = i / ratio
        i0 = int(pos)
        frac = pos - i0
        if i0 + 1 < n_frames:
            out[i] = max(-32768, min(32767, int(src[i0] * (1 - frac) + src[i0+1] * frac)))
        elif i0 < n_frames:
            out[i] = src[i0]
    out_buf = io.BytesIO()
    with wave.open(out_buf, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(struct.pack(f"<{new_n}h", *out))
    return out_buf.getvalue()


def is_hallucination(text):
    if not text:
        return True
    t = text.strip()
    if len(t) < 3:
        return True
    if HALLUCINATION_RE.match(t):
        return True
    if t.lower() in HALLUCINATION_PHRASES:
        return True
    return False


def transcribe_deepgram(wav_bytes):
    if not HAS_REQUESTS or not DEEPGRAM_API_KEY:
        raise RuntimeError("Deepgram not configured")
    headers = {'Authorization': f'Token {DEEPGRAM_API_KEY}', 'Content-Type': 'audio/wav'}
    resp = requests.post(DEEPGRAM_URL, headers=headers, data=wav_bytes, timeout=30)
    resp.raise_for_status()
    alt = resp.json()['results']['channels'][0]['alternatives'][0]
    return alt.get('transcript', '').strip(), alt.get('confidence', 0.0), 'nova-3'


def transcribe_whisper_cpp(wav_bytes, src_rate):
    model_path = whisper_model()
    if not model_path:
        raise RuntimeError("No whisper model available")
    wav_16k = resample_wav_16k(wav_bytes, src_rate)
    tmp = f'/tmp/whisper_{os.getpid()}_{int(time.time())}.wav'
    try:
        with open(tmp, 'wb') as f:
            f.write(wav_16k)
        cmd = [
            WHISPER_CLI, '-m', model_path, '-f', tmp, '-l', 'en',
            '--no-timestamps', '-np', '--suppress-nst',
            '--no-speech-thold', '0.50', '--entropy-thold', '2.2',
            '--prompt', WHISPER_PROMPT, '-t', '4',
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        lines = [l.strip() for l in result.stdout.splitlines()
                 if l.strip() and not l.startswith('[') and not l.startswith('whisper_')]
        text = ' '.join(lines).strip()
        model_label = whisper_model_label(model_path)
        if is_hallucination(text):
            log.info('whisper hallucination suppressed: "%s"', text)
            return '', 0.0, model_label
        return text, 0.70, model_label
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    model = whisper_model()
    model_name = os.path.basename(model) if model else 'none'
    dg_status = 'configured' if DEEPGRAM_API_KEY else 'not configured'
    log.info('Transcriber started. whisper=%s deepgram=%s bandpass=ON suppress-nst=ON', model_name, dg_status)

    while True:
        try:
            with get_conn() as conn:
                rows = conn.execute("""
                    SELECT t.id, t.begin_frequency, t.end_frequency,
                           t.data_file, t.begin_date, t.end_date
                    FROM sdr_transmission t
                    LEFT JOIN sdr_group g ON g.id = t.group_id
                    LEFT JOIN sdr_transcript tr ON tr.transmission_id = t.id
                    WHERE tr.id IS NULL AND t.data_file IS NOT NULL AND g.modulation = 'AM'
                      AND (julianday(t.end_date) - julianday(t.begin_date)) * 86400 >= ?
                    ORDER BY t.id ASC LIMIT 10
                """, (MIN_DURATION_S,)).fetchall()

            if not rows:
                time.sleep(POLL_INTERVAL_S)
                continue

            log.info('Found %d pending transmission(s)', len(rows))

            for row in rows:
                tx_id     = row['id']
                data_file = row['data_file']
                filepath  = os.path.join(DATA_ROOT, data_file)
                sr        = row['end_frequency'] - row['begin_frequency']

                if not os.path.exists(filepath):
                    with get_conn() as conn:
                        conn.execute(
                            'INSERT OR REPLACE INTO sdr_transcript '
                            '(transmission_id, text, confidence, model, error) VALUES (?,?,?,?,?)',
                            (tx_id, '', 0.0, 'none', 'file_missing'))
                        conn.commit()
                    continue

                wav = decode_cu8_to_wav(filepath, sr)
                if not wav:
                    continue

                with get_conn() as conn:
                    use_deepgram = DEEPGRAM_API_KEY and count_today(conn) < MAX_DAILY

                try:
                    if use_deepgram:
                        text, conf, model_name = transcribe_deepgram(wav)
                        log.info('tx %d: [deepgram %.0f%%] %s', tx_id, conf*100, text[:80] if text else '(no speech)')
                    elif whisper_ready():
                        text, conf, model_name = transcribe_whisper_cpp(wav, sr)
                        log.info('tx %d: [%s] %s', tx_id, model_name, text[:80] if text else '(no speech)')
                    else:
                        log.info('tx %d: no transcription engine available — waiting', tx_id)
                        time.sleep(60)
                        break

                    if not text:
                        try:
                            os.remove(filepath)
                        except OSError:
                            pass

                    with get_conn() as conn:
                        conn.execute(
                            'INSERT OR REPLACE INTO sdr_transcript '
                            '(transmission_id, text, confidence, model) VALUES (?,?,?,?)',
                            (tx_id, text, conf, model_name))
                        conn.commit()

                except Exception as e:
                    log.error('tx %d error: %s', tx_id, e)
                    if use_deepgram and whisper_ready():
                        try:
                            text, conf, model_name = transcribe_whisper_cpp(wav, sr)
                            with get_conn() as conn:
                                conn.execute(
                                    'INSERT OR REPLACE INTO sdr_transcript '
                                    '(transmission_id, text, confidence, model) VALUES (?,?,?,?)',
                                    (tx_id, text, conf, model_name))
                                conn.commit()
                        except Exception:
                            pass

        except Exception as e:
            log.error('Main loop error: %s', e)
            time.sleep(30)


if __name__ == '__main__':
    main()
PYEOF

# ── Write aircraft_tracker.py ───────────────────────────────────────────────
info "Writing aircraft tracker..."
cat > "$INSTALL_DIR/aircraft_tracker.py" << PYEOF
#!/usr/bin/env python3
"""Polls tar1090 for aircraft positions near your station. Stores to aircraft.db."""
import datetime, logging, math, os, requests, sqlite3, time

TAR1090_URL   = os.environ.get('TAR1090_URL', '$TAR1090_URL')
DB_PATH       = os.environ.get('AIRCRAFT_DB', '$INSTALL_DIR/aircraft.db')
LOG_FILE      = '$INSTALL_DIR/aircraft_tracker.log'
STATION_LAT   = float(os.environ.get('STATION_LAT', '$STATION_LAT'))
STATION_LON   = float(os.environ.get('STATION_LON', '$STATION_LON'))
MAX_RANGE_KM  = int(os.environ.get('AIRCRAFT_RANGE_KM', '$AIRCRAFT_RANGE_KM'))
KEEP_HOURS    = 48
POLL_INTERVAL = 8

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(LOG_FILE)]
)
log = logging.getLogger('aircraft-tracker')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            ts       TEXT NOT NULL,
            hex      TEXT,
            flight   TEXT,
            lat      REAL NOT NULL,
            lon      REAL NOT NULL,
            alt_baro INTEGER,
            gs       REAL,
            track    REAL,
            squawk   TEXT,
            dist_km  REAL
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ts ON positions(ts)')
    conn.commit()
    conn.close()


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(min(1.0, a)))


def poll():
    try:
        r = requests.get(TAR1090_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return 0

    now = datetime.datetime.utcnow().isoformat()
    rows = []
    for ac in data.get('aircraft', []):
        lat, lon = ac.get('lat'), ac.get('lon')
        if lat is None or lon is None:
            continue
        dist = haversine(STATION_LAT, STATION_LON, lat, lon)
        if dist > MAX_RANGE_KM:
            continue
        rows.append((now, ac.get('hex',''), (ac.get('flight') or '').strip(),
                      lat, lon, ac.get('alt_baro'), ac.get('gs'),
                      ac.get('track'), ac.get('squawk',''), round(dist,1)))

    if rows:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.executemany(
            'INSERT INTO positions (ts,hex,flight,lat,lon,alt_baro,gs,track,squawk,dist_km) '
            'VALUES (?,?,?,?,?,?,?,?,?,?)', rows)
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=KEEP_HOURS)).isoformat()
        conn.execute('DELETE FROM positions WHERE ts < ?', (cutoff,))
        conn.commit()
        conn.close()
    return len(rows)


def main():
    init_db()
    log.info('Aircraft tracker started - station %.3f,%.3f range %dkm',
             STATION_LAT, STATION_LON, MAX_RANGE_KM)
    counter = 0
    while True:
        n = poll()
        counter += 1
        if counter % 75 == 0:
            log.info('Polling... last: %d aircraft within %dkm', n, MAX_RANGE_KM)
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
PYEOF

# ── Write transcript_viewer.py ──────────────────────────────────────────────
info "Writing transcript viewer..."
cat > "$INSTALL_DIR/transcript_viewer.py" << PYEOF
#!/usr/bin/env python3
"""
Airband Transcript Viewer — Web UI for browsing radio transcripts + radar maps.
Configurable via environment variables for any location.
"""
import array, datetime, io, math, os, re, sqlite3, struct, socketserver, wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime as dt

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


# ── Config from environment ──────────────────────────────────────────────────
DB_PATH      = os.environ.get('DB_PATH', '/opt/sdr-hub/data/db.sqlite3')
DATA_ROOT    = os.environ.get('DATA_ROOT', '/opt/sdr-hub/data/public/media')
AIRCRAFT_DB  = os.environ.get('AIRCRAFT_DB', '/opt/airband/aircraft.db')
PORT         = int(os.environ.get('VIEWER_PORT', '8002'))
STATION_LAT  = float(os.environ.get('STATION_LAT', '0'))
STATION_LON  = float(os.environ.get('STATION_LON', '0'))
STATION_NAME = os.environ.get('STATION_NAME', 'HOME')
MAP_SIZE     = 440
MAP_RADIUS_KM = 100

# Users can add their own frequencies in config
KNOWN_FREQS = {}
_extra = os.environ.get('KNOWN_FREQS_CSV', '')  # format: "freq1:label1,freq2:label2"
if _extra:
    for pair in _extra.split(','):
        if ':' in pair:
            f, l = pair.split(':', 1)
            try:
                KNOWN_FREQS[float(f)] = l.strip()
            except ValueError:
                pass

# Some well-known global frequencies
KNOWN_FREQS.setdefault(121.500, "EMERGENCY")
KNOWN_FREQS.setdefault(123.450, "AIR-AIR")

# ATIS frequencies (for transmitter guessing — ATIS is a ground broadcast)
ATIS_MHZ = set()
LOCAL_TWR_MHZ = set()
LOCAL_APP_MHZ = set()
_atis = os.environ.get('ATIS_FREQS', '')
if _atis:
    for f in _atis.split(','):
        try:
            ATIS_MHZ.add(float(f.strip()))
        except ValueError:
            pass

# ── Phonetic alphabet for callsign extraction ────────────────────────────────
PHONETIC = {
    'alpha':'A','bravo':'B','charlie':'C','delta':'D','echo':'E',
    'foxtrot':'F','golf':'G','hotel':'H','india':'I','juliet':'J',
    'kilo':'K','lima':'L','mike':'M','november':'N','oscar':'O',
    'papa':'P','quebec':'Q','romeo':'R','sierra':'S','tango':'T',
    'uniform':'U','victor':'V','whiskey':'W','xray':'X','x-ray':'X',
    'yankee':'Y','zulu':'Z',
    'zero':'0','one':'1','two':'2','three':'3','four':'4',
    'five':'5','six':'6','seven':'7','eight':'8','nine':'9','niner':'9',
}


def _decode_phonetic(text):
    results = []
    words = re.findall(r'\b\w+\b', text.lower())
    run = []
    for w in words:
        if w in PHONETIC:
            run.append(PHONETIC[w])
        else:
            if len(run) >= 3:
                results.append(''.join(run))
            run = []
    if len(run) >= 3:
        results.append(''.join(run))
    return results


def guess_transmitter(text, aircraft, freq_hz):
    fc = freq_hz / 1e6
    if any(abs(fc - f) < 0.015 for f in ATIS_MHZ):
        return None, "ATIS/ground broadcast"
    if not aircraft or not text:
        return None, ""
    text_up = text.upper()
    direct   = set(re.findall(r'\b([A-Z]{2,3}[0-9]{1,5}[A-Z]{0,2})\b', text_up))
    oo_regs  = set(re.findall(r'\bOO[- ]?([A-Z]{3})\b', text_up))
    phonetic = set(_decode_phonetic(text))
    scored = []
    for ac in aircraft:
        flight = (ac.get('flight') or '').strip().upper()
        hex_id = ac.get('hex', '')
        dist   = ac.get('dist_km') or 999
        alt    = ac.get('alt_baro') or 0
        score  = 0
        reason = ''
        if flight:
            for cs in direct:
                if cs == flight or flight.startswith(cs[:4]) or cs.startswith(flight[:4]):
                    score = max(score, 92)
                    reason = f'callsign "{cs}" in transcript'
            for rm in oo_regs:
                if rm in flight:
                    score = max(score, 88)
                    reason = f'registration OO-{rm}'
            for ps in phonetic:
                if len(ps) >= 4 and (ps == flight or flight in ps or ps in flight):
                    score = max(score, 78)
                    reason = f'phonetic "{ps}"'
        if score == 0 and dist < 30 and alt < 10000:
            score = max(5, 22 - int(dist * 0.6))
            reason = f'nearest {dist:.0f}km, {alt}ft'
        if score > 0:
            scored.append((score, hex_id, reason))
    if not scored:
        return None, "no match"
    scored.sort(reverse=True)
    best = scored[0]
    if best[0] < 10:
        return None, "low confidence"
    return best[1], f"{best[2]} (score {best[0]})"


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def freq_label(hz):
    mhz = hz / 1e6
    label = KNOWN_FREQS.get(round(mhz, 3))
    if label:
        return f"{mhz:.3f} {label}"
    return f"{mhz:.3f} MHz"


def decode_cu8_to_wav(filepath, sample_rate):
    with open(filepath, 'rb') as f:
        raw = f.read()
    iq = array.array('B', raw)
    n = len(iq) // 2
    if n == 0:
        return None
    envelope = [math.sqrt((iq[2*i]-127.5)**2 + (iq[2*i+1]-127.5)**2) for i in range(n)]
    mean = sum(envelope) / n
    envelope = [v - mean for v in envelope]
    peak = max(abs(v) for v in envelope) or 1.0
    scale = 29000.0 / peak
    samples = struct.pack(f"<{n}h", *[max(-32768, min(32767, int(v*scale))) for v in envelope])
    buf = io.BytesIO()
    with wave.open(buf, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples)
    return buf.getvalue()


# ── SVG helpers ──────────────────────────────────────────────────────────────
def _km_to_px(km):
    return km * (MAP_SIZE / 2) / MAP_RADIUS_KM

def _latlon_to_xy(lat, lon):
    cx, cy = MAP_SIZE / 2, MAP_SIZE / 2
    dlat = lat - STATION_LAT
    dlon = lon - STATION_LON
    dy_km = -dlat * 111.0
    dx_km = dlon * 111.0 * math.cos(math.radians(STATION_LAT))
    px_per_km = (MAP_SIZE / 2) / MAP_RADIUS_KM
    return cx + dx_km * px_per_km, cy + dy_km * px_per_km

def _alt_color(alt):
    if alt is None: return "#6e7681"
    if alt < 3000:  return "#f85149"
    if alt < 10000: return "#d29922"
    if alt < 28000: return "#58a6ff"
    return "#6e7681"

def _aircraft_svg(x, y, track, color, size=8):
    t = track or 0
    pts = f"M 0,{-size} L {size*0.45},{size*0.4} L 0,{size*0.1} L {-size*0.45},{size*0.4} Z"
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({t:.0f})">'
            f'<path d="{pts}" fill="{color}" stroke="#0d1117" stroke-width="0.8"/></g>')


def generate_map_svg(tx_id, begin_date, end_date, label, freq_hz=0, text=None):
    cx, cy = MAP_SIZE / 2, MAP_SIZE / 2
    aircraft = []
    try:
        if os.path.exists(AIRCRAFT_DB):
            t0 = (dt.fromisoformat(begin_date.replace("Z","")) -
                  datetime.timedelta(seconds=90)).isoformat()
            t1 = (dt.fromisoformat(end_date.replace("Z","")) +
                  datetime.timedelta(seconds=90)).isoformat()
            conn = sqlite3.connect(AIRCRAFT_DB, timeout=5)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT hex, flight, lat, lon, alt_baro, gs, track, dist_km, MAX(ts) as last_seen
                FROM positions WHERE ts BETWEEN ? AND ? GROUP BY hex ORDER BY dist_km ASC
            """, (t0, t1)).fetchall()
            conn.close()
            aircraft = [dict(r) for r in rows]
    except Exception:
        pass

    best_hex, match_reason = guess_transmitter(text, aircraft, freq_hz)

    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{MAP_SIZE}" height="{MAP_SIZE}" '
             f'style="background:#0d1117;border-radius:8px;display:block">')

    for km, stroke in [(25,"#1a1f2e"),(50,"#1e2436"),(75,"#212840"),(100,"#242c45")]:
        r = _km_to_px(km)
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{stroke}" stroke-width="1"/>')
        p.append(f'<text x="{cx+r+3:.0f}" y="{cy-3:.0f}" fill="#2d3550" font-size="9" font-family="monospace">{km}km</text>')

    p.append(f'<line x1="{cx:.0f}" y1="0" x2="{cx:.0f}" y2="{MAP_SIZE}" stroke="#161b28" stroke-width="1"/>')
    p.append(f'<line x1="0" y1="{cy:.0f}" x2="{MAP_SIZE}" y2="{cy:.0f}" stroke="#161b28" stroke-width="1"/>')

    for txt, ax, ay, anchor in [("N",cx,13,"middle"),("S",cx,MAP_SIZE-4,"middle"),
                                 ("E",MAP_SIZE-4,cy+4,"end"),("W",5,cy+4,"start")]:
        p.append(f'<text x="{ax:.0f}" y="{ay:.0f}" text-anchor="{anchor}" fill="#3d4663" font-size="10" font-family="monospace">{txt}</text>')

    # Station marker
    p.append(f'<line x1="{cx-12:.0f}" y1="{cy:.0f}" x2="{cx+12:.0f}" y2="{cy:.0f}" stroke="#3fb950" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<line x1="{cx:.0f}" y1="{cy-12:.0f}" x2="{cx:.0f}" y2="{cy+12:.0f}" stroke="#3fb950" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="4" fill="#3fb950"/>')
    p.append(f'<text x="{cx+16:.0f}" y="{cy-8:.0f}" fill="#3fb950" font-size="10" font-family="monospace" font-weight="bold">{STATION_NAME}</text>')

    for ac in aircraft:
        x, y = _latlon_to_xy(ac["lat"], ac["lon"])
        if not (5 < x < MAP_SIZE-5 and 5 < y < MAP_SIZE-5):
            continue
        is_best = (ac["hex"] == best_hex)
        color = "#f0c030" if is_best else _alt_color(ac["alt_baro"])
        if is_best:
            p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="22" fill="none" stroke="#f0c030" stroke-width="1" opacity="0.2"/>')
            p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="none" stroke="#f0c030" stroke-width="1.5" opacity="0.45"/>')
        p.append(_aircraft_svg(x, y, ac.get("track"), color))
        flight = (ac["flight"] or ac["hex"] or "?").strip()
        alt = ac["alt_baro"]
        alt_str = f" FL{alt//100:03d}" if alt and alt >= 10000 else (f" {alt}ft" if alt else "")
        lbl = flight + alt_str
        lx = x + 12
        if lx + len(lbl)*5.5 > MAP_SIZE-4: lx = x - 12 - len(lbl)*5.5
        ly = y - 7
        if ly < 14: ly = y + 16
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{color}" font-size="9.5" font-family="monospace"'
                 + (' font-weight="bold"' if is_best else '') + f'>{lbl}</text>')
        if is_best:
            p.append(f'<text x="{lx:.0f}" y="{ly+10:.0f}" fill="#f0c030" font-size="8" font-family="monospace">&#9654; likely tx</text>')

    if not aircraft:
        p.append(f'<text x="{cx:.0f}" y="{cy+40:.0f}" text-anchor="middle" fill="#30363d" font-size="12" font-family="monospace">no aircraft data</text>')

    legend_y = MAP_SIZE - 6
    for i, (col, lbl) in enumerate([("#f85149","<3000ft"),("#d29922","<10000ft"),
                                     ("#58a6ff","<FL280"),("#6e7681","high"),("#f0c030","likely tx")]):
        lx = 4 + i * 76
        p.append(f'<circle cx="{lx+4}" cy="{legend_y-3}" r="4" fill="{col}"/>')
        p.append(f'<text x="{lx+11}" y="{legend_y}" fill="{col}" font-size="8" font-family="monospace">{lbl}</text>')

    try:
        time_str = dt.fromisoformat(begin_date.replace("Z","")).strftime("%H:%M:%S UTC")
    except Exception:
        time_str = begin_date[:8]
    p.append(f'<text x="5" y="12" fill="#58a6ff" font-size="9" font-family="monospace">{label}</text>')
    p.append(f'<text x="{MAP_SIZE-5}" y="12" text-anchor="end" fill="#8b949e" font-size="9" font-family="monospace">{time_str}</text>')
    if match_reason:
        rc = "#f0c030" if best_hex else "#6e7681"
        p.append(f'<text x="5" y="{MAP_SIZE-18}" fill="{rc}" font-size="8" font-family="monospace">{match_reason[:60]}</text>')
    p.append(f'<text x="{MAP_SIZE-5}" y="{MAP_SIZE-18}" text-anchor="end" fill="#2d3550" font-size="8" font-family="monospace">{len(aircraft)} ac</text>')
    p.append('</svg>')
    return "".join(p)


PER_PAGE = 50

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        if path.startswith('/audio/'):
            try:
                tx_id = int(path.split('/')[2])
                return self.serve_audio(tx_id)
            except Exception:
                return self.send_error(400)

        if path.startswith('/map/'):
            try:
                tx_id = int(path.split('/')[2])
                return self.serve_map(tx_id)
            except Exception:
                return self.send_error(400)

        if path == '/' or path == '':
            return self.serve_index(parsed)

        self.send_error(404)

    def serve_audio(self, tx_id):
        conn = get_db()
        row = conn.execute(
            "SELECT begin_frequency, end_frequency, data_file FROM sdr_transmission WHERE id=?",
            (tx_id,)).fetchone()
        conn.close()
        if not row or not row["data_file"]:
            return self.send_error(404)
        filepath = os.path.join(DATA_ROOT, row["data_file"])
        if not os.path.exists(filepath):
            return self.send_error(404)
        sr = row["end_frequency"] - row["begin_frequency"]
        wav = decode_cu8_to_wav(filepath, sr)
        if not wav:
            return self.send_error(500)
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", len(wav))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(wav)

    def serve_map(self, tx_id):
        conn = get_db()
        row = conn.execute(
            "SELECT t.begin_frequency, t.end_frequency, t.begin_date, t.end_date, tr.text "
            "FROM sdr_transmission t LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id "
            "WHERE t.id=?", (tx_id,)).fetchone()
        conn.close()
        if not row:
            return self.send_error(404)
        fc = (row["begin_frequency"] + row["end_frequency"]) / 2
        label = freq_label(fc)
        svg = generate_map_svg(tx_id, row["begin_date"], row["end_date"],
                               label, freq_hz=fc, text=row["text"])
        data = svg.encode()
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def serve_index(self, parsed):
        qs = parse_qs(parsed.query)
        page    = max(1, int(qs.get('page', ['1'])[0]))
        search  = qs.get('q', [''])[0]
        freq_f  = qs.get('freq', [''])[0]
        speech  = qs.get('speech', [''])[0]
        hide_p  = qs.get('hidepending', [''])[0]

        wheres, params = [], []
        if search:
            wheres.append("tr.text LIKE ?")
            params.append(f"%{search}%")
        if freq_f:
            try:
                fhz = float(freq_f) * 1e6
                wheres.append("abs((t.begin_frequency+t.end_frequency)/2.0 - ?) < 20000")
                params.append(fhz)
            except ValueError:
                pass
        if speech == '1':
            wheres.append("tr.text IS NOT NULL AND tr.text != ''")
        if hide_p == '1':
            wheres.append("tr.id IS NOT NULL")

        where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""

        conn = get_db()
        total = conn.execute(
            f"SELECT COUNT(*) FROM sdr_transmission t "
            f"LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id "
            f"{where_sql}", params).fetchone()[0]
        offset = (page - 1) * PER_PAGE

        rows = conn.execute(f"""
            SELECT t.id, t.begin_frequency, t.end_frequency,
                   t.begin_date, t.end_date, t.data_file,
                   tr.id as tr_id, tr.text, tr.confidence, tr.error, tr.model
            FROM sdr_transmission t
            LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id
            {where_sql}
            ORDER BY t.id DESC LIMIT ? OFFSET ?
        """, params + [PER_PAGE, offset]).fetchall()

        freqs_rows = conn.execute("""
            SELECT DISTINCT round((begin_frequency+end_frequency)/2.0/1e6, 3) as mhz
            FROM sdr_transmission ORDER BY mhz
        """).fetchall()
        conn.close()

        # Stats
        stats_html = ""
        if HAS_PSUTIL:
            disk = psutil.disk_usage('/opt')
            mem = psutil.virtual_memory()
            stats_html = (
                f'<span style="color:#8b949e;font-size:0.85rem">'
                f'Disk: {disk.free/1e9:.1f}GB free | '
                f'RAM: {mem.percent:.0f}% | '
                f'Total: {total}</span>'
            )

        # Build page rows
        table_rows = []
        for r in rows:
            fc = (r["begin_frequency"] + r["end_frequency"]) / 2
            fl = freq_label(fc)
            try:
                ts = dt.fromisoformat(r["begin_date"].replace("Z","")).strftime("%H:%M:%S")
                ds = dt.fromisoformat(r["begin_date"].replace("Z","")).strftime("%Y-%m-%d")
            except Exception:
                ts = r["begin_date"][:8]
                ds = ""

            tx_id_val = r["id"]
            text = r["text"] or ""
            model = r.get("model") or ""

            if r["tr_id"] is None:
                badge = '<span style="background:#30363d;color:#8b949e;padding:2px 6px;border-radius:4px;font-size:0.75rem">PENDING</span>'
            elif r["error"]:
                badge = f'<span style="background:#da3633;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.75rem">ERR</span>'
            elif 'whisper' in model:
                badge = f'<span style="background:#8957e5;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.75rem">WHISPER</span>'
            elif 'nova' in model:
                badge = f'<span style="background:#1f6feb;color:#fff;padding:2px 6px;border-radius:4px;font-size:0.75rem">DEEPGRAM</span>'
            else:
                badge = ''

            has_file = r["data_file"] and os.path.exists(os.path.join(DATA_ROOT, r["data_file"])) if r["data_file"] else False
            audio_html = ''
            if has_file:
                audio_html = (
                    f'<button class="play-btn" onclick="loadAudio(this,{tx_id_val})">&#9654;</button>'
                    f'<span id="ap{tx_id_val}"></span>'
                )

            map_btn = f'<button class="map-btn" onclick="showMap({tx_id_val})">&#128752;</button>'

            table_rows.append(
                f'<tr>'
                f'<td style="white-space:nowrap">{fl}</td>'
                f'<td style="white-space:nowrap;color:#8b949e">{ds}<br>{ts}</td>'
                f'<td>{text}</td>'
                f'<td>{badge}</td>'
                f'<td style="white-space:nowrap">{audio_html} {map_btn}</td>'
                f'</tr>'
            )

        total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        base_qs = f"q={search}&freq={freq_f}&speech={speech}&hidepending={hide_p}"

        freq_options = ''.join(
            f'<option value="{r["mhz"]}" {"selected" if str(r["mhz"])==freq_f else ""}>{r["mhz"]:.3f}</option>'
            for r in freqs_rows
        )

        pagination = []
        if page > 1:
            pagination.append(f'<a href="/?{base_qs}&page={page-1}">&laquo; Prev</a>')
        pagination.append(f'<span>Page {page}/{total_pages}</span>')
        if page < total_pages:
            pagination.append(f'<a href="/?{base_qs}&page={page+1}">Next &raquo;</a>')
        pag_html = ' '.join(pagination)

        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Airband Scanner - {STATION_NAME}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:16px}}
h1{{color:#58a6ff;margin-bottom:4px;font-size:1.4rem}}
.stats{{margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;margin-top:8px}}
th{{background:#161b22;color:#8b949e;padding:8px;text-align:left;font-size:0.85rem;position:sticky;top:0}}
td{{padding:8px;border-bottom:1px solid #21262d;font-size:0.9rem;vertical-align:top}}
tr:hover{{background:#161b22}}
.filters{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0;align-items:center}}
.filters input,.filters select{{background:#0d1117;border:1px solid #30363d;color:#e6edf3;padding:6px 10px;border-radius:6px;font-size:0.85rem}}
.filters button{{background:#238636;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer}}
.filters label{{color:#8b949e;font-size:0.85rem;display:flex;align-items:center;gap:4px}}
a{{color:#58a6ff;text-decoration:none}}
.pag{{display:flex;gap:12px;align-items:center;justify-content:center;margin:16px 0;font-size:0.9rem}}
.play-btn,.map-btn{{background:none;border:1px solid #30363d;color:#58a6ff;padding:4px 8px;border-radius:4px;cursor:pointer;font-size:0.9rem}}
.play-btn:hover,.map-btn:hover{{background:#161b22}}
#mapModal{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:100;align-items:center;justify-content:center}}
#mapBox{{background:#161b22;padding:16px;border-radius:12px;border:1px solid #30363d}}
</style>
</head><body>
<h1>Airband Scanner &mdash; {STATION_NAME}</h1>
<div class="stats">{stats_html}</div>
<form class="filters" method="get">
  <input type="text" name="q" placeholder="Search transcripts..." value="{search}">
  <select name="freq"><option value="">All frequencies</option>{freq_options}</select>
  <label><input type="checkbox" name="speech" value="1" {"checked" if speech=="1" else ""}> Speech only</label>
  <label><input type="checkbox" name="hidepending" value="1" {"checked" if hide_p=="1" else ""}> Hide pending</label>
  <button type="submit">Filter</button>
</form>
<table>
<tr><th>Frequency</th><th>Time</th><th>Transcript</th><th>Engine</th><th>Audio / Map</th></tr>
{''.join(table_rows)}
</table>
<div class="pag">{pag_html}</div>

<div id="mapModal" onclick="this.style.display='none'">
  <div id="mapBox" onclick="event.stopPropagation()">
    <div style="display:flex;justify-content:space-between;margin-bottom:8px">
      <span id="mapTitle" style="color:#e6edf3;font-weight:600"></span>
      <button onclick="document.getElementById('mapModal').style.display='none'" style="background:none;border:none;color:#8b949e;cursor:pointer;font-size:1.2rem">&times;</button>
    </div>
    <div id="mapSvg"></div>
  </div>
</div>

<script>
function loadAudio(btn, txId) {{
  btn.disabled = true; btn.textContent = '...';
  var span = document.getElementById('ap' + txId);
  var audio = document.createElement('audio');
  audio.controls = true; audio.style.height = '28px';
  audio.src = '/audio/' + txId;
  span.appendChild(audio);
  audio.play().catch(function(){{}});
}}
function showMap(txId) {{
  document.getElementById('mapSvg').innerHTML = 'Loading...';
  document.getElementById('mapModal').style.display = 'flex';
  fetch('/map/' + txId)
    .then(function(r) {{ return r.text(); }})
    .then(function(svg) {{ document.getElementById('mapSvg').innerHTML = svg; }})
    .catch(function() {{ document.getElementById('mapSvg').textContent = 'No data'; }});
}}
</script>
</body></html>"""

        data = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)


def main():
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    print(f"Transcript viewer on http://0.0.0.0:{PORT}")
    server.serve_forever()

if __name__ == '__main__':
    main()
PYEOF

# ── Write disk_rotation.py ──────────────────────────────────────────────────
info "Writing disk rotation script..."
cat > "$INSTALL_DIR/disk_rotation.py" << PYEOF
#!/usr/bin/env python3
"""Delete transcribed .bin audio files older than N days. Run daily via cron."""
import sqlite3, os, datetime, logging

DB_PATH   = os.environ.get('DB_PATH', '/opt/sdr-hub/data/db.sqlite3')
DATA_ROOT = os.environ.get('DATA_ROOT', '/opt/sdr-hub/data/public/media')
MAX_DAYS  = int(os.environ.get('RETENTION_DAYS', '7'))
LOG_FILE  = '/opt/airband/rotation.log'

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE)])
log = logging.getLogger('rotation')

conn = sqlite3.connect(DB_PATH, timeout=30)
conn.execute("PRAGMA journal_mode=WAL")
cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=MAX_DAYS)).isoformat()

rows = conn.execute("""
    SELECT t.id, t.data_file FROM sdr_transmission t
    JOIN sdr_transcript tr ON tr.transmission_id = t.id
    WHERE t.data_file IS NOT NULL AND t.begin_date < ?
""", (cutoff,)).fetchall()

deleted = freed = 0
for tx_id, data_file in rows:
    path = os.path.join(DATA_ROOT, data_file)
    if os.path.exists(path):
        freed += os.path.getsize(path)
        os.remove(path)
        deleted += 1

log.info("Rotation: deleted %d files, freed %.1f MB", deleted, freed/1024/1024)
conn.close()
PYEOF

# ── Systemd services ────────────────────────────────────────────────────────
info "Creating systemd services..."

cat > /etc/systemd/system/airband-transcriber.service << SVCEOF
[Unit]
Description=Airband Transcription Worker
After=network.target docker.service

[Service]
Type=simple
EnvironmentFile=$CONFIG_FILE
Environment=DB_PATH=/opt/sdr-hub/data/db.sqlite3
Environment=DATA_ROOT=/opt/sdr-hub/data/public/media
Environment=LOG_FILE=$INSTALL_DIR/transcriber.log
Environment=WHISPER_CLI=/opt/whisper.cpp/build/bin/whisper-cli
ExecStart=/usr/bin/python3 $INSTALL_DIR/transcriber.py
WorkingDirectory=$INSTALL_DIR
Restart=on-failure
RestartSec=30
StandardOutput=append:$INSTALL_DIR/transcriber.log
StandardError=append:$INSTALL_DIR/transcriber.log

[Install]
WantedBy=multi-user.target
SVCEOF

cat > /etc/systemd/system/airband-viewer.service << SVCEOF
[Unit]
Description=Airband Transcript Viewer Web UI
After=network.target

[Service]
Type=simple
EnvironmentFile=$CONFIG_FILE
Environment=DB_PATH=/opt/sdr-hub/data/db.sqlite3
Environment=DATA_ROOT=/opt/sdr-hub/data/public/media
Environment=AIRCRAFT_DB=$INSTALL_DIR/aircraft.db
Environment=VIEWER_PORT=$VIEWER_PORT
ExecStartPre=/bin/bash -c 'iptables -C INPUT -i tailscale0 -p tcp --dport $VIEWER_PORT -j ACCEPT 2>/dev/null || iptables -I INPUT 1 -i tailscale0 -p tcp --dport $VIEWER_PORT -j ACCEPT 2>/dev/null || true'
ExecStart=/usr/bin/python3 $INSTALL_DIR/transcript_viewer.py
WorkingDirectory=$INSTALL_DIR
Restart=on-failure
RestartSec=10
StandardOutput=append:$INSTALL_DIR/viewer.log
StandardError=append:$INSTALL_DIR/viewer.log

[Install]
WantedBy=multi-user.target
SVCEOF

cat > /etc/systemd/system/airband-tracker.service << SVCEOF
[Unit]
Description=Aircraft Position Tracker (tar1090 poller)
After=network.target docker.service

[Service]
Type=simple
EnvironmentFile=$CONFIG_FILE
Environment=AIRCRAFT_DB=$INSTALL_DIR/aircraft.db
ExecStart=/usr/bin/python3 $INSTALL_DIR/aircraft_tracker.py
WorkingDirectory=$INSTALL_DIR
Restart=on-failure
RestartSec=15
StandardOutput=append:$INSTALL_DIR/aircraft_tracker.log
StandardError=append:$INSTALL_DIR/aircraft_tracker.log

[Install]
WantedBy=multi-user.target
SVCEOF

# ── Build whisper.cpp ────────────────────────────────────────────────────────
info "Building whisper.cpp (this takes ~15 min on Pi4)..."
if [[ -f "$WHISPER_DIR/build/bin/whisper-cli" ]]; then
    info "whisper.cpp already built — skipping"
else
    if [[ ! -d "$WHISPER_DIR/.git" ]]; then
        git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git "$WHISPER_DIR"
    fi
    mkdir -p "$WHISPER_DIR/build"
    cd "$WHISPER_DIR/build"
    cmake .. -DCMAKE_BUILD_TYPE=Release -DGGML_OPENMP=OFF > /dev/null 2>&1
    info "  cmake configured, building with $(nproc) threads..."
    cmake --build . -j"$(nproc)" > "$WHISPER_DIR/build.log" 2>&1 &
    BUILD_PID=$!
    cd "$INSTALL_DIR"
fi

# ── Download whisper model ───────────────────────────────────────────────────
MODEL_FILE="ggml-${WHISPER_MODEL}.bin"
MODEL_PATH="$WHISPER_DIR/models/$MODEL_FILE"
if [[ -f "$MODEL_PATH" ]]; then
    info "Whisper model $MODEL_FILE already downloaded"
else
    info "Downloading whisper model: $MODEL_FILE..."
    wget -q --show-progress -O "$MODEL_PATH" \
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$MODEL_FILE" &
    DL_PID=$!
fi

# ── Set up cron ──────────────────────────────────────────────────────────────
info "Setting up disk rotation cron..."
CRON_LINE="0 3 * * * /usr/bin/python3 $INSTALL_DIR/disk_rotation.py"
(crontab -l 2>/dev/null | grep -v "disk_rotation.py"; echo "$CRON_LINE") | crontab -

# ── Wait for build if running ────────────────────────────────────────────────
if [[ -n "${BUILD_PID:-}" ]]; then
    info "Waiting for whisper.cpp build to finish (PID $BUILD_PID)..."
    wait "$BUILD_PID" 2>/dev/null || true
    if [[ -f "$WHISPER_DIR/build/bin/whisper-cli" ]]; then
        info "whisper.cpp built successfully"
    else
        err "whisper.cpp build failed — check $WHISPER_DIR/build.log"
        warn "Transcription will only work with Deepgram until whisper is built"
    fi
fi

# Wait for model download
if [[ -n "${DL_PID:-}" ]]; then
    info "Waiting for model download..."
    wait "$DL_PID" 2>/dev/null || true
    if [[ -f "$MODEL_PATH" ]]; then
        info "Model downloaded: $MODEL_PATH"
    else
        err "Model download failed"
    fi
fi

# ── Enable and start services ────────────────────────────────────────────────
info "Starting services..."
systemctl daemon-reload
systemctl enable --now airband-transcriber airband-viewer airband-tracker

sleep 3

echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Installation complete!${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo ""

IP=$(hostname -I | awk '{print $1}')

echo -e "  ${CYAN}Transcript Viewer:${NC}  http://${IP}:${VIEWER_PORT}"
echo -e "  ${CYAN}SDR-Hub Scanner:${NC}    http://${IP}:${SDR_HUB_PORT}"
echo ""
echo -e "  ${YELLOW}NEXT STEPS:${NC}"
echo -e "  1. Open sdr-hub at http://${IP}:${SDR_HUB_PORT}"
echo -e "     Configure your RTL-SDR device and add airband frequencies"
echo -e "     (typically 118-137 MHz AM for aviation)"
echo -e "  2. Once sdr-hub is recording, transcripts appear automatically"
echo -e "     at http://${IP}:${VIEWER_PORT}"
echo ""
echo -e "  ${BOLD}Service management:${NC}"
echo -e "    systemctl status airband-transcriber airband-viewer airband-tracker"
echo -e "    journalctl -u airband-transcriber -f"
echo ""
echo -e "  ${BOLD}Logs:${NC}"
echo -e "    tail -f $INSTALL_DIR/transcriber.log"
echo -e "    tail -f $INSTALL_DIR/viewer.log"
echo ""
echo -e "  ${BOLD}Config:${NC}  $CONFIG_FILE"
echo -e "  ${BOLD}Data:${NC}    $SDR_HUB_DIR/data/"
echo ""
echo -e "  ${BOLD}Uninstall:${NC}"
echo -e "    sudo bash $(realpath "$0") --uninstall"
echo ""

# ── Uninstall mode ───────────────────────────────────────────────────────────
if [[ "${1:-}" == "--uninstall" ]]; then
    warn "Uninstalling airband-scanner..."
    systemctl stop airband-transcriber airband-viewer airband-tracker 2>/dev/null || true
    systemctl disable airband-transcriber airband-viewer airband-tracker 2>/dev/null || true
    rm -f /etc/systemd/system/airband-{transcriber,viewer,tracker}.service
    systemctl daemon-reload
    docker stop sdr-hub 2>/dev/null || true
    docker rm sdr-hub 2>/dev/null || true
    ask "Delete all data in $SDR_HUB_DIR and $INSTALL_DIR? [y/N]:"
    read -r del_data
    if [[ "${del_data,,}" == "y" ]]; then
        rm -rf "$SDR_HUB_DIR" "$INSTALL_DIR" "$WHISPER_DIR"
        info "All data deleted"
    fi
    info "Uninstalled"
    exit 0
fi
