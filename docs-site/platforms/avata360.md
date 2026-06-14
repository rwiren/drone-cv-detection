# DJI Avata 360

## Hardware Specs

- **Format:** Dual-fisheye (2× 200° f/1.9 lenses)
- **Layout:** Right lens = nadir (ground), Left lens = zenith (sky)
- **Proxy:** .LRF — 1920×960 (two 960×960 fisheye circles)
- **Full-res:** .OSV — dual-fisheye at higher resolution
- **Telemetry:** SRT sidecar at 60fps (GPS, altitude, yaw, pitch per frame)
- **Stabilization:** RockSteady 3.0 (horizon lock regardless of FPV maneuvers)
- **Coverage:** 360° omnidirectional — no gimbal pointing required

## Pipeline

```
Dual-fisheye frame (1920×960)
        │
        ▼
Split: Right lens (960×960) = nadir
        │
        ▼
Equidistant fisheye projection (r = f·θ)
        │
        ▼
8 perspective views (640×480, every 45°)
        │
        ▼
YOLO ensemble: v8m (aerial) + COCO (close)
        │
        ▼
Best detection per view → report azimuth + confidence
```

## Detection Results (Descent Sequence)

| 15.1m (4 persons) | 5.1m (3 persons) | 2.2m (5 persons) | 2.2m (close, 0.90) |
|------|------|------|------|
| ![15m](../images/detect_15m.jpg) | ![5m](../images/detect_5m.jpg) | ![multi](../images/detect_2m_multi.jpg) | ![close](../images/detect_2m_close.jpg) |

| Altitude | VisDrone v8m | COCO yolov8s | Ensemble |
|----------|-------------|-------------|----------|
| 8.4m | **0.60** | 0.36 | 0.60 |
| 4.4m | **0.46** | 0.33 | 0.46 |
| 2.9m | **0.41** | miss | 0.41 |
| 2.2m | 0.50 | **0.89** | 0.89 |

## Parking Detection from Avata

The nadir view (pitch=0) captures vehicles from directly below:

| Timestamp | Altitude | Vehicles Detected |
|-----------|----------|-------------------|
| t=10s | 21.0m | 38 |
| t=30s | 48.2m | 46 |
| t=180s | 2.3m | 24 |

## Key Finding: Dual-Fisheye, Not Equirectangular

![Raw dual-fisheye](../images/dual_fisheye_raw.jpg)

The DJI Avata 360 .LRF files are **not** equirectangular panoramas. They contain raw dual-fisheye (two circular images). The correct projection is:

```python
# Equidistant fisheye: r = f_fish * theta
theta = np.arccos(np.clip(z, -1, 1))
phi = np.arctan2(y, x)
r = f_fish * theta
src_x = cx + r * np.cos(phi)
src_y = cy + r * np.sin(phi)
```

This was the root cause of broken detection in early versions — using equirectangular (lon/lat) mapping produced rotated garbage output.
