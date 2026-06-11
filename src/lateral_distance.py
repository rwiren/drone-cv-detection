"""
WO2025034145A1 — UAV Lateral Distance Safety Monitor

Calculates lateral distance from UAV to detected objects using:
- YOLO object detection (persons, vehicles)
- DJI SRT telemetry (focal length, gimbal pitch, altitude)
- Patent formula for monocular distance estimation

Checks compliance with the EU 1:1 rule (lateral distance >= altitude).
"""
import cv2
import numpy as np
import re
import argparse
from pathlib import Path
from ultralytics import YOLO


OBJECT_HEIGHTS = {
    'pedestrian': 1.70,
    'people': 1.70,
    'car': 1.50,
    'van': 2.00,
    'truck': 2.50,
    'bus': 3.20,
    'bicycle': 1.00,
    'motor': 1.10,
}


def parse_srt(srt_path):
    """Parse DJI SRT file into per-frame telemetry list."""
    with open(srt_path, 'r') as f:
        content = f.read()

    frames = []
    entries = re.split(r'\n\n+', content.strip())

    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) < 3:
            continue
        data_str = ' '.join(lines[2:])
        frame_data = {}

        m = re.search(r'FrameCnt:\s*(\d+)', data_str)
        if m: frame_data['frame'] = int(m.group(1))

        m = re.search(r'focal_len\s*:\s*(\d+)', data_str)
        if m: frame_data['focal_len'] = int(m.group(1)) / 10.0

        m = re.search(r'rel_alt:\s*([\d.]+)', data_str)
        if m: frame_data['altitude'] = float(m.group(1))

        m = re.search(r'latitude:\s*([\d.]+)', data_str)
        if m: frame_data['lat'] = float(m.group(1))

        m = re.search(r'longtitude:\s*([\d.]+)', data_str)
        if m: frame_data['lon'] = float(m.group(1))

        m = re.search(r'Pitch:([-\d.]+)', data_str)
        if m: frame_data['pitch'] = float(m.group(1))

        m = re.search(r'Yaw:([-\d.]+)', data_str)
        if m: frame_data['yaw'] = float(m.group(1))

        m = re.search(r'fnum\s*:\s*(\d+)', data_str)
        if m: frame_data['fnum'] = int(m.group(1)) / 100.0

        m = re.search(r'dzoom_ratio:\s*(\d+)', data_str)
        if m: frame_data['zoom'] = int(m.group(1)) / 10000.0

        if frame_data:
            frames.append(frame_data)

    return frames


def calculate_lateral_distance(bbox_center_x, bbox_center_y, image_width_px,
                                image_height_px, focal_len_mm, gimbal_pitch_deg,
                                altitude_m, sensor_width_mm=8.8, sensor_height_mm=6.17):
    """
    WO2025034145A1 lateral distance calculation.

    Two methods depending on viewing angle:
    - Near-nadir (|pitch| < 15°): GSD projection from image center offset
    - Angled view (|pitch| >= 15°): Ray-casting through pixel to ground plane

    The patent formula using bounding box height is only valid for angled views
    where the full height of the person is visible. From near-nadir, the GSD
    method is geometrically correct.

    Args:
        bbox_center_x, bbox_center_y: Center of detected bounding box (pixels)
        image_width_px, image_height_px: Frame dimensions
        focal_len_mm: Camera focal length (from SRT metadata)
        gimbal_pitch_deg: Camera pitch angle (negative = looking down)
        altitude_m: UAV altitude above ground (meters)
        sensor_width_mm, sensor_height_mm: Camera sensor dimensions
    Returns:
        (lateral_distance_m, method_str)
    """
    pitch_rad = np.radians(gimbal_pitch_deg)
    f_px_w = (focal_len_mm / sensor_width_mm) * image_width_px
    f_px_h = (focal_len_mm / sensor_height_mm) * image_height_px

    dx_px = bbox_center_x - image_width_px / 2
    dy_px = bbox_center_y - image_height_px / 2

    if abs(gimbal_pitch_deg) < 15:
        # Near-nadir: GSD-based ground distance from nadir point
        gsd_x = (sensor_width_mm * altitude_m) / (focal_len_mm * image_width_px)
        gsd_y = (sensor_height_mm * altitude_m) / (focal_len_mm * image_height_px)
        ground_dx = dx_px * gsd_x
        ground_dy = dy_px * gsd_y
        pitch_offset = altitude_m * np.tan(abs(pitch_rad))
        d_lateral = np.sqrt(ground_dx**2 + (ground_dy + pitch_offset)**2)
        return d_lateral, "GSD"
    else:
        # Angled view: ray-ground intersection
        angle_y = np.arctan(dy_px / f_px_h)
        angle_x = np.arctan(dx_px / f_px_w)
        look_angle = abs(pitch_rad) + angle_y
        if look_angle <= 0:
            return float('inf'), "RAY"
        d_forward = altitude_m / np.tan(look_angle)
        d_sideways = altitude_m * np.tan(angle_x) / np.sin(look_angle)
        d_lateral = np.sqrt(d_forward**2 + d_sideways**2)
        return d_lateral, "RAY"


