"""
YOLO Car Counter - Video File Mode
Usage: source ~/cv_env/bin/activate && python yolo_car_counter.py

Press 'q' to quit the video window.
"""
from __future__ import annotations

from ultralytics import YOLO
import cv2
import urllib.request
import os

from config import COCO_VEHICLE_CLASSES
from logging_utils import get_logger

log = get_logger(__name__)


def main() -> None:
    model = YOLO("yolov8n.pt")

    # Download a sample traffic video if not present
    video = "traffic.mp4"
    if not os.path.exists(video):
        log.info("Downloading sample traffic video...")
        urllib.request.urlretrieve(
            "https://github.com/intel-iot-devkit/sample-videos/raw/master/car-detection.mp4",
            video,
        )
        log.info("Downloaded.")

    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        log.error("Cannot open video file.")
        raise SystemExit(1)

    log.info("Playing video. Press 'q' to quit.")
    out_frames: list = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)[0]

        count = 0
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id in COCO_VEHICLE_CLASSES:
                count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                label = f"{COCO_VEHICLE_CLASSES[cls_id]} {conf:.2f}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.putText(frame, f"Vehicles: {count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Save first 5 annotated frames as images
        if len(out_frames) < 5:
            out_frames.append(frame)

        try:
            cv2.imshow("YOLO Car Counter", frame)
            if cv2.waitKey(30) & 0xFF == ord("q"):
                break
        except Exception:
            pass  # no display available

    cap.release()
    cv2.destroyAllWindows()

    # Save sample frames
    for i, f in enumerate(out_frames):
        cv2.imwrite(f"yolo_frame_{i}.jpg", f)
    log.info("Saved %d annotated frames as yolo_frame_0.jpg ... yolo_frame_%d.jpg",
             len(out_frames), len(out_frames) - 1)


if __name__ == "__main__":
    main()
