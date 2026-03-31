#!/usr/bin/env python3
"""tangosierra.cc – pixel-art index portal (port 8003)"""
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

_HTML_SRC = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TANGO SIERRA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#050508;
  --crt:#0a0f0a;
  --green:#00e640;
  --green-dim:#003a10;
  --green-lo:#1a3a1a;
  --amber:#ffb700;
  --cyan:#00cfcf;
  --red:#ff2442;
  --border:#00e640;
}
html,body{
  height:100%;
  background:var(--bg);
  color:var(--green);
  font-family:'Press Start 2P',monospace;
  overflow:hidden;
  display:flex;align-items:center;justify-content:center;
}
/* CRT vignette */
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:200;
  background:radial-gradient(ellipse 90% 90% at 50% 50%,transparent 55%,rgba(0,0,0,.85) 100%);
}
/* Scanlines */
body::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:201;
  background:repeating-linear-gradient(
    to bottom,
    transparent 0px,transparent 3px,
    rgba(0,0,0,.18) 3px,rgba(0,0,0,.18) 4px
  );
}
.wrap{
  text-align:center;
  padding:24px 16px;
  max-width:900px;
  width:100%;
  position:relative;
  z-index:10;
}

/* ── HEADER ── */
.logo{
  font-size:clamp(22px,5vw,48px);
  letter-spacing:.2em;
  color:var(--green);
  text-shadow:0 0 8px var(--green),0 0 24px #00802280,0 0 60px #00401108;
  animation:flicker 7s infinite;
  margin-bottom:6px;
}
.logo-sub{
  font-size:clamp(7px,1.5vw,11px);
  letter-spacing:.35em;
  color:var(--amber);
  text-shadow:0 0 8px var(--amber);
  margin-bottom:40px;
}
.blink{animation:blink 1.1s step-end infinite}
.ts-cursor{display:inline-block;width:0.55em;height:1em;background:var(--green);vertical-align:text-bottom;animation:blink 1s step-end infinite;margin-left:0.15em}

