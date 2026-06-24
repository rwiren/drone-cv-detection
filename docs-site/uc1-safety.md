# UC1: Person Detection & 1:1 Safety Rule

Detect persons from UAV, calculate lateral distance, enforce the 1:1 safety rule.

## How It Works

The system uses monocular camera geometry to calculate horizontal distance from the drone to detected persons:

1. **YOLO detects persons** in the camera frame
2. **Bounding box height** + focal length + gimbal pitch → distance estimate
3. **Compare** lateral distance against `safety_value × altitude`
4. **Alert** if the rule is violated (person too close relative to flight height)

## Per-Platform Implementation

| Capability | DJI M2EA | Autel MAX 4T V2 xe | DJI Avata 360 |
|---|---|---|---|
| Object detection | VisDrone YOLOv8s on RGB | VisDrone + onboard AI | Dual-fisheye → ensemble |
| Distance method | GSD + ray-cast from SRT | LRF direct measurement | GSD from perspective crop |
| Gimbal pitch | DJI SRT `Pitch:` field | MQTT OSD `gimbal_pitch` | N/A (360°) |
| Multispectral | RGB + Thermal | RGB + Thermal + AI | RGB only |
| Output | Offline analysis | **Real-time MQTT** | Offline analysis |
| Coverage | Single direction | Single direction | **360° all directions** |

## Validation Results

| Platform | Method | Alt Range | Best Conf | Result |
|----------|--------|-----------|-----------|--------|
| **DJI M2EA** | GSD + SRT pitch | 15-70m | 0.49 at 70m | ✅ Detects pedestrians |
| **Autel MAX 4T** | LRF + MQTT GPS | 18-26m | — | ✅ 4 violations flagged |
| **Autel MAX 4T** | RGB + VisDrone 1280 | 18-26m | — | ✅ 2 persons in 4K |
| **DJI Avata 360** | Dual-fisheye + ensemble | 2-7m | 0.90 at 2m | ✅ Full descent |

## Usage

```bash
# Lateral distance calculation (DJI M2EA + SRT)
python src/lateral_distance.py --video DJI_0042.MP4 --srt DJI_0042.SRT \
  --model models/visdrone_yolov8s_1280_best.pt

# 1:1 rule monitor (Autel MQTT, live)
python src/rule_monitor.py --live --broker localhost --port 1883

# 360° person detection (DJI Avata 360)
python src/avata360_monitor.py --video DJI_...LRF --srt DJI_...SRT \
  --model yolov8s.pt --aerial-model models/visdrone_yolov8m_1280_best.pt
```

## Reference

- Patent: [WO2025034145A1](https://patents.google.com/patent/WO2025034145A1/en) — "Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object" (2025)
