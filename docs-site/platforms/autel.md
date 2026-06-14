# Autel EVO MAX 4T V2

## Overview

Multi-sensor drone with **onboard AI** that runs person/vehicle detection on the NPU during flight. Publishes detections over MQTT in real-time — the only platform in this project capable of fully autonomous detection without ground processing.

## Sensors

| Sensor | Resolution | FOV | Use |
|--------|-----------|-----|-----|
| Wide RGB | 1/1.3" 50MP | 84° DFOV | Visual detection, mapping |
| Thermal (640T) | 640×512, uncooled VOx | 42° DFOV (13mm) | Person detection, night ops |
| Zoom | 1/2" 48MP | 15-60° (optical zoom) | Identification |
| LRF | Laser rangefinder | Point | Direct distance measurement |

## Onboard AI

The Autel firmware (v1.9.1.219) runs object detection on the NPU:
- Detects persons, vehicles, boats in thermal + wide simultaneously
- Publishes bounding boxes over MQTT to controller
- Real-time GPS position of detected targets

## Novel Finding: Firmware FOV Mismatch

!!! warning "Undocumented Firmware Behavior"
    MQTT bounding box coordinates use **wide-camera coordinate space** (84° FOV) even for thermal detections (42° FOV). This causes a systematic offset when overlaying on saved thermal images.

**Correction:**
```python
x_corrected = 0.8384 × x_mqtt + 0.0915
y_corrected = y_mqtt + 0.049
```

See full analysis: [Autel EVO MAX 4T V2 AI Verification →](../autel-verification.md)

## Firmware Label Swap

At the MQTT protocol level:
- `wide` stream actually delivers **thermal** imagery
- `thermal` stream actually delivers **wide camera** imagery

This swap is consistent across firmware v1.9.1.219 and must be accounted for in all processing code.
