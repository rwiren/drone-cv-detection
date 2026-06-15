# 5G Drone Development — Project Plan

**Version:** 1.1.0 | **Date:** 2026-06-15

## Overview

Custom-built heavy-lift quadcopter with native 5G connectivity running ArduPilot + BlueOS. The platform validates patent WO2025034145A1 on open-source hardware over a cellular network, while also serving as a testbed for aerial radio measurements and Ericsson 5G product demonstrations.

## Hardware Platform

### Airframe

| Component | Selection | Notes |
|-----------|-----------|-------|
| Frame | Holybro X650 | Foldable carbon fiber |
| Motors | T-motor MN4010 KV470 | ×4 |
| ESC | 4-in-1 | Soldered |
| Propellers | 14×5.5 APC | 14" |
| Battery | 6S LiPo 8Ah (22.2V) | 980g |
| **MTOM** | **~2.8 kg** | Open Cat A1/A3 (C2 class) |

### Avionics

| Component | Selection | Notes |
|-----------|-----------|-------|
| Flight Controller | Cube Orange+ | ArduCopter firmware |
| GNSS | Here 4 | Selected over Here 3+ |
| Companion Computer | Raspberry Pi CM4/5 | Mounted via Ochin Tiny Carrier Board V2 |
| Camera Option 1 (RGB) | SIYI A8 Mini | Monocular Ethernet RTSP gimbal (validates claims 2,4,19) |
| Camera Option 2 (Thermal) | SIYI ZT30 | Dual optical/thermal payload (validates claim 11) |
| Modem | 5G Cellular | AT command interface |
| Telemetry Radio | RFD 868 MHz | Bidirectional, ground station link |
| RC | Taranis+ TX | 2.4 GHz, direct to RX |

### Camera System — Patent Claim Mapping

**SIYI A8 Mini (Primary — RGB):**

- Ethernet RTSP stream → direct to BlueOS pipeline
- Focal length accessible via SDK/RTSP headers → **claim 4**
- Continuous gimbal pitch telemetry (θ) → **claim 2, 19** (vertical alignment)
- S.Bus/UART gimbal control from Pixhawk

**SIYI ZT30 (Multispectral — RGB + Thermal):**

- Dual RTSP channels (visible + LWIR) over single Ethernet
- Cross-examination: thermal profile confirms person classification in low-light → **claim 11**
- Both streams feed into `mavlink_safety_monitor.py` for fused detection

### Power Budget (Hover)

| Load | Current |
|------|---------|
| Motors (4× @ 700g thrust) | 15.2–17.2 A |
| Avionics (Pixhawk + Pi + 5G + Gimbal) | ~3.5 A |
| **Total hover** | **18.7–20.7 A** |
| Endurance (8Ah 6S) | ~23 min hover |

## Software Architecture

### BlueOS Companion Stack

```
┌────────────────────────────────────────────────────────────┐
│  Raspberry Pi CM4/5 — BlueOS                               │
│                                                            │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │ MAVLink      │  │ 5G Modem      │  │ Camera/RTSP    │  │
│  │ Proxy        │  │ (AT commands) │  │ Stream         │  │
│  └──────┬───────┘  └───────┬───────┘  └───────┬────────┘  │
│         │                  │                   │           │
│         │ Ethernet         │ USB               │ Ethernet  │
└─────────┼──────────────────┼───────────────────┼───────────┘
          │                  │                   │
          ▼                  ▼                   ▼
   Cube Orange+         ZeroTier VPN        SIYI Gimbal
   (ArduCopter)              │             (RGB / Thermal)
                             │ 5G Network
                             ▼
              ┌──────────────────────────────┐
              │  Ground Server / GCS         │
              │                              │
              │  ┌────────────────────────┐  │
              │  │ mavlink_safety_monitor │  │
              │  │ (patent claims 7,8,10) │  │
              │  └────────────────────────┘  │
              │                              │
              │  Mission Planner / QGC       │
              │  RFD 868 telemetry backup    │
              └──────────────────────────────┘
```

### Communication Links

| Link | Medium | Purpose | Latency |
|------|--------|---------|---------|
| RC control | 2.4 GHz (Taranis) | Manual pilot override | <20ms |
| Telemetry | RFD 868 MHz | Backup MAVLink, failsafe | ~50ms |
| Primary data | 5G → ZeroTier VPN | MAVLink + video + safety commands | ~30-80ms |
| Safety command-back | 5G → ZeroTier → BlueOS → Pixhawk | HOLD/LOITER on 1:1 violation | ~50-100ms |

### GNSS Architecture Options

**Option A — Independent (Two GNSS):**
```
Here 4 → Cube Orange+ (native GNSS)
5G Modem → RPi/BlueOS (network positioning)
Cube ↔ RPi via MAVLink serial
```

