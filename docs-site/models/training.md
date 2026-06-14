# Training History

## Models Overview

| Model | mAP50 | Car | Pedestrian | Size | Inference |
|-------|-------|-----|-----------|------|-----------|
| `visdrone_yolov8m_1280_best.pt` | **0.581** | 0.890 | 0.681 | 52 MB | 7.5ms GPU |
| `visdrone_yolov8s_1280_best.pt` | 0.532 | 0.873 | 0.629 | 23 MB | 1.6ms GPU |
| `visdrone_autel_yolov8s_best.pt` | 0.345 | 0.757 | 0.372 | 23 MB | ~300ms CPU |

## Run 1 — CPU Baseline (imgsz=640)

- **Model:** YOLOv8s
- **Dataset:** 6553 images (6471 VisDrone + 82 Autel Ericsson Jorvas)
- **Epochs:** 15
- **Hardware:** AMD Ryzen AI 7 PRO 350, ~10h
- **Result:** mAP50 = 34.5% all, 75.7% cars, 37.2% pedestrians
- **Lesson:** imgsz=640 misses small objects at altitude; SAHI needed for >2000px images

## Run 2 — YOLOv8s A100 (imgsz=1280)

- **Model:** YOLOv8s
- **Dataset:** VisDrone2019-DET (6471 train, 548 val)
- **Epochs:** 30 (batch=16, cos_lr, patience=10)
- **Hardware:** NVIDIA A100-SXM4-40GB, Colab, ~55 min
- **Result:** mAP50 = 53.2% all, 87.3% cars, 62.9% pedestrians
- **Improvement:** +54% mAP50 overall — imgsz=1280 is the single biggest gain

## Run 3 — YOLOv8m A100 (imgsz=1280)

- **Model:** YOLOv8m (25.9M params, 79.1 GFLOPs)
- **Dataset:** VisDrone2019-DET (6471 train, 548 val)
- **Epochs:** 30 (batch=8, cos_lr, patience=10)
- **Hardware:** NVIDIA A100-SXM4-40GB, Colab, ~1.6h
- **Result:** mAP50 = 58.1% all, 89.0% cars, 68.1% pedestrians
- **Improvement vs v8s:** +9.2% mAP50, +8.3% pedestrian

## Run 4 — Combined Dataset (VisDrone + Avata 360)

- **Model:** YOLOv8m
- **Dataset:** 7717 images (6471 VisDrone + 1246 Avata 360 perspective crops, pseudo-labeled at conf>0.5)
- **Epochs:** 30 (batch=8, cos_lr, patience=10, imgsz=1280)
- **Hardware:** NVIDIA A100-SXM4-40GB, Colab, ~1.8h
- **Result:** mAP50 = 58.0% all, 88.8% cars, 68.0% pedestrians
- **Domain impact:** +0.27 conf on Avata parking frame (0.63 vs 0.36 with v8m-only)
- **Trade-off:** High-altitude detection slightly worse — v8m VisDrone-only remains best overall

## Key Lessons

1. **imgsz=1280** is the single biggest improvement (+54% mAP50 vs 640)
2. **YOLOv8m** adds +9% over v8s — most impactful at >5m altitude
3. Fine-tuning on small domain data alone → **catastrophic forgetting** (must combine with VisDrone)
4. **Dual-model ensemble** beats any single model across altitude range
5. `cos_lr + patience=10 + 30 epochs` → best weights around epoch 25-27
6. v8m is too conservative for parking (misses vehicles at conf=0.25) — use v8s for that
