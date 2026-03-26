# ADS-B Troubleshooting Log — Styto-EBAW (Raspberry Pi, 192.168.1.188)

---

## 2026-03-26 — Reduced Range: Wrong Antenna on ADS-B Dongle

### Problem
ADS-B reception range dropped to roughly **half normal** for approximately 2–3 weeks (estimated since ~March 7, 2026).

**Symptoms observed:**
- Max range: 142 km over a full 10-hour session (normal should be 250+ km)
- Aircraft with position: 13–17 at any given time (normal: 35–45+)
- Bad message rate: ~60% (consistently high)
- Peak signal near saturation (−2 to −14 dBFS depending on moment)
- Strong signals: effectively 0 per minute → autogain saw no reason to reduce gain

**What was ruled out during diagnosis:**
- ❌ USB interference from airband scanner (bad% unchanged when sdr-hub stopped)
- ❌ ADC saturation / gain too high (strong_signals = 0.008% of messages)
- ❌ Gain setting wrong (autogain correctly settled at 49.6 dB = near max)
- ❌ Software/container issue (all containers healthy, 0 restarts)
- ❌ CPU throttling (not throttled, temp ~50°C)

### Root Cause
**The SMA antenna cables for the two RTL-SDR dongles were swapped.**

| Dongle | Serial | Correct antenna | Was connected to |
|--------|--------|----------------|-----------------|
| RTL-SDR Blog V4 | `00000001` | 1090 MHz ADS-B antenna | VHF airband antenna |
| Generic RTL-SDR | `SDRJUB` | VHF airband antenna (118–137 MHz) | 1090 MHz ADS-B antenna |

The Blog V4 has a built-in **1090 MHz bandpass filter and LNA**. Feeding it a VHF antenna meant:
- Significant impedance mismatch at 1090 MHz → higher noise figure
- Reduced effective gain at 1090 MHz → missed all aircraft beyond ~150 km
- Local aircraft still visible (Blog V4 LNA compensates at short range)
- Autogain didn't trigger because strong_signals remained near zero (just noise, no real saturation)

The autogain re-initialization date (March 7, 2026) correlates with when the cables were likely physically touched/moved during some maintenance.

### Fix
Physically swap the SMA cables back to correct positions:
- **Blog V4 (00000001)** → 1090 MHz ADS-B antenna (short stubby / colinear / magnetic base)
- **Generic RTL (SDRJUB)** → VHF/airband antenna (longer whip)

Reboot the Pi after swapping.

### Results after fix
Within 15 minutes of correct antenna connection:

| Metric | Before fix | After fix (15 min) |
|--------|-----------|-------------------|
| Aircraft with position | 13–17 | **39** |
| Max range | 142 km *(10 hours)* | **186.9 km** *(15 min)* |
| Strong signals/min | 0 | **27** |
| Peak signal | −14 dBFS | −2.3 dBFS |

Range expected to reach 250+ km as session accumulates more flight data.

---

## Hardware Reference — Styto-EBAW Setup

```
Raspberry Pi (192.168.1.188 / Tailscale: 100.120.23.59)
│
├── RTL-SDR Blog V4  (serial: 00000001)
│   ├── Purpose: ADS-B 1090 MHz reception
│   ├── Antenna: 1090 MHz dedicated antenna
│   └── Software: readsb (inside ultrafeeder Docker container)
│
└── Generic RTL-SDR  (serial: SDRJUB)
    ├── Purpose: Airband scanner 118–137 MHz
    ├── Antenna: VHF/airband antenna
    └── Software: sdr-hub Docker container
```

**Key Docker containers:**
- `ultrafeeder` — readsb + mlat + feeds to FlightAware, FR24, ADS-B Exchange, etc.
- `sdr-hub` — airband scanner, stores CU8 IQ recordings in SQLite
- `fr24feed`, `piaware`, `rbfeeder`, `adsbhub` — individual feeder clients

**adsb.im feeder image** — managed via web UI on port 1090

---

## Normal Operating Parameters (for comparison)

- **Gain:** 49.6 dB (autogain-managed, near max is correct for this setup)
- **Bad message rate:** ~60% (normal for EBAW/EBBR area — high secondary radar + TCAS activity)
- **Max range:** 250+ km (high-altitude transatlantic / cruise traffic)
- **Aircraft with position:** 35–55 typical during daytime
- **Load average:** 10–17 (high but normal — 7× mlat-client processes + readsb + sdr-hub)
- **CPU temp:** ~50°C (healthy)
