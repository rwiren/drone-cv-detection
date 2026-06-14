# Person Detection & 1:1 Safety Rule

**Patent:** [WO2025034145A1](https://patents.google.com/patent/WO2025034145A1/en) — "Calculating Lateral Distance from Uncrewed Autonomous Vehicle to Object"

## The EU 1:1 Rule

Under [EU 2019/947](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32019R0947) (EASA Open Category), a drone must maintain a lateral distance from uninvolved persons that is at least equal to its altitude:

```
lateral_distance >= safety_value × altitude
```

Where `safety_value ≥ 1.0`.

## System Architecture

The system detects persons, calculates lateral distance, and issues alerts:

1. **Detect** — YOLO person detection (class 0: pedestrian)
2. **Calculate** — lateral distance from drone position + camera geometry
3. **Compare** — `d_lateral < safety_value × altitude`?
4. **Alert** — publish violation via MQTT or log

## Implementation Per Platform

| Capability | DJI M2EA | Autel MAX 4T | DJI Avata 360 |
|---|---|---|---|
| Detection model | VisDrone v8m 1280 | Onboard AI + VisDrone | v8m + COCO ensemble |
| Distance method | GSD + SRT telemetry | LRF (ground truth) | GSD from perspective crop |
| Alert mechanism | Post-flight analysis | Real-time MQTT | Post-flight analysis |
| Person conf | 0.49 at 70m | Onboard AI | 0.60 at 8m, 0.89 at 2m |

## Dual-Model Ensemble

No single model covers all altitudes:

- **Altitude > 3m** → VisDrone v8m at imgsz=1280 (trained on aerial imagery)
- **Altitude < 3m** → COCO yolov8s (trained on normal-perspective imagery)
- The ensemble takes the best detection per view

## Usage

```bash
# DJI M2EA — lateral distance calculation
python src/lateral_distance.py --video DJI_0398_W.MP4 --srt DJI_0398_W.SRT --frame 1792

# Autel — real-time 1:1 rule monitor (replay)
python src/rule_monitor.py --detections data/autel_mqtt_20260612/detections.jsonl \
  --osd data/autel_mqtt_20260612/osd_drone.jsonl --summary

# Autel — live MQTT monitoring
python src/rule_monitor.py --live --broker localhost --port 1883

# DJI Avata 360 — 360° person detection
python src/avata360_monitor.py --video DJI_...LRF --srt DJI_...SRT \
  --model yolov8s.pt --aerial-model models/visdrone_yolov8m_1280_best.pt
```
