# Calibration Insights

## MQTT Detection Stream → Saved Image Mapping

The Autel onboard AI runs on an internal 1280×960 processing stream. When projecting MQTT bounding boxes onto saved images, a calibrated **affine correction** must be applied — not a simple translation.

**Root cause:** The detection firmware maps all bounding box coordinates using the wide-camera FOV (58.6°), regardless of which sensor produced the detection. The thermal sensor has a 13mm lens (DFOV 42°) — a 1.4× narrower field. This creates a uniform linear scale mismatch (not radial lens distortion), correctable with a simple affine transform. No public documentation of this firmware behavior exists — this is original empirical research (see `docs/Autel EVO MAX 4T V2 AI Verification.md`).

```
Corrected thermal coordinates:
  x_corrected = 0.8384 × x_mqtt + 0.0915
  y_corrected = y_mqtt + 0.049
```

| Target Image | Correction Type | Formula | Implementation |
|---|---|---|---|
| **Thermal JPEG** (640×512) | Affine (scale + translate) | `x' = 0.8384x + 0.0915`, `y' = y + 0.049` | `correct_mqtt_bbox(bbox, 'thermal')` |
| **RGB JPEG** (4000×3000) | FOV scaling from center | `x' = 0.5 + (x-0.5)×1.22` | `correct_mqtt_bbox(bbox, 'rgb')` |
| **Nadir false positives** | Aspect ratio filter | reject if `w/h > 1.4` | Cars are portrait, dumpsters landscape |

These corrections are implemented in `src/autel_telemetry.py:correct_mqtt_bbox()`.

## Why Affine (Not Simple Translation)

The error pattern is:
- Left objects → shifted right
- Right objects → shifted left  
- All objects → shifted upward

This is **uniform linear scaling toward center** — caused by the firmware projecting thermal detections into the wider camera's coordinate space. The scale factor (0.8384) matches the FOV ratio: 42°/58.6° ≈ 0.72 (the additional offset accounts for sensor parallax). The error is position-dependent but **linear** — proven by <2.5px residual across the entire frame with our affine model.

## Firmware Label Swap Discovery

Cross-referencing the [Autel Mission Control](https://github.com/rwiren/autel-mission-control) MQTT schema capture (`docs/autel_raw_schema.json`) revealed that the OSD camera fields are **mislabeled** in the firmware:

| OSD Field Name | Firmware Reports | Actual Physical Camera |
|---|---|---|
| `ir_focal_length` | 9.1mm, FOV 48.1° | Zoom/tele lens (not IR!) |
| `zoom_focal_length` | 4.49mm, FOV 58.6° | Wide camera (not zoom!) |
| Actual thermal (13mm) | — | Not reported in OSD at all |

The AI detection stream uses the `zoom_fov_h: 58.6°` (actually the wide camera) as its coordinate space. This explains why naive bbox mapping to the 13mm thermal JPEG (DFOV 42°) produces systematic compression — the coordinate spaces differ by a factor of ~1.4x.

## Calibration Accuracy (Validated)

| View Geometry | Error | Status | Notes |
|---|---|---|---|
| Nadir (0° pitch, 80m) | **<2.5 px** | ✅ Validated | Sub-pixel accuracy, affine model is correct |
| Angled (-33° pitch, 19m) | ~87 px | ⚠️ Approximate | Affine breaks down; use GPS position instead |

For the 1:1 rule calculation, the angled-view limitation is acceptable: the lateral distance calculation uses the person's **GPS position** from MQTT (independent of bbox pixel alignment), not the pixel coordinates. The bbox overlay on saved images is purely for visualization.

## Architecture: Why Pixel Errors Don't Affect Safety Calculations

```
                MQTT Detection Payload
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    bbox {x,y,w,h}   pos {lat,lon}   LRF distance
    (pixel space)    (GPS, hardware)  (laser, hardware)
          │              │              │
          ▼              ▼              ▼
    Visualization    1:1 Rule Calc   Ground Truth
    (overlay only)   (1:1 rule calc)   (validation)
          │              │              │
    Affected by      IMMUNE to       IMMUNE to
    FOV mismatch     pixel errors    pixel errors
```

The lateral distance calculation (Eq. 10 from WO2025034145A1) and the 1:1 rule comparison operate on the **right branch** — GPS + LRF telemetry from hardware sensor fusion. Bounding box pixel coordinates (left branch) are used only to prove that detection occurred, not for spatial measurement.

**Future work:** A pitch-dependent homography matrix could improve visualization at angled views. This would require calibration points at multiple gimbal angles, or computing the projective transform from the known camera intrinsics + gimbal pitch. Not needed for safety rule validation but useful for real-time operator displays.

## Sensor Specifications (from manufacturer datasheets)

| Spec | DJI M2EA Thermal | Autel MAX 4T Thermal | Autel MAX 4T Wide |
|---|---|---|---|
| Resolution | 640×512 @30Hz | 640×512 | 8192×6144 (50MP) |
| Focal length | 9mm (38mm eq.) | 13mm | 4.5mm (23mm eq.) |
| DFOV | ~57° | 42° | 85° |
| Aperture | — | f/1.2 | f/1.9 |
| Pixel pitch | 12μm | 12μm | — |
| LRF | No | Yes (±1m, 1200m range) | — |

| Spec | DJI M2EA Visual | Autel MAX 4T Zoom |
|---|---|---|
| Sensor | 1/2" 48MP | 1/2" 48MP |
| Focal length | 24mm eq., f/2.8 | 64-234mm eq., f/2.8-4.8 |
| FOV | 84° | Variable (telephoto) |
| Max resolution | 8000×6000 | 8000×6000 |

## Thermal vs RGB Detection Characteristics

| Object | RGB Signature | Thermal Signature | Detection Notes |
|---|---|---|---|
| Parked car (cold) | Clear color/shape | Dark (cool) rectangle, blends with shadows | Thermal may miss cold parked cars |
| Parked car (warm) | Same | Bright (hot), stands out from pavement | Easy in both modalities |
| Person | Clothing/shape | Very bright (body heat 37°C vs ambient) | Thermal excels, esp. in shadows |
| Dumpster | Green/blue container | Varies with sun exposure | Both detect as vehicle FP |
| Shadow on pavement | Visible as dark area | Cool patch, similar to cold car | Thermal can confuse shadow with vehicle |

**Key learning:** The thermal AI detected "cars" where there were actually cold shadows/patches on the pavement adjacent to the real vehicles. This is because cold metal (parked car roof) and cold concrete (shaded pavement) have similar thermal signatures from 80m nadir. The RGB channel resolves this ambiguity instantly — demonstrating why **multispectral fusion** (as described in the safety system design) is valuable.

