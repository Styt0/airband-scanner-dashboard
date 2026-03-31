#!/usr/bin/env python3
"""Airband Transcript Viewer v3.0 — EBAW/EBBR — live SSE + ATC dashboard"""
import array, datetime, html as _he, io, json, math, os, re, shutil, sqlite3, struct
import socketserver, time, wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

try:
    import urllib.request as _ureq
except ImportError:
    _ureq = None

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from datetime import datetime as dt


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


# ── Config ───────────────────────────────────────────────────────────────────
DB_PATH      = "/opt/sdr-hub/data/db.sqlite3"
DATA_ROOT    = "/opt/sdr-hub/data/public/media"
AIRCRAFT_DB  = "/opt/deepgram-worker/aircraft.db"
ADSB_URL     = "http://127.0.0.1:8080/data/aircraft.json"
TAR1090_STATS= "http://127.0.0.1:8080/data/stats.json"
STAGE2_URL   = "http://127.0.0.1/api/stage2_stats"
ADSB_BASE    = "http://192.168.1.188:8080"
PORT         = 8002

GRAPHS_CHARTS = [
    ("local_trailing_rate", "dump1090", "Message Rate"),
    ("aircraft",            "dump1090", "Aircraft Seen"),
    ("tracks",              "dump1090", "Tracks Seen"),
    ("range",               "dump1090", "Max Range"),
    ("signal",              "dump1090", "Signal Level"),
    ("cpu",                 "dump1090", "Decoder CPU"),
    ("cpu",                 "system",   "System CPU"),
    ("temperature",         "system",   "Temperature"),
    ("memory",              "system",   "Memory"),
    ("network_bandwidth",   "system",   "Network"),
    ("df_root",             "system",   "Disk Space"),
]

EBAW_LAT, EBAW_LON = 51.189, 4.460
EBBR_LAT, EBBR_LON = 50.9010, 4.4844
MAP_SIZE      = 440
MAP_RADIUS_KM = 100

KNOWN_FREQS = {
    # ── NOOD / EMERGENCY ──────────────────────────────────────────────────────
    121.500: "EMERGENCY",       243.000: "EMERG UHF",
    123.450: "Air-to-Air",

    # ── EBBR Brussels ─────────────────────────────────────────────────────────
    118.250: "EBBR APP N",      118.475: "EBBR APP",
    118.600: "EBBR APP Z",      119.300: "EBBR TWR",
    120.775: "EBBR TWR N",      121.150: "EBBR GND",
    125.675: "EBBR ATIS",       126.625: "EBBR DEP",

    # ── EBAW Antwerpen ────────────────────────────────────────────────────────
    119.900: "EBAW TWR",        119.975: "EBAW Info",
    120.575: "EBAW ATIS",       126.650: "EBAW APP",
    135.200: "EBAW TWR Bkp",

    # ── EBOS Oostende ─────────────────────────────────────────────────────────
    119.700: "EBOS TWR",        121.750: "EBOS APP",
    125.100: "EBOS ATIS",

    # ── EBLG Luik ─────────────────────────────────────────────────────────────
    120.200: "EBLG TWR",        119.500: "EBLG APP",
    124.870: "EBLG ATIS",

    # ── EBCI Charleroi ────────────────────────────────────────────────────────
    119.400: "EBCI TWR",        118.700: "EBCI APP",
    133.125: "EBCI APP",        126.230: "EBCI ATIS",

    # ── Brussels ACC (EBBU) ───────────────────────────────────────────────────
    126.900: "BXL Info",        127.225: "BXL West Hi",
    127.625: "BXL ACC",         128.158: "BXL Sect 13",
    128.160: "BXL Sect 13",     128.200: "BXL Huldbg",
    128.275: "BXL ACC",         128.450: "BXL East Hi",
    128.800: "BXL APP",         130.950: "BXL Radar S",
    131.100: "BXL Upper",       131.400: "BXL ACC",
    131.425: "BXL ACC",         131.450: "BXL ACC",
    127.368: "BXL ACC",         128.793: "BXL ACC",
    132.950: "BXL Control",

    # ── Maastricht MUAC ───────────────────────────────────────────────────────
    124.433: "MUAC Ruhr Lo",    125.925: "MUAC",
    125.975: "MUAC Olno Hi",    132.083: "MUAC Delta Hi",
    132.085: "MUAC Delta Hi",   132.200: "MUAC Koksy Lo",
    132.750: "MUAC Kok/Nick",   132.850: "MUAC Olno Lo",
    133.350: "MUAC Lux Lo",     135.425: "MUAC",
    135.958: "MUAC Delta Lo",   135.975: "MUAC Nicky",

    # ── ACARS datalink (geen spraak) ──────────────────────────────────────────
    131.725: "ACARS",           131.825: "ACARS",

    # ── Amsterdam ACC ─────────────────────────────────────────────────────────
    123.850: "EHAA South",

    # ── Militaire luchtvaart ──────────────────────────────────────────────────
    122.100: "EBBL Info",       120.525: "EBFS TWR",
    123.300: "EBKH Info",       339.000: "EHWO TWR UHF",

    # ── MARINE VHF ────────────────────────────────────────────────────────────
    156.800: "Marine Nood",     156.000: "Marine Haven",
    156.375: "Kustwacht",       156.600: "Haven Antwerpen",
    156.650: "Bridge-to-Bridge",157.050: "Scheepvaartpolitie",
    161.975: "AIS 1",           162.025: "AIS 2",

    # ── PMR446 ────────────────────────────────────────────────────────────────
    446.00625: "PMR446 Ch1",    446.01875: "PMR446 Ch2",
    446.03125: "PMR446 Ch3",    446.04375: "PMR446 Ch4",
    446.05625: "PMR446 Ch5",    446.06875: "PMR446 Ch6",
    446.08125: "PMR446 Ch7",    446.09375: "PMR446 Ch8",

    # ── AMATEUR RADIO ─────────────────────────────────────────────────────────
    144.800: "APRS",            145.500: "Ham 2m",
    145.600: "Ham 2m",          145.650: "ON0BR Rptr",
    145.725: "ON0LG Rptr",      145.750: "ON0OS Rptr",
    145.7875: "ON0ANT Rptr",    433.500: "Ham 70cm",
    430.825: "ON0ANT 70cm",
}

ATIS_FREQS     = {125.675, 120.575, 125.100, 124.870, 126.230}
ATIS_MHZ       = {125.675, 120.575, 125.100, 124.870, 126.230}
EBAW_LOCAL_MHZ = {119.900, 119.975, 120.575, 126.650, 135.200}
EBBR_LOCAL_MHZ = {118.250, 118.475, 118.600, 119.300, 120.775, 121.150, 125.675, 126.625}

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

CHART_COLORS = ["#3b82f6","#f97316","#f59e0b","#a855f7","#22c55e","#ec4899","#22d3ee","#ef4444"]


# ── Frequency helpers ─────────────────────────────────────────────────────────
def freq_label(hz):
    mhz = hz / 1e6
    # Closest-match within 10 kHz — handles 8.33 kHz airband, 12.5 kHz PMR, 25 kHz marine
    best_f, best_d = None, 0.010
    for f in KNOWN_FREQS:
        d = abs(mhz - f)
        if d < best_d:
            best_f, best_d = f, d
    return KNOWN_FREQS[best_f] if best_f is not None else f"{mhz:.3f} MHz"

def freq_type_info(label):
    u = label.upper()
    # Emergency / distress
    if 'EMERG' in u or 'NOOD' in u:         return '#ef4444', '#ef444420', 'EMER',   'emer'
    # Tower
    if 'TWR' in u:                           return '#3b82f6', '#3b82f620', 'TWR',    'twr'
    # Approach / Arrival
    if 'APP' in u or 'APPROACH' in u:        return '#f97316', '#f9731620', 'APP',    'app'
    if 'ARR' in u or 'ARRIVAL' in u:         return '#f59e0b', '#f59e0b20', 'ARR',    'arr'
    # Departure / Delivery
    if 'DEP' in u or 'DEPART' in u:          return '#a855f7', '#a855f720', 'DEP',    'dep'
    if 'DEL' in u or 'DELIVERY' in u:        return '#ec4899', '#ec489920', 'DEL',    'del'
    # Ground
    if 'GND' in u or 'GROUND' in u:          return '#71717a', '#71717a20', 'GND',    'gnd'
    # ATIS
    if 'ATIS' in u:                          return '#22c55e', '#22c55e20', 'ATIS',   'atis'
    # ACC / Area Control / MUAC
    if any(k in u for k in ('ACC','BELUX','BRUSSELS','BXL','MUAC','RADAR','EHAA')):
                                             return '#f5c518', '#f5c51820', 'ACC',    'acc'
    # ACARS datalink
    if 'ACARS' in u:                         return '#22d3ee', '#22d3ee20', 'DATA',   'info'
    # Air-to-Air
    if 'AIR-TO-AIR' in u or 'A2A' in u:     return '#e879f9', '#e879f920', 'A2A',    'a2a'
    # Marine
    if 'MARINE' in u or 'KUSTWACHT' in u or 'BRIDGE' in u or 'HAVEN' in u or 'POLITIE' in u:
                                             return '#0ea5e9', '#0ea5e920', 'MARINE', 'marine'
    if 'AIS' in u:                           return '#22d3ee', '#22d3ee20', 'AIS',    'marine'
    # PMR446
    if 'PMR446' in u or 'PMR' in u:         return '#84cc16', '#84cc1620', 'PMR',    'pmr'
    # Amateur radio
    if 'HAM' in u or 'ON0' in u or 'RPTR' in u or '70CM' in u or 'SIMPLEX' in u:
                                             return '#fb923c', '#fb923c20', 'HAM',    'ham'
    # Military info
    if 'INFO' in u or 'EBBL' in u or 'EBFS' in u or 'EBKH' in u:
                                             return '#22d3ee', '#22d3ee20', 'INFO',   'info'
    return '#52525b', '#52525b20', '—', ''

def dur_bar_html(begin, end, n=10, max_s=10.0):
    """Signal duration bar — filled segments proportional to TX length."""
    try:
        a = dt.fromisoformat(begin.replace("Z", ""))
        b = dt.fromisoformat(end.replace("Z", ""))
        secs = (b - a).total_seconds()
    except:
        return ''
    filled = max(1, min(n, round(secs / max_s * n)))
    col = '#22c55e' if secs >= 4 else ('#f5c518' if secs >= 2 else '#ef4444')
    segs = ''.join(
        f'<div class="cs" style="background:{col}"></div>' if i < filled
        else '<div class="cs"></div>'
        for i in range(n)
    )
    return f'<div class="cbar" title="{secs:.1f}s">{segs}</div>'


# ── Time helpers ──────────────────────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo as _ZI
    _LOCAL_TZ = _ZI('Europe/Brussels')
except Exception:
    _LOCAL_TZ = None

def fmt_time(s):
    try:
        utc = dt.fromisoformat(s.replace("Z","")).replace(tzinfo=datetime.timezone.utc)
        if _LOCAL_TZ:
            loc = utc.astimezone(_LOCAL_TZ)
        else:
            yr = utc.year
            def _last_sun(mo):
                d = datetime.datetime(yr, mo, 31, 1, tzinfo=datetime.timezone.utc)
                return d - datetime.timedelta(days=(d.weekday()+1)%7)
            off = 2 if _last_sun(3) <= utc < _last_sun(10) else 1
            loc = utc + datetime.timedelta(hours=off)
        return loc.strftime("%H:%M:%S")
    except:
        return s[11:19] if s else ""

def fmt_date(s):
    try:
        utc = dt.fromisoformat(s.replace("Z","")).replace(tzinfo=datetime.timezone.utc)
        if _LOCAL_TZ:
            loc = utc.astimezone(_LOCAL_TZ)
        else:
            loc = utc + datetime.timedelta(hours=1)
        return loc.strftime("%d/%m")
    except:
        return ""

def fmt_dur(begin, end):
    try:
        a = dt.fromisoformat(begin.replace("Z", ""))
        b = dt.fromisoformat(end.replace("Z", ""))
        return f"{(b - a).total_seconds():.1f}s"
    except:
        return ""


# ── DB helpers ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def decode_cu8_to_wav(filepath, sample_rate):
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        iq = array.array("B", raw)
        n = len(iq) // 2
        if n == 0: return None
        envelope = [math.sqrt((iq[2*i]-127.5)**2+(iq[2*i+1]-127.5)**2) for i in range(n)]
        mean  = sum(envelope) / n
        envelope = [v - mean for v in envelope]
        peak  = max(abs(v) for v in envelope) or 1.0
        scale = 29000.0 / peak
        samples = struct.pack(f"<{n}h", *[max(-32768,min(32767,int(v*scale))) for v in envelope])
        buf = io.BytesIO()
        with wave.open(buf, "w") as wf:
            wf.setnchannels(1); wf.setsampwidth(2)
            wf.setframerate(sample_rate); wf.writeframes(samples)
        return buf.getvalue()
    except:
        return None


