"""Autel EVO MAX 4T V2 xe MQTT telemetry parser — analogous to DJI M2EA parse_srt() in lateral_distance.py.

Loads drone OSD from JSONL, provides per-frame telemetry lookup for video files
by interpolating timestamps. Designed to work alongside the DJI pipeline for comparison.
"""

import json
import bisect
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config import (
    AUTEL_VIDEOS,
    AUTEL_RGB,
    AUTEL_THERMAL,
    MQTT_THERMAL_CALIB,
    MQTT_RGB_FOV_SCALE,
)
from logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class TelemetryFrame:
    timestamp_utc: float
    latitude: float
    longitude: float
    height_agl: float  # meters above ground
    gimbal_pitch: float  # degrees (0=horizon, -90=nadir)
    gimbal_yaw: float
    gimbal_roll: float
    drone_yaw: float  # attitude_head
    drone_pitch: float
    drone_roll: float
    horizontal_speed: float
    vertical_speed: float
    # Camera intrinsics (from OSD)
    zoom_focal_length: float  # mm
    zoom_fov_h: float  # degrees
    zoom_fov_v: float
    ir_focal_length: float
    ir_fov_h: float
    ir_fov_v: float


def load_osd(osd_jsonl_path: str) -> list[TelemetryFrame]:
    """Load drone OSD JSONL into sorted TelemetryFrame list."""
    frames = []
    with open(osd_jsonl_path) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            d = r['data']
            gimbal = d.get('10052-0-0', {})
            cam = d.get('cameras', [{}])[0] if d.get('cameras') else {}
            frames.append(TelemetryFrame(
                timestamp_utc=r['arrival_ts'],
                latitude=d['latitude'],
                longitude=d['longitude'],
                height_agl=d['height'],
                gimbal_pitch=gimbal.get('gimbal_pitch', 0.0),
                gimbal_yaw=gimbal.get('gimbal_yaw', 0.0),
                gimbal_roll=gimbal.get('gimbal_roll', 0.0),
                drone_yaw=d.get('attitude_head', 0.0),
                drone_pitch=d.get('attitude_pitch', 0.0),
                drone_roll=d.get('attitude_roll', 0.0),
                horizontal_speed=d.get('horizontal_speed', 0.0),
                vertical_speed=d.get('vertical_speed', 0.0),
                zoom_focal_length=cam.get('zoom_focal_length', 9.1),
                zoom_fov_h=cam.get('zoom_fov_h', 48.1),
                zoom_fov_v=cam.get('zoom_fov_v', 38.4),
                ir_focal_length=cam.get('ir_focal_length', 4.49),
                ir_fov_h=cam.get('ir_fov_h', 58.6),
                ir_fov_v=cam.get('ir_fov_v', 45.5),
            ))
    frames.sort(key=lambda f: f.timestamp_utc)
    return frames


def get_telemetry_at(frames: list[TelemetryFrame], timestamp_utc: float) -> TelemetryFrame:
    """Get interpolated telemetry at a given UTC epoch timestamp (nearest-neighbor)."""
    timestamps = [f.timestamp_utc for f in frames]
    idx = bisect.bisect_left(timestamps, timestamp_utc)
    if idx == 0:
        return frames[0]
    if idx >= len(frames):
        return frames[-1]
    # Pick nearest
    if (timestamp_utc - timestamps[idx - 1]) < (timestamps[idx] - timestamp_utc):
        return frames[idx - 1]
    return frames[idx]


def video_frame_to_timestamp(video_start_utc: float, frame_number: int, fps: float) -> float:
    """Convert video frame number to UTC epoch."""
    return video_start_utc + frame_number / fps


def get_video_telemetry(frames: list[TelemetryFrame], video_start_utc: float,
                        fps: float, frame_number: int) -> TelemetryFrame:
    """Get telemetry for a specific video frame."""
    ts = video_frame_to_timestamp(video_start_utc, frame_number, fps)
    return get_telemetry_at(frames, ts)



def correct_mqtt_bbox(bbox: dict, target: str = 'thermal') -> tuple[float, float, float, float]:
    """Apply calibrated affine correction to MQTT detection bbox.

    The detection stream has different effective FOV/crop than saved images.
    Error is position-dependent (not simple translation).

    Calibration accuracy:
      - Nadir (pitch ~0°): <2.5px error (sub-pixel, validated)
      - Angled (pitch -33°): ~87px error (affine model breaks down)

    For angled views, the GPS position from MQTT is more reliable than
    pixel-level bbox alignment. Use bbox for visualization only.

    Args:
        bbox: dict with keys {x, y, w, h} — normalized coordinates from MQTT
        target: 'thermal' for IR JPEG (640x512), 'rgb' for RGB JPEG (4000x3000)

    Returns:
        (cx, cy, w, h) corrected normalized coordinates in target image space
    """
    bx, by, bw, bh = bbox['x'], bbox['y'], bbox['w'], bbox['h']

    if target == 'thermal':
        cal = MQTT_THERMAL_CALIB
        cx = cal['x_scale'] * bx + cal['x_offset']
        cy = by + cal['y_offset']
        cw = bw * cal['x_scale']  # width also scales
        return (cx, cy, cw, bh)
    elif target == 'rgb':
        # FOV scaling from center: detection stream is wider than RGB saved image
        sx = MQTT_RGB_FOV_SCALE['sx']
        sy = MQTT_RGB_FOV_SCALE['sy']
        return ((bx - 0.5) * sx + 0.5, (by - 0.5) * sy + 0.5, bw * sx, bh * sy)
    return (bx, by, bw, bh)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Autel MQTT telemetry lookup')
    parser.add_argument('--osd', default='data/autel_mqtt_20260612/osd_drone.jsonl')
    parser.add_argument('--video', help='Video filename (e.g. MAX_0042.MP4)')
    parser.add_argument('--frame', type=int, default=0, help='Frame number')
    args = parser.parse_args()

    frames = load_osd(args.osd)
    log.info("Loaded %d OSD samples, %.0f - %.0f",
             len(frames), frames[0].timestamp_utc, frames[-1].timestamp_utc)

    if args.video:
        vid = AUTEL_VIDEOS[args.video]
        telem = get_video_telemetry(frames, vid['start_utc'], vid['fps'], args.frame)
        log.info("Frame %d of %s:", args.frame, args.video)
        log.debug("  Position: (%.6f, %.6f)", telem.latitude, telem.longitude)
        log.info("  Height AGL: %.1fm", telem.height_agl)
        log.info("  Gimbal pitch: %.1f°  yaw: %.1f°", telem.gimbal_pitch, telem.gimbal_yaw)
        log.info("  Drone yaw: %.1f°", telem.drone_yaw)
        log.info("  Speed: h=%.1f  v=%.1f m/s", telem.horizontal_speed, telem.vertical_speed)
