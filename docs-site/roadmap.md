# Roadmap

## Completed ✅

- [x] **360° full pipeline** — dual-fisheye extraction with correct equidistant projection
- [x] **Colab A100 training** — YOLOv8s (mAP50 0.532) and YOLOv8m (mAP50 0.581) at imgsz=1280
- [x] **Dual-model ensemble** — v8m (aerial >3m) + COCO (close <3m), validated on Avata 360
- [x] **DJI M2EA person re-validation** — VisDrone 1280 detects pedestrians at 70m (0.86 conf)
- [x] **3-platform validation** — all drones tested with 1280 models for both use cases
- [x] **Combined 3-platform training** — VisDrone + 1246 Avata 360 crops (mAP50 0.580)
- [x] **Full Avata 360 8K processing** — stitched equirect from DJI Studio (86% detection rate, 32/37 frames)

## Near-term

- [ ] **Thermal person detection** — fine-tune YOLOv8 on existing IR video frames (Autel IRX_*.MP4)
- [ ] **Real-time MQTT monitor** — validate live 1:1 rule alerting during next flight session

## Medium-term

- [ ] **Thermal person detection model** — fine-tune YOLOv8 on IR images (night/low-light)
- [ ] **Real-time MQTT monitor deployment** — live 1:1 rule alerting during flight
- [ ] **Pitch-dependent homography** — fix angled-view bbox overlay (currently 87px error)
- [ ] **Parking slot geometry** — define static ROIs for per-slot occupancy counting
- [ ] **Multi-sensor fusion** — combine RGB + thermal confidence scores for robust detection
- [ ] **Tracker de-fragmentation** — cluster Autel's 123 IDs → actual person count

## Research Directions

- [ ] **360° spherical object detection** — native dual-fisheye inference (no perspective extraction)
- [ ] **Depth estimation from 360°** — monocular depth from fisheye for distance without GSD
- [ ] **SecuringSkies integration** — publish 1:1 rule violations to MQTT for SITREP generation
- [ ] **Edge deployment** — run YOLO on Jetson/RPi connected to drone RTSP stream
- [ ] **Multi-drone collaborative detection** — A-Mesh networked swarm with shared detections
- [ ] **Temporal tracking across 360° views** — consistent IDs as persons move between perspective tiles
