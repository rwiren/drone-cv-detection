# Model Training

## Models Overview

| Model | Use Case | Training | mAP50 (all) | Key Class | Inference |
|-------|----------|----------|-------------|-----------|-----------|
| `visdrone_yolov8m_1280_best.pt` | Aerial person (best) | VisDrone, 30ep, imgsz=1280, A100 | **0.581** | car: 0.890, ped: 0.681 | 7.5ms GPU |
| `combined_v8m_1280_best.pt` | Avata 360 domain-adapted | VisDrone+Avata, 30ep, imgsz=1280, A100 | 0.580 | car: 0.888, ped: 0.680 | 7.5ms GPU |
| `visdrone_yolov8s_1280_best.pt` | Parking occupancy | VisDrone, 30ep, imgsz=1280, A100 | 0.532 | car: 0.873, ped: 0.629 | 1.6ms GPU |
| `visdrone_autel_yolov8s_best.pt` | Parking (legacy) | VisDrone+Autel, 15ep, imgsz=640, CPU | 0.345 | car: 0.757, ped: 0.372 | ~300ms CPU |
| `yolov8s.pt` (COCO) | Close-range person | COCO pretrained | — | person: excellent <3m | ~300ms CPU |

## Model Selection by Use Case

**1:1 Person Detection:**

- Altitude > 5m → VisDrone **v8m** 1280 (0.60 conf at 8m, 0.56 at 5.7m)
- Altitude < 3m → COCO yolov8s (0.89 conf at 2m)
- Ensemble: run both, take best per view

**Parking Occupancy:**

- Nadir > 50m → VisDrone **v8s** at imgsz=1280
- Nadir > 100m → VisDrone v8s 1280 + SAHI slicing
- Close-range angled → COCO

## Training Runs

### Run 1 — CPU Baseline (imgsz=640)

- Dataset: 6553 images (6471 VisDrone + 82 Autel)
- Hardware: AMD Ryzen AI 7 PRO 350, ~10h
- Result: mAP50 = 34.5%

### Run 2 — YOLOv8s A100 (imgsz=1280)

- Dataset: VisDrone2019-DET (6471 train)
- Hardware: NVIDIA A100, ~55 min
- Result: mAP50 = 53.2% (+54% improvement from imgsz alone)

### Run 3 — YOLOv8m A100 (imgsz=1280)

- Dataset: VisDrone2019-DET (6471 train)
- Hardware: NVIDIA A100, ~1.6h
- Result: mAP50 = **58.1%** (car: 89.0%, ped: 68.1%)

### Run 4 — Combined Domain Adaptation

- Dataset: 7717 images (6471 VisDrone + 1246 Avata 360 crops)
- Hardware: NVIDIA A100, ~1.8h
- Result: mAP50 = 58.0% — no forgetting on VisDrone val
- Finding: Domain-adapted but high-altitude detection degraded slightly

## Lessons Learned

1. **imgsz=1280** is the single biggest improvement for aerial small-object detection (+54% mAP50)
2. **YOLOv8m** adds +9% over v8s — most impactful at >5m altitude
3. Fine-tuning on 82 images causes **catastrophic forgetting** (0 detections)
4. Combined training preserves generalization while adding site-specific patterns
5. **Dual-model ensemble** beats any single model across the full altitude range
6. Pseudo-labels from same model family don't improve val metrics but help domain frames