**Option B — Combined/Injected:**
```
Here 4 → RPi/BlueOS
5G Modem → RPi/BlueOS
RPi blends/processes → injects combined GNSS into Cube
```

Option A is simpler and safer (Cube has native GNSS for failsafe). Option B enables RTK-over-5G and network-assisted positioning research.

## Patent Validation on This Platform

### Claims Demonstrated

| Claim | How This Platform Validates |
|-------|----------------------------|
| 1: Detect + calculate + compare + issue | Safety monitor on ground server, video over 5G |
| 2: Gimbal for rotation | SIYI gimbal with continuous pitch feedback |
| 4: Focal length from metadata | RTSP stream headers / SIYI SDK / MAVLink CAMERA_INFORMATION |
| 7: Prevent further approach | Ground server sends GUIDED_LOITER via ZeroTier → BlueOS → Cube |
| 8: Initiated by receiving unit | The ground server (receiving unit) triggers the hold command |
| 10: External communication device | Ground server is external, communicates over 5G/3GPP |
| 11: Multispectral | SIYI ZT30 dual RGB+thermal over single Ethernet |
| 15 (PCT): 3GPP wireless network | 5G is the communication bearer |
| 19: Fraction x=2 if centered by gimbal | Gimbal auto-adjusts pitch to center target in frame |

### Key Advantage Over Commercial Drones

Unlike the Autel/DJI validation (proprietary, closed MQTT), this platform:
- Runs entirely on **open-source** software (ArduPilot + BlueOS + MAVLink)
- Uses **standard 3GPP 5G** as the communication network
- Allows **full bidirectional control** — actual flight commands, not just telemetry
- Is **reproducible** by anyone — strengthens patent prosecution
- Provides **accessible metadata** (focal length, gimbal pitch) from open protocols

## Development Status

### ✅ Completed

- [x] Physical frame assembly (Holybro X650)
- [x] ArduCopter base configuration
- [x] ESC power soldering
- [x] Radio system / Taranis calibration
- [x] 3D printing custom mounting brackets
- [x] BEC soldering and secondary power routing
- [x] First structural test flight
- [x] Motor direction and load testing
- [x] Custom telemetry wiring cable fabrication
- [x] `mavlink_safety_monitor.py` — detection + lateral distance + command-back
- [x] `mavlink_mqtt_bridge.py` — MAVLink ↔ MQTT bidirectional bridge

### 🟡 In Progress

- [ ] GNSS evaluation: comparing Option A vs Option B architectures
- [ ] 5G modem AT command automation scripts
- [ ] Power brick replacement (voltage readings inconsistent)
- [ ] BlueOS installation on companion RPi

### 🔴 Next Steps

- [ ] BlueOS + ZeroTier deployment on RPi CM4
- [ ] 5G modem integration with BlueOS (network verified)
- [ ] Camera gimbal physical mounting and Ethernet interface setup (SIYI A8 Mini or ZT30)
- [ ] RTSP focal length extraction script (claim 4 metadata validation)
- [ ] End-to-end patent demo: detect person → calculate distance → HOLD over 5G
- [ ] Flight test: safety monitor triggers hold during controlled approach to person
- [ ] Grafana dashboard (from `dronedata` repo: Telegraf → InfluxDB → Grafana)
- [ ] Integrate with SecuringSkies MQTT infrastructure for live demo

## Integration with Existing Work

| Repository | Role |
|-----------|------|
| `lmfwire/detection-with-drone` | Safety monitor code, CV models, patent validation |
| `lmfwire/dronedata` | Telemetry pipeline (MAVLink → MQTT → InfluxDB → Grafana) |
| `rwiren/autel-mission-control` | Reference for MQTT command architecture |
| `lmfwire/lmf-isac-docs` | Flight operations manual, EHS risk assessment |

## Suppliers & References

- **Frame:** [Holybro X650](https://holybro.com/)
- **Flight Controller:** [CubePilot Cube Orange+](https://www.cubepilot.org/)
- **GNSS:** [CubePilot Here 4](https://www.cubepilot.org/)
- **Motors:** [T-Motor MN4010](https://store.tmotor.com/)
- **Camera (RGB):** [SIYI A8 Mini](https://siyi.biz/a8-mini)
- **Camera (Thermal):** [SIYI ZT30](https://siyi.biz/zt30)
- **BlueOS:** [Blue Robotics BlueOS](https://blueos.cloud/docs/latest/usage/overview/)
- **ArduPilot:** [ardupilot.org](https://ardupilot.org/)
- **ZeroTier:** [zerotier.com](https://www.zerotier.com/)
- **Telemetry:** [RFDesign RFD868](http://rfdesign.com.au/)
- **Carrier Board:** [Ochin Tiny V2](https://www.seeedstudio.com/Ochin-Tiny-Carrier-Board-V2-for-Raspberry-Pi-CM4-p-5887.html)
