"""Autel EVO MAX 4T V2 xe MQTT telemetry parser — analogous to DJI M2EA parse_srt() in lateral_distance.py.

Loads drone OSD from JSONL, provides per-frame telemetry lookup for video files
by interpolating timestamps. Designed to work alongside the DJI pipeline for comparison.
"""

import json
import bisect
from dataclasses import dataclass
from datetime import datetime, timezone


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


# Video metadata (from exiftool)
AUTEL_VIDEOS = {
    'MAX_0016.MP4': {'start_utc': 1781262523.0, 'fps': 29.897, 'res': (4000, 3000), 'sensor': 'rgb'},
    'MAX_0041.MP4': {'start_utc': 1781262589.0, 'fps': 29.826, 'res': (4000, 3000), 'sensor': 'rgb'},
    'MAX_0042.MP4': {'start_utc': 1781263400.0, 'fps': 29.826, 'res': (4000, 3000), 'sensor': 'rgb'},
    'MAX_0009.MP4': {'start_utc': 1781262001.0, 'fps': 29.826, 'res': (4000, 3000), 'sensor': 'rgb'},
    'IRX_0016.MP4': {'start_utc': 1781262523.0, 'fps': 24.683, 'res': (640, 512), 'sensor': 'thermal'},
    'IRX_0041.MP4': {'start_utc': 1781262589.0, 'fps': 24.683, 'res': (640, 512), 'sensor': 'thermal'},
    'IRX_0042.MP4': {'start_utc': 1781263400.0, 'fps': 24.683, 'res': (640, 512), 'sensor': 'thermal'},
    'IRX_0009.MP4': {'start_utc': 1781262000.0, 'fps': 24.683, 'res': (640, 512), 'sensor': 'thermal'},
}

# Camera specs (from EXIF + OSD)
AUTEL_RGB = {
    'sensor_width_mm': 7.68,  # IMX586: 1/2" sensor
    'sensor_height_mm': 5.76,
    'focal_length_mm': 9.1,  # zoom lens at 1x
    'fov_h': 48.1,
    'fov_v': 38.4,
    'image_width': 4000,
    'image_height': 3000,
}

AUTEL_THERMAL = {
    'sensor_width_mm': 7.68,
    'sensor_height_mm': 6.14,
    'focal_length_mm': 4.49,
    'fov_h': 58.6,
    'fov_v': 45.5,
    'image_width': 640,
    'image_height': 512,
}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Autel MQTT telemetry lookup')
    parser.add_argument('--osd', default='data/autel_mqtt_20260612/osd_drone.jsonl')
    parser.add_argument('--video', help='Video filename (e.g. MAX_0042.MP4)')
    parser.add_argument('--frame', type=int, default=0, help='Frame number')
    args = parser.parse_args()

    frames = load_osd(args.osd)
    print(f"Loaded {len(frames)} OSD samples, {frames[0].timestamp_utc:.0f} - {frames[-1].timestamp_utc:.0f}")

    if args.video:
        vid = AUTEL_VIDEOS[args.video]
        telem = get_video_telemetry(frames, vid['start_utc'], vid['fps'], args.frame)
        print(f"\nFrame {args.frame} of {args.video}:")
        print(f"  Position: ({telem.latitude:.6f}, {telem.longitude:.6f})")
        print(f"  Height AGL: {telem.height_agl:.1f}m")
        print(f"  Gimbal pitch: {telem.gimbal_pitch:.1f}°")
        print(f"  Gimbal yaw: {telem.gimbal_yaw:.1f}°")
        print(f"  Drone yaw: {telem.drone_yaw:.1f}°")
        print(f"  Speed: h={telem.horizontal_speed:.1f} v={telem.vertical_speed:.1f} m/s")
