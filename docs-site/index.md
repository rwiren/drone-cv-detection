# Drone CV Detection

[![Version](https://img.shields.io/badge/version-1.4.0-blue)](https://github.com/rwiren/drone-cv-detection/blob/main/CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/rwiren/drone-cv-detection/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)](#)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](#)
[![YOLOv8](https://img.shields.io/badge/YOLO-v8-purple.svg)](https://docs.ultralytics.com/)
[![Platforms](https://img.shields.io/badge/Platforms-3_Drones-teal)](#)

Multi-platform aerial computer vision research — **four use cases** validated across three drone platforms.

## Use Cases

| # | Use Case | Status | Key Result |
|---|----------|--------|------------|
| UC1 | **Person Detection & 1:1 Safety Rule** | ✅ Validated | Lateral distance enforcement across 3 platforms |
| UC2 | **Parking Occupancy** | ✅ Validated | 104 vehicles from 134m nadir |
| UC3 | **[GNSS-Denied Navigation](gnss-denied.md)** | ✅ Validated | Median 5.8m accuracy (CNN cross-view) |
| UC4 | **[3D Gaussian Splatting](gaussian-splatting.md)** | ✅ Validated | PSNR 34.2 dB photorealistic 3D |

## UC1: Person Detection & 1:1 Safety Rule

The system detects persons from a UAV, calculates lateral distance using monocular camera geometry, compares it against `determined_value × altitude`, and issues alerts when the safety rule is violated.

| Capability | DJI M2EA | Autel MAX 4T V2 xe | DJI Avata 360 |
|---|---|---|---|
| Object detection (YOLO) | VisDrone YOLOv8s on RGB | VisDrone + COCO + onboard AI | Dual-fisheye → v8m + COCO ensemble |
| Lateral distance calculation | GSD + ray-cast from SRT | LRF direct measurement | GSD from perspective crop + SRT |
| Gimbal pitch from metadata | DJI SRT `Pitch:` field | MQTT OSD `gimbal_pitch` | N/A (360° omnidirectional) |
| Multispectral detection | RGB + Thermal | RGB + Thermal + onboard AI | RGB only (dual-fisheye) |
| Alert/message output | Offline analysis | **Real-time MQTT** | Offline analysis |
| Coverage | Single direction (gimbal) | Single direction (gimbal) | **360° all directions** |

## UC2: Parking Occupancy

| Platform | Method | Altitude | Vehicles Detected |
|----------|--------|----------|-------------------|
| **DJI M2EA** | VisDrone 1280 | 70m | 55 cars + 5 peds + 2 trucks |
| **Autel MAX 4T** | VisDrone 1280 | 80m | 95 cars + 3 vans |
| **Autel MAX 4T** | Thermal stream | 80m | 43 cars + 29 vans |
| **DJI Avata 360** | Nadir perspective crop | 21-48m | 38-46 vehicles |

## Key Results

| Pipeline | Detection Rate | Max Confidence | Model |
|----------|---------------|----------------|-------|
| Autel onboard AI (thermal) | Real-time | N/A (firmware) | Built-in |
| M2EA thermal + YOLOv8 | Per-frame | 0.85 | VisDrone v8s |
| Avata 360 LRF (dual-fisheye) | ~70% | 0.90 | Ensemble |
| Avata 360 8K (equirectangular) | **86%** (32/37 frames) | 0.79 | Ensemble |
| **GNSS-Denied positioning** | — | — | **5.8m median** |
| **Gaussian Splatting** | — | — | **PSNR 34.2 dB** |

## Documentation

- **[Platforms](platforms/m2ea.md)** — DJI M2EA, Autel MAX 4T, DJI Avata 360
- **[Sample Detections](samples/detections.md)** — Images from all platforms
- **[Validation Results](validation.md)** — Per-platform per-use-case tables
- **[Capabilities](capabilities.md)** — What works, PoC, limitations
- **[3D Gaussian Splatting](gaussian-splatting.md)** — Photorealistic 3D reconstruction
- **[GNSS-Denied Navigation](gnss-denied.md)** — Visual positioning (5.8m)
- **[Calibration](calibration/index.md)** — MQTT FOV mismatch, affine correction
- **[Models & Training](models/training.md)** — 4 training runs, VisDrone + domain adaptation
- **[Setup & Usage](usage.md)** — CLI commands, installation
- **[Research Papers](autel-verification.md)** — Original findings (firmware FOV, 360° architecture)

## Source Code

Repository: [github.com/rwiren/drone-cv-detection](https://github.com/rwiren/drone-cv-detection)
