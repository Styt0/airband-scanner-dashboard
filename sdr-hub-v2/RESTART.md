# RESTART.md — Session State

## Last session: 2026-04-02

### What we did
1. **Audio player**: replaced `<audio controls>` bar with SVG circular progress ring around the button
   - 32×32 wrap, r=13 cyan ring, `stroke-dashoffset` driven by `timeupdate`
   - Play/pause toggle ▶/⏸, no layout shift
2. **Freq column styling**: swapped visibility — label (EBBR APP) now bright + role colour, badge (APP/ACC) now neutral grey pill
3. **`/sync-session-docs` skill**: created at `~/.claude/skills/sync-session-docs/` — global, reusable across projects
4. Deployed `transcript_viewer_new.py` → `pi-adsb` twice (once per change), both active

### Current Pi state
- `sdr-hub` container: running
- `transcript-viewer.service`: running on port 8002
- All crons active: disk_rotation (03:00), reboot (04:00), watchdog (*/15)

### Where we stopped
UI polish done. Code backlog items still pending — see BACKLOG.md.
Next: hardcoded config values (BACKLOG 🟡) or `portal.py` footer fix (🟢).
