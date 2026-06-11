# Drone CV Parking Monitor

Aerial vehicle detection and parking occupancy monitoring using drone RGB + thermal video.

## Features

- **Vehicle Detection**: YOLOv8s fine-tuned on VisDrone aerial dataset (72% mAP on cars)
- **Object Tracking**: ByteTrack persistent ID assignment across frames
- **Parking Occupancy**: Two-stream RGB+Thermal fusion with oriented bounding boxes
- **Static ROI Layout**: JSON-defined slot polygons for production deployment

## Architecture

```
RGB Video (DJI) ──► YOLO Detection ──► Confidence Filter ──┐
                                                            ├──► Slot Occupancy
Thermal Video ────► Thermal Contrast ──► Confirmation ─────┘        │
                                                                     ▼
Static Layout (parking_layout.json) ─────────────────────► Availability Dashboard
```

## Setup

```bash
python3 -m venv ~/cv_env
source ~/cv_env/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics segmentation-models-pytorch opencv-python-headless sahi
```

## Usage

### Detection on drone video
```python
from ultralytics import YOLO
model = YOLO("models/visdrone_yolov8s_best.pt")
results = model("your_drone_video.mp4", conf=0.3)
```

### Parking occupancy monitor
```bash
source ~/cv_env/bin/activate
python src/parking_monitor.py --rgb data/DJI_0398_W.MP4 --thermal data/DJI_0399_T.MP4
```

### Object tracking
```bash
python src/vehicle_tracker.py --video data/DJI_0398_W.MP4 --output outputs/tracked.mp4
```

## Model Training

Fine-tuned on VisDrone2019-DET (6471 images, 10 aerial classes):
- Base: YOLOv8s (pretrained COCO)
- Epochs: 5 on CPU (~4h) 
- Image size: 640
- Best mAP50: 29.5% (all classes), 72% (cars)

## Key Learnings

- Standard YOLO (COCO) produces many false positives from aerial views (train, cell phone, boat)
- VisDrone fine-tuning eliminates these completely
- SAHI slicing helps but is slow; fine-tuned model detects small objects natively
- Thermal is useful for segmentation (car vs asphalt) but NOT for determining if recently driven
- Solar loading dominates thermal signature, not engine heat
- Object tracking with moving drone produces ID fragmentation — static camera needed for accurate counting
- Parking slot detection requires known slot geometry (static ROI) for production reliability

## Files

- `src/parking_monitor.py` — Main parking occupancy pipeline
- `src/vehicle_tracker.py` — ByteTrack object tracking
- `src/detect.py` — Basic YOLO detection on video
- `data/parking_layout.json` — Static slot polygon definitions
- `models/` — Fine-tuned weights (not in git, see training instructions)

## Hardware

- Drone: DJI (RGB 1920x1080 + Thermal 640x512)
- Inference: CPU (AMD Ryzen AI 7 PRO 350) — ~0.3s/frame
- Training: CPU — ~4h for 5 epochs (GPU recommended for production training)
