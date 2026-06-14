# Drone CV — Detection & Parking Monitor

Multi-platform aerial computer vision research with **two core use cases** validated across three drone platforms:

1. **[Person Detection & 1:1 Safety Rule](use-cases/person-detection.md)** — detect persons, calculate lateral distance, enforce EU 1:1 rule
2. **[Parking Occupancy Monitoring](use-cases/parking.md)** — count vehicles, identify free slots, thermal fusion

## Platform Matrix

| Use Case | DJI M2EA | Autel MAX 4T V2 xe | DJI Avata 360 |
|----------|----------|-------------------|---------------|
| **1:1 Person Detection** | GSD formula + SRT | LRF ground truth + MQTT | 360° dual-fisheye + ensemble |
| **Parking Occupancy** | VisDrone + ByteTrack | VisDrone + SAHI + onboard AI | Nadir perspective crops |

## Validation Results

### Person Detection & 1:1 Rule

| Platform | Method | Alt Range | Model | Best Conf | Validated |
|----------|--------|-----------|-------|-----------|-----------|
| **DJI M2EA** | GSD + SRT pitch | 15-70m | VisDrone 1280 | 0.49 at 70m, 0.34 at 15m | ✅ |
| **Autel MAX 4T** | LRF + MQTT GPS | 18-26m | Onboard AI (thermal) | — | ✅ 4 violations flagged |
| **DJI Avata 360** (LRF) | Dual-fisheye + ensemble | ~2-7m | COCO + VisDrone v8m | 0.90 at 2m, 0.63 at ~7m | ✅ |
| **DJI Avata 360** (8K) | Equirectangular + ensemble | 2-32m | COCO + VisDrone v8m | 0.79, **86% detection rate** | ✅ |

### Parking Occupancy

| Platform | Method | Alt | Vehicles Detected | Validated |
|----------|--------|-----|-------------------|-----------|
| **DJI M2EA** | VisDrone 1280 (native) | 70m | 55 cars + 5 peds + 2 trucks | ✅ |
| **Autel MAX 4T** | VisDrone 1280 (native) | 80m | 95 cars + 3 vans | ✅ |
| **Autel MAX 4T** | VisDrone 1280 (thermal) | 80m | 43 cars + 29 vans | ✅ |

## Quick Start

```bash
# 360° person detection
python src/avata360_monitor.py --video DJI_...LRF --srt DJI_...SRT \
  --model yolov8s.pt --aerial-model models/visdrone_yolov8s_1280_best.pt

# Vehicle detection
python src/detect.py --input image.jpg --model models/visdrone_yolov8s_1280_best.pt

# 1:1 rule monitoring (live MQTT)
python src/rule_monitor.py --live --broker localhost --port 1883
```