/* ── GRID ── */
.grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  gap:18px;
  margin:0 auto 36px;
}
.card{
  display:block;
  text-decoration:none;
  border:2px solid var(--border);
  padding:22px 14px 18px;
  background:var(--bg);
  color:var(--green);
  position:relative;
  cursor:pointer;
  /* pixel shadow */
  box-shadow:4px 4px 0 var(--green-lo);
  image-rendering:pixelated;
  transition:none;
}
.card::before{
  content:'';
  position:absolute;inset:0;
  background:var(--green);
  opacity:0;
  transition:opacity .05s step-end;
}
.card:hover::before{opacity:.12}
.card:hover{
  box-shadow:6px 6px 0 var(--green-dim);
  border-color:var(--amber);
  color:var(--amber);
}
.card:hover .card-icon{color:var(--amber)}
.card:hover .card-title{color:var(--amber)}
.card:hover .card-desc{color:#6a5000}
.card:hover .card-url{color:#6a5000}
.card:active{box-shadow:2px 2px 0 var(--green-lo);transform:translate(2px,2px)}

.card-icon{
  display:block;
  font-size:26px;
  margin-bottom:14px;
  color:var(--amber);
  text-shadow:0 0 10px var(--amber);
  image-rendering:pixelated;
}
.card-title{
  font-size:clamp(9px,1.8vw,12px);
  letter-spacing:.12em;
  margin-bottom:10px;
  color:var(--green);
}
.card-desc{
  font-size:clamp(5px,1.2vw,7px);
  letter-spacing:.08em;
  color:#2a5a2a;
  line-height:2;
  margin-bottom:10px;
}
.card-url{
  font-size:clamp(5px,1vw,6px);
  letter-spacing:.06em;
  color:var(--green-lo);
  border-top:1px solid var(--green-lo);
  padding-top:8px;
  margin-top:4px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
/* coloured accents per card */
.card.c-sdr   {border-color:#3b82f6}.card.c-sdr:hover{border-color:#60a5fa;color:#60a5fa}
.card.c-sdr:hover .card-icon,.card.c-sdr:hover .card-title{color:#60a5fa}
.card.c-adsb  {border-color:#22d3ee}.card.c-adsb:hover{border-color:#67e8f9;color:#67e8f9}
.card.c-adsb:hover .card-icon,.card.c-adsb:hover .card-title{color:#67e8f9}
.card.c-sky   {border-color:#a855f7}.card.c-sky:hover{border-color:#c084fc;color:#c084fc}
.card.c-sky:hover .card-icon,.card.c-sky:hover .card-title{color:#c084fc}
.card.c-fr24  {border-color:#f97316}.card.c-fr24:hover{border-color:#fb923c;color:#fb923c}
.card.c-fr24:hover .card-icon,.card.c-fr24:hover .card-title{color:#fb923c}

/* ── FOOTER ── */
.footer{
  font-size:clamp(5px,1vw,7px);
  letter-spacing:.18em;
  color:var(--green-lo);
  line-height:2.2;
}
.footer span{color:#1a3a1a}
.cursor{
  display:inline-block;width:8px;height:12px;
  background:var(--green);vertical-align:middle;
  animation:blink 1s step-end infinite;
}

@keyframes blink{50%{opacity:0}}
@keyframes flicker{
  0%,93%,100%{opacity:1}
  94%{opacity:.85}95%{opacity:1}97%{opacity:.7}98%{opacity:1}
}
</style>
</head>
<body>
<div class="wrap">

  <div class="logo">TS<span class="ts-cursor"></span></div>
  <div class="logo-sub">TANGO&nbsp;&nbsp;SIERRA&nbsp;&nbsp;/&nbsp;&nbsp;ANTWERP&nbsp;&middot;&nbsp;BE</div>

  <div class="grid">

    <a class="card c-sdr" href="https://sdr.tangosierra.one" target="_blank" rel="noopener">
      <span class="card-icon">&#128225;</span>
      <div class="card-title">SDR&nbsp;VIEWER</div>
      <div class="card-desc">AIRBAND MONITOR<br>EBAW &middot; EBBR<br>LIVE TRANSCRIPTS<br>METAR &middot; TAF &middot; NOTAM</div>
      <div class="card-url">sdr.tangosierra.one</div>
    </a>

    <a class="card c-adsb" href="https://1090.tangosierra.one" target="_blank" rel="noopener">
      <span class="card-icon">&#9992;</span>
      <div class="card-title">TAR1090</div>
      <div class="card-desc">ADS-B RADAR<br>1090&nbsp;MHz RECEIVER<br>LIVE AIRCRAFT MAP<br>MLAT &middot; UAT</div>
      <div class="card-url">1090.tangosierra.one</div>
    </a>

    <a class="card c-sky" href="https://skyaware.tangosierra.one" target="_blank" rel="noopener">
      <span class="card-icon">&#127760;</span>
      <div class="card-title">SKYAWARE</div>
      <div class="card-desc">PIAWARE VIEWER<br>ADS-B &middot; MLAT<br>AIRCRAFT TRACKING<br>FA FEEDER</div>
      <div class="card-url">skyaware.tangosierra.one</div>
    </a>

    <a class="card c-fr24" href="https://fr24.tangosierra.one" target="_blank" rel="noopener">
      <span class="card-icon">&#128752;</span>
      <div class="card-title">FR24&nbsp;FEED</div>
      <div class="card-desc">FLIGHTRADAR24<br>FEEDER STATUS<br>LIVE STATISTICS<br>FR24 NETWORK</div>
      <div class="card-url">fr24.tangosierra.one</div>
    </a>

  </div>

  <div class="footer">
    EBAW&nbsp;ANTWERP&nbsp;INTL&nbsp;&middot;&nbsp;JO21EC&nbsp;&middot;&nbsp;51&deg;N&nbsp;004&deg;E<br>
    <span>SDR-HUB v3 &middot; ZIMABOARD &middot; TAILSCALE</span>
  </div>

</div>
</body>
</html>"""
HTML = _HTML_SRC.encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, fmt, *a): pass

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(HTML)))
            self.send_header("Cache-Control", "public, max-age=300")
            self.end_headers()
            self.wfile.write(HTML)
        else:
            self.send_response(301)
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8003), Handler)
    print("tangosierra.cc portal on :8003")
    server.serve_forever()
