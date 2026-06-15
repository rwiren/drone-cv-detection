# MAVLink Safety Monitor — Patent WO2025034145A1 Proof-of-Concept

Implements claims 1, 4, 5, 6, 7, 8, 10 on open-source ArduPilot/MAVLink.

## Architecture

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────────┐
│  Pixhawk/       │ MAVLink │  mavlink_    │  MQTT   │  mavlink_safety_    │
│  ArduPilot      │◄───────►│  mqtt_bridge │◄───────►│  monitor.py         │
│  (on drone)     │  UDP    │  .py         │  TLS    │  (external device)  │
└─────────────────┘         └──────────────┘         └─────────────────────┘
                                                              │
                                                     ┌────────┴────────┐
                                                     │ YOLO Detection  │
                                                     │ + Lateral Dist  │
                                                     │ + 1:1 Compare   │
                                                     └─────────────────┘
```

## Claim Mapping

| Patent Claim | Implementation |
|-------------|----------------|
| 1: Detect + calculate + compare + issue message | `process_frame()` → full pipeline |
| 4: Focal length from metadata or sensor width | `CameraConfig.focal_length_px` property |
| 5: Select shortest distance | `min(distances)` across all detected persons |
| 6: Determined value ≥ 1 | `--safety-value` argument (default 1.0) |
| 7: Prevent further approach | `_send_hold_command()` → MAV_CMD_NAV_LOITER |
| 8: Prevention initiated by receiving unit | Bridge receives MQTT command, sends to drone |
| 10: Communication device external to UAV | Monitor runs on ground station/server |
| 11: Multispectral | Supports thermal + RGB camera inputs |

## Usage

### 1. Start the MAVLink ↔ MQTT Bridge (on companion computer or GCS)

```bash
python src/mavlink_safety/mavlink_mqtt_bridge.py \
  --mav udp:127.0.0.1:14550 \
  --broker mqtt.server.com --port 8883 \
  --username user --password pass
```

### 2. Start the Safety Monitor (on external server — claim 10)

```bash
python src/mavlink_safety/mavlink_safety_monitor.py \
  --broker mqtt.server.com --port 8883 \
  --camera rtsp://drone:8554/stream \
  --model models/visdrone_yolov8m_1280_best.pt \
  --safety-value 1.0 \
  --username user --password pass
```

### 3. Simulated Testing (no hardware)

```bash
# Terminal 1: Simulated MAVLink
mavproxy.py --master=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551

# Terminal 2: Bridge
python src/mavlink_safety/mavlink_mqtt_bridge.py --mav udp:127.0.0.1:14551 --no-tls

# Terminal 3: Monitor with webcam
python src/mavlink_safety/mavlink_safety_monitor.py --camera 0 --no-tls --broker localhost --port 1883
```

## Dependencies

```
pip install pymavlink paho-mqtt ultralytics opencv-python-headless
```

## References

- [MAVLink Protocol](https://mavlink.io/en/)
- [ArduPilot MAVLink Commands](https://ardupilot.org/dev/docs/mavlink-commands.html)
- [MAVProxy](https://ardupilot.org/mavproxy/)
- Patent: [WO2025034145A1](https://patents.google.com/patent/WO2025034145A1/en)
