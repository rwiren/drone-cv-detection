# DJI Mavic 2 Enterprise Advanced

## Overview

Dual-sensor drone (thermal + RGB) used for person detection, vehicle tracking, and parking occupancy monitoring. Primary platform for 1:1 safety rule validation.

## Sensors

| Sensor | Resolution | FOV | Use |
|--------|-----------|-----|-----|
| RGB (1/2" CMOS) | 4000×3000 (48MP) | 84° | Vehicle detection, tracking |
| Thermal (uncooled VOx) | 640×512 | 61° DFOV | Person detection (day/night) |

## Detection Capabilities

| Task | Model | Result |
|------|-------|--------|
| Vehicle detection | VisDrone YOLOv8s (imgsz=1280) | mAP50 87.3% (car) |
| Person detection (aerial) | VisDrone YOLOv8m (imgsz=1280) | mAP50 68.1% (pedestrian) |
| Vehicle tracking | ByteTrack | Persistent IDs across frames |
| Parking occupancy | Segmentation OBB | Slot-level monitoring |
| Lateral distance | GSD + SRT gimbal pitch | 1:1 rule validation |

## Telemetry

DJI SRT format with GPS, altitude, gimbal angles per frame:
```
GPS(60.1316, 24.5126, 15.5) BAROMETER:15.2
ISO:400 Shutter:1/1000 Fnum:2.8 EV:-0.7
[Pitch:-45.0] [Yaw:131.9] [Roll:0.2]
```

## Safety Distance Calculation

```python
GSD = altitude / (focal_length_px × cos(gimbal_pitch))
lateral_distance = pixel_offset × GSD
safety_ratio = lateral_distance / altitude  # Must be ≥ 1.0
```
