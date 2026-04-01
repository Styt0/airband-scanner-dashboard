# MEMORY.md — Key Facts & Decisions

## Project identity
- Domain: `tangosierra.one` / `sdr.tangosierra.one`
- Location: EBAW Antwerp Intl · JO21EC · 51°N 004°E, altitude 12m
- SDR device: RTL-SDR serial `SDRJUB`, alias `Airband_EBAW_EBBR`
- Sample rate: 2.4 MHz, tuner gain: 32.8 dB
- Scan range: 108–137 MHz (airband) + 144–146.5 MHz (2m ham)

## Infrastructure
| Thing | Value |
|-------|-------|
| Pi LAN IP | 192.168.1.188 |
| Pi Tailscale IP | 100.120.23.59 |
| Pi user | root |
| Dashboard port | 8002 |
| Portal port | 8003 |
| ADS-B port | 8080 (tar1090) |
| DB path | /opt/sdr-hub/data/db.sqlite3 |
| Media path | /opt/sdr-hub/data/public/media |
| Aircraft DB | /opt/deepgram-worker/aircraft.db |

## ATIS cron schedule (on Pi via config.json)
| Airport | Freq | Minute |
|---------|------|--------|
| EBBR | 125.675 MHz | :05 |
| EBAW | 120.575 MHz | :10 |
| EBOS | 125.100 MHz | :15 |
| EBLG | 124.870 MHz | :20 |
| EBCI | 126.230 MHz | :25 |

## Archive script (Windows → Pi)
- Runs manually or via Task Scheduler
- `--audio` flag downloads .bin audio files
- `--days N` controls how many days back (default 7)
- Keeps 7 daily DB backups + 7 daily CSVs
- Uses paramiko over Tailscale

## Known design choices
- `log_message` is intentionally empty (suppresses HTTP access logs)
- Silent `except: pass` blocks are intentional in network fetch paths (Pi unreachable = graceful degradation), but NOT in DB query paths
- ADSB_BASE is intentionally referenced in embedded JS as a runtime override-able global
