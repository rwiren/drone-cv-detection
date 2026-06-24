"""Shared constants and default configuration for drone-cv-detection.

This module centralises all hardware specs, calibration values, and
default runtime parameters so they are maintained in one place and
can be imported by any pipeline script.

Import examples::

    from config import OBJECT_HEIGHTS, AUTEL_RGB, MQTT_THERMAL_CALIB
    from config import MODELS, CONF_AERIAL
"""
from pathlib import Path

# ─── Repository root ─────────────────────────────────────────────────────────
REPO_ROOT: Path = Path(__file__).resolve().parent.parent


# ─── VisDrone2019 class names ────────────────────────────────────────────────
VISDRONE_CLASSES: dict[int, str] = {
    0: "pedestrian",
    1: "people",
    2: "bicycle",
    3: "car",
    4: "van",
    5: "truck",
    6: "tricycle",
    7: "awning-tricycle",
    8: "bus",
    9: "motor",
}

# ─── COCO vehicle class ids (for YOLOv8 COCO pretrained weights) ─────────────
COCO_VEHICLE_CLASSES: dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# ─── Known real-world heights used for monocular distance estimation ─────────
# Authoritative source for lateral_distance.py (patent WO2025034145A1, Eq. 10).
OBJECT_HEIGHTS: dict[str, float] = {
    "pedestrian": 1.70,
    "people": 1.70,
    "car": 1.50,
    "van": 2.00,
    "truck": 2.50,
    "bus": 3.20,
    "bicycle": 1.00,
    "motor": 1.10,
}

# ─── Default confidence thresholds ───────────────────────────────────────────
CONF_DEFAULT: float = 0.25
CONF_PERSON: float = 0.20       # lower threshold captures marginal person detections
CONF_VEHICLE: float = 0.25
CONF_AERIAL: float = 0.20       # aerial models benefit from lower thresholds

# ─── Default model paths (relative to REPO_ROOT) ─────────────────────────────
MODELS: dict[str, str] = {
    # VisDrone fine-tuned — best for aerial nadir imagery
    "visdrone_v8m_1280": "models/visdrone_yolov8m_1280_best.pt",   # 58.1% mAP50, best person
    "visdrone_v8s_1280": "models/visdrone_yolov8s_1280_best.pt",   # 53.2% mAP50, fastest
    "visdrone_autel_v8s": "models/visdrone_autel_yolov8s_best.pt", # combined 15ep CPU
    "visdrone_v8s": "models/visdrone_yolov8s_best.pt",             # VisDrone-only 5ep fallback
    # Domain-adapted (VisDrone + Avata 360 pseudo-labels)
    "combined_v8m_1280": "models/combined_v8m_1280_best.pt",
    # COCO pretrained — best for close-range (<3 m) person detection
    "coco_v8s": "yolov8s.pt",
    "coco_v8n": "yolov8n.pt",
    # Cross-view geolocalisation (GNSS-denied navigation)
    "crossview": "models/crossview_effb2_512d_v2.pth",
}

# ─── DJI Mavic 2 Enterprise Advanced (M2EA) specs ────────────────────────────
M2EA_RGB: dict[str, float | int] = {
    "sensor_width_mm": 8.8,
    "sensor_height_mm": 6.17,
    "focal_length_mm": 24.0,     # 24 mm equivalent (actual physical ~9 mm)
    "fov_h_deg": 84.0,
    "image_width_px": 1920,
    "image_height_px": 1080,
}

M2EA_THERMAL: dict[str, float | int] = {
    "sensor_width_mm": 7.68,     # 640 px × 12 μm pixel pitch
    "sensor_height_mm": 6.14,    # 512 px × 12 μm pixel pitch
    "focal_length_mm": 9.0,
    "dfov_deg": 57.0,
    "image_width_px": 640,
    "image_height_px": 512,
    "pixel_pitch_um": 12,
}

# ─── Autel EVO MAX 4T V2 xe specs ────────────────────────────────────────────
AUTEL_RGB: dict[str, float | int] = {
    "sensor_width_mm": 7.68,     # 1/1.28″ IMX586 (same pixel pitch as thermal)
    "sensor_height_mm": 5.76,
    "focal_length_mm": 9.1,      # wide lens at 1× zoom
    "fov_h_deg": 48.1,
    "fov_v_deg": 38.4,
    "image_width_px": 4000,      # typical 4 K video crop; max photo: 8192 × 6144
    "image_height_px": 3000,
}

