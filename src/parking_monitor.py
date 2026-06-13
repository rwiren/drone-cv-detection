"""
Parking Occupancy Monitor — Two-Stream RGB+Thermal Fusion
Detects occupied/free parking slots from drone aerial video.
"""
import cv2
import numpy as np
import json
import argparse
from pathlib import Path
from ultralytics import YOLO


def load_model(weights_path):
    return YOLO(weights_path)


def detect_vehicles(model, frame, conf=0.25):
    """Run YOLO and return confirmed vehicle bounding boxes."""
    results = model(frame, conf=conf, verbose=False)[0]
    vehicles = []
    for box in results.boxes:
        cls_name = results.names[int(box.cls[0])]
        if cls_name in ("car", "van", "truck", "bus"):
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            vehicles.append({
                "bbox": (x1, y1, x2, y2),
                "conf": float(box.conf[0]),
                "cls": cls_name
            })
    return vehicles


def thermal_confirm(detections, thermal_gray, boost_threshold=0.2):
    """Confirm marginal YOLO detections using thermal contrast."""
    confirmed = []
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        conf = det["conf"]
        roi = thermal_gray[y1:y2, x1:x2]
        if roi.size == 0:
            if conf >= 0.35:
                confirmed.append(det)
            continue

        car_temp = np.mean(roi)
        bg_temp = np.mean(thermal_gray)
        contrast = abs(car_temp - bg_temp)

        edges = cv2.Canny(roi, 30, 100)
        edge_density = np.sum(edges > 0) / edges.size

        if conf >= 0.35:
            confirmed.append(det)
        elif conf >= boost_threshold and (contrast > 5 or edge_density > 0.05):
            det["boosted"] = True
            confirmed.append(det)

    return confirmed


