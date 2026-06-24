# Drone CV — Multi-Platform Aerial Computer Vision

[![Version](https://img.shields.io/badge/Version-v1.4.0-blue.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](#)
[![Docs](https://img.shields.io/badge/📖_Documentation-Pages-blue.svg)](https://rwiren.github.io/drone-cv-detection/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](#)
[![YOLOv8](https://img.shields.io/badge/YOLO-v8-purple.svg)](https://docs.ultralytics.com/)

> **📖 Full documentation:** [https://rwiren.github.io/drone-cv-detection/](https://rwiren.github.io/drone-cv-detection/)

Multi-platform aerial computer vision research with **four use cases** validated across three drone platforms.

| Autel — 95 cars at 80m (4K) | Autel — thermal person (18.8m) | Avata 360 — person 0.90 (dual-fisheye) |
|---|---|---|
| <img src="docs-site/images/MAX_0042_visdrone1280.jpg" width="300"> | <img src="docs-site/images/IRX_0043_person_overlay.jpg" width="300"> | <img src="docs-site/images/detect_2m_close.jpg" width="300"> |

## Use Cases

| # | Use Case | Key Result | Documentation |
|---|----------|------------|---------------|
| UC1 | **Person Detection & 1:1 Safety Rule** | Lateral distance enforcement, 3 platforms | [→ Details](https://rwiren.github.io/drone-cv-detection/uc1-safety/) |
| UC2 | **Parking Occupancy** | 104 vehicles from 134m nadir | [→ Details](https://rwiren.github.io/drone-cv-detection/uc2-parking/) |
| UC3 | **GNSS-Denied Navigation** | Median 5.8m (CNN cross-view) | [→ Details](https://rwiren.github.io/drone-cv-detection/gnss-denied/) |
| UC4 | **3D Gaussian Splatting** | PSNR 34.2 dB, photorealistic 3D | [→ Details](https://rwiren.github.io/drone-cv-detection/gaussian-splatting/) |

## Quick Start

```bash
# Person detection — DJI Avata 360
python src/avata360_monitor.py --video DJI_...LRF --srt DJI_...SRT \
  --model yolov8s.pt --aerial-model models/visdrone_yolov8m_1280_best.pt

# Vehicle detection
python src/detect.py --input image.jpg --model models/visdrone_yolov8s_1280_best.pt

# 1:1 rule monitor (live MQTT)
python src/rule_monitor.py --live --broker localhost --port 1883
```

## Models

| Model | mAP50 | Best For | Inference |
|-------|-------|----------|-----------|
| `visdrone_yolov8m_1280_best.pt` | **0.581** | Aerial person detection (>5m) | 7.5ms GPU |
| `combined_v8m_1280_best.pt` | 0.580 | Avata 360 domain-adapted | 7.5ms GPU |
| `visdrone_yolov8s_1280_best.pt` | 0.532 | Parking occupancy (fast) | 1.6ms GPU |

## Project Structure

```
src/
├── lateral_distance.py    — Patent formula: lateral distance from bbox geometry
├── rule_monitor.py        — 1:1 safety rule enforcement (replay + live MQTT)
├── avata360_monitor.py    — 360° omnidirectional person detection
├── parking_monitor.py     — RGB + thermal parking occupancy
├── autel_telemetry.py     — Autel MQTT OSD parser + bbox calibration
├── config.py              — Centralized constants and camera specs
├── cli.py                 — Unified CLI entry point
notebooks/
├── gaussian_splat_avata360_v4.ipynb  — 3D Gaussian Splatting (Colab A100)
├── gnss_denied_crossview_training.ipynb — GNSS-denied CNN training
tests/                     — 48 unit tests
```

## Documentation

| Section | Link |
|---------|------|
| **All Use Cases** | [Use Cases →](https://rwiren.github.io/drone-cv-detection/) |
| Platforms (M2EA, Autel, Avata 360) | [Platforms →](https://rwiren.github.io/drone-cv-detection/platforms/m2ea/) |
| Sample Detections | [Samples →](https://rwiren.github.io/drone-cv-detection/samples/detections/) |
| Calibration (MQTT FOV, Affine) | [Calibration →](https://rwiren.github.io/drone-cv-detection/calibration/) |
| Models & Training | [Training →](https://rwiren.github.io/drone-cv-detection/models/training/) |
| Validation Results | [Validation →](https://rwiren.github.io/drone-cv-detection/validation/) |
| Research Papers | [Papers →](https://rwiren.github.io/drone-cv-detection/autel-verification/) |

## References

- **WO2025034145A1** — ["Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"](https://patents.google.com/patent/WO2025034145A1/en) (2025)
- [VisDrone2019](https://github.com/VisDrone/VisDrone-Dataset) — Aerial object detection dataset
- [Ultralytics YOLOv8](https://docs.ultralytics.com/) — Detection framework
- [SecuringSkies Platform](https://github.com/rwiren/securingskies-platform) — Multi-agent fusion (companion project)

## License

MIT — see [LICENSE](LICENSE) for details.
