# Calibration

## Autel MQTT FOV Mismatch

The Autel EVO MAX 4T V2 firmware maps all AI detection bounding box coordinates using the **wide-camera FOV (84°)** regardless of which sensor produced the detection. The thermal sensor has 42° FOV — causing a 1.4× coordinate space mismatch.

### Correction Model

```python
x_corrected = 0.8384 × x_mqtt + 0.0915
y_corrected = y_mqtt + 0.049
```

Achieves **<2.5px** accuracy across the entire frame.

### Key Evidence

- Error is **flat** across the image (not radial) → proves firmware coordinate mismatch, not lens distortion
- Simple affine model works perfectly — no radial correction needed
- No public documentation of this behavior exists

Full paper: [Autel EVO MAX 4T V2 AI Verification →](../autel-verification.md)

## Firmware Label Swap

At the MQTT protocol level, sensor labels are swapped:

| MQTT Label | Actual Sensor |
|-----------|---------------|
| `wide` | Thermal (640×512, 42° FOV) |
| `thermal` | Wide camera (8000×6000, 84° FOV) |

This is consistent across firmware v1.9.1.219.

## DJI Avata 360 — SRT Altitude

The SRT `rel_alt` field reports altitude relative to the **takeoff point**, not absolute AGL. Measured discrepancy: up to 5m difference from visual observation when operating over terrain at different elevation from takeoff.