def main():
    parser = argparse.ArgumentParser(description="WO2025034145A1 Lateral Distance Monitor")
    parser.add_argument("--video", required=True, help="RGB video path")
    parser.add_argument("--srt", required=True, help="DJI SRT telemetry file")
    parser.add_argument("--model", default="models/visdrone_yolov8s_best.pt")
    parser.add_argument("--frame", type=int, default=0, help="Frame to analyze")
    parser.add_argument("--safety-value", type=float, default=1.0, help="Multiplier for 1:1 rule")
    parser.add_argument("--sensor-height", type=float, default=6.17, help="Sensor height mm")
    parser.add_argument("--output", default="outputs/lateral_distance.jpg")
    args = parser.parse_args()

    telemetry = parse_srt(args.srt)
    print(f"Telemetry: {len(telemetry)} frames")

    model = YOLO(args.model)

    telem = telemetry[min(args.frame, len(telemetry) - 1)]
    altitude = telem['altitude']
    min_distance = args.safety_value * altitude

    cap = cv2.VideoCapture(args.video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, args.frame)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to read frame")
        return

    h_img, w_img = frame.shape[:2]
    results = model(frame, conf=0.2, verbose=False)[0]

    vis = frame.copy()
    violations = []

    for box in results.boxes:
        cls_name = results.names[int(box.cls[0])]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        if cls_name not in OBJECT_HEIGHTS:
            continue

        d_lateral, method = calculate_lateral_distance(
            bbox_center_x=(x1 + x2) / 2,
            bbox_center_y=(y1 + y2) / 2,
            image_width_px=w_img,
            image_height_px=h_img,
            focal_len_mm=telem['focal_len'],
            gimbal_pitch_deg=telem['pitch'],
            altitude_m=altitude,
        )

        is_violation = d_lateral <= min_distance
        color = (0, 0, 255) if is_violation else (0, 255, 0)
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis, f"{cls_name} {d_lateral:.1f}m [{method}]", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

        if is_violation and cls_name in ('pedestrian', 'people'):
            violations.append((cls_name, d_lateral, conf))

    # Dashboard
    cv2.rectangle(vis, (0, 0), (700, 110), (0, 0, 0), -1)
    cv2.putText(vis, "WO2025034145A1 - UAV LATERAL DISTANCE MONITOR", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(vis, f"Alt: {altitude:.0f}m | Pitch: {telem['pitch']}deg | Focal: {telem['focal_len']}mm",
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(vis, f"1:1 Rule: Min lateral distance = {min_distance:.0f}m",
                (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    if violations:
        cv2.putText(vis, f"WARNING: {len(violations)} person(s) in safety perimeter!",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        print(f"\n⚠️  {len(violations)} SAFETY VIOLATION(S)")
        for cls, d, c in violations:
            print(f"  {cls}: {d:.1f}m (min: {min_distance:.1f}m)")
    else:
        cv2.putText(vis, f"STATUS: SAFE - All persons beyond {min_distance:.0f}m",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        print(f"\n✓ SAFE — all persons beyond {min_distance:.0f}m")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(args.output, vis)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
