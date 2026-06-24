# UC2: Parking Occupancy

Vehicle detection and counting from aerial nadir imagery across RGB and thermal sensors.

## Results

| Platform | Method | Altitude | Vehicles Detected | Validated |
|----------|--------|----------|-------------------|-----------| 
| **DJI M2EA** | VisDrone 1280 (native) | 70m | 55 cars + 5 peds + 2 trucks | ✅ |
| **Autel MAX 4T** | VisDrone 1280 (native) | 80m | 95 cars + 3 vans | ✅ |
| **Autel MAX 4T** | VisDrone 1280 (thermal) | 80m | 43 cars + 29 vans | ✅ |
| **Autel MAX 4T** | Onboard AI (134m nadir) | 134m | 104 vehicles (~59% occupancy) | ✅ |
| **DJI Avata 360** | Nadir perspective crop | 21-48m | 38-46 vehicles | ✅ |

## How It Works

1. **Fly over parking area** at nadir (camera pointing straight down)
2. **YOLO detection** identifies vehicles (car, van, truck, bus)
3. **Aspect ratio filtering** removes false positives (dumpsters, HVAC units: width/height > 1.4)
4. **ByteTrack** provides persistent IDs for moving vehicles
5. **Count** = unique vehicle detections in frame

## False Positive Filtering

From 134m nadir, YOLO may detect dumpsters, skylights, or HVAC equipment as vehicles. Post-processing with aspect ratio filtering (`width/height > 1.4 = non-vehicle`) eliminates these.

## Thermal vs RGB

| Condition | RGB | Thermal |
|-----------|-----|---------|
| Daytime | ✅ Best (color, texture) | ⚠️ Solar loading confuses |
| Night | ❌ No visibility | ✅ Engine heat visible |
| Recently parked | ✅ Normal detection | ✅ Warm engine stands out |
| Cold/long-parked | ✅ Normal detection | ⚠️ Blends with pavement |

## Usage

```bash
# Parking occupancy monitor (RGB + optional thermal)
python src/parking_monitor.py --video rgb.mp4 --thermal thermal.mp4 \
  --model models/visdrone_yolov8m_1280_best.pt

# Vehicle detection on single image
python src/detect.py --input parking_nadir.jpg \
  --model models/visdrone_yolov8s_1280_best.pt

# Vehicle tracking with persistent IDs
python src/vehicle_tracker.py --video traffic.mp4 \
  --model models/visdrone_yolov8s_1280_best.pt
```
