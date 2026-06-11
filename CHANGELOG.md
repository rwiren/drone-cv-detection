# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0] - 2026-06-11
### Added
- Patent WO2025034145A1 lateral distance implementation (`src/lateral_distance.py`)
- DJI SRT telemetry parser (focal length, gimbal pitch, altitude, GPS per frame)
- Instance segmentation for per-car oriented bounding boxes (YOLOv8-seg + minAreaRect)
- Two-stream RGB+Thermal fusion parking monitor (`src/parking_monitor.py`)
- Thermal overlay visualization

### Changed
- Patent demo now shows only person detections (not cars) — factually correct per patent scope
- Replaced 32m altitude demo (low confidence: 0.21-0.31) with 17m demo (0.59-0.81 confidence)
- Cleaned sample images — removed misleading results

### Known Issues
- Person detection confidence drops below 0.3 at altitudes >30m (VisDrone model limitation)
- Parking oriented boxes require instance segmentation; COCO-seg model misses ~25% of cars from aerial view
- Parking empty slot detection is gap-based heuristic, not ground-truth validated

## [0.1.0] - 2026-06-11
### Added
- YOLOv8s fine-tuned on VisDrone2019-DET (5 epochs, 6471 images, CPU training)
- Vehicle detection achieving 72% mAP50 on cars from aerial views
- ByteTrack object tracking with persistent IDs and trajectory visualization
- SAHI slicing for small object detection in high-altitude imagery
- Basic parking occupancy estimation (row gap analysis)
- YOLO webcam car counter script
- Project structure with README, .gitignore, data symlinks

### Training Results
- mAP50 all classes: 29.5%
- mAP50 cars: 72.0%
- mAP50 pedestrians: 34.1%
- mAP50 buses: 40.5%
- Inference: ~0.3s/frame on CPU (AMD Ryzen AI 7 PRO 350)
