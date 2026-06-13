# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.4.0] - 2026-06-12
### Added
- **Combined VisDrone + Autel training** (6553 images, 15 epochs, ~10h CPU)
  - mAP50 all: 34.5% (was 29.5%), cars: 75.7% (was 72.0%), pedestrians: 37.2% (was 34.1%)
  - mAP50-95 cars: 50.8% — major improvement in localization accuracy
  - Model: `models/visdrone_autel_yolov8s_best.pt`
- SAHI sliced inference for high-res Autel images (4000×3000 → 48 tiles × 640px)
- Training dataset: `datasets/combined_visdrone_autel/` (symlinked, not in git)
- Autel pseudo-label generation from MQTT AI detections with FOV correction

### Changed
- Default model now `visdrone_autel_yolov8s_best.pt` (15ep combined) for aerial work
- Keep `visdrone_yolov8s_best.pt` (5ep VisDrone-only) as fallback

### Technical Notes
- Fine-tuning on small Autel-only dataset (82 images) causes catastrophic forgetting
- Combined training preserves generalization while adding campus-specific patterns
- SAHI required for 4000×3000 Autel images — direct inference at imgsz=1280 misses small objects

## [0.3.0] - 2026-06-12
### Added
- **Autel EVO MAX 4T V2 xe support** alongside existing DJI M2EA pipeline
  - `src/autel_telemetry.py`: MQTT OSD telemetry parser (analogous to DJI `parse_srt()`)
  - Gimbal pitch/yaw/roll from payload `10052-0-0`, camera intrinsics from OSD
  - Per-frame video telemetry lookup with timestamp interpolation
- **MQTT data capture** from Autel drone flight (Ericsson Jorvas campus, 2026-06-12)
  - `data/autel_mqtt_20260612/osd_drone.jsonl` — 436 drone state samples (1Hz)
  - `data/autel_mqtt_20260612/detections.jsonl` — 8,297 onboard AI detections
  - `data/autel_mqtt_20260612/ai_stats.jsonl` — target count summaries
  - `data/autel_mqtt_20260612/osd_controller.jsonl` — controller/camera state
- **3-way detection comparison** (VisDrone vs COCO YOLOv8 vs Autel onboard AI)
  - VisDrone best for aerial nadir views (parking)
  - COCO best for angled person detection
  - Autel AI conservative but correct, runs on thermal stream
- **1:1 lateral distance rule** with Autel LRF (laser rangefinder)
  - Direct slant distance measurement — no GSD estimation needed
  - All 4 test images correctly flagged as violations (ratio 0.27x–0.66x)
  - Major improvement over DJI's GSD-only approach
- **Parking occupancy monitoring** at Ericsson Jorvas campus
  - 134m nadir: 104 vehicles detected, ~59% occupancy (Friday afternoon/mökki season 🏖️)
  - 80m nadir: 7 vehicles in closer parking area view
- Detection result images in `outputs/autel_20260612/`

### Technical Findings
- Autel MQTT AI detections use the **IR camera** FOV (58.6°×45.5°), not RGB (48.1°×38.4°)
- FOV correction factor for IR→RGB bbox mapping: 1.22x horizontal, 1.18x vertical
- Autel has no SRT sidecars — telemetry via MQTT + rich EXIF (incl. LRF range, principal point)
- Best altitude for person detection: 19–26m (conf 0.82–0.91 with COCO model)
- VisDrone model fails on close-range angled person views (classifies as "car")

### DJI vs Autel Comparison
| Feature | DJI M2EA | Autel MAX 4T V2 xe |
|---------|----------|---------------------|
| Telemetry source | SRT sidecar | MQTT OSD (1Hz) |
| Distance measurement | GSD estimation | LRF (laser) |
| Person detection range | >30m: low conf | 19–26m: 0.82–0.91 |
| Onboard AI | None | Yes (thermal stream) |
| Thermal | Separate sensor | Co-registered dual |
| Image metadata | Basic EXIF | Rich EXIF + LRF + principal point |

## [0.2.0] - 2026-06-11
### Added
- Patent WO2025034145A1 lateral distance implementation (`src/lateral_distance.py`)
- DJI SRT telemetry parser (focal length, gimbal pitch, altitude, GPS per frame)
- Instance segmentation for per-car oriented bounding boxes (YOLOv8-seg + minAreaRect)
- Two-stream RGB+Thermal fusion parking monitor (`src/parking_monitor.py`)
- Thermal overlay visualization

### Changed
- Patent demo now shows only person detections (not cars) — factually correct per patent scope
- Replaced 32m altitude demo (low confidence: 0.21-0.31) with 17m demo (0.59-0.81 confidence)
- Cleaned sample images — removed misleading results

### Known Issues
- Person detection confidence drops below 0.3 at altitudes >30m (VisDrone model limitation)
- Parking oriented boxes require instance segmentation; COCO-seg model misses ~25% of cars from aerial view
- Parking empty slot detection is gap-based heuristic, not ground-truth validated

## [0.1.0] - 2026-06-11
### Added
- YOLOv8s fine-tuned on VisDrone2019-DET (5 epochs, 6471 images, CPU training)
- Vehicle detection achieving 72% mAP50 on cars from aerial views
- ByteTrack object tracking with persistent IDs and trajectory visualization
- SAHI slicing for small object detection in high-altitude imagery
- Basic parking occupancy estimation (row gap analysis)
- YOLO webcam car counter script
- Project structure with README, .gitignore, data symlinks

### Training Results
- mAP50 all classes: 29.5%
- mAP50 cars: 72.0%
- mAP50 pedestrians: 34.1%
- mAP50 buses: 40.5%
- Inference: ~0.3s/frame on CPU (AMD Ryzen AI 7 PRO 350)
