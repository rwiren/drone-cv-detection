# Model Comparison

## Per-Platform Test Results

### DJI M2EA (70m, parking lot)

| Model | Vehicles | Persons | Total |
|-------|----------|---------|-------|
| VisDrone v8s 1280 | 57 | 5 | 62 |
| VisDrone v8m 1280 | 55 | 0 | 55 |

**Winner for parking:** v8s (detects more, including persons)

### Autel MAX 4T (4K, ~80m)

| Model | Vehicles | Persons | Total |
|-------|----------|---------|-------|
| VisDrone v8s 1280 | 98 | 2 | 100 |
| VisDrone v8m 1280 | 99 | 0 | 100 |

**Winner for parking:** v8s (also detects persons)

### DJI Avata 360 (Descent, person detection)

| Altitude | v8s 1280 | v8m 1280 | COCO | Best Strategy |
|----------|----------|----------|------|---------------|
| 8.4m | 0.45 | **0.60** | 0.36 | v8m |
| 5.7m | 0.44 | **0.56** | 0.21 | v8m |
| 4.4m | **0.56** | 0.46 | 0.33 | v8s |
| 2.9m | **0.47** | 0.41 | miss | v8s or v8m |
| 2.2m | miss | 0.50 | **0.89** | COCO |

**Winner for aerial person detection (>5m):** v8m
**Winner for close-range person (<3m):** COCO

## Recommendation

| Use Case | Model | Why |
|----------|-------|-----|
| Parking occupancy | VisDrone v8s 1280 | Higher recall, detects persons too |
| Person at altitude (>5m) | VisDrone v8m 1280 | +33% conf at 8m vs v8s |
| Person close-range (<3m) | COCO yolov8s | Trained on normal perspective |
| Combined 360° pipeline | v8m + COCO ensemble | Altitude-adaptive |
