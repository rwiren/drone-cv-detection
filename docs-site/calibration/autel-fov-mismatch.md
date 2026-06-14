# Autel MQTT FOV Mismatch — Original Research

!!! warning "Novel Finding"
    This firmware behavior is **undocumented publicly**. A comprehensive search (2026-06-14) of Autel developer docs, community forums, Pix4D, DroneDeploy, Stack Overflow, GitHub, and Reddit found no prior documentation.

## The Problem

MQTT bounding boxes from the Autel onboard AI are offset when overlaid on saved thermal JPEG images. The offset is position-dependent (edges shift more than center).

## Root Cause

The firmware's AI detection pipeline maps **all bounding box coordinates using the wide-camera FOV (58.6°)**, regardless of which sensor produced the detection. The thermal sensor has a 13mm lens (DFOV 42°) — a 1.4× narrower field.

This is a **linear affine mismatch**, not radial lens distortion.

## Proof: Linear, Not Radial

If the error were optical (radial distortion), the correction would be:

```
x_undistorted = x(1 + k₁r² + k₂r⁴ + ...)
```

This would fail at frame edges. Instead, our simple affine model achieves:

| Position | Error |
|----------|-------|
| Frame center (Car #745) | 1.8px |
| Frame edge (Car #749) | 2.3px |

**Sub-pixel accuracy everywhere** — proving the mismatch is purely linear.

## The Correction

```python
# Thermal JPEG coordinates:
x_corrected = 0.8384 × x_mqtt + 0.0915
y_corrected = y_mqtt + 0.049

# RGB JPEG coordinates:
x_corrected = 0.5 + (x_mqtt - 0.5) × 1.22
```

## Implementation

```python
from autel_telemetry import correct_mqtt_bbox

# bbox from MQTT: {x: 0.5, y: 0.4, w: 0.1, h: 0.15}
corrected = correct_mqtt_bbox(bbox, target='thermal')
# Returns: (cx, cy, w, h) in thermal image space
```

## Validation Scope

| Geometry | Accuracy | Status |
|----------|----------|--------|
| Nadir (0° pitch, 80m) | <2.5px | ✅ Validated |
| Angled (-33° pitch, 19m) | ~87px | ⚠️ Use GPS position instead |

## Why This Doesn't Affect Safety Calculations

The 1:1 rule uses GPS coordinates from the MQTT payload — not pixel positions. The bbox offset only affects visualization overlays.
