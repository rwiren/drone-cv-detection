# DJI Mavic 2 Enterprise Advanced

## Specs
- Visual: 1/2" 48MP, 24mm eq. f/2.8, FOV 84°
- Thermal: 640×512 @30Hz, 9mm (38mm eq.), DFOV ~57°
- Gimbal: 3-axis, tilt -90°→+30°
- Telemetry: SRT sidecar per frame

## Pipeline
- `src/lateral_distance.py` — Patent Eq.10 lateral distance
- `src/parking_monitor.py` — RGB + thermal parking
- `src/vehicle_tracker.py` — ByteTrack tracking

## Results
- Person detection: 0.49 conf at 70m (VisDrone v8s 1280)
- Parking: 55 cars + 5 peds at 70m
- 1:1 rule: 89 measurements, all violations correctly flagged

