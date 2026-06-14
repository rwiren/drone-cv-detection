# Drone CV Detection

Multi-platform aerial computer vision for person detection and parking occupancy monitoring.

## Safety Distance System — EU 1:1 Rule

The system detects persons from a UAV, calculates lateral distance using monocular camera geometry, compares it against `determined_value × altitude`, and issues alerts when the EU 1:1 rule is violated.

| Capability | DJI M2EA | Autel MAX 4T V2 xe | DJI Avata 360 |
|---|---|---|---|
| Object detection (YOLO) | VisDrone YOLOv8s on RGB | VisDrone + COCO + onboard AI | Dual-fisheye → v8m + COCO ensemble |
| Lateral distance calculation | GSD + ray-cast from SRT | LRF direct measurement | GSD from perspective crop + SRT |
| Gimbal pitch from metadata | DJI SRT `Pitch:` field | MQTT OSD `gimbal_pitch` | N/A (360° omnidirectional) |
| Multispectral detection | RGB + Thermal | RGB + Thermal + onboard AI | RGB only (dual-fisheye) |
| Alert/message output | Offline analysis | **Real-time MQTT** | Offline analysis |
| Coverage | Single direction (gimbal) | Single direction (gimbal) | **360° all directions** |

## Key Results

| Pipeline | Detection Rate | Max Confidence | Model |
|----------|---------------|----------------|-------|
| Autel onboard AI (thermal) | Real-time | N/A (firmware) | Built-in |
| M2EA thermal + YOLOv8 | Per-frame | 0.85 | VisDrone v8s |
| Avata 360 LRF (dual-fisheye) | ~70% | 0.90 | Ensemble |
| Avata 360 8K (equirectangular) | **86%** (32/37 frames) | 0.79 | Ensemble |

## Platforms

- [DJI Mavic 2 Enterprise Advanced](platforms/m2ea.md) — Thermal + RGB, safety distance
- [Autel EVO MAX 4T V2](platforms/autel.md) — Onboard AI, MQTT real-time
- [DJI Avata 360](platforms/avata360.md) — 8K 360° omnidirectional

## Research Papers

- [Autel EVO MAX 4T V2 AI Verification](autel-verification.md) — Novel finding: firmware coordinate projection mismatch
- [DJI Avata 360 Pipeline Analysis](avata360-analysis.md) — Novel findings: file format architecture, dual pipeline comparison

## Source Code

Full README and repository: [github.com/rwiren/drone-cv-detection](https://github.com/rwiren/drone-cv-detection)
