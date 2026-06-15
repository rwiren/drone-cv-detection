# 5G Drone — Patent WO2025034145A1 Validation Platform

**Goal:** Prove the patent claims with a flying open-source drone over 5G.

> **Note:** This platform also serves as a testbed for GNSS-denied navigation — particularly relevant given our geographical location and current geopolitical environment. The computer vision pipeline provides position-independent safety monitoring that complements the 5G positioning team's work on network-based navigation.

> **Supply chain policy:** Avoid Chinese-manufactured electronics where possible. Prefer European, US, Vietnamese, Israeli, or other allied-nation suppliers for cameras, companion computers, and communication modules.

## What We Need to Prove

| EP Claim | What to Demonstrate | How |
|----------|--------------------|----|
| 1 | Detect person → calculate lateral distance → compare with value×altitude → issue message | Safety monitor receives video, runs YOLO, calculates, alerts |
| 4 | Focal length from image metadata or sensor width | Camera RTSP stream → known sensor specs → f_px |
| 7 | Prevent drone from moving toward person | Send GUIDED_LOITER command when violated |
| 8 | Prevention initiated by receiving unit | Ground server (not the drone) triggers the hold |
| 10 | Communication device external to UAV | All CV processing on ground server, connected over 5G |
| 11 | Multispectral detection | RGB + thermal streams fused |

## Use Cases

### UC1: 1:1 Safety Rule (Patent Core)
Detect persons, calculate lateral distance, enforce safety rule, hold if violated.

### UC2: Parking Occupancy
Detect vehicles from nadir, count occupancy — validated on M2EA and Autel.

### UC3: GNSS-Denied Navigation
Fly autonomously using only camera-based positioning when GNSS is unavailable or jammed. Uses:

- **BlueOS Optical Flow Extension** — downward camera feeds velocity to EKF3
- **Visual odometry** — feature matching for frame-to-frame displacement
- **Reference image matching** — absolute position correction against a known nadir image of the site
- **No satellite images needed** — uses the onboard camera + a pre-captured reference photo

The camera serves dual purpose: pointing down for optical flow navigation, pointing forward for person detection. ArduPilot's EKF3 fuses optical flow + rangefinder + IMU for full autonomous flight without GPS.

**Satellite Reference Matching (Validated):**
Pre-loaded satellite/aerial imagery of the flight area enables absolute position correction:
- Reference: ESRI World Imagery tiles stitched (768×768, GSD 0.30 m/px)
- Method: ORB feature matching (drone downward camera vs. satellite reference)
- **Result: 0.5m position error** on simulated test at Jorvas site
- No internet needed in flight — reference pre-loaded before takeoff

**Why this matters:** In a GNSS-denied/jammed environment, the drone can still:
1. Maintain stable hover (optical flow)
2. Execute autonomous waypoint missions (visual odometry)
3. Continue safety monitoring (CV pipeline works regardless of GPS)

## Hardware (Minimum Viable)

| Component | Part | Origin | Status |
|-----------|------|--------|--------|
| Drone | Holybro X650 + Cube Orange+ (ArduCopter) | 🇺🇸/🇦🇺 | ✅ Flying |
| Companion | RPi CM4 + Ochin Tiny V2 + BlueOS | 🇬🇧/🇺🇸 | 🟡 Next |
| Connectivity | 5G modem + ZeroTier VPN | TBD (non-Chinese) | 🟡 Next |
| Camera/Gimbal | Gremsy Pixy U or Mio + IP camera | 🇻🇳 Vietnam | 🔴 To acquire |
| Thermal (opt.) | FLIR Boson 640 | 🇺🇸 USA | 🔴 Optional |
| Ground server | Any PC on same ZeroTier network | — | ✅ Ready |

### Camera Selection (Non-Chinese)

#### Primary: Gremsy Pixy U / Mio + Action Camera

- **Gimbal:** Gremsy (Vietnam) — MAVLink native, 3-axis, pitch telemetry
- **Camera:** Sony/GoPro or similar (known focal length, EXIF accessible)
- **Stream:** HDMI capture → `v4l2rtspserver` on BlueOS RPi → RTSP over network
- **Patent claims validated:**
  - **Claims 2 & 19** — Gremsy provides continuous gimbal pitch angle (θ) via MAVLink
  - **Claim 4** — focal length known from camera specs (sensor width + image width)
- **Price:** Gremsy Mio ~€900, Pixy U ~€1,500

#### Multispectral: FLIR Boson 640 (USA) or Workswell WIRIS (Czech Republic)

- **FLIR Boson 640:** Uncooled VOx thermal core, 640×512, USB/analog, ~€1,500–3,000
- **Workswell WIRIS Pro:** Integrated RGB + thermal, Ethernet, Czech-made, ~€8,000
- **Patent claim validated:**
  - **Claim 11** — dual RGB + thermal for enhanced person classification

