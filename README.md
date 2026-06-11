# Drone CV — Detection & Parking Monitor

[![Version](https://img.shields.io/badge/Version-v0.2.0-yellow.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/Status-Development-yellow.svg)](#)
[![Domain](https://img.shields.io/badge/Domain-Aerial_CV-blue.svg)](#)
[![Hardware](https://img.shields.io/badge/Hardware-DJI_Mavic3E-purple.svg)](#)
[![Changelog](https://img.shields.io/badge/View-Changelog-orange.svg)](CHANGELOG.md)
[![Contributing](https://img.shields.io/badge/View-Contributing-green.svg)](CONTRIBUTING.md)

**Internal GitLab:** `lmfwire/detection-with-drone`

Aerial computer vision using DJI drone RGB + thermal video. Includes vehicle detection, object tracking, parking occupancy estimation, and a proof-of-concept implementation of patent WO2025034145A1 (lateral distance safety monitoring).

## Capabilities

### Working well
- **Vehicle detection** from aerial video using YOLOv8s fine-tuned on VisDrone (72% mAP50 on cars)
- **Object tracking** with ByteTrack (persistent IDs, trajectory trails)
- **Thermal+RGB fusion** visualization
- **Person detection** with lateral distance calculation (patent PoC)
- **Instance segmentation** for per-car oriented bounding boxes (YOLOv8-seg + minAreaRect)

### Proof-of-concept (limitations documented)
- **Parking occupancy** — works for detecting occupied spots; empty slot detection relies on gap analysis which is imperfect
- **Patent 1:1 rule** — formula implemented and produces reasonable distances; person detection confidence is low at >30m altitude (0.2-0.3)
- **Object tracking unique count** — inflated with moving drone camera due to ID fragmentation; works correctly with static camera

### Known limitations
- Standard YOLO (COCO) produces false positives from aerial views; VisDrone fine-tuning eliminates this
- Oriented bounding boxes require instance segmentation (COCO-seg only detects 18/25 cars from aerial); a VisDrone-trained OBB model would be needed for production
- Thermal segmentation is affected by solar loading — car surface temperature correlates with sun exposure and paint color, NOT engine activity
- Parking empty slot detection needs pre-defined slot geometry (static ROI) for production reliability

## Sample Results

| Detection (VisDrone) | Tracking (ByteTrack) | Patent 1:1 Rule |
|---|---|---|
| ![detection](docs/samples/detection_aerial.jpg) | ![tracking](docs/samples/tracking_bytetrack.jpg) | ![patent](docs/samples/patent_1to1_persons.jpg) |

| Segmentation OBB | Parking Occupancy | Thermal Overlay |
|---|---|---|
| ![seg](docs/samples/parking_seg_obb.jpg) | ![parking](docs/samples/parking_campus_wide.jpg) | ![thermal](docs/samples/thermal_overlay.jpg) |

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

### Patent WO2025034145A1 — Lateral distance to persons
```bash
python src/lateral_distance.py --video data/DJI_0398_W.MP4 --srt data/DJI_0398_W.SRT --frame 1792
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
├── lateral_distance.py    — Patent WO2025034145A1 implementation
└── yolo_car_counter.py    — Webcam/video car counter
data/
├── parking_layout.json    — Static slot polygon definitions
models/
└── visdrone_yolov8s_best.pt  — Fine-tuned weights (not in git)
docs/samples/              — Example output images
```

## Hardware

- **Drone**: DJI Mavic 3 Enterprise (RGB 1920×1080 + Thermal 640×512)
- **Inference**: CPU (AMD Ryzen AI 7 PRO 350) — ~0.3s/frame detection, ~1.7min for full video tracking
- **Training**: CPU — ~4h for 5 epochs (GPU recommended)

## References

- [VisDrone2019](https://github.com/VisDrone/VisDrone-Dataset) — Aerial object detection dataset
- [Ultralytics YOLOv8](https://docs.ultralytics.com/) — Detection, segmentation, tracking
- [SAHI](https://github.com/obss/sahi) — Slicing Aided Hyper Inference for small objects
- WO2025034145A1 — "Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"
