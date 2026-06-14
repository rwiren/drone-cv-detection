# DJI Avata 360

## Overview

360° FPV camera drone with two back-to-back 1/1.1" fisheye sensors providing full spherical coverage. No gimbal pointing needed — detects persons in all directions simultaneously.

## Sensors

| Parameter | Value |
|-----------|-------|
| Sensor | Two 1/1.1-inch square CMOS, 64MP each |
| Lens FOV | 200° per lens (equidistant fisheye) |
| Focal length | 2.5 mm |
| Aperture | f/1.9 |
| 360° Video | 8K: 7680×3840 @ 60/50fps |
| Stabilization | Single-axis mechanical gimbal + RockSteady 3.0 |

## File Formats (Novel Finding)

| File | Resolution | Content | CV Usability |
|------|-----------|---------|--------------|
| `.LRF` | 1920×960 | Both lenses side-by-side (dual-fisheye) | ✅ Direct access |
| `.OSV` | 3840×3840 | **Zenith lens only** (sky) | ❌ Not for ground CV |
| `.MP4` (DJI Studio) | 7680×3840 | Stitched equirectangular | ✅ Best coverage |
| `.SRT` | Text | GPS, altitude, gimbal @ 60fps | ✅ Telemetry |

!!! info "Critical: OSV is single-lens"
    The `.OSV` file contains **only the sky-facing lens**. Ground detection requires `.LRF` (both lenses at low res) or DJI Studio export (8K stitched).

## Two Extraction Pipelines

### Pipeline A: Dual-Fisheye (LRF)

```
LRF (1920×960) → Split right lens (nadir) → Equidistant fisheye projection
→ 8× perspective views (640×480) → YOLO → Detections
```

- Projection: `r = f_fish × θ` (equidistant fisheye)
- Pitch convention: 0 = nadir (straight down)
- **~70% detection rate**, peak confidence 0.90

### Pipeline B: 8K Equirectangular (DJI Studio)

```
MP4 (7680×3840) → Lon/lat equirectangular projection
→ 12× perspective views (1280×960) → YOLO → Detections
```

- Projection: standard spherical (longitude/latitude mapping)
- Pitch convention: 0 = horizon, negative = look down
- **86% detection rate** (32/37 frames), max confidence 0.79

## Results Comparison

| Metric | LRF (Pipeline A) | 8K Equirect (Pipeline B) |
|--------|------------------|--------------------------|
| Detection rate | ~70% | **86%** |
| Max confidence | **0.90** | 0.79 |
| False positives at altitude | High | **Low** |
| Processing (A100) | ~1 min | 7.4 min |
| Resolution per view | 640×480 | 1280×960 |

See full analysis: [DJI Avata 360 Pipeline Analysis →](../avata360-analysis.md)
