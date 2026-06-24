# Data Schemas

This page documents the JSONL/JSON schemas used by the drone-cv-detection pipeline.
All files are UTF-8 encoded, one JSON object per line unless otherwise noted.

---

## OSD Drone Telemetry — `osd_drone.jsonl`

Produced by the Autel MQTT bridge. One record per drone heartbeat (~1 Hz).

```json
{
  "arrival_ts": 1781262523.456,
  "topic": "thing/product/ABC123/osd",
  "data": {
    "latitude":   60.123456,
    "longitude":  24.567890,
    "height":     80.5,
    "abs_alt":    130.5,
    "speed_x":    0.1,
    "speed_y":    0.0,
    "speed_z":   -0.1,
    "pitch":     -90.0,
    "roll":        0.0,
    "yaw":        45.0,
    "home_lat":   60.100000,
    "home_lon":   24.500000,
    "battery_pct": 72
  }
}
```

| Field | Type | Unit | Notes |
|---|---|---|---|
| `arrival_ts` | float | Unix seconds | Wall-clock receive time on capture machine |
| `data.latitude` | float | decimal degrees WGS-84 | |
| `data.longitude` | float | decimal degrees WGS-84 | |
| `data.height` | float | metres | Relative altitude above home point |
| `data.abs_alt` | float | metres | AMSL altitude |
| `data.speed_*` | float | m/s | Body-frame velocities |
| `data.pitch/roll/yaw` | float | degrees | Gimbal/drone attitude |

---

## Detections — `detections.jsonl`

Produced by the Autel MQTT bridge when `method == target_detect_result_report`. One record per detection event (~2 Hz during flight).

```json
{
  "arrival_ts": 1781262525.123,
  "topic": "thing/product/ABC123/state",
  "method": "target_detect_result_report",
  "data": {
    "objs": [
      {
        "cls_id":  30,
        "cls_name": "person",
        "conf":    0.87,
        "bbox_norm": [0.41, 0.55, 0.07, 0.12],
        "pos": {
          "latitude":  60.123490,
          "longitude": 24.567910
        }
      }
    ]
  }
}
```

| Field | Type | Notes |
|---|---|---|
| `data.objs[].cls_id` | int | COCO class index (30 = person) |
| `data.objs[].conf` | float | Detection confidence [0, 1] |
| `data.objs[].bbox_norm` | float[4] | `[cx, cy, w, h]` normalised to [0, 1] in MQTT stream space |
| `data.objs[].pos.latitude/longitude` | float | Firmware-projected GPS position of detection |

> **Note:** `bbox_norm` coordinates are in the firmware's internal 1280×960 IR stream space (FOV 58.6°×45.5°), not the saved thermal JPEG space. Apply `correct_mqtt_bbox()` from `src/autel_telemetry.py` before overlaying on saved frames.

---

## 1:1 Rule Timeline — `1to1_rule_timeline.csv`

Produced by `src/rule_monitor.py` in replay mode. One row per person detection event.

| Column | Type | Notes |
|---|---|---|
| `timestamp_utc` | ISO-8601 | Wall-clock UTC time |
| `altitude_m` | float | Drone relative altitude |
| `lateral_distance_m` | float | Haversine distance drone↔person |
| `ratio` | float | `lateral_distance_m / altitude_m` |
| `violation` | bool | `True` if ratio < safety_value |
| `person_lat/lon` | float | Person GPS position |
| `drone_lat/lon` | float | Drone GPS position at detection time |
| `num_persons` | int | Total persons detected in frame |

---

## Evaluation Results — `eval_results.json`

Produced by `scripts/eval_*.py`. One JSON file per evaluation run.

```json
{
  "run_id":       "autel_20260612_v1",
  "model":        "models/autel_yolov8s_best.pt",
  "video":        "data/MAX_0016.MP4",
  "srt":          "data/MAX_0016.SRT",
  "date_utc":     "2026-06-12T14:23:01Z",
  "frames_processed": 892,
  "interval_s":   1.0,
  "detections": {
    "total":      1243,
    "persons":    847,
    "vehicles":   396
  },
  "rule_1to1": {
    "safety_value":  1.0,
    "measurements":  412,
    "violations":    38,
    "violation_pct": 9.2,
    "min_ratio":     0.31,
    "min_lateral_m": 15.6
  },
  "performance": {
    "avg_fps":    4.2,
    "total_s":    212.4
  }
}
```

---

## Avata 360 SRT Telemetry — `*.SRT`

One block per video frame (60 fps). Parsed by `parse_avata_srt()` in `src/avata360_monitor.py`.

```
1
00:00:00,016 --> 00:00:00,033
<font size="28">FrameCnt: 1, DiffTime: 16ms
2026-06-12 15:01:00.016
[iso: 400] [shutter: 1/2000] [fnum: 2.8] [ev: 0] [ct: 5500] [color_md: default] [focal_len: 0]
[latitude: 60.123456] [longitude: 24.567890]
[rel_alt: 50.000 abs_alt: 130.000]
[gb_yaw: 45.0 gb_pitch: -70.0 gb_roll: 0.0]</font>
```

Extracted fields: `frame_cnt`, `latitude`, `longitude`, `rel_alt`, `abs_alt`, `gb_yaw`, `gb_pitch`, `gb_roll`.

---

## M2EA SRT Telemetry — `*.SRT`

One block per video frame (~30 fps). Parsed by `parse_srt()` in `src/lateral_distance.py`.

```
1
00:00:00,033 --> 00:00:00,066
<font size="28">FrameCnt: 1, DiffTime: 33ms
2026-06-12 14:23:01.033
[fov_h:48.10,fov_v:38.40,focal_len:9.10]
[latitude: 60.123456] [longitude: 24.567890]
[altitude: 80.5] [abs_alt: 130.5]
[gb_yaw: 45.0,gb_pitch: -90.0,gb_roll: 0.0]
[home_latitude: 60.100000] [home_longitude: 24.500000]</font>
```

Extracted fields: `frame_cnt`, `latitude`, `longitude`, `altitude`, `abs_alt`, `gb_yaw`, `gb_pitch`, `gb_roll`, `fov_h`, `fov_v`, `home_latitude`, `home_longitude`.
