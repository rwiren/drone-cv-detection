# Engineering Analysis of the DJI Avata 360 Dual-Fisheye Computer Vision Pipeline

## Abstract

This document presents an engineering analysis of the DJI Avata 360 camera system for automated computer vision detection, focusing on the dual-fisheye-to-perspective extraction pipeline and its application to aerial person and vehicle detection. Through systematic experimentation, we document several novel findings regarding the DJI file format architecture, projection mathematics, and the comparative performance of two distinct processing pipelines (raw dual-fisheye vs. stitched equirectangular). These findings are not documented in any publicly available DJI developer resources.

## 1. Hardware Architecture

### 1.1 Camera Specifications

| Parameter | Value |
|-----------|-------|
| Sensor | Two 1/1.1-inch square CMOS, 64MP each |
| Lens FOV | 200° per lens (equidistant fisheye) |
| Focal length | 2.5 mm (7.8 mm format equivalent) |
| Aperture | f/1.9 |
| 360° Video | 8K: 7680×3840 @ 60/50fps (H.265) |
| 6K Video | 6000×3000 @ 60fps |
| Stabilization | Single-axis mechanical gimbal + RockSteady 3.0 |
| File formats | .OSV (raw), .LRF (proxy), .SRT (telemetry) |
| Telemetry | 60fps SRT sidecar (GPS, altitude, yaw, pitch per frame) |

### 1.2 Lens Configuration

The DJI Avata 360 mounts two fisheye lenses in a back-to-back configuration on a single-axis mechanical gimbal:

- **Nadir lens** (ground-facing): Captures the hemisphere below the aircraft
- **Zenith lens** (sky-facing): Captures the hemisphere above the aircraft

The 200° FOV per lens provides >20° overlap between the two hemispheres, enabling seamless stitching by the DJI Studio software.

## 2. File Format Architecture (Novel Finding)

### 2.1 Discovery

Through direct analysis of the raw output files, we determined the following undocumented file format architecture:

| File | Resolution | Layout | Content | CV Usability |
|------|-----------|--------|---------|--------------|
| `.LRF` | 1920×960 | Side-by-side | Both lenses (left=zenith, right=nadir) | ✅ Primary source |
| `.OSV` | 3840×3840 | Single circle | **Zenith lens only** (sky) | ❌ Not usable for ground detection |
| `.MP4` (DJI Studio export) | 7680×3840 | Equirectangular | Both lenses, stitched | ✅ Best coverage |
| `.SRT` | Text | Per-frame | GPS, altitude, yaw, pitch @ 60fps | ✅ Telemetry |

### 2.2 Critical Finding: OSV Contains Only One Lens

The raw `.OSV` file (3840×3840 pixels) contains a single fisheye circle filling the entire frame. Through visual inspection, this was identified as the **zenith (sky) lens only**. The nadir (ground) lens at full resolution is not accessible from any raw file without DJI Studio processing.

**Implication:** Developers attempting to use .OSV files directly for ground-based computer vision will obtain only sky imagery. The .LRF proxy (despite lower resolution) is the only direct-access source containing both lenses.

**Search result:** No public DJI documentation, developer forums, or community resources describe this single-lens limitation of the .OSV format. This appears to be an undocumented implementation detail.

### 2.3 SRT Telemetry Reliability

The SRT `rel_alt` field reports altitude relative to the takeoff point, not absolute height above ground level. In scenarios where the drone operates over terrain at different elevations from the takeoff point, the reported altitude can significantly disagree with visual observation.

**Measured discrepancy:** At t=183s, SRT reports `rel_alt: 2.2m`, while visual analysis of the perspective extraction clearly shows the drone at approximately 7m above the parking surface.

## 3. Two Extraction Pipelines

### 3.1 Pipeline A: Raw Dual-Fisheye (LRF)

**Input:** `.LRF` file (1920×960, both lenses side-by-side)

**Projection model:** Equidistant fisheye

```
r = f_fish × θ
f_fish = radius / radians(FOV / 2)
```

Where:
- `r` = radial distance from fisheye center (pixels)
- `θ` = angle from optical axis (radians)
- `f_fish` = fisheye focal length in pixels
- FOV = 200° (per DJI specifications)

**Coordinate system:**
- pitch = 0 → straight down (nadir)
- pitch = 90 → horizon
- yaw = 0-360 → azimuth rotation

**Output:** 640×480 perspective views (8 views at 45° intervals)

### 3.2 Pipeline B: Stitched Equirectangular (DJI Studio Export)

**Input:** `.MP4` from DJI Studio (7680×3840, equirectangular)

**Projection model:** Spherical (longitude/latitude)

```
lon = arctan2(x, z)
lat = arcsin(y)
pixel_x = (lon/π + 1) / 2 × width
pixel_y = (0.5 - lat/π) × height
```

**Coordinate system:**
- pitch = 0 → horizon
- pitch < 0 → look down toward ground
- pitch > 0 → look up toward sky
- yaw = 0-360 → horizontal rotation

**Output:** 1280×960 perspective views (12 views at 30° intervals, 7 pitch angles)

### 3.3 Critical Difference in Orientation Convention

The two pipelines use **opposite** pitch conventions:

