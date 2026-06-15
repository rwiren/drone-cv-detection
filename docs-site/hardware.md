# Hardware

## Drone Platforms

### DJI Mavic 2 Enterprise Advanced (M2EA)

- **Visual:** 1/2" 48MP, 24mm eq. f/2.8, FOV 84°, max 8000×6000
- **Thermal:** 640×512 @30Hz, 9mm (38mm eq.), uncooled VOx, 12μm pitch, DFOV ~57°
- **Gimbal:** 3-axis, tilt -90°→+30°, pan ±75°
- **Telemetry:** SRT sidecar per frame

### Autel EVO MAX 4T V2 xe

- **Wide:** 1/1.28" 50MP, 4.5mm (23mm eq.) f/1.9, FOV 85°, max 8192×6144
- **Zoom:** 1/2" 48MP, 11.8-43.3mm (64-234mm eq.) f/2.8-4.8, max 8000×6000
- **Thermal:** 640×512, 13mm f/1.2, DFOV 42°, IFOV 0.92mrad, 12μm pitch, uncooled VOx
- **LRF:** ±1m accuracy, 1200m range
- **Firmware:** v1.9.1.219 | Controller: Smart Controller V3
- **Onboard AI:** vehicle (cls_id=3), person (cls_id=30), bicycle (cls_id=2) via MQTT

### DJI Avata 360

- **Dual-fisheye:** 2× 200° f/1.9 lenses (right = nadir, left = zenith)
- **Full-res .OSV:** single zenith lens (3840×3840)
- **Proxy .LRF:** 1920×960 (both lenses)
- **DJI Studio export:** 7680×3840 equirectangular
- **SRT telemetry:** 60fps (GPS, altitude, yaw, pitch per frame)
- **Stabilization:** RockSteady 3.0 (horizon lock regardless of FPV maneuvers)
- **Coverage:** 360° omnidirectional — no gimbal pointing required

## Compute

| Task | Hardware | Performance |
|------|----------|-------------|
| Inference (imgsz=640) | AMD Ryzen AI 7 PRO 350 (CPU) | ~0.3s/frame |
| Inference (SAHI) | CPU | ~0.3s/tile |
| Training (15ep, 640) | CPU | ~10h |
| Training (30ep, 1280) | NVIDIA A100 (Colab) | ~55 min (v8s), ~1.6h (v8m) |

## References

- [WO2025034145A1](https://patents.google.com/patent/WO2025034145A1/en) — "Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object" (Wirén, Grancharov — 2025)
- [EU 2019/947](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32019R0947) — EASA Open Category drone regulation (1:1 rule)
- [Autel Mission Control](https://github.com/rwiren/autel-mission-control) — MQTT bridge, DVR, Grafana dashboards (companion project)
- [VisDrone2019](https://github.com/VisDrone/VisDrone-Dataset) — Aerial object detection dataset
- [Ultralytics YOLOv8](https://docs.ultralytics.com/) — Detection, segmentation, tracking
- [SAHI](https://github.com/obss/sahi) — Slicing Aided Hyper Inference for small objects
