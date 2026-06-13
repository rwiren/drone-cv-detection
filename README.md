# Drone CV — Detection & Parking Monitor

[![Version](https://img.shields.io/badge/Version-v0.4.0-yellow.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/Status-Development-yellow.svg)](#)
[![Domain](https://img.shields.io/badge/Domain-Aerial_CV-blue.svg)](#)
[![Hardware](https://img.shields.io/badge/Hardware-DJI_M2EA-purple.svg)](#)
[![Hardware](https://img.shields.io/badge/Hardware-Autel_MAX4TV2xe-purple.svg)](#)
[![Changelog](https://img.shields.io/badge/View-Changelog-orange.svg)](CHANGELOG.md)
[![Contributing](https://img.shields.io/badge/View-Contributing-green.svg)](CONTRIBUTING.md)

**Internal GitLab:** `lmfwire/detection-with-drone`

Aerial computer vision for vehicle detection, parking occupancy monitoring, and person safety distance verification using two drone platforms side by side. Implements patent WO2025034145A1 (1:1 lateral distance rule) with both GSD-based and laser rangefinder methods.

## Patent WO2025034145A1 — What We're Proving

**Patent:** "Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"
**Inventors:** Richard Wirén, Volodya Grancharov | **Assignee:** Telefonaktiebolaget LM Ericsson | **Status:** Pending

The patent describes a system where a communication device (on or associated with a UAV) detects persons, calculates lateral distance using monocular camera geometry, compares it against `determined_value × altitude`, and issues a message to a receiving unit if the 1:1 rule is violated. The message can trigger the UAV to stop moving toward the person.

**This repo implements and validates the patent claims on two platforms:**

| Patent Claim | DJI M2EA Implementation | Autel MAX 4T V2 xe Implementation |
|---|---|---|
| Object detection (YOLO/R-CNN) | VisDrone YOLOv8s on RGB video | VisDrone + COCO YOLOv8 + Autel onboard AI |
| Lateral distance formula (Eq. 10) | GSD + ray-cast from SRT telemetry | LRF direct measurement (ground truth) |
| Gimbal pitch from metadata | DJI SRT `Pitch:` field per frame | MQTT OSD `gimbal_pitch` + EXIF `Pitch` |
| Multispectral detection | RGB + Thermal (separate sensors) | RGB + Thermal (co-registered) + onboard AI fusion |
| Message to receiving unit | Offline analysis (post-flight) | **Real-time MQTT** — detection + GPS published instantly |
| Determined value (≥1) | Configurable `--safety-value` | Same — can add dynamic margin |

The Autel platform is particularly close to the patent's architecture: the drone detects a person on its onboard AI, calculates the target GPS position, and publishes the result over MQTT to the controller (receiving unit) — all in real time during flight. The LRF provides a ground-truth distance measurement that validates the monocular formula's output.

## Two Platforms, Two Approaches

| | DJI Mavic 2 Enterprise Advanced | Autel EVO MAX 4T V2 xe |
|---|---|---|
| **Telemetry** | SRT sidecar files (per-frame) | MQTT OSD stream (1 Hz) |
| **Distance method** | GSD estimation from altitude + pitch | Laser Rangefinder (LRF) — direct measurement |
| **Onboard AI** | None — all inference on ground | Built-in detector on thermal stream |
| **RGB** | 1920×1080, 48MP (24mm eq. f/2.8, FOV 84°) | 8192×6144, 50MP (23mm eq. f/1.9, FOV 85°) |
| **Thermal** | 640×512, 9mm (DFOV ~57°) | 640×512, 13mm f/1.2 (DFOV 42°) |
| **AI detection stream** | — | 1280×960 (firmware maps to ~58.6° FOV internally) |
| **Strengths** | Proven SRT workflow, wider thermal FOV | LRF precision, onboard AI, rich EXIF, tighter thermal |

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

| Parking Occupancy 134m | Parking Occupancy 80m (filtered) |
|---|---|
| ![parking_wide](outputs/autel_20260612/MAX_0055_campus_occupancy.jpg) | ![parking_close](outputs/autel_20260612/MAX_0048_parking_occupancy.jpg) |

104 vehicles detected at 134m altitude (GSD ~3.4 cm/px). Ericsson Jorvas campus at ~59% occupancy on a Friday afternoon — mökki season in full effect 🏖️

The 80m view shows aspect ratio filtering in action: dumpsters and roof equipment (wide/landscape aspect) are rejected, keeping only the 2 actual cars (portrait aspect from nadir).

| 1:1 Rule — 18.8m (LRF 6.05m) | 1:1 Rule — 25.8m (LRF 19.87m) |
|---|---|
| ![rule_close](outputs/autel_20260612/MAX_0043_1to1_rule.jpg) | ![rule_far](outputs/autel_20260612/MAX_0046_1to1_rule.jpg) |

All images correctly flagged as **VIOLATIONS** — lateral distance (5.09m–16.97m) is less than altitude (18.8m–25.8m). The Autel LRF provides direct slant-range measurement with no GSD estimation needed — serving as ground truth to validate the patent's monocular formula.

| Image | Alt (m) | LRF Slant (m) | Lateral (m) | Ratio | Status |
|---|---|---|---|---|---|
| MAX_0043 | 18.8 | 6.05 | 5.09 | 0.27x | ✗ VIOLATION |
| MAX_0044 | 21.7 | 12.19 | 10.27 | 0.47x | ✗ VIOLATION |
| MAX_0045 | 21.7 | 12.23 | 10.30 | 0.47x | ✗ VIOLATION |
| MAX_0046 | 25.8 | 19.87 | 16.97 | 0.66x | ✗ VIOLATION |

| Thermal Person (MQTT AI) | RGB + Thermal Parking (MQTT AI) |
|---|---|
| ![thermal_person](outputs/autel_20260612/IRX_0043_person_overlay.jpg) | ![thermal_parking](outputs/autel_20260612/IRX_0050_mqtt_overlay.jpg) |

Autel's onboard AI runs on the thermal stream and publishes detections via MQTT with GPS coordinates and tracker IDs — matching the patent's "issuing a message to a receiving unit" architecture. Person clearly visible in IR at 18.8m — the hi-vis vest is invisible in thermal but body heat signature is unmistakable.

### Model Comparison — VisDrone vs COCO vs Autel Onboard AI

| Parking (80m nadir) | Person (19m angled) |
|---|---|
| ![cmp_parking](outputs/autel_20260612/MAX_0050_comparison.jpg) | ![cmp_person](outputs/autel_20260612/MAX_0043_comparison.jpg) |

**Key insight:** No single model wins everywhere.
- **VisDrone YOLOv8s** excels at aerial/nadir views (trained on drone imagery) but misclassifies close-range persons as "car"
- **COCO YOLOv8s** handles normal-perspective person detection (0.91 confidence) but hallucinates "TV" and "cell phone" from bird's-eye view
- **Autel onboard AI** is conservative (fewer detections) but has zero false positives and provides GPS coordinates per target

The optimal pipeline uses VisDrone for aerial vehicle counting and COCO for person detection at moderate angles.

## Calibration Insights

### MQTT Detection Stream → Saved Image Mapping

The Autel onboard AI runs on an internal 1280×960 processing stream. When projecting MQTT bounding boxes onto saved images, a calibrated **affine correction** must be applied — not a simple translation.

**Root cause:** The detection firmware maps pixel coordinates using wide-camera FOV parameters (~58.6°), but the thermal sensor actually has a much tighter 13mm lens (DFOV 42°, IFOV 0.92mrad). This mismatch causes non-linear compression: objects near frame edges are squeezed inward, and there's a systematic vertical offset from the physical parallax between sensors in the gimbal housing.

```
Corrected thermal coordinates:
  x_corrected = 0.8384 × x_mqtt + 0.0915
  y_corrected = y_mqtt + 0.049
```

| Target Image | Correction Type | Formula | Implementation |
|---|---|---|---|
| **Thermal JPEG** (640×512) | Affine (scale + translate) | `x' = 0.8384x + 0.0915`, `y' = y + 0.049` | `correct_mqtt_bbox(bbox, 'thermal')` |
| **RGB JPEG** (4000×3000) | FOV scaling from center | `x' = 0.5 + (x-0.5)×1.22` | `correct_mqtt_bbox(bbox, 'rgb')` |
| **Nadir false positives** | Aspect ratio filter | reject if `w/h > 1.4` | Cars are portrait, dumpsters landscape |

These corrections are implemented in `src/autel_telemetry.py:correct_mqtt_bbox()`.

### Why the Error is Non-Linear (Not Simple Translation)

The error pattern is:
- Left objects → shifted right
- Right objects → shifted left  
- All objects → shifted upward

This is **radial compression toward center** — classic for a focal length / FOV mismatch in the coordinate pipeline. The Autel firmware hardcodes wide-camera geometry (~58.6° FOV) for the detection output coordinate space, but the actual thermal lens has 42° DFOV (13mm). Our affine calibration compensates for this.

### Calibration Accuracy (Validated)

| View Geometry | Error | Status | Notes |
|---|---|---|---|
| Nadir (0° pitch, 80m) | **<2.5 px** | ✅ Validated | Sub-pixel accuracy, affine model is correct |
| Angled (-33° pitch, 19m) | ~87 px | ⚠️ Approximate | Affine breaks down; use GPS position instead |

For the patent 1:1 rule, the angled-view limitation is acceptable: the lateral distance calculation uses the person's **GPS position** from MQTT (independent of bbox pixel alignment), not the pixel coordinates. The bbox overlay on saved images is purely for visualization.

### Architecture: Why Pixel Errors Don't Affect Safety Calculations

```
                MQTT Detection Payload
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    bbox {x,y,w,h}   pos {lat,lon}   LRF distance
    (pixel space)    (GPS, hardware)  (laser, hardware)
          │              │              │
          ▼              ▼              ▼
    Visualization    1:1 Rule Calc   Ground Truth
    (overlay only)   (patent core)   (validation)
          │              │              │
    Affected by      IMMUNE to       IMMUNE to
    FOV mismatch     pixel errors    pixel errors
```

The patent's lateral distance calculation (Eq. 10) and the 1:1 rule comparison operate on the **right branch** — GPS + LRF telemetry from hardware sensor fusion. Bounding box pixel coordinates (left branch) are used only to prove that detection occurred, not for spatial measurement.

**Future work:** A pitch-dependent homography matrix could improve visualization at angled views. This would require calibration points at multiple gimbal angles, or computing the projective transform from the known camera intrinsics + gimbal pitch. Not needed for patent validation but useful for real-time operator displays.

### Sensor Specifications (from manufacturer datasheets)

| Spec | DJI M2EA Thermal | Autel MAX 4T Thermal | Autel MAX 4T Wide |
|---|---|---|---|
| Resolution | 640×512 @30Hz | 640×512 | 8192×6144 (50MP) |
| Focal length | 9mm (38mm eq.) | 13mm | 4.5mm (23mm eq.) |
| DFOV | ~57° | 42° | 85° |
| Aperture | — | f/1.2 | f/1.9 |
| Pixel pitch | 12μm | 12μm | — |
| LRF | No | Yes (±1m, 1200m range) | — |

| Spec | DJI M2EA Visual | Autel MAX 4T Zoom |
|---|---|---|
| Sensor | 1/2" 48MP | 1/2" 48MP |
| Focal length | 24mm eq., f/2.8 | 64-234mm eq., f/2.8-4.8 |
| FOV | 84° | Variable (telephoto) |
| Max resolution | 8000×6000 | 8000×6000 |

### Thermal vs RGB Detection Characteristics

| Object | RGB Signature | Thermal Signature | Detection Notes |
|---|---|---|---|
| Parked car (cold) | Clear color/shape | Dark (cool) rectangle, blends with shadows | Thermal may miss cold parked cars |
| Parked car (warm) | Same | Bright (hot), stands out from pavement | Easy in both modalities |
| Person | Clothing/shape | Very bright (body heat 37°C vs ambient) | Thermal excels, esp. in shadows |
| Dumpster | Green/blue container | Varies with sun exposure | Both detect as vehicle FP |
| Shadow on pavement | Visible as dark area | Cool patch, similar to cold car | Thermal can confuse shadow with vehicle |

**Key learning:** The thermal AI detected "cars" where there were actually cold shadows/patches on the pavement adjacent to the real vehicles. This is because cold metal (parked car roof) and cold concrete (shaded pavement) have similar thermal signatures from 80m nadir. The RGB channel resolves this ambiguity instantly — demonstrating why **multispectral fusion** (as described in the patent) is valuable.

## Capabilities

### Working well
- **Vehicle detection** from aerial video using YOLOv8s fine-tuned on VisDrone+Autel (75.7% mAP50 on cars)
- **Object tracking** with ByteTrack (persistent IDs, trajectory trails)
- **Thermal+RGB fusion** visualization and cross-validation
- **Person detection** with lateral distance calculation (patent PoC)
- **1:1 rule with LRF** — Autel laser rangefinder provides ground-truth distance
- **Parking occupancy** — 104 vehicles detected from 134m nadir at Ericsson Jorvas
- **False positive filtering** — aspect ratio heuristic removes dumpsters/equipment from nadir views

### Proof-of-concept (limitations documented)
- **Patent 1:1 rule (DJI)** — GSD formula works but person detection confidence drops below 0.3 at >30m altitude
- **Object tracking unique count** — inflated with moving drone camera due to ID fragmentation; works correctly with static camera
- **MQTT-to-video sync** — Autel OSD at 1 Hz requires interpolation; no issues with still images
- **Thermal-only detection** — cold parked cars can be confused with cold pavement shadows; RGB cross-check resolves ambiguity

### Known limitations
- Standard YOLO (COCO) produces false positives from aerial views; VisDrone fine-tuning eliminates this
- Autel MQTT AI bounding boxes require calibration offset when overlaid on saved thermal images (dx=+0.045)
- Thermal segmentation is affected by solar loading — car surface temp correlates with sun exposure, NOT engine activity
- Parking empty slot detection needs pre-defined slot geometry for production reliability
- Fine-tuning on small domain-specific dataset alone causes catastrophic forgetting — must combine with base VisDrone data

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
python src/detect.py --input path/to/image_or_video.mp4 --model models/visdrone_autel_yolov8s_best.pt
```

### Track vehicles with persistent IDs
```bash
python src/vehicle_tracker.py --video data/DJI_0398_W.MP4 --model models/visdrone_autel_yolov8s_best.pt
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

### High-resolution detection with SAHI slicing
```python
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

model = AutoDetectionModel.from_pretrained(model_type='yolov8',
    model_path='models/visdrone_autel_yolov8s_best.pt', confidence_threshold=0.2)
result = get_sliced_prediction('image_4000x3000.jpg', model,
    slice_height=640, slice_width=640, overlap_height_ratio=0.2, overlap_width_ratio=0.2)
```

## Model Training

Fine-tuned YOLOv8s on VisDrone2019-DET + Autel campus data:
- **Base**: YOLOv8s pretrained on COCO
- **Dataset**: 6553 training images (6471 VisDrone + 82 Autel Ericsson Jorvas), 548 validation
- **Training**: 15 epochs, imgsz=640, batch=8, CPU (~10h on AMD Ryzen AI 7 PRO 350)
- **Result**: mAP50 = 34.5% all classes, **75.7% cars**, 37.2% pedestrians, 50.8% mAP50-95 cars
- **Inference**: Use SAHI slicing for images >2000px (e.g., Autel 4000×3000 at 134m → 48 tiles)

### Training Lessons Learned
- Fine-tuning on 82 Autel-only images caused **catastrophic forgetting** (0 detections)
- Combined VisDrone + Autel training preserves generalization while adding site-specific patterns
- Autel MQTT pseudo-labels (from onboard AI with FOV correction) are usable as training data
- imgsz=640 training works when paired with SAHI slicing at inference time

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
├── autel_training/        — Generated training labels from MQTT pseudo-labels
├── parking_layout.json    — Static slot polygon definitions
models/
├── visdrone_autel_yolov8s_best.pt  — Combined training weights (not in git, 22.6MB)
└── visdrone_yolov8s_best.pt        — Original VisDrone-only weights (fallback)
outputs/
└── autel_20260612/        — Detection result images
docs/
├── REGULATORY_BACKGROUND.md — EU 1:1 rule, Traficom, FAA comparison
└── samples/               — DJI M2EA example output images
```

## Hardware

- **DJI Mavic 2 Enterprise Advanced (M2EA)**
  - Visual: 1/2" 48MP, 24mm eq. f/2.8, FOV 84°, max 8000×6000
  - Thermal: 640×512 @30Hz, 9mm (38mm eq.), uncooled VOx, 12μm pitch, DFOV ~57°
  - Gimbal: 3-axis, tilt -90°→+30°, pan ±75°
  - Telemetry: SRT sidecar per frame
- **Autel EVO MAX 4T V2 xe**
  - Wide: 1/1.28" 50MP, 4.5mm (23mm eq.) f/1.9, FOV 85°, max 8192×6144
  - Zoom: 1/2" 48MP, 11.8-43.3mm (64-234mm eq.) f/2.8-4.8, max 8000×6000
  - Thermal: 640×512, 13mm f/1.2, DFOV 42°, IFOV 0.92mrad, 12μm pitch, uncooled VOx
  - LRF: ±1m accuracy, 1200m range
  - Firmware: v1.9.1.219 | Controller: Smart Controller V3 (TH7825451059)
  - Onboard AI: vehicle (cls_id=3), person (cls_id=30), bicycle (cls_id=2) via MQTT
- **Inference**: CPU (AMD Ryzen AI 7 PRO 350) — ~0.3s/frame at imgsz=640, ~0.3s/tile with SAHI
- **Training**: CPU ~10h for 15 epochs (GPU recommended for faster iteration)

## References

- **WO2025034145A1** — ["Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"](https://patents.google.com/patent/WO2025034145A1/en) (Wirén, Grancharov — Ericsson, 2025)
- [EU 2019/947](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32019R0947) — EASA Open Category drone regulation (1:1 rule)
- [VisDrone2019](https://github.com/VisDrone/VisDrone-Dataset) — Aerial object detection dataset
- [Ultralytics YOLOv8](https://docs.ultralytics.com/) — Detection, segmentation, tracking
- [SAHI](https://github.com/obss/sahi) — Slicing Aided Hyper Inference for small objects