def get_oriented_boxes(detections, thermal_gray):
    """Extract oriented bounding boxes using thermal edge information."""
    rects = []
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        roi = thermal_gray[y1:y2, x1:x2]

        if roi.size == 0 or roi.shape[0] < 10 or roi.shape[1] < 10:
            cx, cy = (x1+x2)//2, (y1+y2)//2
            rects.append({"center": (cx, cy), "size": (x2-x1, y2-y1), "angle": 0})
            continue

        roi_t = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 15, -3)
        cnts, _ = cv2.findContours(roi_t, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if cnts:
            largest = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(largest) > 100:
                offset = largest + np.array([x1, y1])
                rect = cv2.minAreaRect(offset)
                c, (rw, rh), a = rect
                if rw < rh:
                    rw, rh = rh, rw
                    a += 90
                rects.append({"center": (c[0], c[1]), "size": (rw, rh), "angle": a % 180})
                continue

        cx, cy = (x1+x2)//2, (y1+y2)//2
        rects.append({"center": (cx, cy), "size": (x2-x1, y2-y1), "angle": 0})

    return rects


def find_empty_slots(car_rects, thermal_gray, frame_shape):
    """Find empty parking slots in gaps between cars within rows."""
    if len(car_rects) < 3:
        return []

    centers = np.array([r["center"] for r in car_rects])
    angles = [r["angle"] for r in car_rects if r["angle"] != 0]
    parking_angle = np.median(angles) if angles else 90
    median_w = np.median([r["size"][0] for r in car_rects])
    median_h = np.median([r["size"][1] for r in car_rects])

    # Project onto perpendicular axis for row clustering
    perp_rad = np.radians(parking_angle + 90)
    park_rad = np.radians(parking_angle)
    perp_proj = centers[:, 0] * np.cos(perp_rad) + centers[:, 1] * np.sin(perp_rad)
    park_proj = centers[:, 0] * np.cos(park_rad) + centers[:, 1] * np.sin(park_rad)

    # Cluster rows
    sorted_idx = np.argsort(perp_proj)
    rows = []
    current_row = [sorted_idx[0]]
    for i in range(1, len(sorted_idx)):
        if perp_proj[sorted_idx[i]] - perp_proj[sorted_idx[i-1]] < median_h * 1.2:
            current_row.append(sorted_idx[i])
        else:
            rows.append(current_row)
            current_row = [sorted_idx[i]]
    rows.append(current_row)

    # Find gaps in each row
    h_frame, w_frame = frame_shape[:2]
    car_temps = []
    for r in car_rects[:10]:
        cx, cy = int(r["center"][0]), int(r["center"][1])
        hw, hh = int(r["size"][0]//4), int(r["size"][1]//4)
        patch = thermal_gray[max(0,cy-hh):cy+hh, max(0,cx-hw):cx+hw]
        if patch.size > 0:
            car_temps.append(np.mean(patch))
    avg_car_temp = np.mean(car_temps) if car_temps else 128

    empty_slots = []
    for row in rows:
        if len(row) < 2:
            continue
        row_proj = park_proj[row]
        sort_order = np.argsort(row_proj)
        spacings = np.diff(row_proj[sort_order])
        if len(spacings) == 0:
            continue
        normal_spacing = np.median(spacings)
        if normal_spacing < 20:
            continue

        for i in range(len(sort_order) - 1):
            gap = spacings[i]
            if gap > normal_spacing * 1.7:
                num_empty = max(1, round(gap / normal_spacing) - 1)
                for s in range(1, num_empty + 1):
                    t = s / (num_empty + 1)
                    idx_a, idx_b = row[sort_order[i]], row[sort_order[i+1]]
                    ecx = centers[idx_a][0] * (1-t) + centers[idx_b][0] * t
                    ecy = centers[idx_a][1] * (1-t) + centers[idx_b][1] * t

                    ex, ey = int(ecx), int(ecy)
                    if 0 < ex < w_frame and 0 < ey < h_frame:
                        patch = thermal_gray[max(0,ey-20):ey+20, max(0,ex-20):ex+20]
                        if patch.size > 0 and np.mean(patch) < avg_car_temp * 0.95:
                            empty_slots.append({
                                "center": (ecx, ecy),
                                "size": (median_w, median_h),
                                "angle": parking_angle
                            })

    return empty_slots


def visualize(frame, car_rects, empty_slots):
    """Draw occupancy visualization on frame."""
    vis = frame.copy()

    for r in car_rects:
        box_pts = cv2.boxPoints((r["center"], r["size"], r["angle"])).astype(int)
        cv2.drawContours(vis, [box_pts], 0, (0, 0, 255), 2)

    for s in empty_slots:
        box_pts = cv2.boxPoints((s["center"], s["size"], s["angle"])).astype(int)
        cv2.drawContours(vis, [box_pts], 0, (0, 255, 0), 2)
        cx, cy = int(s["center"][0]), int(s["center"][1])
        cv2.putText(vis, "FREE", (cx-15, cy+5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    occ, emp = len(car_rects), len(empty_slots)
    total = occ + emp
    pct = occ / total * 100 if total > 0 else 0

    cv2.rectangle(vis, (0, 0), (500, 80), (0, 0, 0), -1)
    cv2.putText(vis, f"Occupied: {occ} | Free: {emp} | {pct:.0f}% full", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(vis, f"Total slots: {total}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    return vis


def main():
    parser = argparse.ArgumentParser(description="Parking occupancy monitor")
    parser.add_argument("--rgb", required=True, help="RGB video path")
    parser.add_argument("--thermal", help="Thermal video path (optional)")
    parser.add_argument("--frame", type=int, default=0, help="Frame index to analyze")
    parser.add_argument("--model", default="models/visdrone_yolov8s_best.pt", help="YOLO weights")
    parser.add_argument("--output", default="outputs/parking_result.jpg", help="Output image path")
    args = parser.parse_args()

    model = load_model(args.model)

    cap_rgb = cv2.VideoCapture(args.rgb)
    cap_rgb.set(cv2.CAP_PROP_POS_FRAMES, args.frame)
    ret, rgb = cap_rgb.read()
    cap_rgb.release()
    if not ret:
        print("Failed to read RGB frame")
        return

    h, w = rgb.shape[:2]

    # Load thermal if available
    if args.thermal:
        cap_t = cv2.VideoCapture(args.thermal)
        cap_t.set(cv2.CAP_PROP_POS_FRAMES, args.frame)
        ret, thermal = cap_t.read()
        cap_t.release()
        thermal_gray = cv2.cvtColor(cv2.resize(thermal, (w, h)), cv2.COLOR_BGR2GRAY)
    else:
        thermal_gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)

    # Pipeline
    detections = detect_vehicles(model, rgb)
    confirmed = thermal_confirm(detections, thermal_gray)
    car_rects = get_oriented_boxes(confirmed, thermal_gray)
    empty_slots = find_empty_slots(car_rects, thermal_gray, rgb.shape)

    vis = visualize(rgb, car_rects, empty_slots)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(args.output, vis)

    print(f"Occupied: {len(car_rects)}, Free: {len(empty_slots)}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
