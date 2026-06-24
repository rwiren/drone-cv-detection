# Capabilities

## Working Well

- **Vehicle detection** from aerial video — VisDrone 1280: 87.3% mAP50 on cars
- **Person detection ensemble** — COCO (close) + VisDrone 1280 (aerial), validated on Avata 360 at ~2-7m altitude
- **Object tracking** with ByteTrack (persistent IDs, trajectory trails)
- **Thermal+RGB fusion** visualization and cross-validation
- **1:1 rule with LRF** — Autel laser rangefinder provides ground-truth distance
- **Parking occupancy** — 104 vehicles detected from 134m nadir
- **360° omnidirectional detection** — dual-fisheye extraction, no blind spots
- **False positive filtering** — aspect ratio heuristic removes dumpsters/equipment from nadir views
- **3D Gaussian Splatting** — PSNR 34.2 dB photorealistic reconstruction
- **GNSS-denied navigation** — 5.8m median position accuracy (CNN cross-view)

## Proof-of-Concept (Limitations Documented)

- **Object tracking unique count** — inflated with moving drone camera due to ID fragmentation; works correctly with static camera
- **MQTT-to-video sync** — Autel OSD at 1 Hz requires interpolation; no issues with still images
- **Thermal-only detection** — cold parked cars can be confused with cold pavement shadows; RGB cross-check resolves

## Known Limitations

- Standard YOLO (COCO) produces false positives from aerial views; VisDrone fine-tuning eliminates this
- Autel MQTT AI bounding boxes require affine calibration when overlaid on saved thermal images (linear scale + offset)
- Thermal segmentation is affected by solar loading — car surface temp correlates with sun exposure, NOT engine activity
- Parking empty slot detection needs pre-defined slot geometry for production reliability
- Fine-tuning on small domain-specific dataset alone causes catastrophic forgetting — must combine with base VisDrone data
- GNSS-denied cross-view matching fails over: water, dense forest canopy, snow-covered terrain (no features)
