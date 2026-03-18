# Ham Radio Scanner — Plan for Reet, Belgium

## TL;DR

Same stack as airband-scanner but configured for amateur radio bands.
HydraSDR (24–1800 MHz) via SoapySDR → sdr-hub → whisper.cpp → web viewer.
APRS tracker replaces ADS-B tracker. Loop antenna covers VHF/UHF natively.

---

## 1. Hardware

| Item | Spec | Notes |
|------|------|-------|
| HydraSDR RFOne | 24–1800 MHz, 10 MHz BW, Rafael R828D tuner | Via SoapyHydraSDR driver |
| YouLoop antenna | Airspy passive magnetic loop | **HF/VHF only (10 kHz–~300 MHz)** — see antenna note |
| Zima Board 1 (216/832) | Intel Celeron N3350/N3450, 2/8 GB RAM, 16/32 GB eMMC | x86_64 Debian — **not RPi** |

**Platform:** Zima Board runs x86_64 Debian. All prebuilt `apt` packages and Docker images work natively — no ARM cross-compilation, no armhf/arm64 workarounds.

**Zima Board storage:** 16/32 GB eMMC + 2× SATA 6 Gbps ports onboard. Add a 2.5" SATA SSD directly (no USB adapter needed) to solve the disk capacity issue.

**Zima Board USB:** 2× USB 3.0. HydraSDR connects here. PCIe 2.0 x4 slot available for future expansion.

**Antenna limitation — YouLoop:** The YouLoop is a passive magnetic loop optimized for HF and low VHF (10 kHz–~300 MHz). It **does not perform well on 70cm (430–440 MHz)** or higher UHF. For the primary ham scan targets:
- ✅ **10m (28–30 MHz):** YouLoop excellent
- ✅ **12m (24.89 MHz):** YouLoop excellent
- ✅ **2m (144–146 MHz):** YouLoop good
- ✅ **Marine VHF (156 MHz):** YouLoop good
- ⚠️ **70cm (430–440 MHz):** YouLoop marginal to poor — consider adding a simple vertical or discone for UHF
- ❌ **PMR446 (446 MHz):** Same as 70cm — YouLoop not ideal

**HF limitation:** HydraSDR starts at 24 MHz. Covers 12m (24.89 MHz) and 10m (28 MHz) natively.
For 80m/40m/20m/15m you need the HydraSDR HF extension module OR a separate RTL-SDR v4
(which does 500 kHz–1.7 GHz including HF direct sampling).

---

## 2. Frequency Plan — Reet Area (51.10°N, 4.39°E)

### VHF 2m Band (144–146 MHz) — FM/SSB
| Frequency | Mode | Description |
|-----------|------|-------------|
| 144.300 | SSB | 2m SSB calling frequency |
| 144.800 | FM | **APRS** (European standard) |
| 145.200 | FM | ISS uplink (astronaut listens here) |
| 145.500 | FM | **2m FM calling frequency** (most active) |
| 145.800 | FM | **ISS downlink** (voice + SSTV) |
| 145.2375–145.5875 | FM | Repeater outputs (RV48–RV63) |

### UHF 70cm Band (430–440 MHz) — FM
| Frequency | Mode | Description |
|-----------|------|-------------|
| 430.025–430.375 | FM | Repeater outputs (Belgium, 12.5 kHz spacing) |
| 431.625–431.975 | FM | Repeater inputs (-1.6 MHz shift) |
| 433.500 | FM | **70cm FM calling frequency** |
| 433.625–434.000 | FM | Simplex channels |

### Local Repeaters — Antwerp/Reet Area
| Callsign | Output | Input | Shift | CTCSS | Mode | Location |
|----------|--------|-------|-------|-------|------|----------|
| ON0ANR | 145.625 | 145.025 | -600 | TBD | FM | Antwerpen |
| ON0DP | TBD | TBD | TBD | TBD | FM | Antwerpen (was DMR/C4FM, now FM) |
| ON0LG | TBD | TBD | TBD | TBD | FM | Leuven/Brabant |

