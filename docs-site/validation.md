# Validation Results

Per-platform validation of both use cases across all drone platforms.

## Use Case 1: Person Detection & 1:1 Rule

| Platform | Method | Alt Range | Model | Best Conf | Validated |
|----------|--------|-----------|-------|-----------|-----------| 
| **DJI M2EA** | GSD + SRT pitch | 15-70m | VisDrone 1280 | 0.49 at 70m, 0.34 at 15m | ✅ Detects pedestrians |
| **Autel MAX 4T** | LRF + MQTT GPS | 18-26m | Onboard AI (thermal) | — | ✅ 4 violations correctly flagged |
| **Autel MAX 4T** | RGB + VisDrone 1280 | 18-26m | VisDrone 1280 | 2 persons in 4K frame | ✅ |
| **DJI Avata 360** | Dual-fisheye + ensemble | 2-7m | COCO + VisDrone v8m | 0.90 at 2m, 0.63 at ~7m | ✅ Full descent coverage |

## Use Case 2: Parking Occupancy

| Platform | Method | Alt | Vehicles Detected | Validated |
|----------|--------|-----|-------------------|-----------| 
| **DJI M2EA** | VisDrone 1280 (native) | 70m | 55 cars + 5 peds + 2 trucks | ✅ No SAHI needed |
| **Autel MAX 4T** | VisDrone 1280 (native) | 80m | 95 cars + 3 vans | ✅ |
| **Autel MAX 4T** | VisDrone 1280 (thermal) | 80m | 43 cars + 29 vans | ✅ Thermal stream |
| **DJI Avata 360** | Nadir perspective crop | 21-48m | 38-46 vehicles | ✅ From LRF proxy |

## Use Case 3: GNSS-Denied Navigation

| Metric | Result |
|--------|--------|
| **Median position error** | **5.8 m** |
| Mean error | 22.1 m (3 outliers) |
| Under 25m | 70% of tests |
| Model | EfficientNet-B2, 512-d embeddings |

→ [Full UC3 documentation](gnss-denied.md)

## Use Case 4: 3D Gaussian Splatting

| Metric | Result |
|--------|--------|
| COLMAP registration | 432/432 (100%) |
| 3D points | 240,076 |
| **PSNR (30k iter)** | **34.2 dB** |
| Training time | 19 min (A100) |

→ [Full UC4 documentation](gaussian-splatting.md)

## Summary

All four use cases validated on real drone footage. Detection pipeline works across RGB, thermal, fisheye, and equirectangular inputs from 3 drone platforms.