#### Optical Flow (GNSS-Denied)

The BlueOS OpticalFlow extension works with **any RTSP camera** — not vendor-specific. A USB camera + `v4l2rtspserver` on the RPi provides the downward video stream.

### Where to Buy (Europe)

| Supplier | Products | Country |
|----------|----------|---------|
| [Gremsy Store](https://gremsy.com/online-store) | Pixy U, Mio, S1, T3 | 🇻🇳 Vietnam (direct) |
| [FLIR / Teledyne](https://www.flir.eu) | Boson, Lepton | 🇺🇸 via EU distributors |
| [Workswell](https://www.workswell.eu) | WIRIS Pro/Security | 🇨🇿 Czech Republic |
| [Droneshop.nl](https://www.droneshop.nl) | Gremsy, accessories | 🇳🇱 Netherlands |
| [CubePilot](https://www.cubepilot.org) | Cube Orange+, Here 4 | 🇦🇺 Australia |

## Architecture

```
DRONE                              5G / INTERNET                    GROUND
─────                              ────────────                    ──────
Cube Orange+                                              mavlink_safety_monitor.py
    ↕ MAVLink                                                    │
RPi CM4 (BlueOS)                                                 │ YOLO + lateral dist
    ├── MAVLink proxy ──── ZeroTier ──── 5G ────────── MAVLink telemetry (alt, pitch)
    ├── Camera RTSP ────── ZeroTier ──── 5G ────────── Video frames
    └── 5G modem                                                 │
                                                                 ▼
                                                    VIOLATED? → GUIDED_LOITER cmd
                                                                 │
                                                    5G ── ZeroTier ── BlueOS ── Cube
                                                                 │
                                                         Drone holds position
```

## Software — What Exists

```
src/mavlink_safety/
├── mavlink_safety_monitor.py    ← UC1: detect + calculate + compare + hold
├── mavlink_mqtt_bridge.py       ← MAVLink ↔ MQTT (telemetry + commands)
├── rtsp_metadata_extractor.py   ← Claim 4: focal length from camera metadata
└── gnss_denied_nav.py           ← UC3: visual odometry + reference matching
```

BlueOS provides additionally:
- **OpticalFlow Extension** — any RTSP camera downward for velocity → EKF3
- **ZeroTier Extension** — 5G connectivity to ground server
- **MAVLink Endpoints** — bidirectional command over network

## Steps to First Demo

### Phase 1: BlueOS + Network (no camera yet)

1. Flash BlueOS on RPi CM4 via Ochin board
2. Connect Cube Orange+ to RPi via Ethernet (MAVLink)
3. Install 5G modem, verify internet on BlueOS
4. Install ZeroTier extension in BlueOS, join network
5. From ground PC: connect to drone MAVLink via ZeroTier IP:14550
6. **Test:** Ground PC receives live telemetry (altitude, position) over 5G

### Phase 2: Camera + Detection

7. Mount Gremsy gimbal + camera, connect to RPi
8. Verify RTSP stream accessible from ground PC over ZeroTier
9. Run `rtsp_metadata_extractor.py` to confirm focal length extraction
10. Run `mavlink_safety_monitor.py` with real RTSP + real telemetry
11. **Test:** Walk under drone → detection + lateral distance calculated + alert issued

### Phase 3: Command-Back (the patent proof)

12. Fly drone in GUIDED mode approaching a person
13. Safety monitor detects person, calculates d_H < value × altitude
14. Monitor sends GUIDED_LOITER command back over 5G
15. **Drone stops.** ← This proves claims 7, 8, 10.
16. Record video + telemetry logs as evidence

### Phase 4: GNSS-Denied Flight

17. Enable BlueOS OpticalFlow Extension (downward camera)
18. Attach rangefinder (lidar for altitude)
19. Set ArduPilot: `FLOW_TYPE=5`, `EK3_FLOW_DELAY=150`, disable GPS
20. Hover test in Loiter mode without GPS — confirm stable position hold
21. Run `gnss_denied_nav.py` with reference image for absolute position correction
22. **Test:** Autonomous waypoint mission with GPS disabled, safety monitor still active
23. Record flight as evidence — CV safety works even without satellites

## Key Script: End-to-End Demo

```bash
# On ground server (external device — claim 10):
python src/mavlink_safety/mavlink_safety_monitor.py \
  --broker <zt-drone-ip> --port 14550 \
  --camera rtsp://<zt-drone-ip>:8554/main.264 \
  --model models/visdrone_yolov8m_1280_best.pt \
  --safety-value 1.0 \
  --person-height 1.75
```

## What's NOT in Scope

- Radio measurements / coverage testing
- Grafana dashboards
- SecuringSkies integration
- Multiple GNSS schemes
- Ericsson product demos

Those are separate projects. This platform exists to prove the patent.
