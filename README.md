# Drone CV — Detection & Parking Monitor

[![Version](https://img.shields.io/badge/Version-v0.3.0-yellow.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/Status-Development-yellow.svg)](#)
[![Domain](https://img.shields.io/badge/Domain-Aerial_CV-blue.svg)](#)
[![Hardware](https://img.shields.io/badge/Hardware-DJI_M2EA-purple.svg)](#)
[![Hardware](https://img.shields.io/badge/Hardware-Autel_MAX4TV2xe-purple.svg)](#)
[![Changelog](https://img.shields.io/badge/View-Changelog-orange.svg)](CHANGELOG.md)
[![Contributing](https://img.shields.io/badge/View-Contributing-green.svg)](CONTRIBUTING.md)

**Internal GitLab:** `lmfwire/detection-with-drone`

Aerial computer vision for vehicle detection, parking occupancy monitoring, and person safety distance verification using two drone platforms side by side. Implements patent WO2025034145A1 (1:1 lateral distance rule) with both GSD-based and laser rangefinder methods.

## Two Platforms, Two Approaches

| | DJI Mavic 2 Enterprise Advanced | Autel EVO MAX 4T V2 xe |
|---|---|---|
| **Telemetry** | SRT sidecar files (per-frame) | MQTT OSD stream (1 Hz) |
| **Distance method** | GSD estimation from altitude + pitch | Laser Rangefinder (LRF) — direct measurement |
| **Onboard AI** | None — all inference on ground | Built-in detector on thermal stream |
| **RGB** | 1920×1080, 12MP | 4000×3000, 48MP (IMX586) |
| **Thermal** | 640×512 (separate) | 640×512 (co-registered, same optical axis) |
| **AI detection stream** | — | 1280×960, IR FOV (58.6°×45.5°) |
| **Strengths** | Proven SRT workflow, good tracking data | LRF precision, onboard AI, rich EXIF |

The DJI M2EA pipeline uses `.SRT` subtitle files embedded with per-frame GPS, altitude, and gimbal angles. The Autel MAX 4T V2 xe publishes telemetry over MQTT (drone OSD at 1 Hz with gimbal pitch/yaw/roll, camera intrinsics, battery state) and delivers onboard AI detection results with GPS-positioned bounding boxes — all in real time. The Autel also embeds laser rangefinder distance in image EXIF, giving ground-truth slant range without estimation.

## Sample Results

### DJI M2EA — Vehicle Detection & Tracking

| Detection (VisDrone) | Tracking (ByteTrack) | Patent 1:1 Rule |
|---|---|---|
| ![detection](docs/samples/detection_aerial.jpg) | ![tracking](docs/samples/tracking_bytetrack.jpg) | ![patent](docs/samples/patent_1to1_persons.jpg) |

| Segmentation OBB | Parking Occupancy | Thermal Overlay |
|---|---|---|
| ![seg](docs/samples/parking_seg_obb.jpg) | ![parking](docs/samples/parking_campus_wide.jpg) | ![thermal](docs/samples/thermal_overlay.jpg) |

### Autel MAX 4T V2 xe — Parking & Person Detection (2026-06-12, Ericsson Jorvas)

| Parking Occupancy 134m | Parking Occupancy 80m |
|---|---|
| ![parking_wide](outputs/autel_20260612/MAX_0055_campus_occupancy.jpg) | ![parking_close](outputs/autel_20260612/MAX_0048_parking_occupancy.jpg) |

104 vehicles detected at 134m altitude (GSD ~3.4 cm/px). Ericsson Jorvas campus at ~59% occupancy on a Friday afternoon — mökki season in full effect 🏖️

| 1:1 Rule — 18.8m (LRF 6.05m) | 1:1 Rule — 25.8m (LRF 19.87m) |
|---|---|
| ![rule_close](outputs/autel_20260612/MAX_0043_1to1_rule.jpg) | ![rule_far](outputs/autel_20260612/MAX_0046_1to1_rule.jpg) |

All images correctly flagged as **VIOLATIONS** — lateral distance (5.09m–16.97m) is less than altitude (18.8m–25.8m). The Autel LRF provides direct slant-range measurement with no GSD estimation needed.

| Thermal Person (MQTT AI) | Thermal Parking (MQTT AI) |
|---|---|
| ![thermal_person](outputs/autel_20260612/IRX_0043_person_overlay.jpg) | ![thermal_parking](outputs/autel_20260612/IRX_0050_mqtt_overlay.jpg) |

Autel's onboard AI runs on the thermal stream and publishes detections via MQTT with GPS coordinates and tracker IDs. Person clearly visible in IR at 18.8m — the hi-vis vest is invisible in thermal but body heat signature is unmistakable.

### Model Comparison — VisDrone vs COCO vs Autel Onboard AI

| Parking (80m nadir) | Person (19m angled) |
|---|---|
| ![cmp_parking](outputs/autel_20260612/MAX_0050_comparison.jpg) | ![cmp_person](outputs/autel_20260612/MAX_0043_comparison.jpg) |

**Key insight:** No single model wins everywhere.
- **VisDrone YOLOv8s** excels at aerial/nadir views (trained on drone imagery) but misclassifies close-range persons as "car"
- **COCO YOLOv8s** handles normal-perspective person detection (0.91 confidence) but hallucinates "TV" and "cell phone" from bird's-eye view
- **Autel onboard AI** is conservative (fewer detections) but has zero false positives and provides GPS coordinates per target

The optimal pipeline uses VisDrone for aerial vehicle counting and COCO for person detection at moderate angles.

## Capabilities

### Working well
- **Vehicle detection** from aerial video using YOLOv8s fine-tuned on VisDrone (72% mAP50 on cars)
- **Object tracking** with ByteTrack (persistent IDs, trajectory trails)
- **Thermal+RGB fusion** visualization
- **Person detection** with lateral distance calculation (patent PoC)
- **1:1 rule with LRF** — Autel laser rangefinder provides ground-truth distance
- **Parking occupancy** — 104 vehicles detected from 134m nadir at Ericsson Jorvas

### Proof-of-concept (limitations documented)
- **Patent 1:1 rule (DJI)** — GSD formula works but person detection confidence drops below 0.3 at >30m altitude
- **Object tracking unique count** — inflated with moving drone camera due to ID fragmentation; works correctly with static camera
- **MQTT-to-video sync** — Autel OSD at 1 Hz requires interpolation; no issues with still images

### Known limitations
- Standard YOLO (COCO) produces false positives from aerial views; VisDrone fine-tuning eliminates this
- Autel MQTT AI bounding boxes map to IR camera FOV (58.6°) — need FOV correction (1.22x/1.18x) for RGB overlay
- Thermal segmentation is affected by solar loading — car surface temp ≠ engine activity
- Parking empty slot detection needs pre-defined slot geometry for production reliability

## Setup

```bash
python3 -m venv ~/cv_env
source ~/cv_env/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics opencv-python-headless sahi
```

## Usage

### Detect vehicles in aerial imagery
```bash
python src/detect.py --input path/to/image_or_video.mp4 --model models/visdrone_yolov8s_best.pt
```

### Track vehicles with persistent IDs
```bash
python src/vehicle_tracker.py --video data/DJI_0398_W.MP4 --model models/visdrone_yolov8s_best.pt
```

### Parking occupancy monitor (RGB + optional thermal)
```bash
python src/parking_monitor.py --rgb data/DJI_0398_W.MP4 --thermal data/DJI_0399_T.MP4 --frame 1792
```

### Patent WO2025034145A1 — Lateral distance (DJI M2EA + SRT)
```bash
python src/lateral_distance.py --video data/DJI_0398_W.MP4 --srt data/DJI_0398_W.SRT --frame 1792
```

### Autel telemetry lookup (MQTT OSD)
```bash
python src/autel_telemetry.py --osd data/autel_mqtt_20260612/osd_drone.jsonl --video MAX_0042.MP4 --frame 100
```

## Model Training

Fine-tuned YOLOv8s on VisDrone2019-DET:
- **Base**: YOLOv8s pretrained on COCO
- **Dataset**: 6471 training images, 10 classes (pedestrian, people, bicycle, car, van, truck, tricycle, awning-tricycle, bus, motor)
- **Training**: 5 epochs, imgsz=640, batch=8, CPU
- **Result**: mAP50 = 29.5% all classes, 72% cars, 34% pedestrians

## Project Structure

```
src/
├── detect.py              — Simple YOLO detection
├── vehicle_tracker.py     — ByteTrack object tracking
├── parking_monitor.py     — Two-stream parking occupancy
├── lateral_distance.py    — Patent WO2025034145A1 (DJI M2EA + SRT)
├── autel_telemetry.py     — Autel MAX 4T V2 xe MQTT telemetry parser
└── yolo_car_counter.py    — Webcam/video car counter
data/
├── autel_mqtt_20260612/   — Autel MQTT capture (OSD, detections, AI stats)
├── autel_20260612/        — Media manifest (images/video stored locally)
├── parking_layout.json    — Static slot polygon definitions
models/
└── visdrone_yolov8s_best.pt  — Fine-tuned weights (not in git)
outputs/
└── autel_20260612/        — Detection result images
docs/samples/              — DJI M2EA example output images
```

## Hardware

- **DJI Mavic 2 Enterprise Advanced (M2EA)**: RGB 1920×1080 + Thermal 640×512, SRT telemetry
- **Autel EVO MAX 4T V2 xe**: RGB 4000×3000 + Thermal 640×512, MQTT telemetry, LRF, onboard AI
- **Inference**: CPU (AMD Ryzen AI 7 PRO 350) — ~0.3s/frame detection, ~1.7min for full video tracking
- **Training**: CPU — ~4h for 5 epochs (GPU recommended)

## References

- [VisDrone2019](https://github.com/VisDrone/VisDrone-Dataset) — Aerial object detection dataset
- [Ultralytics YOLOv8](https://docs.ultralytics.com/) — Detection, segmentation, tracking
- [SAHI](https://github.com/obss/sahi) — Slicing Aided Hyper Inference for small objects
- WO2025034145A1 — "Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"
