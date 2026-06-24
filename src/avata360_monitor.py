"""DJI Avata 360 — omnidirectional person detection for 1:1 rule.

Extracts perspective views from dual-fisheye 360° video using equidistant
fisheye projection (r = f × θ). Runs YOLO person detection on each view
and calculates lateral distance using SRT telemetry.

The DJI Avata 360 records dual-fisheye format: two circular fisheye images
side by side (right lens = nadir/ground, left lens = zenith/sky).
  - .LRF (low-res proxy): 1920×960 (two 960×960 fisheye circles)
  - .OSV/.MP4 (full res): dual-fisheye at higher resolution

Patent WO2025034145A1 relevance:
  - "select the shortest lateral distance if two or more objects are detected"
  - 360° eliminates gimbal pointing requirement
  - Simultaneous multi-direction monitoring
"""
from __future__ import annotations

import cv2
import numpy as np
import re
import math
import argparse
from pathlib import Path
from typing import Any
from ultralytics import YOLO

from logging_utils import get_logger

log = get_logger(__name__)


def extract_perspective(
    dual_fisheye: np.ndarray,
    fov_deg: float = 90,
    yaw_deg: float = 0,
    pitch_deg: float = 0,
    out_size: tuple[int, int] = (640, 480),
    fisheye_fov: float = 200,
    lens: str = 'right',
) -> np.ndarray:
    """Extract rectilinear perspective view from DJI Avata 360 dual-fisheye frame.

    The LRF/OSV files contain dual fisheye (two 960×960 circles side by side).
    Right lens = nadir/down, Left lens = zenith/up.

    Args:
        dual_fisheye: Full dual-fisheye frame (H×W×3, e.g. 960×1920)
        fov_deg: Output perspective field of view
        yaw_deg: Azimuth rotation (0-360, 0=top of fisheye circle)
        pitch_deg: Angle from nadir (0=straight down, 90=horizon)
        out_size: Output (width, height)
        fisheye_fov: Total FOV of fisheye lens in degrees
        lens: 'right' (nadir) or 'left' (zenith)
    """
    h, w = dual_fisheye.shape[:2]
    if lens == 'right':
        fisheye = dual_fisheye[:, w//2:]
    else:
        fisheye = dual_fisheye[:, :w//2]

    radius = min(fisheye.shape[:2]) / 2
    cx, cy = fisheye.shape[1] / 2, fisheye.shape[0] / 2
    f_fish = radius / np.radians(fisheye_fov / 2)

    out_w, out_h = out_size
    f_persp = out_w / (2 * np.tan(np.radians(fov_deg / 2)))

    # Output pixel grid -> 3D rays (z = optical axis = nadir)
    u = np.arange(out_w, dtype=np.float64) - out_w / 2
    v = np.arange(out_h, dtype=np.float64) - out_h / 2
    u, v = np.meshgrid(u, v)

    x, y, z = u, v, np.full_like(u, f_persp)
    norm = np.sqrt(x**2 + y**2 + z**2)
    x, y, z = x/norm, y/norm, z/norm

    # Pitch rotation (tilt away from nadir toward horizon)
    p = np.radians(pitch_deg)
    y2 = y * np.cos(p) - z * np.sin(p)
    z2 = y * np.sin(p) + z * np.cos(p)
    y, z = y2, z2

    # Yaw rotation (rotate around nadir axis)
    ya = np.radians(yaw_deg)
    x2 = x * np.cos(ya) - y * np.sin(ya)
    y2 = x * np.sin(ya) + y * np.cos(ya)
    x, y = x2, y2

    # Fisheye equidistant projection: r = f_fish * theta
    theta = np.arccos(np.clip(z, -1, 1))
    phi = np.arctan2(y, x)
    r = f_fish * theta

    src_x = (cx + r * np.cos(phi)).astype(np.float32)
    src_y = (cy + r * np.sin(phi)).astype(np.float32)

    return cv2.remap(fisheye, src_x, src_y, cv2.INTER_LINEAR)


def parse_avata_srt(srt_path: str | Path) -> list[dict[str, Any]]:
    """Parse DJI Avata 360 SRT file into per-frame telemetry."""
    with open(srt_path) as f:
        content = f.read()

    frames = []
    for match in re.finditer(
        r'FrameCnt: (\d+).*?'
        r'latitude: ([\d.]+).*?longitude: ([\d.]+).*?'
        r'rel_alt: ([\d.]+).*?'
        r'gb_yaw: ([-\d.]+).*?gb_pitch: ([-\d.]+)',
        content, re.DOTALL
    ):
        frames.append({
            'frame': int(match.group(1)),
            'lat': float(match.group(2)),
            'lon': float(match.group(3)),
            'altitude': float(match.group(4)),
            'yaw': float(match.group(5)),
            'pitch': float(match.group(6)),
        })
    return frames


def process_frame_360(
    frame: np.ndarray,
    model: Any,
    yaw_offset: float = 0,
    pitch: float = 50,
    n_views: int = 8,
    fov: float = 90,
) -> list[tuple[float, Any]]:
    """Run person detection on perspective views extracted from dual-fisheye frame.

    Args:
        frame: Dual-fisheye frame (right lens = nadir)
        model: YOLO model or list of (model, imgsz) tuples for ensemble
        pitch: Angle from nadir in degrees (0=down, 50=angled toward horizon)

    Returns list of (azimuth_deg, detections) tuples.
    """
    # Support single model or ensemble
    if isinstance(model, list):
        models = model
    else:
        models = [(model, 640)]

    results = []
    for i in range(n_views):
        yaw = (i * 360 / n_views + yaw_offset) % 360
        view = extract_perspective(frame, fov_deg=fov, yaw_deg=yaw, pitch_deg=pitch)
        best_dets = None
        best_conf = 0
        for m, imgsz in models:
            dets = m(view, conf=0.3, classes=[0], imgsz=imgsz, verbose=False)[0]
            if len(dets.boxes) > 0:
                conf = max(float(b.conf) for b in dets.boxes)
                if conf > best_conf:
                    best_conf = conf
                    best_dets = dets
        if best_dets is not None:
            results.append((yaw, best_dets))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Avata 360 Person Monitor')
    parser.add_argument('--video', required=True, help='Path to .LRF or .OSV/.MP4')
    parser.add_argument('--srt', required=True, help='Path to .SRT telemetry file')
    parser.add_argument('--model', default='yolov8s.pt', help='YOLO model path (person detection)')
    parser.add_argument('--aerial-model', default=None, help='Aerial model for high-alt (e.g. visdrone 1280)')
    parser.add_argument('--start', type=float, default=0, help='Start time in seconds')
    parser.add_argument('--interval', type=float, default=2, help='Seconds between checks')
    args = parser.parse_args()

    # Build model ensemble: COCO (close-range) + VisDrone 1280 (aerial)
    models = [(YOLO(args.model), 640)]
    if args.aerial_model:
        models.append((YOLO(args.aerial_model), 1280))

    telemetry = parse_avata_srt(args.srt)
    log.info("Loaded %d SRT frames", len(telemetry))
    log.info("Models: %d (%s)", len(models),
             ", ".join(str(m[0].ckpt_path) for m in models))

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps
    log.info("Video: %d frames, %.0f fps, %.1f s", total, fps, duration)

    print(f'\n{"Time":>6} | {"Alt":>5} | {"Dir":>5} | {"Conf":>5} | 1:1 Rule')
    print('-' * 45)

    t = args.start
    while t < duration:
        frame_num = int(t * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            break

        # Get telemetry (nearest SRT frame at ~60fps, video may be 30fps)
        srt_idx = min(int(t * 60), len(telemetry) - 1)  # SRT at 60fps
        telem = telemetry[srt_idx] if srt_idx < len(telemetry) else telemetry[-1]

        # Detect persons in all directions
        detections = process_frame_360(frame, models, yaw_offset=telem['yaw'])

        if detections:
            for azimuth, dets in detections:
                conf = max(float(b.conf) for b in dets.boxes)
                # At low altitude, rough lateral estimate from azimuth
                # (precise would require depth estimation or GSD)
                status = '⚠️ CLOSE' if telem['altitude'] < 5 else '—'
                print(f'{t:>5.1f}s | {telem["altitude"]:>4.1f}m | {azimuth:>4.0f}° | {conf:>.2f} | {status}')

        t += args.interval

    cap.release()
