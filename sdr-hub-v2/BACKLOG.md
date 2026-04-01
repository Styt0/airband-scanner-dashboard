# BACKLOG.md — Everything Left To Do

## ⭐ Next session (do these first)
- [x] **ADS-B panel: 50/50 height split** — `.radar-wrap` and `.ac-list` now both `flex:1 1 50%;min-height:0`
- [x] **Real country flags** — `_icao_flag()` and JS `hexFlag()` now return `<img src="https://flagcdn.com/16x12/{cc}.png">` instead of emoji

## 🔴 Security
- [x] `archive_transmissions.py` line 35: plaintext `PI_PASS` removed — now uses `os.environ.get("SDR_PI_PASS")`, falls back to SSH key auth

## 🟠 Reliability (silent failures)
- [x] `transcript_viewer_new.py` — added `import logging`
- [x] Line 604: tar1090 stats fetch → `logging.warning(..., exc_info=True)`
- [x] Line 610: stage2 stats fetch → `logging.warning(..., exc_info=True)`
- [x] Line 808: aircraft DB query → `logging.warning(..., exc_info=True)`
- [x] Line 889: aircraft map fetch → `logging.warning(..., exc_info=True)`
- [x] Line 1882: freq filter parse → `logging.debug(...)`
- [ ] SSE streaming (lines 1817, 1824) — left silent intentionally (client disconnects are normal)

## 🟡 Config / hardcoded values
- [ ] `transcript_viewer_new.py` line 30–33: ADSB URLs + ADSB_BASE hardcoded
  → Could be loaded from `config.json` if multi-device support ever needed
- [ ] `transcript_viewer_new.py` line ~1466: `ADSB_BASE` default still hardcoded in embedded JS
  → Has `window.ADSB_BASE ||` fallback — low priority
- [ ] `archive_transmissions.py` line 135: audio path hardcoded to `device_3`
  → Should be dynamic if a second SDR device is added

## 🟢 Minor / nice to have
- [x] `ATIS_FREQS` and `ATIS_MHZ` deduplicated — `ATIS_MHZ = ATIS_FREQS`
- [ ] `archive_transmissions.py`: no `--dry-run` flag
- [ ] `portal.py`: footer says "SDR-HUB v3" but project is v2 — align versioning
- [ ] `mockup_radar_v3.html` — still being iterated or can it be archived?
- [ ] Add `logging.basicConfig()` so Pi systemd captures logs via `journalctl -u transcript-viewer`