# ── Stats collectors ──────────────────────────────────────────────────────────
def get_uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            secs = float(f.read().split()[0])
    except:
        if HAS_PSUTIL:
            try:   secs = time.time() - psutil.boot_time()
            except: return "—"
        else:
            return "—"
    days  = int(secs // 86400)
    hours = int((secs % 86400) // 3600)
    mins  = int((secs % 3600) // 60)
    if days > 0:  return f"{days}d {hours}h"
    if hours > 0: return f"{hours}h {mins}m"
    return f"{mins}m"

def get_live_adsb():
    if not _ureq: return {'total': 0, 'with_pos': 0, 'online': False}
    try:
        with _ureq.urlopen(ADSB_URL, timeout=3) as r:
            data = json.loads(r.read())
        ac       = data.get('aircraft', [])
        with_pos = sum(1 for a in ac if a.get('lat') and a.get('lon'))
        return {'total': len(ac), 'with_pos': with_pos, 'online': True}
    except:
        return {'total': 0, 'with_pos': 0, 'online': False}

def get_freq_stats():
    try:
        conn = get_db()
        cutoff = (dt.utcnow() - datetime.timedelta(hours=24)).isoformat()
        top_tx = conn.execute("""
            SELECT ROUND((t.begin_frequency+t.end_frequency)/2.0/10000.0)*10000 AS fc,
                   COUNT(*) AS cnt
            FROM sdr_transmission t
            LEFT JOIN sdr_group g ON g.id=t.group_id
            WHERE g.modulation='AM' AND t.data_file IS NOT NULL
              AND t.begin_date > ?
            GROUP BY fc ORDER BY cnt DESC LIMIT 12
        """, (cutoff,)).fetchall()
        top_dec = conn.execute("""
            SELECT ROUND((t.begin_frequency+t.end_frequency)/2.0/10000.0)*10000 AS fc,
                   COUNT(*) AS cnt
            FROM sdr_transmission t
            LEFT JOIN sdr_group g ON g.id=t.group_id
            LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id
            WHERE g.modulation='AM' AND tr.text IS NOT NULL AND tr.text!=''
              AND t.begin_date > ?
            GROUP BY fc ORDER BY cnt DESC LIMIT 12
        """, (cutoff,)).fetchall()
        conn.close()
        return {
            'top_tx':  [{'fc': r[0], 'count': r[1], 'label': freq_label(r[0])} for r in top_tx],
            'top_dec': [{'fc': r[0], 'count': r[1], 'label': freq_label(r[0])} for r in top_dec],
        }
    except:
        return {'top_tx': [], 'top_dec': []}

def get_sys_stats():
    s = {}
    try:
        d = shutil.disk_usage(DATA_ROOT)
        s['disk_free_gb']  = round(d.free/(1024**3), 1)
        s['disk_used_pct'] = int(d.used*100//d.total)
    except:
        s['disk_free_gb'] = 0; s['disk_used_pct'] = 0
    if HAS_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            s['mem_avail_mb'] = mem.available//(1024*1024)
            s['mem_pct']      = round(mem.percent,1)
            s['cpu_pct']      = round(psutil.cpu_percent(interval=None),1)
        except:
            s['mem_avail_mb']=0; s['mem_pct']=0; s['cpu_pct']=0
    return s


# ── METAR ─────────────────────────────────────────────────────────────────────
_metar_cache = {'data': None, 'ts': 0.0}
METAR_TTL    = 600  # 10 minutes

def colorize_metar(raw):
    """Wrap METAR tokens with coloured HTML spans (inline CSS only)."""
    import re as _re
    if not raw:
        return '<span style="color:#2e2e50">N/A</span>'
    icao_done = False
    out = []
    for tok in raw.split():
        if not icao_done:                                       # Station ICAO — skip (shown as label)
            icao_done = True
            continue
        elif _re.match(r'^\d{6}Z$', tok):                      # Obs time
            out.append(f'<span style="color:#3a3a60">{tok}</span>')
        elif _re.match(r'^(VRB|\d{3})\d{2,3}(G\d{2,3})?KT$', tok):  # Wind
            out.append(f'<span style="color:#f5c518">{tok}</span>')
        elif tok == 'CAVOK':
            out.append(f'<span style="color:#22c55e">{tok}</span>')
        elif _re.match(r'^(\d{4}|\d+SM)$', tok):               # Visibility
            out.append(f'<span style="color:#22d3ee">{tok}</span>')
        elif _re.match(r'^R\d{2}[LRC]?/\d{4}', tok):           # RVR
            out.append(f'<span style="color:#22d3ee">{tok}</span>')
        elif _re.match(r'^(RE)?([-+])?(VC)?(MI|BC|PR|DR|BL|SH|TS|FZ)*(DZ|RA|SN|SG|IC|PL|GR|GS|UP|FG|VA|BR|HZ|DU|FU|SA|PY|SQ|FC|TS)+$', tok):  # Wx/RE wx
            out.append(f'<span style="color:#f97316">{tok}</span>')
        elif _re.match(r'^(FEW|SCT|BKN|OVC|VV)\d{3}', tok) or tok in ('NSC','SKC','NCD','CLR'):  # Cloud
            out.append(f'<span style="color:#3b82f6">{tok}</span>')
        elif _re.match(r'^M?\d+/M?\d+$', tok):                 # Temp/DP
            out.append(f'<span style="color:#22c55e">{tok}</span>')
        elif _re.match(r'^[QA]\d{4}$', tok):                    # QNH
            out.append(f'<span style="color:#a855f7">{tok}</span>')
        elif tok in ('NOSIG','TEMPO','BECMG','PROB30','PROB40','RMK'):
            out.append(f'<span style="color:#f59e0b">{tok}</span>')
        else:
            out.append(f'<span style="color:#4b5563">{tok}</span>')
    return '&nbsp;'.join(out)


# Military colour scale: index 0 (BLU, best) → 5 (RED, worst)
_MIL_COLORS = [
    ('BLU', '#1d4ed8', 2500, 8000),   # cloud≥2500ft, vis≥8000m
    ('WHT', '#cbd5e1', 1500, 5000),   # cloud≥1500ft, vis≥5000m
    ('GRN', '#16a34a',  700, 3700),   # cloud≥700ft,  vis≥3700m
    ('YLO', '#ca8a04',  300, 1600),   # cloud≥300ft,  vis≥1600m
    ('AMB', '#ea580c',  200,  800),   # cloud≥200ft,  vis≥800m
    ('RED', '#dc2626',    0,    0),   # below AMB
]

def mil_color_state(raw):
    """Return index 0-5 into _MIL_COLORS for a raw METAR string."""
    import re as _re
    if not raw:
        return 5
    tokens = raw.split()
    if 'CAVOK' in tokens:
        return 0  # BLU: unlimited vis, no significant cloud
    vis_m = 9999
    cloud_ft = 9999
    for tok in tokens:
        if _re.match(r'^\d{4}$', tok):
            v = int(tok)
            if v <= 9999:
                vis_m = min(vis_m, v)
        elif _re.match(r'^\d+SM$', tok):
            vis_m = min(vis_m, int(_re.match(r'^(\d+)', tok).group(1)) * 1609)
        m = _re.match(r'^(SCT|BKN|OVC|VV)(\d{3})', tok)
        if m:
            cloud_ft = min(cloud_ft, int(m.group(2)) * 100)
    # Determine state independently for vis and cloud, take worst
    def _state(cloud, vis):
        for i, (_, _, c_min, v_min) in enumerate(_MIL_COLORS):
            if cloud >= c_min and vis >= v_min:
                return i
        return 5
    return _state(cloud_ft, vis_m)

def mil_bar_html(idx):
    """Render a 6-segment coloured bar chart; segment[idx] is active."""
    segs = []
    for i, (label, color, _, _) in enumerate(_MIL_COLORS):
        if i == idx:
            segs.append(
                f"<span title='{label}' style='display:inline-block;width:5px;height:14px;"
                f"border-radius:1px;background:{color};"
                f"box-shadow:0 0 5px {color};opacity:1'></span>"
            )
        else:
            segs.append(
                f"<span title='{label}' style='display:inline-block;width:5px;height:14px;"
                f"border-radius:1px;background:{color};opacity:0.2'></span>"
            )
    label = _MIL_COLORS[idx][0]
    color = _MIL_COLORS[idx][1]
    bar   = "<span style='display:inline-flex;align-items:center;gap:1px;flex-shrink:0'>" + ''.join(segs) + "</span>"
    code  = f"<span style='font-size:8px;font-weight:900;letter-spacing:.06em;color:{color};flex-shrink:0;margin-left:3px'>{label}</span>"
    return f"<span style='display:inline-flex;align-items:center;gap:0;flex-shrink:0;margin-right:5px'>{bar}{code}</span>"


def taf_base_mil_state(raw_taf):
    """Return mil colour index for TAF base forecast (conditions before first TEMPO/BECMG/FM)."""
    import re as _re
    if not raw_taf:
        return 5
    base = []
    for tok in raw_taf.split():
        if tok in ('TEMPO','BECMG','PROB30','PROB40','PROB') or _re.match(r'^FM\d{4,6}$', tok):
            break
        base.append(tok)
    return mil_color_state(' '.join(base))


def get_metar():
    """Return EBAW + EBBR METAR from aviationweather.gov with 10-min cache."""
    global _metar_cache
    now = time.time()
    if _metar_cache['data'] and (now - _metar_cache['ts']) < METAR_TTL:
        return _metar_cache['data']
    result = {'EBAW': '', 'EBBR': '', 'ts': '--:--'}
    if not _ureq:
        return result
    try:
        url = 'https://aviationweather.gov/api/data/metar?ids=EBAW,EBBR&format=json&hours=2'
        req = _ureq.Request(url, headers={'User-Agent': 'sdr-hub/1.0'})
        with _ureq.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        # API returns newest-first; take the first hit for each ICAO
        for item in data:
            icao = item.get('icaoId', '')
            raw  = item.get('rawOb', '').replace('METAR ', '').replace('SPECI ', '').strip()
            if icao in result and not result[icao]:
                result[icao] = raw
        result['ts'] = dt.utcnow().strftime('%H:%M')
        _metar_cache = {'data': result, 'ts': now}
    except Exception:
        if _metar_cache['data']:
            return _metar_cache['data']
    return result

# ── TAF ───────────────────────────────────────────────────────────────────────
_taf_cache = {'data': None, 'ts': 0.0}
TAF_TTL    = 1800  # 30 minutes

def get_taf():
    """Return EBAW + EBBR TAF from aviationweather.gov with 30-min cache."""
    global _taf_cache
    now = time.time()
    if _taf_cache['data'] and (now - _taf_cache['ts']) < TAF_TTL:
        return _taf_cache['data']
    result = {'EBAW': '', 'EBBR': '', 'ts': '--:--'}
    if not _ureq:
        return result
    try:
        url = 'https://aviationweather.gov/api/data/taf?ids=EBAW,EBBR&format=json&hours=24'
        req = _ureq.Request(url, headers={'User-Agent': 'sdr-hub/1.0'})
        with _ureq.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        for item in data:
            icao = item.get('icaoId', '')
            raw  = item.get('rawTAF', '').replace('\n', ' ').strip()
            if icao in result and not result[icao]:
                result[icao] = raw
        result['ts'] = dt.utcnow().strftime('%H:%M')
        _taf_cache = {'data': result, 'ts': now}
    except Exception:
        if _taf_cache['data']:
            return _taf_cache['data']
    return result


# ── NOTAM ─────────────────────────────────────────────────────────────────────
_notam_cache = {'data': None, 'ts': 0.0}
NOTAM_TTL    = 3600  # 1 hour

def get_notam():
    """Return active NOTAMs for EBAW+EBBR from notams.aim.faa.gov (hourly cache)."""
    global _notam_cache
    now = time.time()
    if _notam_cache['data'] and (now - _notam_cache['ts']) < NOTAM_TTL:
        return _notam_cache['data']
    result = {'EBAW': [], 'EBBR': [], 'total': 0, 'ts': '--:--'}
    if not _ureq:
        return result
    url  = 'https://notams.aim.faa.gov/notamSearch/search'
    hdrs = {'User-Agent': 'sdr-hub/1.0',
            'Content-Type': 'application/x-www-form-urlencoded'}
    def _fetch(icao):
        body = f'searchType=0&designatorsForLocation={icao}&radiusForLocation=5'.encode()
        req  = _ureq.Request(url, data=body, headers=hdrs)
        with _ureq.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    try:
        for icao in ('EBAW', 'EBBR'):
            items = []
            for n in _fetch(icao).get('notamList', []):
                if n.get('cancelledOrExpired', False):
                    continue
                items.append({
                    'id':      n.get('notamNumber', ''),
                    'icao':    n.get('facilityDesignator', icao),
                    'msg':     n.get('icaoMessage', n.get('traditionalMessage', '')).strip(),
                    'keyword': n.get('keyword', ''),
                    'start':   n.get('startDate', ''),
                    'end':     n.get('endDate', ''),
                })
            result[icao] = items
        result['total'] = len(result['EBAW']) + len(result['EBBR'])
        result['ts'] = dt.utcnow().strftime('%H:%M')
        _notam_cache = {'data': result, 'ts': now}
    except Exception:
        if _notam_cache['data']:
            return _notam_cache['data']
    return result


def get_adsb_stats():
    result = {'tar1090': {}, 'stage2': {}}
    if not _ureq: return result
    try:
        with _ureq.urlopen(TAR1090_STATS, timeout=3) as r:
            s = json.loads(r.read())
        l1 = s.get('last1min', {}).get('local', {})
        l5 = s.get('last5min', {})
        result['tar1090'] = {
            'aircraft_with_pos': s.get('aircraft_with_pos', 0),
            'aircraft_total':    s.get('aircraft_with_pos', 0) + s.get('aircraft_without_pos', 0),
            'gain_db':           s.get('gain_db'),
            'ppm':               s.get('estimated_ppm'),
            'signal':            round(l1.get('signal', 0), 1),
            'noise':             round(l1.get('noise', 0), 1),
            'peak_signal':       round(l1.get('peak_signal', 0), 1),
            'msgs_1min':         l1.get('accepted', [0])[0] if l1.get('accepted') else 0,
            'max_range_km':      round(l5.get('max_distance', 0) / 1000, 0),
        }
    except: pass
    try:
        with _ureq.urlopen(STAGE2_URL, timeout=3) as r:
            s2 = json.loads(r.read())
        if isinstance(s2, list) and s2: s2 = s2[0]
        result['stage2'] = s2
    except: pass
    return result

def get_db_stats(conn):
    return {
        'total':    conn.execute("SELECT COUNT(*) FROM sdr_transmission").fetchone()[0],
        'tr':       conn.execute("SELECT COUNT(*) FROM sdr_transcript").fetchone()[0],
        'speech':   conn.execute("SELECT COUNT(*) FROM sdr_transcript WHERE text IS NOT NULL AND text!=''").fetchone()[0],
        'pending':  conn.execute(
            "SELECT COUNT(*) FROM sdr_transmission t "
            "LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id "
            "WHERE tr.id IS NULL AND t.data_file IS NOT NULL").fetchone()[0],
        'today_dg': conn.execute(
            "SELECT COUNT(*) FROM sdr_transcript WHERE date(created_at)=date('now') AND model LIKE 'nova%'").fetchone()[0],
        'today_wh': conn.execute(
            "SELECT COUNT(*) FROM sdr_transcript WHERE date(created_at)=date('now') AND model LIKE 'whisper%'").fetchone()[0],
    }

def get_hourly_data():
    """Return 24 counts for completed rolling hours: slot[0]=now-24h (oldest), slot[23]=now-1h (most recent)."""
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT strftime('%Y-%m-%d %H', begin_date) AS slot, COUNT(*) AS cnt
            FROM sdr_transmission
            WHERE begin_date >= datetime('now', '-25 hours')
            AND data_file IS NOT NULL
            GROUP BY slot ORDER BY slot
        """).fetchall()
        conn.close()
        row_dict = {r[0]: r[1] for r in rows}
        now = dt.utcnow()
        from datetime import timedelta as _td
        # 24 completed hours: (now-24h) to (now-1h), oldest first
        # Uses -25h in SQL to ensure the earliest slot always gets its full data
        slots = [
            (now - _td(hours=24 - i)).strftime('%Y-%m-%d %H')
            for i in range(24)
        ]
        return [row_dict.get(s, 0) for s in slots]
    except:
        return [0] * 24

def _icao_flag(hex_str):
    """Return a flag emoji for a given ICAO 24-bit hex address."""
    try:
        n = int(hex_str, 16)
        if 0x300000 <= n <= 0x33FFFF: return '🇮🇹'
        if 0x340000 <= n <= 0x37FFFF: return '🇪🇸'
        if 0x380000 <= n <= 0x3BFFFF: return '🇫🇷'
        if 0x3C0000 <= n <= 0x3FFFFF: return '🇩🇪'
        if 0x400000 <= n <= 0x43FFFF: return '🇬🇧'
        if 0x440000 <= n <= 0x447FFF: return '🇦🇹'
        if 0x448000 <= n <= 0x44FFFF: return '🇧🇪'
        if 0x450000 <= n <= 0x457FFF: return '🇧🇬'
        if 0x458000 <= n <= 0x45FFFF: return '🇩🇰'
        if 0x460000 <= n <= 0x467FFF: return '🇫🇮'
        if 0x468000 <= n <= 0x46FFFF: return '🇬🇷'
        if 0x470000 <= n <= 0x477FFF: return '🇭🇺'
        if 0x480000 <= n <= 0x487FFF: return '🇳🇱'
        if 0x488000 <= n <= 0x48FFFF: return '🇨🇭'
        if 0x490000 <= n <= 0x497FFF: return '🇨🇿'
        if 0x498000 <= n <= 0x49FFFF: return '🇵🇱'
        if 0x4A8000 <= n <= 0x4AFFFF: return '🇸🇪'
        if 0x4B0000 <= n <= 0x4B7FFF: return '🇳🇴'
        if 0x700000 <= n <= 0x73FFFF: return '🇦🇪'
        if 0xA00000 <= n <= 0xAFFFFF: return '🇺🇸'
    except Exception:
        pass
    return ''


def get_aircraft_list():
    if not _ureq: return []
    try:
        with _ureq.urlopen(ADSB_URL, timeout=3) as r:
            data = json.loads(r.read())
        result = []
        for ac in data.get('aircraft', []):
            lat, lon = ac.get('lat'), ac.get('lon')
            if not lat or not lon: continue
            dx = (lon - EBAW_LON) * 111.0 * math.cos(math.radians(EBAW_LAT))
            dy = -(lat - EBAW_LAT) * 111.0
            dist = round(math.sqrt(dx**2 + dy**2), 1)
            if dist > 150: continue
            alt = ac.get('alt_baro')
            result.append({
                'hex':      ac.get('hex', ''),
                'flight':   (ac.get('flight') or '').strip(),
                't':        (ac.get('t') or '').strip(),
                'squawk':   ac.get('squawk', ''),
                'r':        (ac.get('r') or '').strip(),
                'alt':      alt,
                'gs':       ac.get('gs'),
                'track':    ac.get('track'),
                'dist_km':  dist,
                'dist_nmi': round(dist / 1.852, 1),
            })
        result.sort(key=lambda a: a['dist_km'])
        return result[:30]
    except:
        return []


# ── Phonetic / transmitter identification ─────────────────────────────────────
def _decode_phonetic(text):
    results = []
    words = re.findall(r'\b\w+\b', text.lower())
    run = []
    for w in words:
        if w in PHONETIC: run.append(PHONETIC[w])
        else:
            if len(run) >= 3: results.append(''.join(run))
            run = []
    if len(run) >= 3: results.append(''.join(run))
    return results

def guess_transmitter(text, aircraft, freq_hz):
    fc = freq_hz / 1e6
    if any(abs(fc-f) < 0.015 for f in ATIS_MHZ):
        return None, "ATIS/ground broadcast"
    if not aircraft or not text:
        return None, ""
    text_up  = text.upper()
    direct   = set(re.findall(r'\b([A-Z]{2,3}[0-9]{1,5}[A-Z]{0,2})\b', text_up))
    oo_regs  = set(re.findall(r'\bOO[- ]?([A-Z]{3})\b', text_up))
    phonetic = set(_decode_phonetic(text))
    scored = []
    for ac in aircraft:
        flight = (ac.get('flight') or '').strip().upper()
        hex_id = ac.get('hex','')
        dist   = ac.get('dist_km') or 999
        alt    = ac.get('alt_baro') or 0
        score  = 0; reason = ''
        if flight:
            for cs in direct:
                if cs==flight or flight.startswith(cs[:4]) or cs.startswith(flight[:4]):
                    score = max(score,92); reason = f'callsign "{cs}" in transcript'
            for rm in oo_regs:
                if rm in flight:
                    score = max(score,88); reason = f'registration OO-{rm} in transcript'
            for ps in phonetic:
                if len(ps)>=4:
                    if ps==flight or flight in ps or ps in flight:
                        score = max(score,78); reason = f'phonetic "{ps}" -> {flight}'
                    elif sum(a==b for a,b in zip(ps,flight))>=4:
                        score = max(score,60); reason = f'partial phonetic match {flight}'
        if score==0:
            if any(abs(fc-f)<0.015 for f in EBAW_LOCAL_MHZ):
                if dist<25 and alt<8000:
                    score = max(5,48-int(dist*1.8)); reason = f'{dist:.0f}km EBAW, {alt}ft'
            elif any(abs(fc-f)<0.015 for f in EBBR_LOCAL_MHZ):
                if dist<80:
                    score = max(5,32-int(dist*0.4)); reason = f'{dist:.0f}km, EBBR freq'
            elif dist<30 and alt<10000:
                score = max(5,22-int(dist*0.6)); reason = f'nearest {dist:.0f}km, {alt}ft'
        if score>0: scored.append((score,hex_id,reason))
    if not scored: return None,"no match"
    scored.sort(reverse=True)
    bs,bh,br = scored[0]
    if bs<10: return None,"low confidence"
    return bh, f"{br} (score {bs})"


# ── SVG Map (per-transmission modal) ─────────────────────────────────────────
def _km_to_px(km):   return km*(MAP_SIZE/2)/MAP_RADIUS_KM
def _latlon_to_xy(lat,lon):
    cx,cy = MAP_SIZE/2, MAP_SIZE/2
    dx = (lon-EBAW_LON)*111.0*math.cos(math.radians(EBAW_LAT))
    dy = -(lat-EBAW_LAT)*111.0
    ppk = (MAP_SIZE/2)/MAP_RADIUS_KM
    return cx+dx*ppk, cy+dy*ppk
def _alt_color(alt):
    if alt is None: return "#71717a"
    if alt<3000:    return "#fb2c36"
    if alt<10000:   return "#fcbb00"
    if alt<28000:   return "#3b82f6"
    return "#52525b"
def _aircraft_svg(x,y,track,color):
    t = track or 0
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({t:.0f})">'
            f'<polygon points="0,-9 5,6 0,2 -5,6" fill="{color}" stroke="#050508" stroke-width="1.2"/>'
            f'</g>')

def generate_map_svg(tx_id, begin_date, end_date, label, freq_hz=0, text=None):
    cx,cy = MAP_SIZE/2, MAP_SIZE/2
    aircraft = []
    try:
        if os.path.exists(AIRCRAFT_DB):
            t0 = (dt.fromisoformat(begin_date.replace("Z",""))-datetime.timedelta(seconds=90)).isoformat()
            t1 = (dt.fromisoformat(end_date.replace("Z",""))+datetime.timedelta(seconds=90)).isoformat()
            conn = sqlite3.connect(AIRCRAFT_DB,timeout=5)
            conn.execute("PRAGMA journal_mode=WAL"); conn.row_factory=sqlite3.Row
            rows = conn.execute("""
                SELECT hex,flight,lat,lon,alt_baro,gs,track,dist_km,MAX(ts) as last_seen
                FROM positions WHERE ts BETWEEN ? AND ? GROUP BY hex ORDER BY dist_km ASC
            """,(t0,t1)).fetchall()
            conn.close(); aircraft=[dict(r) for r in rows]
    except: pass
    best_hex,match_reason = guess_transmitter(text,aircraft,freq_hz)
    p=[]
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{MAP_SIZE}" height="{MAP_SIZE}" style="background:#050508;border-radius:10px;display:block">')
    for km,stroke in [(25,"#12122a"),(50,"#10102a"),(75,"#0e0e28"),(100,"#0c0c26")]:
        r=_km_to_px(km)
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{stroke}" stroke-width="1"/>')
        p.append(f'<text x="{cx+r+3:.0f}" y="{cy-3:.0f}" fill="#1e1e3a" font-size="9" font-family="monospace">{km}km</text>')
    p.append(f'<line x1="{cx:.0f}" y1="0" x2="{cx:.0f}" y2="{MAP_SIZE}" stroke="#0e0e28" stroke-width="1"/>')
    p.append(f'<line x1="0" y1="{cy:.0f}" x2="{MAP_SIZE}" y2="{cy:.0f}" stroke="#0e0e28" stroke-width="1"/>')
    bx,by = _latlon_to_xy(EBBR_LAT,EBBR_LON)
    p.append(f'<line x1="{bx-10:.0f}" y1="{by:.0f}" x2="{bx+10:.0f}" y2="{by:.0f}" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<line x1="{bx:.0f}" y1="{by-10:.0f}" x2="{bx:.0f}" y2="{by+10:.0f}" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="3.5" fill="#3b82f6"/>')
    p.append(f'<text x="{bx+13:.0f}" y="{by-6:.0f}" fill="#3b82f6" font-size="9" font-family="monospace" font-weight="bold">EBBR</text>')
    p.append(f'<line x1="{cx-12:.0f}" y1="{cy:.0f}" x2="{cx+12:.0f}" y2="{cy:.0f}" stroke="#22c55e" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<line x1="{cx:.0f}" y1="{cy-12:.0f}" x2="{cx:.0f}" y2="{cy+12:.0f}" stroke="#22c55e" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="4" fill="#22c55e"/>')
    p.append(f'<text x="{cx+16:.0f}" y="{cy-8:.0f}" fill="#22c55e" font-size="10" font-family="monospace" font-weight="bold">EBAW</text>')
    for ac in aircraft:
        x,y = _latlon_to_xy(ac["lat"],ac["lon"])
        if not (5<x<MAP_SIZE-5 and 5<y<MAP_SIZE-5): continue
        is_best = (ac["hex"]==best_hex)
        color   = "#fcbb00" if is_best else _alt_color(ac["alt_baro"])
        if is_best:
            p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="22" fill="none" stroke="#fcbb00" stroke-width="1" opacity="0.2"/>')
            p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="none" stroke="#fcbb00" stroke-width="1.5" opacity="0.5"/>')
        p.append(_aircraft_svg(x,y,ac.get("track"),color))
        flight  = (ac["flight"] or ac["hex"] or "?").strip()
        alt     = ac["alt_baro"]
        alt_str = (f" {round(alt*0.3048/1000,1)}km" if alt>=10000 else f" {round(alt*0.3048)}m") if alt is not None else ""
        lbl     = flight+alt_str
        lx = x+12
        if lx+len(lbl)*5.5>MAP_SIZE-4: lx=x-12-len(lbl)*5.5
        ly = y-7
        if ly<14: ly=y+16
        p.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{color}" font-size="9.5" font-family="monospace"'
                 +(' font-weight="bold"' if is_best else '')+f'>{lbl}</text>')
        if is_best:
            p.append(f'<text x="{lx:.0f}" y="{ly+10:.0f}" fill="#fcbb00" font-size="8" font-family="monospace">likely tx</text>')
    if not aircraft:
        p.append(f'<text x="{cx:.0f}" y="{cy+40:.0f}" text-anchor="middle" fill="#1e1e3a" font-size="12" font-family="monospace">no aircraft data</text>')
    try:   time_str=dt.fromisoformat(begin_date.replace("Z","")).strftime("%H:%M:%S UTC")
    except: time_str=begin_date[:8]
    p.append(f'<text x="5" y="12" fill="#3b82f6" font-size="9" font-family="monospace">{label}</text>')
    p.append(f'<text x="{MAP_SIZE-5}" y="12" text-anchor="end" fill="#3a3a5a" font-size="9" font-family="monospace">{time_str}</text>')
    if match_reason:
        rc="#fcbb00" if best_hex else "#3a3a5a"
        p.append(f'<text x="5" y="{MAP_SIZE-18}" fill="{rc}" font-size="8" font-family="monospace">{match_reason[:60]}</text>')
    p.append(f'<text x="{MAP_SIZE-5}" y="{MAP_SIZE-18}" text-anchor="end" fill="#1e1e3a" font-size="8" font-family="monospace">{len(aircraft)} ac</text>')
    p.append('</svg>')
    return "".join(p)


# ── Live global radar SVG ─────────────────────────────────────────────────────
def generate_live_radar_svg():
    # ── V3: 500×500 square canvas, VFR chart style ───────────────────────────
    W, H = 500, 500
    cx, cy = W / 2, H / 2
    ppk = cy / 20   # 12.5 px/km — 20 km radius

    def xy(lat, lon):
        """Convert lat/lon to SVG x,y relative to EBAW centre."""
        dx = (lon - EBAW_LON) * 111.0 * math.cos(math.radians(EBAW_LAT))
        dy = -(lat - EBAW_LAT) * 111.0
        return cx + dx * ppk, cy + dy * ppk

    # ── Fetch live aircraft ───────────────────────────────────────────────────
    aircraft = []
    if _ureq:
        try:
            with _ureq.urlopen(ADSB_URL, timeout=3) as r:
                data = json.loads(r.read())
            for ac in data.get('aircraft', []):
                lat, lon = ac.get('lat'), ac.get('lon')
                if not lat or not lon: continue
                dx = (lon - EBAW_LON) * 111.0 * math.cos(math.radians(EBAW_LAT))
                dy = -(lat - EBAW_LAT) * 111.0
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 22: continue
                aircraft.append({**ac, '_x': cx + dx*ppk, '_y': cy + dy*ppk, '_dist': dist})
        except:
            pass

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="background:#05050a;display:block">']

    # ── EBBU TMA boundary ring (~17 km) ──────────────────────────────────────
    tma_r = 17 * ppk
    p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{tma_r:.1f}" '
             f'fill="rgba(40,100,220,0.07)" stroke="rgba(60,120,240,0.40)" '
             f'stroke-width="1" stroke-dasharray="5,4"/>')
    p.append(f'<text x="{cx-tma_r+6:.0f}" y="{cy-4:.0f}" fill="rgba(80,140,255,0.45)" '
             f'font-size="8" font-family="monospace" font-weight="bold">EBBU TMA</text>')
    p.append(f'<text x="{cx-tma_r+6:.0f}" y="{cy+8:.0f}" fill="rgba(80,140,255,0.35)" '
             f'font-size="7" font-family="monospace">FL095 / 3500ft</text>')

    # ── Range rings ───────────────────────────────────────────────────────────
    for km, stroke in [(5, '#12122a'), (10, '#10102a'), (20, '#0a0a22')]:
        r = km * ppk
        p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{stroke}" stroke-width="0.8"/>')
        if km < 20:
            p.append(f'<text x="{cx+r+3:.0f}" y="{cy-3:.0f}" fill="#18183a" font-size="7" font-family="monospace">{km}km</text>')

    # ── Cross-hairs ───────────────────────────────────────────────────────────
    p.append(f'<line x1="{cx:.0f}" y1="0" x2="{cx:.0f}" y2="{H}" stroke="rgba(255,255,255,0.022)" stroke-width="0.5"/>')
    p.append(f'<line x1="0" y1="{cy:.0f}" x2="{W}" y2="{cy:.0f}" stroke="rgba(255,255,255,0.022)" stroke-width="0.5"/>')

    # ── EBAW CTR (~9 km, magenta dashed) ─────────────────────────────────────
    ctr_r = 9 * ppk
    p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{ctr_r:.1f}" '
             f'fill="none" stroke="#d048e8" stroke-width="1.4" stroke-dasharray="6,4" opacity="0.65"/>')
    ctr_lx, ctr_ly = cx + ctr_r * 0.68, cy + ctr_r * 0.72
    p.append(f'<text x="{ctr_lx:.0f}" y="{ctr_ly:.0f}" fill="#d048e8" '
             f'font-size="8" font-family="monospace" font-weight="bold" opacity="0.70">EBAW CTR</text>')
    p.append(f'<text x="{ctr_lx:.0f}" y="{ctr_ly+10:.0f}" fill="#d048e8" '
             f'font-size="7" font-family="monospace" opacity="0.50">FL065 / SFC</text>')

    # ── Rivers (chart blue, brighter) ─────────────────────────────────────────
    _schelde = [
        (51.38, 4.25), (51.33, 4.28), (51.29, 4.31), (51.25, 4.36),
        (51.22, 4.40), (51.19, 4.40), (51.16, 4.38), (51.13, 4.38),
        (51.10, 4.36), (51.07, 4.32), (51.04, 4.29),
    ]
    _rupel = [
        (51.10, 4.56), (51.09, 4.49), (51.08, 4.43), (51.07, 4.36), (51.07, 4.32),
    ]
    _kleine_nete = [
        (51.075, 4.53), (51.078, 4.48), (51.085, 4.44),
    ]
    for _river, _sw in [(_schelde, 3.0), (_rupel, 2.0), (_kleine_nete, 1.5)]:
        pts_str = ' '.join(f'{xy(la,lo)[0]:.1f},{xy(la,lo)[1]:.1f}' for la, lo in _river)
        p.append(f'<polyline points="{pts_str}" fill="none" stroke="#2068a8" stroke-width="{_sw}" '
                 f'stroke-linecap="round" stroke-linejoin="round" opacity="0.75"/>')

    # ── VFR reporting points (AIP 30 DEC 2021 exact coords) ──────────────────
    _waypoints = [
        ('KONTI', 51.12639, 4.42917),   # Kontich cloverleaf E19
        ('RUPEL', 51.12056, 4.30833),   # Rupelmonde junction Rupel/Schelde
        ('DUFFY', 51.08528, 4.49472),   # Duffel railway bridge
        ('WISKY', 51.08000, 4.36639),   # Rupel Yacht Club, Willebroek
        ('PORTA', 51.23083, 4.44111),   # Merksem Sportpaleis
        ('BRUNO', 51.11861, 4.84222),   # DVOR-DME BUN (off-radar at 20 km)
    ]
    for _name, _wlat, _wlon in _waypoints:
        wx, wy = xy(_wlat, _wlon)
        if not (2 < wx < W-2 and 2 < wy < H-2): continue
        s = 6
        p.append(f'<g opacity="0.55">'
                 f'<polygon points="{wx:.0f},{wy-s:.0f} {wx-s:.0f},{wy+s:.0f} {wx+s:.0f},{wy+s:.0f}" '
                 f'fill="rgba(212,168,0,0.12)" stroke="#d4a800" stroke-width="1.3"/>'
                 f'<text x="{wx+9:.0f}" y="{wy+4:.0f}" fill="#d4a800" font-size="8" '
                 f'font-family="monospace" font-weight="bold">{_name}</text>'
                 f'</g>')

    # ── EBAW airport symbol ───────────────────────────────────────────────────
    asz = 9
    p.append(f'<line x1="{cx-asz:.0f}" y1="{cy:.0f}" x2="{cx+asz:.0f}" y2="{cy:.0f}" stroke="#22c55e" stroke-width="2" stroke-linecap="round"/>')
    p.append(f'<line x1="{cx:.0f}" y1="{cy-asz:.0f}" x2="{cx:.0f}" y2="{cy+asz:.0f}" stroke="#22c55e" stroke-width="2" stroke-linecap="round"/>')
    p.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{asz+4:.0f}" fill="none" stroke="#22c55e" stroke-width="0.7" opacity="0.45"/>')
    p.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="3" fill="#22c55e"/>')
    p.append(f'<text x="{cx+16:.0f}" y="{cy-7:.0f}" fill="#22c55e" font-size="9" font-family="monospace" font-weight="bold">EBAW</text>')

    # ── North indicator ───────────────────────────────────────────────────────
    p.append(f'<text x="{cx-4:.0f}" y="16" fill="#202040" font-size="10" font-family="monospace" font-weight="bold">N</text>')
    p.append(f'<line x1="{cx:.0f}" y1="19" x2="{cx:.0f}" y2="28" stroke="#202040" stroke-width="1.2"/>')

    # ── Aircraft: dot + glow ring + heading tick + labels ────────────────────
    for ac in aircraft:
        x, y = ac['_x'], ac['_y']
        if not (4 < x < W-4 and 4 < y < H-4): continue
        col   = _alt_color(ac.get('alt_baro'))
        track = ac.get('track') or 0
        hr    = math.radians(track)
        tx    = x + math.sin(hr) * 16
        ty    = y - math.cos(hr) * 16
        alt   = ac.get('alt_baro')
        flight = (ac.get('flight') or '').strip()
        alt_lbl = (f"FL{alt//100:03d}" if alt >= 1800 else f"{alt}ft") if alt else ''
        p.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" '
                 f'stroke="{col}" stroke-width="1.2" opacity="0.6"/>')
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="none" stroke="{col}" stroke-width="0.7" opacity="0.35"/>')
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{col}" opacity="0.9"/>')
        if flight:
            p.append(f'<text x="{x+9:.1f}" y="{y-3:.1f}" fill="{col}" font-size="9" font-family="monospace" font-weight="bold">{flight}</text>')
        if alt_lbl:
            p.append(f'<text x="{x+9:.1f}" y="{y+8:.1f}" fill="{col}" font-size="8" font-family="monospace" opacity="0.75">{alt_lbl}</text>')

    if not aircraft:
        p.append(f'<text x="{cx:.0f}" y="{cy+35:.0f}" text-anchor="middle" fill="#1e1e3a" font-size="11" font-family="monospace">no aircraft data</text>')

    # ── Legend ────────────────────────────────────────────────────────────────
    for i, (col, lbl) in enumerate([('#3b82f6', '<FL280'), ('#fcbb00', '<10k'), ('#fb2c36', '<3k'), ('#52525b', 'high')]):
        lx = 6 + i * 88
        p.append(f'<circle cx="{lx+3}" cy="{H-7}" r="3" fill="{col}"/>')
        p.append(f'<text x="{lx+9}" y="{H-3}" fill="{col}" font-size="7" font-family="monospace">{lbl}</text>')

    p.append(f'<text x="{W-4}" y="{H-3}" text-anchor="end" fill="#1e1e3a" font-size="7" font-family="monospace">{len(aircraft)} ac</text>')
    p.append('</svg>')
    return ''.join(p)


# ── Donut chart (for analytics strip) ────────────────────────────────────────
def build_donut_svg(slices, size=100):
    cx = cy = size / 2
    r   = size * 0.355
    sw  = size * 0.135
    C   = 2 * math.pi * r
    out = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">']
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="none" stroke="#1e1e38" stroke-width="{sw:.2f}"/>')
    offset = 0.0
    for frac, color in slices:
        if frac <= 0: continue
        dash = frac * C
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="none" '
            f'stroke="{color}" stroke-width="{sw:.2f}" '
            f'stroke-dasharray="{dash:.3f} {C:.3f}" '
            f'stroke-dashoffset="{-(offset*C):.3f}" '
            f'transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += frac
    out.append('</svg>')
    return ''.join(out)


# ── Sparkline SVG ─────────────────────────────────────────────────────────────
def build_sparkline_svg(hourly, W=280, H=110):
    from datetime import timedelta as _td
    now   = dt.utcnow()
    max_v = max(hourly) or 1
    N     = len(hourly)  # 24
    pts   = []
    for i, v in enumerate(hourly):
        x = i * W / (N - 1)
        y = H - 8 - (v / max_v) * (H - 18)
        pts.append((x, y))
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = path + f" L{W},{H} L0,{H} Z"
    p = [f'<svg width="100%" height="{H}" viewBox="0 0 {W} {H}" preserveAspectRatio="none">']
    p.append('<defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">')
    p.append('<stop offset="0%" stop-color="#f5c518" stop-opacity=".25"/>')
    p.append('<stop offset="100%" stop-color="#f5c518" stop-opacity="0"/>')
    p.append('</linearGradient></defs>')
    for y_pos in [H * 0.25, H * 0.5, H * 0.75]:
        p.append(f'<line x1="0" y1="{y_pos:.0f}" x2="{W}" y2="{y_pos:.0f}" stroke="#1e1e38" stroke-width="1"/>')
    p.append(f'<path d="{area}" fill="url(#sg)"/>')
    p.append(f'<path d="{path}" fill="none" stroke="#f5c518" stroke-width="1.5"/>')
    # "now" cursor always at the right edge — slot[N-1] is always the most recent completed hour
    p.append(f'<line x1="{W}" y1="0" x2="{W}" y2="{H}" stroke="#f5c518" stroke-width="1" stroke-dasharray="3,3" opacity=".4"/>')
    # Dynamic UTC labels: find which slot index corresponds to 00z, 06z, 12z, 18z
    # slot[i] = (now - (24 - i)) hours truncated to hour
    for lh in [0, 6, 12, 18]:
        for i in range(N):
            if (now - _td(hours=24 - i)).hour == lh:
                x = i * W / (N - 1)
                p.append(f'<text x="{x:.0f}" y="{H}" fill="#4a4a6a" font-size="8" font-family="monospace">{lh:02d}z</text>')
                break
    p.append(f'<text x="{W}" y="{H}" text-anchor="end" fill="#f5c518" font-size="8" font-family="monospace">now</text>')
    p.append('</svg>')
    return ''.join(p)


# ── Card builder (shared by page render + SSE) ──────────────────────────────
def build_card_html(r, fresh=False):
    fc     = (r["begin_frequency"] + r["end_frequency"]) / 2
    label  = freq_label(fc)
    dur    = fmt_dur(r["begin_date"], r["end_date"])
    tr_id  = r["tr_id"]; model = r["model"] or ""; text = r["text"]; err = r["error"]
    stripe_color, badge_bg, type_short, data_t = freq_type_info(label)
    freq_html = (
        f"<div class='tx-freq'>"
        f"<div class='tx-mhz'>{fc/1e6:.3f}</div>"
        f"<span class='tx-badge' style='background:{badge_bg};color:{stripe_color};"
        f"border:1px solid {stripe_color}40'>{type_short}</span>"
        f"<div class='tx-fname'>{label}</div></div>")
    bars = dur_bar_html(r["begin_date"], r["end_date"])
    if tr_id is None:
        tx_html = "<div class='tx-speech empty'>Pending transcription\u2026</div>"
        badge   = "<span class='md-badge md-pd'>Pending</span>"
    elif err == "file_missing":
        tx_html = "<div class='tx-speech empty'>File missing</div>"
        badge   = "<span class='md-badge md-er'>Error</span>"
    elif text:
        conf_val = r["confidence"]
        conf_s   = f" {int(conf_val*100)}%" if conf_val else ""
        tx_html  = f"<div class='tx-speech'>{text}</div>"
        if "nova" in model:       badge = f"<span class='md-badge md-dg'>Deepgram{conf_s}</span>"
        elif "whisper" in model:  badge = f"<span class='md-badge md-wh'>Whisper{conf_s}</span>"
        else:                     badge = f"<span class='md-badge md-pd'>{model}</span>"
    else:
        tx_html = "<div class='tx-speech empty'>No speech detected</div>"
        badge   = "<span class='md-badge md-ns'>No speech</span>"
    rid       = r['id']
    tm        = fmt_time(r['begin_date'])
    dat       = fmt_date(r['begin_date'])
    map_title = label + " \u2014 " + dat + " " + tm
    map_tj    = map_title.replace("'", "\\'")
    fresh_cls = " fresh" if fresh else ""
    pending_attr = " data-pending='1'" if (tr_id is None or not text) else ""
    audio_html = (
        f"<button class='btn-play' onclick='loadAudio(this,{rid})'>&#9654;</button>"
        f"<span id='ap{rid}'></span>"
    ) if (tr_id is not None and err != "file_missing") else ""
    map_btn = f"<button class='btn-map' onclick='showMap({rid},\"{map_tj}\")'>radar</button>"
    return (
        f"<div class='tx-card{fresh_cls}' data-t='{data_t}'{pending_attr} data-id='{rid}'>"
        f"<div class='tx-stripe' style='background:{stripe_color}'></div>"
        f"<div class='tx-time'>"
        f"<div class='tx-tm'>{tm}</div>"
        f"<div class='tx-dt'>{dat}</div>"
        f"<div class='tx-dur'>{dur}</div></div>"
        f"{freq_html}"
        f"<div class='tx-body'>{tx_html}"
        f"<div class='tx-meta'>{badge}{bars}</div></div>"
        f"<div class='tx-actions'>{audio_html}{map_btn}</div>"
        f"</div>")


# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg-void:#050508;--bg-deep:#080810;--bg-panel:#0c0c16;--bg-card:#10101e;
  --bg-lift:#161628;--border:#1e1e38;--border-hi:#2a2a50;
  --text-hi:#f0f0ff;--text-mid:#7878a8;--text-lo:#2e2e50;
  --yellow:#f5c518;--cyan:#22d3ee;--blue:#3b82f6;--green:#22c55e;
  --orange:#f97316;--red:#ef4444;--purple:#a855f7;--pink:#ec4899;
}
html.light{
  --bg-void:#f0f2f5;--bg-deep:#e4e8ee;--bg-panel:#f8f8fb;--bg-card:#eef0f4;
  --bg-lift:#e4e6ec;--border:#c8cad4;--border-hi:#a8aabb;
  --text-hi:#0c0c20;--text-mid:#50507a;--text-lo:#9090a8;
}
html.light body{background:var(--bg-void);color:var(--text-hi)}
html.light .wx-text{color:#505070}
html.light .tx-card{background:var(--bg-card) !important}
html.light .tx-card:hover{background:var(--bg-lift) !important}
html.light .tx-card[data-t="twr"]{background:#dce8f8 !important}
html.light .tx-card[data-t="twr"]:hover{background:#ccdaee !important}
html.light .tx-card[data-t="app"]{background:#f8eddc !important}
html.light .tx-card[data-t="app"]:hover{background:#ede0ca !important}
html.light .tx-card[data-t="arr"]{background:#f8f0dc !important}
html.light .tx-card[data-t="dep"]{background:#eeddf8 !important}
html.light .tx-card[data-t="emer"]{background:#f8dcdc !important}
html.light .feed-hdr{background:var(--bg-panel)}
html.light .feed-scroll .tx-speech{color:var(--text-hi)}
html.light .search-mini input{background:var(--bg-card);color:var(--text-hi)}
html,body{height:100%;overflow:hidden;font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;
  background:var(--bg-void);color:var(--text-hi);font-size:13px;line-height:1.5}

/* ── TOPBAR ── */
.topbar{height:56px;display:flex;align-items:center;justify-content:space-between;
  padding:0 18px;background:var(--bg-deep);border-bottom:1px solid var(--border);
  position:relative;z-index:50;flex-shrink:0}
.tb-left{display:flex;align-items:center;gap:14px}
.logo{font-size:13px;font-weight:900;letter-spacing:.06em;color:var(--text-hi);
  display:flex;align-items:center;gap:8px}
.logo-badge{background:var(--yellow);color:#000;font-size:9px;font-weight:900;
  letter-spacing:.12em;padding:2px 6px;border-radius:4px}
.tb-sep{width:1px;height:24px;background:var(--border-hi)}
.tb-stat{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--text-mid)}
.tb-stat strong{color:var(--text-hi);font-weight:700}
.pulse-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.pd-green{background:var(--green);animation:blink 2s infinite}
.pd-yellow{background:var(--yellow)}
.pd-cyan{background:var(--cyan)}
.pd-red{background:var(--red);animation:none}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}
.tb-center{display:flex;align-items:baseline;gap:10px;font-family:ui-monospace,monospace}
.clk-local{font-size:16px;font-weight:800;color:var(--yellow);letter-spacing:.03em}
.clk-tag{font-size:9px;font-weight:700;letter-spacing:.1em;margin-left:2px}
.clk-tag-lcl{color:var(--yellow);opacity:.6}
.clk-tag-z{color:var(--cyan);opacity:.6}
.clk-sep{color:var(--text-lo);font-size:16px;font-weight:300;margin:0 2px}
.clk-zulu{font-size:16px;font-weight:800;color:var(--cyan);letter-spacing:.03em}
.clk-date{font-size:16px;font-weight:700;color:var(--text-mid);letter-spacing:.06em;
  margin-left:6px;padding-left:8px;border-left:1px solid var(--border-hi)}
.tb-right{display:flex;align-items:center;gap:12px}
.btn-tb{background:none;border:1px solid var(--border-hi);color:var(--text-mid);
  border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;cursor:pointer;
  letter-spacing:.04em;transition:all .15s;font-family:inherit}
.btn-tb:hover{background:var(--bg-lift);color:var(--text-hi)}
.btn-tb.on{background:var(--yellow);color:#000;border-color:var(--yellow)}
.sse-dot{width:7px;height:7px;border-radius:50%;background:var(--green);
  animation:blink 2s infinite;margin-right:4px;display:inline-block}
.sse-dot.off{background:var(--red);animation:none}

/* ── METAR STYLING (used in wx-bar rows) ── */
.metar-icao{font-size:11px;font-weight:800;letter-spacing:.08em;flex-shrink:0}
.metar-raw{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;line-height:1.6;flex:1}
.metar-div{width:1px;height:14px;background:var(--border-hi);flex-shrink:0}

/* ── WX LABELS & TEXT ── */
.wx-label{font-size:9px;font-weight:800;letter-spacing:.12em;flex-shrink:0;
  color:var(--text-lo);text-transform:uppercase}
.wx-text{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;
  color:#4b5563;line-height:1.6;flex:1}
.wx-notam-link{display:flex;align-items:center;gap:6px;flex-shrink:0;
  text-decoration:none;color:inherit}
.wx-notam-link:hover .wx-label{color:#94a3b8}
.wx-notam-link:hover .notam-badge{opacity:.8}
.notam-badge{background:#f97316;color:#fff;font-size:8px;font-weight:900;
  border-radius:3px;padding:1px 4px;letter-spacing:.04em;flex-shrink:0}
.notam-badge.zero{background:#1a1a2e;color:var(--text-lo)}
.wx-age{flex-shrink:0;font-size:9px;color:var(--text-lo);
  letter-spacing:.06em;margin-left:auto;padding-left:12px}

/* ── APP GRID ── */
.app{display:grid;grid-template-columns:min(750px, 1fr) 360px;grid-template-rows:1fr 196px;
  height:calc(100vh - 112px)}

/* ── WX-BAR (METAR -> TAF layout) ── */
.wx-bar{background:#06060f;border-bottom:1px solid var(--border);
  padding:4px 18px;display:flex;flex-direction:column;gap:4px;
  font-family:ui-monospace,monospace;font-size:10px;
  flex-shrink:0;min-height:auto;overflow:hidden;position:relative}
.wx-row{display:flex;align-items:center;gap:10px;min-height:24px}
.wx-row-metar{display:flex;align-items:baseline;gap:8px;flex:1;min-width:0}
.wx-row-taf{display:flex;align-items:baseline;gap:6px;flex:1;min-width:0}
.wx-sep{width:1px;height:14px;background:var(--border);flex-shrink:0}

/* ── FEED PANEL ── */
.feed-panel{grid-row:1/2;grid-column:1/2;display:flex;flex-direction:column;
  border-right:1px solid var(--border);overflow:hidden}

.feed-hdr{padding:9px 16px 8px;border-bottom:1px solid var(--border);
  background:var(--bg-panel);flex-shrink:0}
.feed-hdr-row{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}
.feed-label{font-size:8px;font-weight:800;letter-spacing:.22em;color:var(--text-lo);
  text-transform:uppercase;margin-bottom:6px}
.pill-row{display:flex;gap:4px;flex-wrap:wrap}
.pill{padding:3px 10px;border-radius:20px;font-size:10px;font-weight:700;
  letter-spacing:.06em;border:1px solid transparent;cursor:pointer;
  transition:all .15s;white-space:nowrap;background:none}
.pill.active,.pill:hover{opacity:1}
.pill-all   {color:#000;background:var(--yellow);border-color:var(--yellow)}
.pill-twr   {color:var(--blue);border-color:#1e3070;background:#0a1228}
.pill-app   {color:var(--orange);border-color:#3a2010;background:#160c04}
.pill-arr   {color:#f59e0b;border-color:#33280f;background:#130f04}
.pill-dep   {color:var(--purple);border-color:#2e1a55;background:#110820}
.pill-gnd   {color:#71717a;border-color:#252528;background:#101012}
.pill-atis  {color:var(--green);border-color:#0a2e14;background:#030e06}
.pill-emer  {color:var(--red);border-color:#3d1010;background:#160404}
.pill-acc   {color:var(--yellow);border-color:#332800;background:#130f00}
.pill-marine{color:#0ea5e9;border-color:#082438;background:#030d16}
.pill-pmr   {color:#84cc16;border-color:#1e3004;background:#0a1200}
.pill-ham   {color:#fb923c;border-color:#3a1e08;background:#140900}
.pill-toggle{color:var(--text-lo);border-color:var(--border);background:transparent}
.pill-toggle.active{color:var(--yellow);border-color:var(--yellow);background:transparent}
.tx-card[data-pending="1"]{display:none}
.search-mini{display:flex;gap:5px}
.search-mini input{background:var(--bg-card);border:1px solid var(--border);color:var(--text-hi);
  padding:4px 8px;border-radius:7px;font-size:11px;outline:none;font-family:inherit;width:140px;
  transition:border-color .15s}
.search-mini input:focus{border-color:var(--yellow)}
.search-mini input::placeholder{color:var(--text-lo)}
.btn-search{background:var(--yellow);border:none;color:#000;padding:4px 10px;
  border-radius:7px;cursor:pointer;font-size:11px;font-weight:800;font-family:inherit}

/* ── FEED SCROLL ── */
.feed-scroll{flex:1;overflow-y:auto;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.feed-scroll::-webkit-scrollbar{width:3px}
.feed-scroll::-webkit-scrollbar-thumb{background:var(--border-hi);border-radius:3px}

/* ── TX CARD ── */
.tx-card{display:grid;grid-template-columns:4px 80px 86px 1fr auto;
  align-items:stretch;border-bottom:1px solid var(--border);
  transition:background .1s;min-height:60px;cursor:default}
.tx-card:hover{background:rgba(255,255,255,.02)}
.tx-card.fresh{animation:fadein .4s ease}
@keyframes fadein{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:none}}
.tx-card[data-t="twr"]{background:#07101e}.tx-card[data-t="twr"]:hover{background:#0c1830}
.tx-card[data-t="app"]{background:#120d07}.tx-card[data-t="app"]:hover{background:#1c1308}
.tx-card[data-t="arr"]{background:#100e04}.tx-card[data-t="arr"]:hover{background:#181405}
.tx-card[data-t="dep"]{background:#0e081e}.tx-card[data-t="dep"]:hover{background:#160d30}
.tx-card[data-t="emer"]{background:#140505}.tx-card[data-t="emer"]:hover{background:#200808}
.tx-stripe{border-radius:0}
/* time */
.tx-time{padding:11px 9px;display:flex;flex-direction:column;justify-content:center;
  border-right:1px solid var(--border)}
.tx-tm{font-family:ui-monospace,monospace;font-size:11.5px;color:var(--text-hi);
  font-weight:600;letter-spacing:.02em;white-space:nowrap}
.tx-dt{font-size:9px;color:var(--text-lo);font-family:ui-monospace,monospace}
.tx-dur{font-size:10px;color:var(--yellow);font-family:ui-monospace,monospace;margin-top:1px}
/* freq */
.tx-freq{padding:9px 9px;display:flex;flex-direction:column;justify-content:center;
  border-right:1px solid var(--border);min-width:0}
.tx-mhz{font-size:14px;font-weight:800;font-family:ui-monospace,monospace;
  color:var(--text-hi);letter-spacing:-.01em;white-space:nowrap}
.tx-badge{display:inline-block;font-size:8px;font-weight:800;letter-spacing:.1em;
  padding:1px 5px;border-radius:3px;margin-top:3px;text-transform:uppercase}
.tx-fname{font-size:9px;color:var(--text-lo);margin-top:1px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* transcript hero */
.tx-body{padding:11px 14px;display:flex;flex-direction:column;justify-content:center;gap:4px}
.tx-speech{font-size:14.5px;line-height:1.55;color:var(--text-hi);font-weight:500}
.tx-speech.empty{font-size:11.5px;color:var(--text-lo);font-style:italic;font-weight:400}
.tx-meta{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.md-badge{font-size:8.5px;font-weight:700;letter-spacing:.08em;padding:2px 7px;
  border-radius:4px;text-transform:uppercase}
.md-dg{background:#021808;color:var(--green);border:1px solid #083018}
.md-wh{background:#020e18;color:var(--cyan);border:1px solid #051e30}
.md-pd{background:var(--bg-lift);color:var(--text-lo);border:1px solid var(--border)}
.md-ns{background:var(--bg-lift);color:var(--text-lo);border:1px solid var(--border)}
.md-er{background:#140404;color:var(--red);border:1px solid #280808}
/* confidence bar */
.cbar{display:flex;gap:2px;align-items:center}
.cs{display:inline-block;width:14px;height:3px;border-radius:2px;background:var(--border-hi)}
.cs.on{background:var(--yellow)}
/* actions */
.tx-actions{padding:9px 10px;display:flex;align-items:center;gap:5px;flex-shrink:0}
.tx-new{width:6px;height:6px;border-radius:50%;background:var(--green);
  animation:blink 2s infinite;flex-shrink:0;margin-bottom:2px}
.btn-play{width:28px;height:28px;border-radius:50%;background:var(--bg-lift);
  border:1px solid var(--border-hi);color:var(--text-hi);cursor:pointer;font-size:9px;
  display:inline-flex;align-items:center;justify-content:center;
  flex-shrink:0;transition:all .15s}
.btn-play:hover{background:var(--yellow);border-color:var(--yellow);color:#000}
.btn-play:disabled{opacity:.2;cursor:default}
audio{height:24px;margin-left:4px;vertical-align:middle}
.btn-map{background:none;border:1px solid var(--border-hi);color:var(--cyan);
  border-radius:6px;padding:3px 7px;cursor:pointer;font-size:9.5px;
  white-space:nowrap;transition:all .15s;font-family:inherit;font-weight:600}
.btn-map:hover{background:#041018;border-color:var(--cyan)}

/* ── PAGINATION ── */
.pag{padding:12px 16px;display:flex;align-items:center;gap:5px;justify-content:center;
  border-top:1px solid var(--border);background:var(--bg-panel);flex-shrink:0}
.pag a{color:var(--text-mid);text-decoration:none;padding:3px 9px;border:1px solid var(--border);
  border-radius:7px;font-size:11px;transition:all .15s}
.pag a:hover{background:var(--bg-lift);color:var(--text-hi)}
.pag .cur{background:var(--yellow);color:#000;padding:3px 9px;border-radius:7px;
  font-size:11px;font-weight:800;border:none}
.pag .info{color:var(--text-lo);font-size:10px}

/* ── ADS-B PANEL ── */
.adsb-panel{grid-row:1/2;grid-column:2/3;display:flex;flex-direction:column;
  overflow:hidden;background:var(--bg-panel)}
.panel-hdr{padding:9px 14px 8px;border-bottom:1px solid var(--border);flex-shrink:0;
  display:flex;align-items:center;justify-content:space-between}
.panel-title{font-size:8px;font-weight:800;letter-spacing:.22em;color:var(--text-lo);
  text-transform:uppercase}
.panel-live{display:flex;align-items:center;gap:5px;font-size:9px;
  font-weight:700;color:var(--green);letter-spacing:.08em}
.radar-wrap{flex-shrink:0;border-bottom:1px solid var(--border);
  background:#05050a;overflow:hidden;height:360px}
.radar-wrap iframe{width:100%;height:100%;border:none;display:block}
.ac-list{flex:1;overflow-y:auto;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.ac-list::-webkit-scrollbar{width:3px}
.ac-list::-webkit-scrollbar-thumb{background:var(--border-hi);border-radius:3px}
.ac-hdr,.ac-row{display:grid;
  grid-template-columns:22px 64px 1fr 36px 44px 62px 42px 46px;
  align-items:center;column-gap:0;padding:4px 10px;border-bottom:1px solid var(--border)}
.ac-hdr{background:var(--bg-deep);position:sticky;top:0;z-index:1}
.ac-hdr span{font-size:7.5px;font-weight:800;letter-spacing:.12em;color:var(--text-lo);
  text-transform:uppercase;text-align:right;padding:0 2px;white-space:nowrap}
.ac-hdr span:nth-child(-n+3){text-align:left}
.ac-row{transition:background .1s;cursor:default}
.ac-row:hover{background:var(--bg-lift)}
.ac-linked{background:#080f1a}.ac-linked:hover{background:#0e1828}
.ac-flag{font-size:13px;line-height:1}
.ac-flight{font-size:11px;font-weight:700;color:var(--text-hi);
  font-family:ui-monospace,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ac-route{font-size:9px;color:var(--text-mid);font-family:ui-monospace,monospace;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:4px}
.ac-type{font-size:8px;font-weight:700;color:#94a3b8;background:var(--bg-lift);
  border:1px solid var(--border);border-radius:3px;padding:1px 3px;letter-spacing:.04em;
  text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ac-sqk{font-size:9.5px;font-family:ui-monospace,monospace;color:var(--text-mid);
  text-align:right;padding-right:2px}
.ac-alt{font-size:10px;font-weight:700;font-family:ui-monospace,monospace;
  text-align:right;padding-right:2px}
.ac-gs{font-size:9.5px;font-family:ui-monospace,monospace;color:var(--text-mid);
  text-align:right;padding-right:2px}
.ac-dist{font-size:9.5px;font-family:ui-monospace,monospace;color:var(--text-mid);
  text-align:right}
.ac-freq-tag{display:inline-block;font-size:8px;font-weight:700;padding:1px 5px;
  border-radius:3px;margin-top:2px;letter-spacing:.05em}
.ac-more{padding:5px 10px;font-size:9.5px;color:var(--text-lo);
  border-top:1px solid var(--border)}

/* ── ANALYTICS STRIP ── */
.analytics-strip{grid-row:2/3;grid-column:1/3;display:grid;
  grid-template-columns:1fr 1fr 1fr 300px;border-top:1px solid var(--border);
  background:var(--bg-deep);overflow:hidden}
.ab{padding:10px 14px;border-right:1px solid var(--border);
  display:flex;flex-direction:column;overflow:hidden}
.ab-title{font-size:8px;font-weight:800;letter-spacing:.2em;color:var(--text-lo);
  text-transform:uppercase;margin-bottom:6px;flex-shrink:0}
/* freq bars */
.fb-row{display:flex;align-items:center;gap:7px;margin-bottom:4px}
.fb-lbl{font-size:9.5px;color:var(--text-mid);width:88px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;flex-shrink:0}
.fb-track{flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden}
.fb-fill{height:100%;border-radius:2px;transition:width .4s}
.fb-cnt{font-size:9.5px;color:var(--text-lo);font-family:ui-monospace,monospace;
  width:30px;text-align:right;flex-shrink:0}
/* donut */
.donut-row{display:flex;align-items:center;gap:10px;flex:1}
.donut-legend{display:flex;flex-direction:column;gap:3px;flex:1;min-width:0}
.dl{display:flex;align-items:center;gap:5px;font-size:9.5px}
.dl-dot{width:7px;height:7px;border-radius:2px;flex-shrink:0}
.dl-lbl{color:var(--text-mid);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dl-pct{color:var(--yellow);font-weight:700;font-family:ui-monospace,monospace;
  width:26px;text-align:right;flex-shrink:0}
/* kpi block */
.kpi-block{padding:8px 12px;display:grid;grid-template-columns:1fr 1fr;gap:5px;align-content:start}
.kpi{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;
  padding:7px 9px;position:relative;overflow:hidden}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:var(--ka,var(--border));border-radius:2px 2px 0 0}
.kpi-lbl{font-size:7.5px;font-weight:700;letter-spacing:.14em;color:var(--text-lo);
  text-transform:uppercase;margin-bottom:3px}
.kpi-val{font-size:16px;font-weight:800;font-family:ui-monospace,monospace;
  line-height:1;font-variant-numeric:tabular-nums}
.kpi-sub{font-size:8.5px;color:var(--text-lo);margin-top:2px}
.kv-y{color:var(--yellow)}.kv-c{color:var(--cyan)}.kv-g{color:var(--green)}
.kv-r{color:var(--red)}.kv-b{color:var(--blue)}.kv-o{color:var(--orange)}

/* ── MAP MODAL ── */
#mapModal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);
  z-index:200;align-items:center;justify-content:center}
#mapModal.open{display:flex}
#mapBox{background:var(--bg-card);border:1px solid var(--border-hi);
  border-radius:12px;padding:14px;max-width:96vw}
#mapHeader{display:flex;justify-content:space-between;align-items:center;
  margin-bottom:10px;gap:20px}
#mapTitle{color:var(--text-hi);font-size:.85rem;font-weight:700}
#mapClose{background:none;border:none;color:var(--text-mid);font-size:1.3rem;
  cursor:pointer;line-height:1}
#mapClose:hover{color:var(--text-hi)}

/* ── RESPONSIVE ── */
@media(max-width:960px){
  .app{grid-template-columns:1fr;grid-template-rows:auto auto auto}
  .adsb-panel{grid-row:2;grid-column:1;max-height:300px}
  .analytics-strip{grid-row:3;grid-column:1;grid-template-columns:1fr 1fr}
  html,body{overflow:auto}.app{height:auto}
}
@media(max-width:600px){
  .analytics-strip{grid-template-columns:1fr}
  .tx-card{grid-template-columns:4px 70px 1fr auto}
  .tx-freq{display:none}
}
"""

# ── JS ────────────────────────────────────────────────────────────────────────
JS = r"""
// ── Theme toggle (persisted via localStorage) ──────────────────────────────
(function(){if(localStorage.getItem('theme')==='light')document.documentElement.classList.add('light');})();
function toggleTheme(){
  var light=document.documentElement.classList.toggle('light');
  localStorage.setItem('theme',light?'light':'dark');
  var btn=document.getElementById('themeBtn');
  if(btn)btn.textContent=light?'●':'◐';
}

(function(){
  var _ADSB_BASE = window.ADSB_BASE || 'http://192.168.1.188:8080';

  // ── Dual clock (LOCAL + ZULU) ────────────────────────────────────────────
  var _months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  var _days   = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
  function tickClocks(){
    var now = new Date();
    var zH=now.getUTCHours(),zM=now.getUTCMinutes(),zS=now.getUTCSeconds();
    var zStr=('0'+zH).slice(-2)+':'+('0'+zM).slice(-2)+':'+('0'+zS).slice(-2);
    try{
      var loc=now.toLocaleTimeString('en-GB',{timeZone:'Europe/Brussels',hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'});
      var dP=now.toLocaleDateString('en-GB',{timeZone:'Europe/Brussels',day:'2-digit',month:'2-digit',year:'numeric'}).split('/');
      var dow=now.toLocaleDateString('en-GB',{timeZone:'Europe/Brussels',weekday:'short'}).substring(0,3).toUpperCase();
      var dateStr=dow+' '+dP[0]+' '+_months[parseInt(dP[1])-1]+' '+dP[2];
    }catch(e){var loc=zStr;var dateStr='';}
    var e1=document.getElementById('clkLocal');if(e1)e1.textContent=loc;
    var e2=document.getElementById('clkZulu');if(e2)e2.textContent=zStr;
    var e3=document.getElementById('clkDate');if(e3)e3.textContent=dateStr;
  }
  setInterval(tickClocks,1000);tickClocks();

  // ── SSE live feed ──────────────────────────────────────────────────────────
  var _lastId=parseInt(document.querySelector('.feed-scroll')?.dataset?.lastId||'0');
  var _sseDot=document.getElementById('sseDot');
  function connectSSE(){
    var es=new EventSource('/stream?last_id='+_lastId);
    es.onopen=function(){if(_sseDot)_sseDot.className='sse-dot';};
    es.onerror=function(){if(_sseDot)_sseDot.className='sse-dot off';};
    es.onmessage=function(ev){
      try{
        var d=JSON.parse(ev.data);
        _lastId=d.id;
        var feed=document.querySelector('.feed-scroll');
        if(!feed)return;
        var tmp=document.createElement('template');
        tmp.innerHTML=d.html;
        var card=tmp.content.firstChild;
        var t=card.dataset.t||'';
        var isPending=card.dataset.pending==='1';
        var typeOk=(_activeType==='all'||t===_activeType);
        var show=typeOk&&(!isPending||_showPending);
        if(show){card.style.display=isPending?'grid':'';}
        else{card.style.display='none';}
        feed.insertBefore(card,feed.firstChild);
        var cnt=document.getElementById('tbTX');
        if(cnt){var n=parseInt(cnt.textContent.replace(/,/g,''))||0;cnt.textContent=(n+1).toLocaleString();}
      }catch(e){}
    };
    return es;
  }
  var _es=null;
  if(_lastId>0)_es=connectSSE();

  // ── Frequency type pill filter (client-side) ──────────────────────────────
  var _activeType = 'all';
  var _showPending = false;

  function applyFilters(){
    document.querySelectorAll('.tx-card').forEach(function(card){
      var t = card.dataset.t || '';
      var isPending = card.dataset.pending === '1';
      var typeOk = (_activeType === 'all' || t === _activeType);
      var show = typeOk && (!isPending || _showPending);
      if(show){ card.style.display = isPending ? 'grid' : ''; }
      else    { card.style.display = 'none'; }
    });
  }

  window.filterType = function(type, el){
    _activeType = type;
    document.querySelectorAll('.pill:not(.pill-toggle)').forEach(function(p){ p.classList.remove('active'); });
    if(el) el.classList.add('active');
    applyFilters();
  };

  window.togglePending = function(el){
    _showPending = !_showPending;
    el.classList.toggle('active', _showPending);
    applyFilters();
  };

  // ── Aircraft list refresh ─────────────────────────────────────────────────
  function altColor(alt){
    if(alt===null||alt===undefined) return '#71717a';
    if(alt<3000) return '#ef4444';
    if(alt<10000) return '#fcbb00';
    if(alt<28000) return '#3b82f6';
    return '#52525b';
  }
  function fmtAlt(alt){
    if(alt===null||alt===undefined) return '\u2014';
    if(alt>=10000) return 'FL'+String(Math.round(alt/100)).padStart(3,'0');
    return alt.toLocaleString()+'ft';
  }
  function hexFlag(hex){
    try{
      var n=parseInt(hex,16);
      if(n>=0x300000&&n<=0x33FFFF) return '\uD83C\uDDEE\uD83C\uDDF9'; // IT
      if(n>=0x340000&&n<=0x37FFFF) return '\uD83C\uDDEA\uD83C\uDDF8'; // ES
      if(n>=0x380000&&n<=0x3BFFFF) return '\uD83C\uDDEB\uD83C\uDDF7'; // FR
      if(n>=0x3C0000&&n<=0x3FFFFF) return '\uD83C\uDDE9\uD83C\uDDEA'; // DE
      if(n>=0x400000&&n<=0x43FFFF) return '\uD83C\uDDEC\uD83C\uDDE7'; // GB
      if(n>=0x440000&&n<=0x447FFF) return '\uD83C\uDDE6\uD83C\uDDF9'; // AT
      if(n>=0x448000&&n<=0x44FFFF) return '\uD83C\uDDE7\uD83C\uDDEA'; // BE
      if(n>=0x450000&&n<=0x457FFF) return '\uD83C\uDDE7\uD83C\uDDEC'; // BG
      if(n>=0x458000&&n<=0x45FFFF) return '\uD83C\uDDE9\uD83C\uDDF0'; // DK
      if(n>=0x460000&&n<=0x467FFF) return '\uD83C\uDDEB\uD83C\uDDEE'; // FI
      if(n>=0x468000&&n<=0x46FFFF) return '\uD83C\uDDEC\uD83C\uDDF7'; // GR
      if(n>=0x470000&&n<=0x477FFF) return '\uD83C\uDDED\uD83C\uDDFA'; // HU
      if(n>=0x480000&&n<=0x487FFF) return '\uD83C\uDDF3\uD83C\uDDF1'; // NL
      if(n>=0x488000&&n<=0x48FFFF) return '\uD83C\uDDE8\uD83C\uDDED'; // CH
      if(n>=0x490000&&n<=0x497FFF) return '\uD83C\uDDE8\uD83C\uDDFF'; // CZ
      if(n>=0x498000&&n<=0x49FFFF) return '\uD83C\uDDF5\uD83C\uDDF1'; // PL
      if(n>=0x4A8000&&n<=0x4AFFFF) return '\uD83C\uDDF8\uD83C\uDDEA'; // SE
      if(n>=0x4B0000&&n<=0x4B7FFF) return '\uD83C\uDDF3\uD83C\uDDF4'; // NO
      if(n>=0x700000&&n<=0x73FFFF) return '\uD83C\uDDE6\uD83C\uDDEA'; // AE
      if(n>=0xA00000&&n<=0xAFFFFF) return '\uD83C\uDDFA\uD83C\uDDF8'; // US
    }catch(e){}
    return '';
  }
  function renderAcList(aircraft){
    var el = document.getElementById('acList');
    if(!el) return;
    if(!aircraft||!aircraft.length){
      el.innerHTML='<div class="ac-more">No aircraft data</div>'; return;
    }
    var html='<div class="ac-hdr">'
      +'<span></span>'
      +'<span style="text-align:left">CALLSIGN</span>'
      +'<span style="text-align:left">ROUTE</span>'
      +'<span>TYPE</span><span>SQWK</span><span>ALT ft</span>'
      +'<span>SPD kt</span><span>DIST</span>'
      +'</div>';
    aircraft.slice(0,30).forEach(function(ac){
      var altCol=altColor(ac.alt);
      var flight=ac.flight||ac.hex||'?';
      var spd=ac.gs?Math.round(ac.gs):'';
      var dist=ac.dist_nmi?ac.dist_nmi+'nm':'';
      html+='<div class="ac-row">';
      html+='<div class="ac-flag">'+hexFlag(ac.hex)+'</div>';
      html+='<div class="ac-flight">'+flight+'</div>';
      html+='<div class="ac-route">'+(ac.r||'')+'</div>';
      html+='<div class="ac-type">'+(ac.t||'')+'</div>';
      html+='<div class="ac-sqk">'+(ac.squawk||'')+'</div>';
      html+='<div class="ac-alt" style="color:'+altCol+'">'+fmtAlt(ac.alt)+'</div>';
      html+='<div class="ac-gs">'+spd+'</div>';
      html+='<div class="ac-dist">'+dist+'</div>';
      html+='</div>';
    });
    if(aircraft.length>30) html+='<div class="ac-more">+'+(aircraft.length-30)+' more within 150km</div>';
    el.innerHTML=html;
  }
  function refreshAircraft(){
    fetch('/api/aircraft').then(function(r){return r.json();}).then(renderAcList).catch(function(){});
  }
  setTimeout(refreshAircraft, 800);
  setInterval(refreshAircraft, 30000);

  // ── KPI + badge refresh ───────────────────────────────────────────────────
  function sv(id,v){var e=document.getElementById(id);if(e)e.textContent=v;}
  function refreshStats(){
    fetch('/api/stats').then(function(r){return r.json();}).then(function(d){
      if(d.live_adsb){
        sv('kpiAC', d.live_adsb.with_pos);
        var dot=document.querySelector('.pd-green,.pd-red');
        if(dot){ dot.className='pulse-dot '+(d.live_adsb.online?'pd-green':'pd-red'); }
        var lbl=document.getElementById('liveLabel');
        if(lbl) lbl.textContent=d.live_adsb.online?'LIVE · '+d.live_adsb.with_pos+' AC':'OFFLINE';
      }
      if(d.db){
        sv('kpiTX', d.db.total.toLocaleString());
        sv('kpiDG', d.db.today_dg+'/500');
        var tbTX=document.getElementById('tbTX');
        if(tbTX) tbTX.textContent=d.db.total.toLocaleString();
      }
      if(d.sys){
        sv('kpiDisk', d.sys.disk_free_gb+'GB');
      }
    }).catch(function(){});
  }
  setInterval(refreshStats, 30000);

  // ── Audio ─────────────────────────────────────────────────────────────────
  window.loadAudio=function(btn,txId){
    btn.disabled=true;
    var wrap=document.getElementById('ap'+txId);
    var a=document.createElement('audio');
    a.controls=true; a.src='/audio/'+txId;
    wrap.appendChild(a); a.play().catch(function(){});
  };

  // ── Radar map modal ───────────────────────────────────────────────────────
  window.showMap=function(txId,title){
    document.getElementById('mapTitle').textContent=title;
    var c=document.getElementById('mapContent');
    c.innerHTML='<div style="color:var(--text-mid);padding:40px;text-align:center;font-size:.8rem">Loading\u2026</div>';
    document.getElementById('mapModal').classList.add('open');
    fetch('/map/'+txId).then(function(r){return r.text();})
      .then(function(s){c.innerHTML=s;})
      .catch(function(){c.innerHTML='<div style="color:var(--red);padding:20px">Failed to load</div>';});
  };
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape') document.getElementById('mapModal').classList.remove('open');
  });

  // ── METAR refresh every 10 min ────────────────────────────────────────────
  function refreshMetar(){
    fetch('/api/metar').then(function(r){return r.json();}).then(function(d){
      var ea=document.getElementById('metarEBAW');
      var eb=document.getElementById('metarEBBR');
      var ag=document.getElementById('metarAge');
      if(ea&&d.EBAW_HTML) ea.innerHTML=d.EBAW_HTML;
      if(eb&&d.EBBR_HTML) eb.innerHTML=d.EBBR_HTML;
      if(ag&&d.ts)        ag.textContent='MET '+d.ts+'Z';
    }).catch(function(){});
  }
  setInterval(refreshMetar, 600000);

  // ── TAF refresh every 30 min ──────────────────────────────────────────────
  function refreshTaf(){
    fetch('/api/taf').then(function(r){return r.json();}).then(function(d){
      var ea=document.getElementById('tafEBAW');
      var eb=document.getElementById('tafEBBR');
      if(ea&&d.EBAW) ea.textContent=d.EBAW;
      if(eb&&d.EBBR) eb.textContent=d.EBBR;
    }).catch(function(){});
  }
  setInterval(refreshTaf, 1800000);

  // ── NOTAM badge refresh every 60 min ─────────────────────────────────────
  function refreshNotam(){
    fetch('/api/notam').then(function(r){return r.json();}).then(function(d){
      var badge=document.getElementById('notamBadge');
      var age  =document.getElementById('wxAge');
      if(badge){
        badge.textContent=d.total;
        badge.className='notam-badge'+(d.total>0?'':' zero');
      }
      if(age&&d.ts) age.textContent='WX '+d.ts+'Z';
    }).catch(function(){});
  }
  setInterval(refreshNotam, 3600000);

})();
"""


# ── HTTP Handler ──────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, format, *args): pass

    def do_GET(self):
        parsed = urlparse(self.path)
        p, qs  = parsed.path, parse_qs(parsed.query)
        if   p == "/":                self.serve_html(qs)
        elif p == "/stream":          self.serve_stream(qs)
        elif p == "/api/stats":       self.serve_api_stats()
        elif p == "/api/metar":       self.serve_api_metar()
        elif p == "/api/taf":         self.serve_api_taf()
        elif p == "/api/notam":       self.serve_api_notam()
        elif p == "/api/adsb_stats":  self._json(get_adsb_stats())
        elif p == "/api/aircraft":    self._json(get_aircraft_list())
        elif p == "/radar.svg":       self.serve_radar_svg()
        elif p.startswith("/audio/"):
            try:   self.serve_audio(int(p.split("/")[2]))
            except: self.send_error(400)
        elif p.startswith("/map/"):
            try:   self.serve_map(int(p.split("/")[2]))
            except: self.send_error(400)
        elif p == "/favicon.ico": self.send_response(204); self.end_headers()
        else: self.send_error(404)

    def _json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers(); self.wfile.write(body)

    def _svg(self, svg_str, maxage=30):
        body = svg_str.encode()
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", f"public, max-age={maxage}")
        self.end_headers(); self.wfile.write(body)

    def serve_radar_svg(self):
        self._svg(generate_live_radar_svg(), maxage=25)

    def serve_api_stats(self):
        conn = get_db(); db = get_db_stats(conn); conn.close()
        self._json({'db': db, 'sys': get_sys_stats(), 'uptime': get_uptime(), 'live_adsb': get_live_adsb()})

    def serve_api_metar(self):
        m = get_metar()
        self._json({
            'EBAW':      m.get('EBAW', ''),
            'EBBR':      m.get('EBBR', ''),
            'EBAW_HTML': colorize_metar(m.get('EBAW', '')),
            'EBBR_HTML': colorize_metar(m.get('EBBR', '')),
            'ts':        m.get('ts', '--:--'),
        })

    def serve_api_taf(self):
        t = get_taf()
        self._json({'EBAW': t.get('EBAW',''), 'EBBR': t.get('EBBR',''),
                    'ts': t.get('ts','--:--')})

    def serve_api_notam(self):
        n = get_notam()
        self._json({'EBAW': n.get('EBAW',[]), 'EBBR': n.get('EBBR',[]),
                    'total': n.get('total',0), 'ts': n.get('ts','--:--')})

    def serve_stream(self, qs):
        """SSE endpoint — pushes new transmissions in real-time."""
        last_id = int(qs.get("last_id", ["0"])[0])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        _atis_excl = " AND ".join(
            f"ABS((t.begin_frequency+t.end_frequency)/2.0-{int(f*1e6)})>=15000"
            for f in ATIS_FREQS)
        tick = 0
        try:
            while True:
                try:
                    conn = get_db()
                    rows = conn.execute(
                        f"SELECT t.id,t.begin_frequency,t.end_frequency,t.begin_date,t.end_date,"
                        f"tr.id as tr_id,tr.text,tr.model,tr.confidence,tr.error "
                        f"FROM sdr_transmission t "
                        f"LEFT JOIN sdr_group g ON g.id=t.group_id "
                        f"LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id "
                        f"WHERE t.id > ? AND t.data_file IS NOT NULL AND g.modulation='AM' "
                        f"AND (JULIANDAY(t.end_date)-JULIANDAY(t.begin_date))*86400 >= 1 "
                        f"AND ({_atis_excl}) "
                        f"ORDER BY t.id ASC LIMIT 20", (last_id,)
                    ).fetchall()
                    conn.close()
                    for r in rows:
                        card = build_card_html(dict(r), fresh=True)
                        data = json.dumps({"id": r["id"], "html": card})
                        self.wfile.write(f"data: {data}\n\n".encode())
                        self.wfile.flush()
                        last_id = r["id"]
                except Exception:
                    pass
                tick += 1
                if tick % 6 == 0:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                time.sleep(5)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def serve_audio(self, tx_id):
        conn = get_db()
        row  = conn.execute(
            "SELECT begin_frequency,end_frequency,data_file FROM sdr_transmission WHERE id=?", (tx_id,)
        ).fetchone(); conn.close()
        if not row or not row["data_file"]: return self.send_error(404)
        fp = os.path.join(DATA_ROOT, row["data_file"])
        if not os.path.exists(fp): return self.send_error(404)
        wav = decode_cu8_to_wav(fp, row["end_frequency"]-row["begin_frequency"])
        if not wav: return self.send_error(500)
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(wav)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers(); self.wfile.write(wav)

    def serve_map(self, tx_id):
        conn = get_db()
        row  = conn.execute(
            "SELECT t.begin_frequency,t.end_frequency,t.begin_date,t.end_date,tr.text "
            "FROM sdr_transmission t "
            "LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id WHERE t.id=?", (tx_id,)
        ).fetchone(); conn.close()
        if not row: return self.send_error(404)
        fc  = (row["begin_frequency"]+row["end_frequency"])/2
        svg = generate_map_svg(tx_id, row["begin_date"], row["end_date"],
                               freq_label(fc), freq_hz=fc, text=row["text"])
        self._svg(svg, maxage=60)

    def serve_html(self, qs):
        page     = max(1, int(qs.get("page", ["1"])[0]))
        search   = qs.get("q",    [""])[0].strip()
        freq_f   = qs.get("freq", [""])[0].strip()
        speech_o = qs.get("speech",       [""])[0] == "1"
        hp       = qs.get("hide_pending", [""])[0] == "1"
        per_page = 50
        offset   = (page-1)*per_page

        # SQL: exclude ATIS + sub-1s transmissions
        _atis_excl = " AND ".join(
            f"ABS((t.begin_frequency+t.end_frequency)/2.0-{int(f*1e6)})>=15000"
            for f in ATIS_FREQS)
        where = [
            "t.data_file IS NOT NULL",
            "g.modulation='AM'",
            "(JULIANDAY(t.end_date)-JULIANDAY(t.begin_date))*86400 >= 1",
            f"({_atis_excl})",
        ]
        params = []
        if search:
            where.append("tr.text LIKE ?"); params.append(f"%{search}%")
        if freq_f:
            try:
                where.append("abs((t.begin_frequency+t.end_frequency)/2.0-?)<20000")
                params.append(float(freq_f)*1e6)
            except: pass
        if speech_o: where.append("tr.text IS NOT NULL AND tr.text!=''")
        if hp:       where.append("tr.id IS NOT NULL")
        w_sql = " AND ".join(where)

        conn        = get_db()
        db_stats    = get_db_stats(conn)
        rows        = conn.execute(
            f"SELECT t.id,t.begin_frequency,t.end_frequency,t.begin_date,t.end_date,"
            f"tr.id as tr_id,tr.text,tr.model,tr.confidence,tr.error "
            f"FROM sdr_transmission t "
            f"LEFT JOIN sdr_group g ON g.id=t.group_id "
            f"LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id "
            f"WHERE {w_sql} ORDER BY t.id DESC LIMIT ? OFFSET ?",
            params+[per_page, offset]
        ).fetchall()
        total_count = conn.execute(
            f"SELECT COUNT(*) FROM sdr_transmission t "
            f"LEFT JOIN sdr_group g ON g.id=t.group_id "
            f"LEFT JOIN sdr_transcript tr ON tr.transmission_id=t.id WHERE {w_sql}", params
        ).fetchone()[0]
        conn.close()

        live_adsb  = get_live_adsb()
        freq_stats = get_freq_stats()
        hourly     = get_hourly_data()
        sys_s      = get_sys_stats()
        uptime     = get_uptime()
        total_pages= max(1, math.ceil(total_count/per_page))
        aircraft   = get_aircraft_list()
        _metar     = get_metar()
        metar_ebaw = colorize_metar(_metar.get('EBAW', ''))
        metar_ebbr = colorize_metar(_metar.get('EBBR', ''))
        metar_ts   = _metar.get('ts', '--:--')
        milbar_ebaw = mil_bar_html(mil_color_state(_metar.get('EBAW', '')))
        milbar_ebbr = mil_bar_html(mil_color_state(_metar.get('EBBR', '')))

        _taf          = get_taf()
        taf_ebaw      = _he.escape(_taf.get('EBAW', 'N/A'))
        taf_ebbr      = _he.escape(_taf.get('EBBR', 'N/A'))
        tafbar_ebaw   = mil_bar_html(taf_base_mil_state(_taf.get('EBAW', '')))
        tafbar_ebbr   = mil_bar_html(taf_base_mil_state(_taf.get('EBBR', '')))

        _notam        = get_notam()
        notam_total   = _notam.get('total', 0)
        notam_badge_c = '' if notam_total > 0 else ' zero'
        notam_ts      = _notam.get('ts', '--:--')

        # ── Build TX cards ───────────────────────────────────────────────────
        cards_html = ""
        first_id   = rows[0]['id'] if rows else 0
        for idx, r in enumerate(rows):
            cards_html += build_card_html(dict(r), fresh=(page == 1 and idx == 0))

        # ── Pagination ───────────────────────────────────────────────────────
        qb = f"&q={search}&freq={freq_f}{'&speech=1' if speech_o else ''}{'&hide_pending=1' if hp else ''}"
        pag = "<div class='pag'>"
        if page > 1:
            pag += f"<a href='/?page=1{qb}'>&laquo;&laquo;</a>"
            pag += f"<a href='/?page={page-1}{qb}'>&laquo;</a>"
        pag += f"<span class='cur'>{page}</span>"
        if page < total_pages:
            pag += f"<a href='/?page={page+1}{qb}'>&raquo;</a>"
            pag += f"<a href='/?page={total_pages}{qb}'>&raquo;&raquo;</a>"
        pag += f"<span class='info'>{total_count:,} transmissions</span></div>"

        # ── Topbar stats ─────────────────────────────────────────────────────
        dot_cls  = "pd-green" if live_adsb['online'] else "pd-red"
        live_lbl = f"LIVE &middot; {live_adsb['with_pos']} AC" if live_adsb['online'] else "OFFLINE"
        dg_count = db_stats['today_dg']

        # ── ADS-B panel ──────────────────────────────────────────────────────
        ac_rows_html = (
            "<div class='ac-hdr'>"
            "<span></span>"
            "<span style='text-align:left'>CALLSIGN</span>"
            "<span style='text-align:left'>ROUTE</span>"
            "<span>TYPE</span><span>SQWK</span><span>ALT ft</span>"
            "<span>SPD kt</span><span>DIST</span>"
            "</div>"
        )
        for ac in aircraft[:30]:
            color    = _alt_color(ac['alt'])
            flight   = _he.escape(ac['flight'] or ac['hex'] or '?')
            alt      = ac['alt']
            alt_str  = (f"FL{alt//100:03d}" if alt >= 10000 else f"{alt:,}ft") if alt is not None else "—"
            gs_str   = str(int(ac['gs'])) if ac.get('gs') else ""
            sqk      = ac.get('squawk') or ''
            route    = _he.escape(ac.get('r') or '')
            type_str = _he.escape(ac.get('t') or '')
            dist_nmi = ac.get('dist_nmi', '')
            flag     = _icao_flag(ac.get('hex', ''))
            ac_rows_html += (
                f"<div class='ac-row'>"
                f"<div class='ac-flag'>{flag}</div>"
                f"<div class='ac-flight'>{flight}</div>"
                f"<div class='ac-route'>{route}</div>"
                f"<div class='ac-type'>{type_str}</div>"
                f"<div class='ac-sqk'>{sqk}</div>"
                f"<div class='ac-alt' style='color:{color}'>{alt_str}</div>"
                f"<div class='ac-gs'>{gs_str}</div>"
                f"<div class='ac-dist'>{dist_nmi}nm</div>"
                f"</div>"
            )
        if len(aircraft) > 30:
            ac_rows_html += f"<div class='ac-more'>+{len(aircraft)-30} more within 150km</div>"
        if not aircraft:
            ac_rows_html = "<div class='ac-more'>No aircraft data available</div>"

        # ── Frequency bars ───────────────────────────────────────────────────
        top_tx = freq_stats.get('top_tx', [])
        fb_max = max((r['count'] for r in top_tx), default=1)
        freq_bars_html = ""
        for i, r in enumerate(top_tx[:10]):
            info = freq_type_info(r['label'])
            col  = info[0]
            pct  = max(4, int(r['count'] * 100 / fb_max))
            freq_bars_html += (
                f"<div class='fb-row'>"
                f"<div class='fb-lbl' style='color:{col}'>{r['label']}</div>"
                f"<div class='fb-track'><div class='fb-fill' style='width:{pct}%;background:{col}'></div></div>"
                f"<div class='fb-cnt'>{r['count']:,}</div></div>"
            )

        # ── Donut chart ──────────────────────────────────────────────────────
        top_dec = freq_stats.get('top_dec', [])
        total_dec = sum(r['count'] for r in top_dec) or 1
        slices = [(r['count']/total_dec, CHART_COLORS[i % len(CHART_COLORS)]) for i, r in enumerate(top_dec[:8])]
        donut_svg = build_donut_svg(slices, size=100)
        donut_legend = ""
        for i, r in enumerate(top_dec[:8]):
            col = CHART_COLORS[i % len(CHART_COLORS)]
            pct = round(r['count'] * 100 / total_dec)
            donut_legend += (
                f"<div class='dl'><div class='dl-dot' style='background:{col}'></div>"
                f"<div class='dl-lbl'>{r['label']}</div>"
                f"<div class='dl-pct'>{pct}%</div></div>"
            )

        # ── Sparkline ────────────────────────────────────────────────────────
        spark_svg = build_sparkline_svg(hourly)

        # ── KPI cards ────────────────────────────────────────────────────────
        dg_cls  = "kv-r" if dg_count >= 490 else ("kv-o" if dg_count >= 400 else "kv-c")
        disk_cls= "kv-r" if sys_s.get('disk_used_pct',0)>85 else ("kv-o" if sys_s.get('disk_used_pct',0)>70 else "kv-g")
        ac_val  = f"<span id='kpiAC'>{live_adsb['with_pos']}</span>"
        dg_val  = f"<span id='kpiDG'>{dg_count}/500</span>"
        tx_val  = f"<span id='kpiTX'>{db_stats['total']:,}</span>"
        dsk_val = f"<span id='kpiDisk'>{sys_s.get('disk_free_gb',0)} GB</span>"
        kpi_html = (
            f"<div class='kpi' style='--ka:var(--yellow)'>"
            f"<div class='kpi-lbl'>Uptime</div>"
            f"<div class='kpi-val kv-y'>{uptime}</div>"
            f"<div class='kpi-sub'>server running</div></div>"

            f"<div class='kpi' style='--ka:var(--green)'>"
            f"<div class='kpi-lbl'>Aircraft</div>"
            f"<div class='kpi-val kv-g'>{ac_val}</div>"
            f"<div class='kpi-sub'>w/ position</div></div>"

            f"<div class='kpi' style='--ka:var(--cyan)'>"
            f"<div class='kpi-lbl'>Deepgram</div>"
            f"<div class='kpi-val {dg_cls}'>{dg_val}</div>"
            f"<div class='kpi-sub'>{500-dg_count} remaining</div></div>"

            f"<div class='kpi' style='--ka:var(--orange)'>"
            f"<div class='kpi-lbl'>Disk Free</div>"
            f"<div class='kpi-val {disk_cls}'>{dsk_val}</div>"
            f"<div class='kpi-sub'>{sys_s.get('disk_used_pct',0)}% used</div></div>"
        )

        # ── Assemble HTML ────────────────────────────────────────────────────
        html = f"""<!DOCTYPE html>
<html lang='en'><head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>STYTO ATC — EBAW/EBBR</title>
<style>{CSS}</style>
<script>window.ADSB_BASE='{ADSB_BASE}';</script>
</head><body>

<div class='topbar'>
  <div class='tb-left'>
    <div class='logo'>&#9992; STYTO ATC <span class='logo-badge'>EBAW&middot;EBBR</span></div>
    <div class='tb-sep'></div>
    <div class='tb-stat'>
      <div class='pulse-dot {dot_cls}'></div>
      <span id='liveLabel'>{live_lbl}</span>
    </div>
    <div class='tb-sep'></div>
    <div class='tb-stat'>
      <div id='sseDot' class='sse-dot'></div>
      <span><strong id='tbTX'>{db_stats['total']:,}</strong> TX</span>
    </div>
    <div class='tb-stat'>
      <span>DG <strong>{dg_count}</strong>/500</span>
    </div>
  </div>
  <div class='tb-center'>
    <span class='clk-local' id='clkLocal'>--:--:--</span><span class='clk-tag clk-tag-lcl'>LCL</span>
    <span class='clk-sep'>/</span>
    <span class='clk-zulu' id='clkZulu'>--:--:--</span><span class='clk-tag clk-tag-z'>Z</span>
    <span class='clk-date' id='clkDate'>-- --- ----</span>
  </div>
  <div class='tb-right'>
    <button class='btn-tb' id='themeBtn' onclick='toggleTheme()' title='Toggle dark / light'>◐</button>
    <a class='wx-notam-link' href='https://notams.aim.faa.gov/notamSearch/' target='_blank' rel='noopener' title='Open NOTAM search'>
      <span class='wx-label'>NOTAM</span>
      <span class='notam-badge{notam_badge_c}' id='notamBadge'>{notam_total}</span>
    </a>
  </div>
</div>

<div class='wx-bar'>
  <!-- Row 1: EBAW METAR + TAF -->
  <div class='wx-row'>
    <div class='wx-row-metar'>
      <span class='metar-icao' style='color:#3b82f6'>EBAW</span>
      {milbar_ebaw}
      <span class='metar-raw' id='metarEBAW'>{metar_ebaw}</span>
    </div>
    <div class='wx-sep'></div>
    <div class='wx-row-taf'>
      <span style='font-size:9px;font-weight:700;color:var(--text-lo);text-transform:uppercase;margin-right:2px'>TAF</span>
      {tafbar_ebaw}
      <span class='wx-text' id='tafEBAW'>{taf_ebaw}</span>
    </div>
  </div>

  <!-- Row 2: EBBR METAR + TAF -->
  <div class='wx-row'>
    <div class='wx-row-metar'>
      <span class='metar-icao' style='color:#f97316'>EBBR</span>
      {milbar_ebbr}
      <span class='metar-raw' id='metarEBBR'>{metar_ebbr}</span>
    </div>
    <div class='wx-sep'></div>
    <div class='wx-row-taf'>
      <span style='font-size:9px;font-weight:700;color:var(--text-lo);text-transform:uppercase;margin-right:2px'>TAF</span>
      {tafbar_ebbr}
      <span class='wx-text' id='tafEBBR'>{taf_ebbr}</span>
    </div>
  </div>

  <!-- Timestamp (right-aligned) -->
  <span class='wx-age' id='wxAge' style='position:absolute;right:18px;bottom:4px'>{metar_ts}Z</span>
</div>

<div class='app'>

  <!-- ── TRANSCRIPT FEED ── -->
  <div class='feed-panel'>
    <div class='feed-hdr'>
      <div class='feed-hdr-row'>
        <div>
          <div class='feed-label'>Live Transmissions</div>
          <div class='pill-row'>
            <button class='pill pill-all active' onclick='filterType("all",this)'>All</button>
            <button class='pill pill-twr'    onclick='filterType("twr",this)'>TWR</button>
            <button class='pill pill-app'    onclick='filterType("app",this)'>APP</button>
            <button class='pill pill-gnd'    onclick='filterType("gnd",this)'>GND</button>
            <button class='pill pill-atis'   onclick='filterType("atis",this)'>ATIS</button>
            <button class='pill pill-acc'    onclick='filterType("acc",this)'>ACC</button>
            <button class='pill pill-emer'   onclick='filterType("emer",this)'>EMER</button>
            <button class='pill pill-marine' onclick='filterType("marine",this)'>MARINE</button>
            <button class='pill pill-pmr'    onclick='filterType("pmr",this)'>PMR</button>
            <button class='pill pill-ham'    onclick='filterType("ham",this)'>HAM</button>
            <button class='pill pill-toggle' onclick='togglePending(this)' title='Show pending &amp; no-speech'>+ pending</button>
          </div>
        </div>
        <form method='get' action='/' class='search-mini'>
          <input type='text' name='q' value='{search}' placeholder='Search transcript&hellip;'>
          <input type='text' name='freq' value='{freq_f}' placeholder='MHz' style='width:60px'>
          <button type='submit' class='btn-search'>Go</button>
        </form>
      </div>
    </div>
    <div class='feed-scroll' data-last-id='{first_id}'>
      {cards_html}
    </div>
    {pag}
  </div>

  <!-- ── ADS-B PANEL ── -->
  <div class='adsb-panel'>
    <div class='panel-hdr'>
      <div class='panel-title'>ADS-B Traffic &middot; 20km</div>
      <div class='panel-live'><div class='pulse-dot pd-green'></div>
        <span id='liveLabel2'>{live_lbl}</span></div>
    </div>
    <div class='radar-wrap' id='radarWrap'>
      <iframe src='https://1090.tangosierra.one/' id='tar1090Frame' frameborder='0'></iframe>
    </div>
    <div class='ac-list' id='acList'>
      {ac_rows_html}
    </div>
  </div>

  <!-- ── ANALYTICS STRIP ── -->
  <div class='analytics-strip'>
    <div class='ab'>
      <div class='ab-title'>Transmission Activity &middot; 24h</div>
      {freq_bars_html}
    </div>
    <div class='ab'>
      <div class='ab-title'>Decoded by Frequency &middot; 24h</div>
      <div class='donut-row'>
        <div style='flex-shrink:0;position:relative;width:100px;height:100px'>
          {donut_svg}
          <div style='position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center'>
            <span style='display:block;font-size:15px;font-weight:800;font-family:ui-monospace,monospace;color:var(--text-hi)'>{db_stats['speech']:,}</span>
            <span style='display:block;font-size:7px;color:var(--text-lo);letter-spacing:.12em;text-transform:uppercase;margin-top:3px'>decoded</span>
          </div>
        </div>
        <div class='donut-legend'>{donut_legend}</div>
      </div>
    </div>
    <div class='ab'>
      <div class='ab-title'>Hourly Transmissions &middot; 24h</div>
      {spark_svg}
    </div>
    <div class='kpi-block'>
      {kpi_html}
    </div>
  </div>

</div><!-- /app -->

<div id='mapModal' onclick='this.classList.remove("open")'>
  <div id='mapBox' onclick='event.stopPropagation()'>
    <div id='mapHeader'>
      <span id='mapTitle'></span>
      <button id='mapClose' onclick='document.getElementById("mapModal").classList.remove("open")'>&times;</button>
    </div>
    <div id='mapContent'></div>
  </div>
</div>

<script>{JS}</script>
</body></html>"""

        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)


if __name__ == "__main__":
    print(f"Transcript viewer v3.0 on http://0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