AUTEL_THERMAL: dict[str, float | int | str] = {
    "sensor_width_mm": 7.68,     # 640 px × 12 μm pixel pitch
    "sensor_height_mm": 6.14,    # 512 px × 12 μm pixel pitch
    "focal_length_mm": 13.0,     # 13 mm f/1.2 lens
    "dfov_deg": 42.0,
    "fov_h_deg": 33.4,           # derived from 13 mm + 7.68 mm sensor
    "fov_v_deg": 26.8,
    "image_width_px": 640,
    "image_height_px": 512,
    "pixel_pitch_um": 12,
    # NOTE: Autel MQTT OSD reports `ir_fov_h = 58.6°` — this is actually the
    # WIDE-camera FOV (firmware label swap, firmware v1.9.1.219).
    # The actual thermal lens FOV is 33.4° H.  See README calibration section
    # and docs/Autel EVO MAX 4T V2 AI Verification.md for full analysis.
    "mqtt_reported_fov_h_deg": 58.6,
    "mqtt_reported_fov_v_deg": 45.5,
}

# ─── Autel MQTT detection-stream calibration ─────────────────────────────────
# The onboard AI detection stream uses the wide-camera coordinate space
# (FOV 58.6° × 45.5°), regardless of which physical sensor made the detection.
#
# Applying the affine below maps normalised MQTT bbox coords to saved-JPEG space:
#   Thermal JPEG (640 × 512):  x' = 0.8384·x + 0.0915,   y' = y + 0.049
#   RGB JPEG    (4000 × 3000): x' = 0.5 + (x−0.5)·1.22,  y' = 0.5 + (y−0.5)·1.18
#
# Accuracy: < 2.5 px at nadir (0° gimbal pitch) — sub-pixel, validated.
#           ~ 87 px at −33° — affine model breaks down; use GPS for distance calc.
#
# Empirically calibrated, firmware v1.9.1.219, flight session 2026-06-12.
MQTT_THERMAL_CALIB: dict[str, float] = {
    "x_scale": 0.8384,    # detection stream x-space compressed vs thermal JPEG
    "x_offset": 0.0915,   # translation component (sensor parallax + crop offset)
    "y_offset": 0.049,    # upward-bias correction (shift boxes down)
}

MQTT_RGB_FOV_SCALE: dict[str, float] = {
    "sx": 58.6 / 48.1,    # detection stream is wider than RGB saved image (H)
    "sy": 45.5 / 38.4,    # … and taller (V)
}

# ─── Autel video catalogue — flight session 2026-06-12, Jorvas ───────────────
# start_utc: UTC epoch of the first video frame (derived from EXIF CreateDate).
AUTEL_VIDEOS: dict[str, dict] = {
    "MAX_0016.MP4": {"start_utc": 1781262523.0, "fps": 29.897, "res": (4000, 3000), "sensor": "rgb"},
    "MAX_0041.MP4": {"start_utc": 1781262589.0, "fps": 29.826, "res": (4000, 3000), "sensor": "rgb"},
    "MAX_0042.MP4": {"start_utc": 1781263400.0, "fps": 29.826, "res": (4000, 3000), "sensor": "rgb"},
    "MAX_0009.MP4": {"start_utc": 1781262001.0, "fps": 29.826, "res": (4000, 3000), "sensor": "rgb"},
    "IRX_0016.MP4": {"start_utc": 1781262523.0, "fps": 24.683, "res": (640, 512), "sensor": "thermal"},
    "IRX_0041.MP4": {"start_utc": 1781262589.0, "fps": 24.683, "res": (640, 512), "sensor": "thermal"},
    "IRX_0042.MP4": {"start_utc": 1781263400.0, "fps": 24.683, "res": (640, 512), "sensor": "thermal"},
    "IRX_0009.MP4": {"start_utc": 1781262000.0, "fps": 24.683, "res": (640, 512), "sensor": "thermal"},
}

# ─── DJI Avata 360 specs ─────────────────────────────────────────────────────
AVATA360: dict[str, int | float] = {
    "fisheye_fov_deg": 200,     # total FOV of each fisheye lens (equidistant)
    "lrf_width_px": 1920,       # LRF proxy file: two 960 × 960 fisheye circles
    "lrf_height_px": 960,
    "srt_fps": 60,              # SRT telemetry frame rate
}