> **Action:** Download full repeater list from https://www.uba.be/en/visiting-belgium/unmanned-stations
> (XLS/PDF with all ON0xxx repeaters, updated regularly)

### 10m Band (28–30 MHz) — HydraSDR native
| Frequency | Mode | Description |
|-----------|------|-------------|
| 28.200 | CW | 10m CW calling |
| 28.600 | SSB | 10m SSB calling |
| 29.600 | FM | **10m FM calling frequency** |
| 29.620–29.680 | FM | 10m repeater outputs |

### 12m Band (24.89–24.99 MHz) — HydraSDR native (edge)
| Frequency | Mode | Description |
|-----------|------|-------------|
| 24.950 | SSB | 12m SSB calling |

### Marine VHF (156–162 MHz) — listen only
| Frequency | Channel | Description |
|-----------|---------|-------------|
| 156.800 | Ch 16 | **International distress/calling** |
| 156.300 | Ch 6 | Ship-to-ship |
| 161.650 | Ch 70 | DSC (Digital Selective Calling) |
| 156.650 | Ch 13 | Bridge-to-bridge / Antwerp port |

### PMR446 (446 MHz) — license-free, listen only
| Frequency | Channel | Description |
|-----------|---------|-------------|
| 446.00625 | Ch 1 | PMR446 (hikers, events, families) |
| 446.01875 | Ch 2 | |
| 446.03125 | Ch 3 | |
| 446.04375 | Ch 4 | |
| 446.05625 | Ch 5 | |
| 446.06875 | Ch 6 | |
| 446.08125 | Ch 7 | |
| 446.09375 | Ch 8 | |

### Other Notable Frequencies
| Frequency | Mode | Description |
|-----------|------|-------------|
| 137.000–138.000 | FM | NOAA/Meteor weather satellites (APT) |
| 143.625 | FM | NOAA 15 downlink |
| 145.825 | FM | ISS APRS digipeater |
| 162.000–163.000 | — | AIS (ship tracking, like ADS-B for ships) |
| 169.400–169.475 | FM | European paging (POCSAG) |

---

## 3. Architecture

```
                     ┌─────────────────────────┐
                     │      HydraSDR RFOne      │
                     │    (Loop Antenna, RX)     │
                     └──────────┬──────────────┘
                                │ USB / SoapySDR
                     ┌──────────▼──────────────┐
                     │  sdr-hub (Docker :8003)   │ ← standalone instance on Zima Board
                     │  AM + FM + SSB scanning   │
                     │  SQLite DB + CU8 files    │
                     └──────────┬──────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                    ▼
    ┌─────────────────┐ ┌──────────────┐  ┌────────────────────┐
    │  ham-transcriber │ │  APRS decoder │  │  ham-viewer (:8004) │
    │  (whisper.cpp)   │ │  (direwolf)   │  │  Web UI + audio     │
    │  FM voice → text │ │  144.800 MHz  │  │  + APRS map overlay │
    └─────────────────┘ └──────────────┘  └────────────────────┘
```

### Key differences from airband stack

| Aspect | Airband | Ham Radio |
|--------|---------|-----------|
| SDR | RTL-SDR (AM only) | HydraSDR (FM + SSB + AM) |
| Frequencies | 118–137 MHz | 24–1800 MHz (multi-band) |
| Modulation | AM only | FM, SSB, AM, CW, digital |
| Tracking | ADS-B (aircraft) | APRS (ham stations) |
| Transcription | Easy (clear ATC) | Harder (QSOs, noise, SSB) |
| Known stations | Airlines/ATC | Callsigns (ON4xxx, etc.) |
| Hardware | RPi 4 (ARM) | Zima Board 1 (x86_64) |
| Docker port | 8001 | 8003 |
| Viewer port | 8002 | 8004 |

---

## 4. Implementation Plan

### Phase 1: SoapySDR + sdr-hub for HydraSDR

```bash
# On Zima Board (x86_64 Debian) — all standard amd64 packages work
apt-get install -y soapysdr-tools libsoapysdr-dev cmake build-essential

# Install SoapyHydraSDR plugin (build from source — no prebuilt package yet)
git clone https://github.com/hydrasdr/SoapyHydraSDR
cd SoapyHydraSDR && mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install
sudo ldconfig

# Verify detection
SoapySDRUtil --find
SoapySDRUtil --probe="driver=hydrasdr"
```

