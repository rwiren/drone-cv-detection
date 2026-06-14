# Firmware Label Swap Discovery

## The Issue

Cross-referencing the [Autel Mission Control](https://github.com/rwiren/autel-mission-control) MQTT schema capture revealed that OSD camera fields are **mislabeled** in the firmware:

| OSD Field Name | Firmware Reports | Actual Physical Camera |
|---|---|---|
| `ir_focal_length` | 9.1mm, FOV 48.1° | Zoom/tele lens (not IR!) |
| `zoom_focal_length` | 4.49mm, FOV 58.6° | Wide camera (not zoom!) |
| Actual thermal (13mm) | — | **Not reported in OSD at all** |

## Impact

The AI detection stream uses `zoom_fov_h: 58.6°` (actually the wide camera) as its coordinate space. This is why naive bbox mapping to the 13mm thermal JPEG (DFOV 42°) produces systematic compression.

## How We Found It

1. Captured raw MQTT OSD telemetry during flight (`data/autel_mqtt_20260612/osd_drone.jsonl`)
2. Compared reported FOV values against manufacturer datasheets
3. Cross-referenced with physical sensor measurements (13mm thermal lens = 42° DFOV)
4. Confirmed: `ir_*` fields describe the zoom lens, `zoom_*` fields describe the wide camera

## Firmware Version

- **Autel EVO MAX 4T V2 xe**
- Firmware: v1.9.1.219
- Controller: Smart Controller V3 (TH7825451059)
- Date verified: 2026-06-12
