# Autel MQTT FOV Mismatch — Summary

!!! info "Full Analysis"
    For the complete engineering document including hardware architecture, NPU pipeline, and thermal detection analysis, see the [Autel EVO MAX 4T V2 AI Verification](../autel-verification.md).

## The Problem

MQTT bounding boxes from the Autel onboard AI are offset when overlaid on saved thermal JPEG images.

## Root Cause

The firmware's AI detection pipeline maps **all bounding box coordinates using the wide-camera FOV (58.6°)**, regardless of which sensor produced the detection. The thermal sensor has a 13mm lens (DFOV 42°) — a 1.4× narrower field.

## The Correction

```python
x_corrected = 0.8384 × x_mqtt + 0.0915
y_corrected = y_mqtt + 0.049
```

## Key Evidence

- Simple affine model achieves **<2.5px** accuracy across entire frame
- Error is flat (not radial) → proves it's a coordinate system mismatch, not lens distortion
- No public documentation of this behavior exists (comprehensive search 2026-06-14)

For full details: [Autel EVO MAX 4T V2 AI Verification →](../autel-verification.md)