> **Note:** On x86_64 Debian, `libusb` and udev rules for HydraSDR should be added:
> ```bash
> # Copy udev rules so HydraSDR is accessible without root
> sudo cp SoapyHydraSDR/udev/*.rules /etc/udev/rules.d/
> sudo udevadm control --reload-rules && sudo udevadm trigger
> # Add your user to the plugdev group
> sudo usermod -aG plugdev $USER
> ```

Configure second sdr-hub instance with ham frequency groups:
```yaml
# /opt/ham-hub/config.json (sdr-hub device config)
{
  "devices": [{
    "serial": "HYDRA01",        # HydraSDR serial
    "driver": "soapy",          # Use SoapySDR backend
    "groups": [
      {
        "name": "2m FM Calling",
        "freq_start": 145475000,
        "freq_stop": 145525000,
        "modulation": "FM",
        "squelch": -30
      },
      {
        "name": "2m Repeaters",
        "freq_start": 145200000,
        "freq_stop": 145600000,
        "modulation": "FM",
        "squelch": -35
      },
      {
        "name": "70cm Calling",
        "freq_start": 433475000,
        "freq_stop": 433525000,
        "modulation": "FM",
        "squelch": -30
      },
      {
        "name": "70cm Repeaters",
        "freq_start": 430000000,
        "freq_stop": 430400000,
        "modulation": "FM",
        "squelch": -35
      },
      {
        "name": "Marine Ch16",
        "freq_start": 156775000,
        "freq_stop": 156825000,
        "modulation": "FM",
        "squelch": -25
      },
      {
        "name": "10m FM",
        "freq_start": 29575000,
        "freq_stop": 29625000,
        "modulation": "FM",
        "squelch": -30
      },
      {
        "name": "PMR446",
        "freq_start": 446000000,
        "freq_stop": 446100000,
        "modulation": "FM",
        "squelch": -25
      },
      {
        "name": "ISS",
        "freq_start": 145775000,
        "freq_stop": 145825000,
        "modulation": "FM",
        "squelch": -40
      },
      {
        "name": "APRS",
        "freq_start": 144775000,
        "freq_stop": 144825000,
        "modulation": "FM",
        "squelch": -40
      }
    ]
  }]
}
```

### Phase 2: Transcription (reuse whisper.cpp)

Same transcriber with ham-specific tweaks:
- **Prompt:** `"Amateur radio QSO. Callsigns ON4, ON7, PA, DL, G, F. Signal reports, 73, QTH, CQ."`
- **FM demodulation** instead of AM (different `decode_cu8_to_wav` — FM uses phase difference, not envelope)
- **SSB challenge:** whisper.cpp struggles with SSB audio quality. For SSB bands, may need to skip transcription or use specialized processing.
- **Callsign extraction:** `ON[0-9][A-Z]{2,3}` pattern for Belgian callsigns

### Phase 3: APRS Tracker (replaces ADS-B)

```bash
# Install direwolf (APRS software modem/TNC)
apt-get install -y direwolf

# Configure to decode APRS from audio pipe
# sdr-hub records 144.800 MHz → direwolf decodes → SQLite
```

**APRS data fields:** callsign, lat/lon, altitude, speed, course, status message, weather data

The viewer's radar map becomes a ham station map:
- Show APRS stations on map instead of aircraft
- Callsign labels instead of flight numbers
- Color by: mobile (car icon), fixed (house), digipeater (tower)
- QTH locator grid overlay (JO21 for Reet area)

### Phase 4: Ham Viewer Web UI

Adapted from airband viewer with:
- Band selector (2m / 70cm / 10m / Marine / PMR)
- Mode indicator (FM / SSB / CW / Digital)
- Callsign regex highlighting
- APRS station map instead of aircraft radar
- Repeater identification (match freq to known repeater DB)
- Signal report display (if extractable from transcript)
- QTH locator grid on map

