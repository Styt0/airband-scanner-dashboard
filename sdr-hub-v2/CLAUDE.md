# CLAUDE.md — SDR-Hub v2 Project Rules

## What this project is
Airband monitoring system for EBAW (Antwerp) and EBBR (Brussels).
RTL-SDR receiver on a Raspberry Pi transcribes ATC audio via Deepgram.
Web dashboard served from the Pi, archived to OneDrive from Windows.

## Stack
- **Pi** — 192.168.1.188 (LAN) / 100.120.23.59 (Tailscale), user: pi (SSH via Tailscale)
- **transcript_viewer_new.py** — main dashboard, port 8002
- **portal.py** — pixel-art index portal (tangosierra.one), port 8003
- **archive_transmissions.py** — Windows-side backup script (paramiko SSH)
- **DB** — `/opt/sdr-hub/data/db.sqlite3` (SQLite on Pi)
- **Audio** — `/opt/sdr-hub/data/public/media/device_3/transmission/`
- **ADS-B** — tar1090 at `http://127.0.0.1:8080`
- **sdr-hub** — Docker container `shajen/sdr-hub` v2.2.2, port 8001 (internal), auto_sdr scanner inside
- **Watchdog** — `/opt/deepgram-worker/sdr_watchdog.sh` (cron */15 min)

## Deployment
```
scp transcript_viewer_new.py pi-adsb:/tmp/transcript_viewer.py && ssh pi-adsb "sudo cp /tmp/transcript_viewer.py /opt/deepgram-worker/transcript_viewer.py && sudo systemctl restart transcript-viewer"
```
Service name: `transcript-viewer.service`
SSH user: `pi` (not root), via Tailscale hostname `pi-adsb`

## Pi maintenance
- Daily reboot at 04:00 CEST (root crontab: `0 4 * * * /sbin/reboot`)
- Disk rotation at 03:00 CEST (`disk_rotation.py`)
- Watchdog every 15 min: reboots if sdr_scanner crashes >5x/5min OR no transmissions for 3h during daytime
- **Known failure mode**: SDRJUB dongle (RTL2838, port 1-1.2) can enter bad USB state after a crash. SoapySDR gets `soapy error: TIMEOUT`. Only fix: physical USB power-cycle or Pi reboot.

## How we work together
- Read the file before suggesting any change.
- Don't add features beyond what's asked.
- Don't add docstrings or comments to untouched code.
- Prefer minimal, targeted edits over rewrites.
- Flag security issues (plaintext creds, exposed IPs) but don't block on them.
- After any change to `transcript_viewer_new.py`, note what needs redeploying to Pi.
- Run `/sync-session-docs` at the end of every session or after a deployment.
