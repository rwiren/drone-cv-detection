# Sample Detections

## DJI M2EA — Vehicle Detection & Tracking

| Detection (VisDrone) | Tracking (ByteTrack) | 1:1 Safety Rule |
|---|---|---|
| ![detection](../images/detection_aerial.jpg) | ![tracking](../images/tracking_bytetrack.jpg) | ![patent](../images/patent_1to1_persons.jpg) |

| Segmentation OBB | Parking Occupancy | Thermal Overlay |
|---|---|---|
| ![seg](../images/parking_seg_obb.jpg) | ![parking](../images/parking_campus_wide.jpg) | ![thermal](../images/thermal_overlay.jpg) |

---

## Autel MAX 4T V2 xe — Parking & Person Detection (2026-06-12)

| Parking Wide | Parking Close | VisDrone 1280 |
|---|---|---|
| ![parking_wide](../images/MAX_0055_campus_occupancy.jpg) | ![parking_close](../images/MAX_0048_parking_occupancy.jpg) | ![visdrone1280](../images/MAX_0042_visdrone1280.jpg) |

| 1:1 Rule (Close) | 1:1 Rule (Far) |
|---|---|
| ![rule_close](../images/MAX_0043_1to1_rule.jpg) | ![rule_far](../images/MAX_0046_1to1_rule.jpg) |

| Thermal Person | Thermal Parking (MQTT overlay) |
|---|---|
| ![thermal_person](../images/IRX_0043_person_overlay.jpg) | ![thermal_parking](../images/IRX_0050_mqtt_overlay.jpg) |

| Model Comparison (Parking) | Model Comparison (Person) |
|---|---|
| ![cmp_parking](../images/MAX_0050_comparison.jpg) | ![cmp_person](../images/MAX_0043_comparison.jpg) |

---

## DJI Avata 360 — 360° Person Detection (2026-06-12)

| Dual-Fisheye Raw | Perspective Extracted |
|---|---|
| ![fisheye](../images/dual_fisheye_raw.jpg) | ![perspective](../images/perspective_extracted.jpg) |

| Parking Detection | Close-Range (2m) |
|---|---|
| ![parking](../images/detect_parking.jpg) | ![close](../images/detect_2m_close.jpg) |

---

## Detection Performance by Altitude

| Altitude | Model | Confidence | Platform |
|----------|-------|-----------|----------|
| 2m | COCO yolov8s | 0.89–0.90 | Avata 360 |
| 5.7m | VisDrone v8m 1280 | 0.56 | Avata 360 |
| 8m | VisDrone v8m 1280 | 0.60 | Avata 360 |
| 32m | VisDrone v8m 1280 | 0.31 | Avata 360 (8K) |
| 70m | VisDrone v8s 1280 | 0.86 | M2EA |