### Phase 5: LoRa / Meshtastic Decode (no extra hardware needed)

The HydraSDR covers 868 MHz (EU LoRa ISM band) natively. Pure-software decode is possible via GNU Radio.

**EU LoRa frequencies (Belgium):**
| Frequency | BW | Use |
|-----------|-----|-----|
| 868.100 | 125 kHz | LoRaWAN CH1 (default uplink) |
| 868.300 | 125 kHz | LoRaWAN CH2 |
| 868.500 | 125 kHz | LoRaWAN CH3 |
| 869.525 | 125 kHz | LoRaWAN downlink (high duty) |
| 869.4–869.65 | varies | Meshtastic EU_868 channel plan |

**Tools (no extra hardware):**
- **`gr-lora_sdr`** ([github.com/tapparelj/gr-lora_sdr](https://github.com/tapparelj/gr-lora_sdr)) — GNU Radio module, works with SoapySDR. Decodes at very low SNR.
- **`Meshtastic_SDR`** ([gitlab.com/crankylinuxuser/meshtastic_sdr](https://gitlab.com/crankylinuxuser/meshtastic_sdr)) — Full Meshtastic RX stack: GNU Radio flowgraph + Python ZMQ decoder → full packet decode including mesh routing fields.
- **`meshtasticd`** Docker image ([hub.docker.com/r/meshtastic/meshtasticd](https://hub.docker.com/r/meshtastic/meshtasticd)) — amd64 supported.

**CPU note (2 GB Zima Board 216):** Meshtastic decode has been demonstrated on RPi hardware. Start with spreading factor SF7/SF8 which is less CPU-intensive. Monitor with `htop` during testing.

```bash
# Install GNU Radio + gr-lora_sdr on Debian Bookworm
apt-get install -y gnuradio cmake libsoapysdr-dev
git clone https://github.com/tapparelj/gr-lora_sdr
cd gr-lora_sdr && mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr && make -j$(nproc) && sudo make install
sudo ldconfig

# Run the included example flowgraph for 868.1 MHz
python3 /usr/share/gr-lora_sdr/examples/rx_to_file.py \
    --freq 868.1e6 --sf 7 --bw 125e3 --device "driver=hydrasdr"
```

**Database:** LoRa/Meshtastic packets stored in `lora_contacts` table (see `db/schema.sql`).

### Phase 6: Optional Enhancements

- **CW decoder:** Use `fldigi` or custom Goertzel tone detector for Morse code → text
- **DMR decoder:** `DSDPlus` or `dsd` for digital voice decoding
- **Satellite passes:** Auto-record ISS (145.800) and NOAA APT during passes (predict with `gpredict`)
- **Waterfall:** Add spectrogram/waterfall display using `csdr` + canvas in viewer
- **QSO logging:** If a complete QSO is captured (both sides via repeater), log as structured data

---

## 5. Frequency Map — What the HydraSDR Can See

```
24 MHz ─────────── HydraSDR native range starts ────────────────
  │  12m band (24.89 MHz) — SSB
  │  CB radio (26.965–27.405 MHz) — AM/FM
  │  10m band (28–30 MHz) — SSB/FM/CW
  │
  │  ~~~ gap (VHF low, not much ham activity) ~~~
  │
  │  Airband (118–137 MHz) — already covered by RTL-SDR
  │  2m band (144–146 MHz) — FM/SSB ← PRIMARY TARGET
  │  Marine VHF (156–162 MHz) — FM
  │  DAB radio (174–230 MHz)
  │  PMR446 (446 MHz) — FM
  │  70cm band (430–440 MHz) — FM ← PRIMARY TARGET
  │  ISM 868 MHz (IoT sensors)
  │  GSM 900/1800
  │  ADS-B 1090 MHz — already covered
  │
1800 MHz ────────── HydraSDR native range ends ──────────────────
```

**Primary scan targets for ham:** 2m (144–146) + 70cm (430–440) + 10m (28–30)
**Bonus targets:** Marine VHF, PMR446, APRS, ISS, CB

---

## 6. Docker Compose (proposed)

```yaml
# /opt/ham-hub/docker-compose.yml
version: "3"
services:
  ham-hub:
    image: shajen/sdr-hub
    container_name: ham-hub
    restart: unless-stopped
    ports:
      - "8003:80"
    volumes:
      - /opt/ham-hub/data:/app/data
      - /opt/ham-hub/log:/var/log/sdr
    devices:
      - /dev/bus/usb   # HydraSDR USB passthrough
    environment:
      - SOAPY_SDR_DRIVER=hydrasdr
```

---

## 7. Resource Estimates

| Resource | Ham stack | Zima Board capacity | Headroom |
|----------|-----------|---------------------|----------|
| CPU | ~20–25% (wider BW + direwolf) | Celeron N3450 quad-core | ✅ plenty |
| RAM | ~500 MB | 2 GB (216) / 8 GB (832) | ✅ fine on 832; tight on 216 |
| Disk (audio/day) | ~5 GB | eMMC 16/32 GB | ⚠️ needs SATA SSD |
| Disk (models) | 466 MB whisper | eMMC | ✅ OK |
| Network | local only (no Deepgram) | — | ✅ |

**Disk plan:** ~5 GB/day × 30 days = 150 GB. The eMMC (16–32 GB) is for the OS and Docker images only.
→ **Install a 2.5" SATA SSD** via the Zima Board's onboard SATA port. Mount at `/opt/ham-data`.
→ No USB adapter needed — SATA is native on the Zima Board.

**RAM note:** If you have the **216 model (2 GB RAM)**, running whisper.cpp + direwolf + sdr-hub simultaneously will be very tight. Consider using the `tiny` or `base` whisper model only. The **832 model (8 GB)** has no such constraint.

---

## 8. What to Do First

1. **Install Debian** on Zima Board (amd64) — standard Debian 12 Bookworm recommended
2. **Mount SATA SSD** at `/opt/ham-data` — do this before deploying anything
   ```bash
   # Example fstab entry after formatting the SSD as ext4:
   /dev/sda1  /opt/ham-data  ext4  defaults,noatime  0  2
   ```
3. **Install Docker** (standard x86_64 Debian method):
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```
4. **Plug in HydraSDR** via USB 3.0 and verify: `lsusb` + `SoapySDRUtil --find`
5. **Build + install SoapyHydraSDR** driver (see Phase 1 above)
6. **Test reception** on 145.500 MHz: `SoapySDRUtil --probe="driver=hydrasdr"`
7. **Deploy sdr-hub** on port 8003 with ham config
8. **Install direwolf** for APRS decoding on 144.800 MHz
9. **Adapt transcriber + viewer** for ham frequencies

> **YouLoop note:** If 70cm reception is weak, add a simple vertical antenna (e.g., a quarter-wave whip on a ground plane) for 430–440 MHz alongside the YouLoop. The YouLoop stays connected for 2m and below.

---

## 9. Known Frequencies Config (for viewer)

```python
HAM_FREQS = {
    # 2m Band
    144.300: "2m SSB Calling",
    144.800: "APRS",
    145.200: "ISS Uplink",
    145.500: "2m FM Calling",
    145.800: "ISS Downlink",
    # 70cm Band
    433.500: "70cm FM Calling",
    # 10m Band
    28.600:  "10m SSB Calling",
    29.600:  "10m FM Calling",
    # Marine
    156.800: "Marine Ch16 Distress",
    156.300: "Marine Ch6 Ship-Ship",
    # PMR446
    446.006: "PMR Ch1",
    446.019: "PMR Ch2",
    446.031: "PMR Ch3",
    446.044: "PMR Ch4",
    446.056: "PMR Ch5",
    446.069: "PMR Ch6",
    446.081: "PMR Ch7",
    446.094: "PMR Ch8",
    # Repeaters (populate from UBA database)
    # ON0ANR: ...
    # ON0DP: ...
}
```

---

## 10. QTH Locator

Reet, Belgium: **JO21EB**
- Grid square center: 51.10°N, 4.39°E
- Useful for: APRS position reference, VHF/UHF contest scoring, DX reporting
