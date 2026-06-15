# Setup & Usage

## Installation

```bash
python3 -m venv ~/cv_env
source ~/cv_env/bin/activate

# CPU inference (lighter install)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics opencv-python-headless sahi

# GPU inference (if CUDA available)
# pip install torch torchvision
# pip install ultralytics opencv-python-headless sahi
```

## Usage

### 360° Person Detection — DJI Avata 360 (dual-model ensemble)

```bash
python src/avata360_monitor.py --video DJI_...LRF --srt DJI_...SRT \
  --model yolov8s.pt --aerial-model models/visdrone_yolov8s_1280_best.pt
```

### Detect Vehicles in Aerial Imagery

```bash
python src/detect.py --input path/to/image_or_video.mp4 --model models/visdrone_yolov8s_1280_best.pt
```

### Track Vehicles with Persistent IDs

```bash
python src/vehicle_tracker.py --video data/DJI_0398_W.MP4 --model models/visdrone_yolov8s_1280_best.pt
```

### Parking Occupancy Monitor (RGB + optional thermal)

```bash
python src/parking_monitor.py --rgb data/DJI_0398_W.MP4 --thermal data/DJI_0399_T.MP4 --frame 1792
```

### Lateral Distance Calculation (1:1 rule)

```bash
python src/lateral_distance.py --video data/DJI_0398_W.MP4 --srt data/DJI_0398_W.SRT --frame 1792
```

### Autel Telemetry Lookup (MQTT OSD)

```bash
python src/autel_telemetry.py --osd data/autel_mqtt_20260612/osd_drone.jsonl --video MAX_0042.MP4 --frame 100
```

### High-Resolution Detection with SAHI Slicing

```python
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

model = AutoDetectionModel.from_pretrained(
    model_type='yolov8',
    model_path='models/visdrone_yolov8s_1280_best.pt',
    confidence_threshold=0.2
)
result = get_sliced_prediction(
    'image_4000x3000.jpg', model,
    slice_height=640, slice_width=640,
    overlap_height_ratio=0.2, overlap_width_ratio=0.2
)
```

## Project Structure

```
src/
├── avata360_monitor.py    — DJI Avata 360° person detection (dual-fisheye + ensemble)
├── rule_monitor.py        — 1:1 rule real-time monitor (replay + live MQTT)
├── lateral_distance.py    — Lateral distance calculation (DJI M2EA + SRT)
├── parking_monitor.py     — Two-stream parking occupancy (RGB + thermal)
├── autel_telemetry.py     — Autel MAX 4T V2 xe MQTT parser + bbox calibration
├── compare_models.py      — Model comparison across Avata 360 footage
├── flight_map.py          — Interactive Folium HTML flight visualization
├── vehicle_tracker.py     — ByteTrack object tracking
├── detect.py              — YOLO detection wrapper
└── yolo_car_counter.py    — Webcam/video car counter
models/
├── visdrone_yolov8m_1280_best.pt   — VisDrone 30ep v8m imgsz=1280 (A100) ← best aerial
├── visdrone_yolov8s_1280_best.pt   — VisDrone 30ep v8s imgsz=1280 (A100) ← fastest
├── visdrone_autel_yolov8s_best.pt  — Combined 15ep imgsz=640 (CPU)
└── visdrone_yolov8s_best.pt        — VisDrone-only 5ep (fallback)
```
