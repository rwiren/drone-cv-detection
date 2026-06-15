# 5G Drone — Patent WO2025034145A1 Validation Platform

**Goal:** Prove the patent claims with a flying open-source drone over 5G.

> **Note:** This platform also serves as a testbed for GNSS-denied navigation — particularly relevant given our geographical location and current geopolitical environment. The computer vision pipeline provides position-independent safety monitoring that complements the 5G positioning team's work on network-based navigation.

## What We Need to Prove

| EP Claim | What to Demonstrate | How |
|----------|--------------------|----|
| 1 | Detect person → calculate lateral distance → compare with value×altitude → issue message | Safety monitor receives video, runs YOLO, calculates, alerts |
| 4 | Focal length from image metadata or sensor width | SIYI RTSP stream → known sensor specs → f_px |
| 7 | Prevent drone from moving toward person | Send GUIDED_LOITER command when violated |
| 8 | Prevention initiated by receiving unit | Ground server (not the drone) triggers the hold |
| 10 | Communication device external to UAV | All CV processing on ground server, connected over 5G |
| 11 | Multispectral detection | RGB + thermal streams fused |

## Hardware (Minimum Viable)

| Component | Part | Status |
|-----------|------|--------|
| Drone | Holybro X650 + Cube Orange+ (ArduCopter) | ✅ Flying |
| Companion | RPi CM4 + Ochin Tiny V2 + BlueOS | 🟡 Next |
| Connectivity | 5G modem + ZeroTier VPN | 🟡 Next |
| Camera | SIYI A8 Mini (Ethernet RTSP, gimbal pitch) | 🔴 To acquire |
| Ground server | Any PC on same ZeroTier network | ✅ Ready |

## Architecture

```
DRONE                              5G / INTERNET                    GROUND
─────                              ────────────                    ──────
Cube Orange+                                              mavlink_safety_monitor.py
    ↕ MAVLink                                                    │
RPi CM4 (BlueOS)                                                 │ YOLO + lateral dist
    ├── MAVLink proxy ──── ZeroTier ──── 5G ────────── MAVLink telemetry (alt, pitch)
    ├── SIYI A8 RTSP ───── ZeroTier ──── 5G ────────── Video frames
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
├── mavlink_safety_monitor.py    ← Main: detect + calculate + compare + hold
├── mavlink_mqtt_bridge.py       ← MAVLink ↔ MQTT (telemetry + commands)
└── rtsp_metadata_extractor.py   ← Focal length from SIYI camera
```

## Steps to First Demo

### Phase 1: BlueOS + Network (no camera yet)

1. Flash BlueOS on RPi CM4 via Ochin board
2. Connect Cube Orange+ to RPi via Ethernet (MAVLink)
3. Install 5G modem, verify internet on BlueOS
4. Install ZeroTier extension in BlueOS, join network
5. From ground PC: connect to drone MAVLink via ZeroTier IP:14550
6. **Test:** Ground PC receives live telemetry (altitude, position) over 5G

### Phase 2: Camera + Detection

7. Mount SIYI A8 Mini, connect Ethernet to Ochin/RPi
8. Verify RTSP stream accessible from ground PC over ZeroTier
9. Run `rtsp_metadata_extractor.py --rtsp rtsp://<drone-zt-ip>:8554/main.264 --model SIYI_A8_MINI`
10. Run `mavlink_safety_monitor.py` with real RTSP + real telemetry
11. **Test:** Walk under drone → detection + lateral distance calculated + alert issued

### Phase 3: Command-Back (the patent proof)

12. Fly drone in GUIDED mode approaching a person
13. Safety monitor detects person, calculates d_H < value × altitude
14. Monitor sends GUIDED_LOITER command back over 5G
15. **Drone stops.** ← This proves claims 7, 8, 10.
16. Record video + telemetry logs as evidence

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

When a person is detected and lateral distance ≤ altitude:
- Alert message published (claim 1)
- GUIDED_LOITER sent to drone (claims 7, 8)
- All over 5G/ZeroTier (claim 10, PCT claim 15)

## What's NOT in Scope

- Radio measurements / coverage testing
- Grafana dashboards
- SecuringSkies integration
- Multiple GNSS schemes
- Ericsson product demos

Those are separate projects. This platform exists to prove the patent.
