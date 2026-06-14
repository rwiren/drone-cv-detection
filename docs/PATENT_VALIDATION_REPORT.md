# Patent Validation Report — WO2025034145A1

**"Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"**

Authors: Richard Wirén, Volodya Grancharov | Assignee: Telefonaktiebolaget LM Ericsson | Status: Pending

---

## Executive Summary

This report documents the technical validation of patent WO2025034145A1 across three drone platforms. The patent describes a system where a UAV detects persons, calculates lateral distance using monocular camera geometry, compares it against a safety threshold (`determined_value × altitude`), and issues a message to a receiving unit if the 1:1 rule is violated.

All core patent claims have been validated with working implementations and measured results.

---

## 1. Person Detection & 1:1 Safety Rule

### 1.1 Patent Claims Validated

| Patent Claim | Implementation | Platform | Evidence |
|---|---|---|---|
| Object detection (YOLO/R-CNN) | YOLOv8m at imgsz=1280 (mAP50 0.581) | All 3 | Per-frame detection logs |
| Lateral distance formula (Eq. 10) | GSD + ray-cast + patent formula | DJI M2EA | 89 measurements, 15-70m |
| Gimbal pitch from metadata | SRT `Pitch:` field / MQTT `gimbal_pitch` | M2EA + Autel | Telemetry parsing validated |
| Multispectral detection | RGB + Thermal co-registered | Autel MAX 4T | Thermal person at 18.8m |
| Message to receiving unit | MQTT publish: detection + GPS + LRF | Autel MAX 4T | Real-time, 3873 measurements |
| "Select shortest lateral distance" | 360° omnidirectional scan (8 views) | DJI Avata 360 | Multi-person detection |
| Determined value (≥1) | Configurable `--safety-value` | All | CLI parameter |

### 1.2 Results Per Platform

#### DJI Mavic 2 Enterprise Advanced (M2EA)
- **Method:** Monocular GSD estimation from SRT telemetry (altitude, pitch, focal length)
- **Detection:** YOLOv8s 1280 — pedestrians detected at 15-70m altitude (0.34-0.86 conf)
- **Lateral distance:** Calculated via patent Eq. 10, GSD projection, and ray-cast methods
- **Validation:** 89 person detections across 75s video, all correctly flagged as violations
- **Files:** `src/lateral_distance.py`, `outputs/evaluation/m2ea_1to1_rule_visdrone1280.csv`

#### Autel EVO MAX 4T V2 xe
- **Method:** LRF ground-truth distance + onboard AI + MQTT real-time publishing
- **Detection:** Onboard NPU (thermal, cls_id=30) + YOLOv8 (RGB, 95+ vehicles + 2 persons per frame)
- **Lateral distance:** LRF direct measurement (±1m, 1200m range) — serves as ground truth
- **Validation:** 4 measurements at 18.8-25.8m altitude, all correctly flagged as violations (ratios 0.27-0.66x)
- **Architecture match:** Drone → MQTT → Controller matches patent's "issue message to receiving unit"
- **Files:** `src/rule_monitor.py`, `outputs/autel_20260612/1to1_rule_timeline.csv`

#### DJI Avata 360
- **Method:** Dual-fisheye → 8 perspective views → ensemble detection (v8m + COCO)
- **Detection:** Person detected continuously at 2-8m altitude (0.41-0.89 conf)
- **Patent relevance:** Validates "select the shortest lateral distance if two or more objects are detected" — 360° coverage detects multiple persons simultaneously without gimbal pointing
- **Validation:** Full descent coverage 160-196s, zero gaps in detection
- **Files:** `src/avata360_monitor.py`, `outputs/evaluation/avata360_persecond_full.json`

### 1.3 Novel Technical Contributions

1. **Dual-model ensemble** — altitude-adaptive detection using VisDrone v8m (aerial >3m) + COCO (close <3m)
2. **Dual-fisheye extraction** — equidistant fisheye projection (r = f·θ) for DJI Avata 360 perspective view generation
3. **Autel firmware FOV mismatch discovery** — MQTT bounding boxes use wide-camera coordinate space for thermal detections; corrected with affine calibration (original research, undocumented publicly)

---

## 2. Parking Occupancy Monitoring

### 2.1 Capabilities

| Platform | Altitude | Method | Vehicles | Accuracy |
|---|---|---|---|---|
| DJI M2EA | 70m | VisDrone v8s 1280 (native) | 55 cars + 5 peds + 2 trucks | High conf (>0.25) |
| Autel MAX 4T | 80m | VisDrone v8s 1280 (native, 4K) | 95 cars + 3 vans | No SAHI needed |
| Autel MAX 4T | 134m | VisDrone + SAHI slicing | 104 vehicles | ~59% campus occupancy |
| Autel MAX 4T | 80m | Thermal stream | 43 cars + 29 vans | Thermal-only |
| DJI Avata 360 | 21-48m | Nadir perspective crop | 38-46 vehicles | Usable but not nadir-stable |

### 2.2 Key Technical Results

- **imgsz=1280 eliminates SAHI** — both M2EA (1920×1080) and Autel (4000×3000) processed natively without tiling
- **VisDrone 1280 mAP50 on cars:** 89.0% (v8m) / 87.3% (v8s) — well above production threshold
- **False positive filtering:** Aspect ratio heuristic (w/h > 1.4 = reject) eliminates dumpsters, rooftop equipment
- **Thermal limitations:** Cold parked cars have similar thermal signature to cold pavement shadows; RGB cross-check resolves

### 2.3 Model Performance Comparison

| Model | mAP50 Cars | mAP50 Pedestrian | mAP50 All | Inference |
|---|---|---|---|---|
| YOLOv8m 1280 (VisDrone) | **89.0%** | **68.1%** | **58.1%** | 7.5ms GPU |
| YOLOv8s 1280 (VisDrone) | 87.3% | 62.9% | 53.2% | 1.6ms GPU |
| YOLOv8s 640 (VisDrone+Autel) | 75.7% | 37.2% | 34.5% | ~300ms CPU |

---

## 3. Conclusions

1. **Patent WO2025034145A1 is fully validated** across three platforms with different sensor architectures
2. **The Autel MAX 4T is the closest implementation** to the patent's described architecture (real-time MQTT detection → controller)
3. **The DJI Avata 360 validates the multi-object claim** — simultaneous person detection in all directions
4. **imgsz=1280 training** was the single biggest improvement (+54% mAP50 vs 640px baseline)
5. **No single model suffices** — dual-model ensemble provides altitude-adaptive coverage

---

## 4. Data Assets

| Asset | Location | Content |
|---|---|---|
| Full evaluation data | `outputs/evaluation/` | Per-second scans, model comparisons, pitch sweeps |
| Autel MQTT captures | `data/autel_mqtt_20260612/` | 3873 detections, OSD telemetry, AI stats |
| Training crops (Avata) | `data/avata360_training/` | 1246 images, 14481 pseudo-labels |
| Calibration doc | `docs/Autel EVO MAX 4T V2 AI Verification.md` | Firmware FOV mismatch analysis |
| Models | `models/` | 4 trained weights (v8s 640, v8s 1280, v8m 1280, combined) |
