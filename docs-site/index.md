# Drone CV Detection

Multi-platform aerial computer vision for person detection and parking occupancy monitoring.

## Platforms

| Platform | Sensor | Use Case | Status |
|----------|--------|----------|--------|
| DJI Mavic 2 Enterprise Advanced | Thermal + RGB | Person detection, safety distance | ✅ Complete |
| Autel EVO MAX 4T V2 | Thermal + Wide + Zoom | Onboard AI verification | ✅ Complete |
| DJI Avata 360 | Dual 1/1.1" fisheye (8K 360°) | Omnidirectional parking monitoring | ✅ Complete |

## Key Results

| Pipeline | Detection Rate | Max Confidence | Model |
|----------|---------------|----------------|-------|
| Autel onboard AI (thermal) | Real-time | N/A (firmware) | Built-in |
| M2EA thermal + YOLOv8 | Per-frame | 0.85 | VisDrone v8s |
| Avata 360 LRF (dual-fisheye) | ~70% | 0.90 | Ensemble |
| Avata 360 8K (equirectangular) | **86%** | 0.79 | Ensemble |

## Research Papers

- [Autel EVO MAX 4T V2 AI Verification](autel-verification.md) — Novel finding: firmware coordinate projection mismatch
- [DJI Avata 360 Pipeline Analysis](avata360-analysis.md) — Novel findings: file format architecture, dual pipeline comparison

## Repository

Source code and full README: [github.com/rwiren/drone-cv-detection](https://github.com/rwiren/drone-cv-detection)
