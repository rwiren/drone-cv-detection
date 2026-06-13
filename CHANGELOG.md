# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.6.0] - 2026-06-13
### Added
- **DJI Avata 360 support** — third platform for patent validation
  - `src/avata360_monitor.py`: equirectangular→perspective extraction + person detection
  - Omnidirectional 360° coverage (8 views × 45° = full horizon)
  - Person detected at 0.89 confidence from 1920×960 proxy (LRF)
  - SRT telemetry parser for Avata 360 (60fps GPS/altitude/yaw)
  - Validates patent claim: "select shortest lateral distance if two or more objects detected"
- DJI Avata 360 hardware badge in README
- Three-platform comparison table (M2EA vs MAX 4T vs Avata 360)

### Technical Notes
- Avata 360 captures 7680×3840 equirectangular @ 60fps (H.265 in .OSV container)
- .LRF file = 1920×960 low-res proxy (ideal for development/prototyping)
- .OSV can be read directly by OpenCV (rename to .mp4 or use as-is)
- At 2-3m altitude, person detection works at 0.45-0.89 confidence
- 360° eliminates gimbal pointing requirement entirely
- EIS (RockSteady 3.0) keeps horizon stable regardless of FPV maneuvers

## [0.5.0] - 2026-06-13
### Added
- **Real-time 1:1 rule monitor** (`src/rule_monitor.py`)
  - Replay mode: validated 3,873 measurements from test flight (99.6% violations)
  - Live mode: paho-mqtt subscription to `thing/product/+/osd` and `+/state` topics
  - Configurable safety_value (patent's `determined_value ≥ 1`)
  - Emoji-coded terminal output (🚨 violation / ✅ pass)
- **Interactive flight map** (`src/flight_map.py` → `outputs/autel_20260612/flight_map.html`)
  - Folium/Leaflet HTML map with drone trajectory
  - Color-coded 1:1 rule status (red=violation, green=pass)
  - Clickable markers with altitude, lateral distance, ratio
  - Standalone HTML — shareable without dependencies
- **Complete validation dataset** (`outputs/autel_20260612/1to1_rule_timeline.csv`)
  - 1,423 unique measurements over 5.5 minutes of flight
  - Columns: timestamp, altitude, lateral_distance, ratio, violation, GPS coordinates
- **Firmware label swap discovery** (documented in README + code)
  - Autel OSD `ir_*` fields = zoom/tele lens (9.1mm, 48.1°)
  - Autel OSD `zoom_*` fields = wide camera (4.49mm, 58.6°)
  - Actual thermal (13mm, 42°) not reported in OSD
  - Confirmed via [autel-mission-control](https://github.com/rwiren/autel-mission-control) schema capture
- **Person tracking analysis**: 123 tracker IDs = ~3 actual persons (ID fragmentation)

### Fixed
- Thermal MQTT bbox calibration: proper affine model (scale + translate), not simple offset
  - Nadir: <2.5px error (validated against RGB ground truth)
  - Angled (-33°): ~87px (documented limitation, GPS used for distance calc)
- Parking 80m: aspect ratio filter removes dumpster false positives
- Architecture diagram showing data path separation (bbox pixels vs GPS measurements)

### Changed
- README: added Ericsson Internal badge, Patent badge, companion repo link
- README: comprehensive calibration section with affine formulation
- README: sensor spec tables from manufacturer datasheets
- Version bumped to v0.5.0

## [0.4.0] - 2026-06-13
### Added
- **Combined VisDrone + Autel training** (6553 images, 15 epochs, ~10h CPU)
  - mAP50 all: 34.5% (was 29.5%), cars: 75.7% (was 72.0%), pedestrians: 37.2% (was 34.1%)
  - mAP50-95 cars: 50.8% — major improvement in localization accuracy
  - Model: `models/visdrone_autel_yolov8s_best.pt`
- SAHI sliced inference for high-res Autel images (4000×3000 → 48 tiles × 640px)
- Training dataset: `datasets/combined_visdrone_autel/` (symlinked, not in git)
- Autel pseudo-label generation from MQTT AI detections with FOV correction
- **Aspect ratio filter** for nadir parking detection (width/height > 1.4 = not a car)
- **Calibration Insights** section in README documenting MQTT→image mapping corrections
- **Thermal vs RGB detection characteristics** table

### Fixed
- Parking 80m: dumpsters/skylights no longer counted as vehicles (aspect ratio filter)
- Thermal MQTT overlay: corrected systematic leftward offset (dx=+0.045, ~1.5 car widths)
  - Root cause: Autel AI detection stream uses different crop/ROI than saved thermal JPEG
- Thermal parking: dumpster detection (#761, aspect=1.46) filtered out

### Changed
- Default model now `visdrone_autel_yolov8s_best.pt` (15ep combined) for aerial work
- Keep `visdrone_yolov8s_best.pt` (5ep VisDrone-only) as fallback
- README version bumped to v0.4.0

### Technical Notes
- Fine-tuning on small Autel-only dataset (82 images) causes catastrophic forgetting
- Combined training preserves generalization while adding campus-specific patterns
- SAHI required for 4000×3000 Autel images — direct inference at imgsz=1280 misses small objects
- Thermal AI confuses cold parked cars with cold pavement shadows — RGB cross-check resolves
- MQTT detection stream offset is consistent per drone/firmware — calibrate once per setup

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