| Convention | Pipeline A (LRF fisheye) | Pipeline B (equirectangular) |
|-----------|--------------------------|------------------------------|
| pitch = 0 | Straight down (nadir) | Horizon |
| Look at ground | pitch = 30-70 | pitch = -5 to -70 |
| Look at horizon | pitch = 90 | pitch = 0 |

This difference is a common source of errors when switching between raw and stitched 360° video processing.

## 4. Comparative Evaluation

### 4.1 Test Conditions

- **Flight:** 2026-06-12, Jorvas, Finland
- **Duration:** 197 seconds (descent from ~32m to ~2m AGL)
- **Evaluation window:** t=160-196s (37 frames, 1 per second)
- **Models:** YOLOv8m (VisDrone 1280) + COCO yolov8s (ensemble)
- **Hardware:** NVIDIA A100 (Colab) + AMD Ryzen AI 7 PRO 350 (local)

### 4.2 Results

| Metric | Pipeline A (LRF, 960px) | Pipeline B (8K equirect) |
|--------|------------------------|--------------------------|
| **Detection rate** | ~70% (with false positives) | **86% (32/37 frames)** |
| **Max confidence** | **0.90** (COCO, close-up) | 0.79 (COCO, close-up) |
| **High-altitude reliability** | Poor (FPs on rooftop equipment) | **Good (0.31-0.69, clean)** |
| **Close-range confidence** | 0.90 | 0.79 |
| **False positive rate** | High at altitude | **Low** |
| **Processing time (A100)** | ~1 min (37 frames) | 7.4 min (37 frames) |
| **Processing time (CPU)** | ~10 min | 43 min |
| **Resolution per view** | 640×480 | 1280×960 |

### 4.3 Analysis

**Pipeline A (LRF) advantages:**
- Direct file access (no DJI Studio processing needed)
- Higher peak confidence at very close range (person fills more of the extracted view)
- Faster processing (lower resolution)

**Pipeline B (8K equirect) advantages:**
- Significantly better detection coverage (86% vs ~70%)
- Clean high-altitude detection without false positives
- 4× more pixels per extracted view (1280×960 vs 640×480)
- More consistent detection across the full descent

**Why LRF has higher peak confidence:**
At very close range (t=190, ~2m), the fisheye extraction at steep pitch angles (70-80° from nadir) produces a perspective view where the person fills a large portion of the frame. The equirectangular extraction at the same scenario produces a slightly more distorted view due to stitching artifacts near the nadir seam.

**Why 8K is better for coverage:**
The higher pixel count means persons are represented by more pixels at every altitude. At t=173 (high altitude), the 8K pipeline detects with 0.53 confidence while the LRF pipeline either misses or produces false positives on rooftop equipment.

## 5. Model Performance on 360° Extracted Views

### 5.1 Ensemble Architecture

No single model covers all altitudes effectively:

| Altitude | Best Model | Confidence | Reasoning |
|----------|-----------|------------|-----------|
| >5m (aerial) | VisDrone v8m (imgsz=1280) | 0.31-0.69 | Trained on aerial drone imagery |
| <3m (close) | COCO yolov8s | 0.60-0.79 | Trained on normal-perspective imagery |

The crossover point occurs at approximately 3-5m altitude, where both models achieve similar confidence levels.

### 5.2 Combined Model (Domain-Adapted)

Training on VisDrone + 1246 Avata 360 perspective crops:
- Same VisDrone validation mAP (0.580 vs 0.581 — no forgetting)
- +0.27 confidence improvement on specific Avata parking lot views
- Trade-off: slight degradation in high-altitude detection

## 6. Conclusions and Novel Contributions

1. **OSV file format is single-lens only** — undocumented by DJI; developers must use .LRF or DJI Studio export for dual-hemisphere CV processing

2. **Two viable pipelines with different strengths** — 8K equirectangular for coverage, LRF fisheye for close-range peak confidence

3. **Pitch convention differs between raw and stitched** — a critical implementation detail not documented in any community resource

4. **86% detection rate from 360° video** — continuous person detection across 37 consecutive frames during descent, validating omnidirectional safety monitoring without gimbal pointing

5. **SRT altitude unreliable for absolute AGL** — `rel_alt` is relative to takeoff, can disagree with visual evidence by 3-5m depending on terrain

## 7. Recommendations for Developers

1. **Use .LRF for prototyping** — fast, both lenses, works directly with OpenCV
2. **Use DJI Studio export for production** — 8K gives significantly better detection coverage
3. **Never use .OSV for ground detection** — it only contains the sky lens
4. **Apply equidistant fisheye projection for LRF** — NOT equirectangular (common mistake)
5. **Apply equirectangular projection for DJI Studio MP4** — standard lon/lat mapping
6. **Use dual-model ensemble** — VisDrone for aerial, COCO for close-range, take max confidence per view

## References

- DJI Avata 360 Specifications: https://www.dji.com/fi/avata-360/specs
- Patent WO2025034145A1 — "Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"
- VisDrone2019 Dataset: https://github.com/VisDrone/VisDrone-Dataset
- Ultralytics YOLOv8: https://docs.ultralytics.com/
