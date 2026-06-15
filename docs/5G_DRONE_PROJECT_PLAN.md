# 5G Drone Development — Project Plan

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
| Companion Computer | Raspberry Pi 4/5 (CM) | Running BlueOS |
| Modem | 5G Cellular | AT command interface |
| Telemetry Radio | RFD 868 MHz | Bidirectional, ground station link |
| RC | Taranis+ TX | 2.4 GHz, direct to RX |

### Power Budget (Hover)

| Load | Current |
|------|---------|
| Motors (4× @ 700g thrust) | 15.2–17.2 A |
| Avionics (Pixhawk + Pi + 5G) | ~3.0 A |
| **Total hover** | **18.2–20.2 A** |
| Endurance (8Ah 6S) | ~24 min hover |

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
   Cube Orange+         ZeroTier VPN        SIYI/IP Camera
   (ArduCopter)              │
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
| 4: Focal length from metadata | Camera EXIF via RTSP metadata or MAVLink CAMERA_INFORMATION |
| 7: Prevent further approach | Ground server sends GUIDED_LOITER via ZeroTier → BlueOS → Cube |
| 8: Initiated by receiving unit | The ground server (receiving unit) triggers the hold command |
| 10: External communication device | Ground server is external, communicates over 5G/3GPP |
| 11: Multispectral | Supports thermal + RGB cameras on ethernet gimbal |
| 15 (PCT): 3GPP wireless network | 5G is the communication bearer |

### Key Advantage Over Commercial Drones

Unlike the Autel/DJI validation (proprietary, closed MQTT), this platform:
- Runs entirely on **open-source** software (ArduPilot + BlueOS + MAVLink)
- Uses **standard 3GPP 5G** as the communication network (not proprietary radio)
- Allows **full bidirectional control** — not just telemetry but actual flight commands
- Is **reproducible** by anyone — strengthens patent prosecution

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
- [x] `mavlink_safety_monitor.py` — software ready (detection + lateral distance + command-back)
- [x] `mavlink_mqtt_bridge.py` — MAVLink ↔ MQTT bidirectional bridge

### 🟡 In Progress

- [ ] GNSS evaluation: comparing Option A vs Option B architectures
- [ ] 5G modem AT command automation scripts
- [ ] Power brick replacement (voltage readings inconsistent)
- [ ] BlueOS installation on companion RPi

### 🔴 Next Steps

- [ ] BlueOS + ZeroTier deployment on RPi CM4
- [ ] 5G modem integration with BlueOS (network verified)
- [ ] Camera gimbal (SIYI A8 or similar) — ethernet RTSP stream
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
- **BlueOS:** [Blue Robotics BlueOS](https://blueos.cloud/docs/latest/usage/overview/)
- **ArduPilot:** [ardupilot.org](https://ardupilot.org/)
- **ZeroTier:** [zerotier.com](https://www.zerotier.com/)
- **Telemetry:** [RFDesign RFD868](http://rfdesign.com.au/)
