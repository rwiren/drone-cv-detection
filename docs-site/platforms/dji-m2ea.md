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
- Parking: 64 cars at 70m (conf>0.35, no false positives)
- 1:1 rule: 89 measurements, all violations correctly flagged

![M2EA aerial detection](../images/detection_aerial.jpg)

*DJI M2EA at 70m — 64 cars detected with VisDrone v8s 1280 model (conf>0.35).*

