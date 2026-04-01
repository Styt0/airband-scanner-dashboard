# CLAUDE.md — SDR-Hub v2 Project Rules

## What this project is
Airband monitoring system for EBAW (Antwerp) and EBBR (Brussels).
RTL-SDR receiver on a Raspberry Pi transcribes ATC audio via Deepgram.
Web dashboard served from the Pi, archived to OneDrive from Windows.

## Stack
- **Pi** — 192.168.1.188 (LAN) / 100.120.23.59 (Tailscale), user: root
- **transcript_viewer_new.py** — main dashboard, port 8002
- **portal.py** — pixel-art index portal (tangosierra.one), port 8003
- **archive_transmissions.py** — Windows-side backup script (paramiko SSH)
- **DB** — `/opt/sdr-hub/data/db.sqlite3` (SQLite on Pi)
- **Audio** — `/opt/sdr-hub/data/public/media/device_3/transmission/`
- **ADS-B** — tar1090 at `http://127.0.0.1:8080`

## Deployment
```
scp transcript_viewer_new.py root@192.168.1.188:/opt/deepgram-worker/transcript_viewer.py
ssh root@192.168.1.188 systemctl restart transcript-viewer
```
Service name: `transcript-viewer.service`

## How we work together
- Read the file before suggesting any change.
- Don't add features beyond what's asked.
- Don't add docstrings or comments to untouched code.
- Prefer minimal, targeted edits over rewrites.
- Flag security issues (plaintext creds, exposed IPs) but don't block on them.
- After any change to `transcript_viewer_new.py`, note what needs redeploying to Pi.
