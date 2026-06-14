# Drone CV — Detection & Parking Monitor

[![Version](https://img.shields.io/badge/Version-v0.7.0-yellow.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen.svg)](#)
[![Internal](https://img.shields.io/badge/Ericsson-Internal_R%26D-003C71.svg)](#)
[![Patent](https://img.shields.io/badge/Patent-WO2025034145A1-red.svg)](https://patents.google.com/patent/WO2025034145A1/en)
[![Pages](https://img.shields.io/badge/📖_Documentation-Pages-blue.svg)](https://gitlabpages-central.internal.ericsson.com/detection-with-drone-a7b724/)

> **📖 Full documentation:** [https://gitlabpages-central.internal.ericsson.com/detection-with-drone-a7b724/](https://gitlabpages-central.internal.ericsson.com/detection-with-drone-a7b724/)

Multi-platform aerial computer vision research with **two core use cases** validated across three drone platforms.

## Use Cases

| Use Case | DJI M2EA | Autel MAX 4T V2 xe | DJI Avata 360 |
|----------|----------|-------------------|---------------|
| **Person Detection & 1:1 Rule** | GSD formula + SRT | LRF ground truth + MQTT | 360° dual-fisheye + ensemble |
| **Parking Occupancy** | VisDrone + ByteTrack | VisDrone + SAHI + onboard AI | Nadir perspective crops |

## Quick Start

```bash
# 360° person detection (DJI Avata 360)
python src/avata360_monitor.py --video DJI_...LRF --srt DJI_...SRT \
  --model yolov8s.pt --aerial-model models/visdrone_yolov8m_1280_best.pt

# Vehicle detection
python src/detect.py --input image.jpg --model models/visdrone_yolov8s_1280_best.pt

# 1:1 rule monitor (Autel MQTT)
python src/rule_monitor.py --live --broker localhost --port 1883
```

## Models

| Model | mAP50 | Best For | Inference |
|-------|-------|----------|-----------|
| `visdrone_yolov8m_1280_best.pt` | **0.581** | Aerial person (>5m) | 7.5ms GPU |
| `visdrone_yolov8s_1280_best.pt` | 0.532 | Parking occupancy | 1.6ms GPU |
| `yolov8s.pt` (COCO) | — | Close-range person (<3m) | ~300ms CPU |

## Project Structure

```
src/
├── avata360_monitor.py    — 360° person detection (dual-fisheye + ensemble)
├── rule_monitor.py        — 1:1 rule monitor (replay + live MQTT)
├── lateral_distance.py    — Lateral distance calculation (DJI M2EA + SRT)
├── parking_monitor.py     — Parking occupancy (RGB + thermal)
├── autel_telemetry.py     — Autel MQTT parser + bbox calibration
├── compare_models.py      — Model comparison tool
├── flight_map.py          — Interactive Folium flight map
├── vehicle_tracker.py     — ByteTrack tracking
├── detect.py              — YOLO detection wrapper
└── yolo_car_counter.py    — Video car counter
```

## Links

- **📖 Documentation:** [GitLab Pages](https://gitlabpages-central.internal.ericsson.com/detection-with-drone-a7b724/)
- **🔗 Companion:** [autel-mission-control](https://github.com/rwiren/autel-mission-control)
- **📄 Patent:** [WO2025034145A1](https://patents.google.com/patent/WO2025034145A1/en)
- **📋 Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **🤝 Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
