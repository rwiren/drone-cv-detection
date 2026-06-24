"""
Vehicle Tracker — ByteTrack persistent ID tracking on drone video.
"""
from __future__ import annotations

import cv2
import sys
import time
import argparse
from collections import defaultdict
from pathlib import Path
from ultralytics import YOLO

from logging_utils import get_logger

log = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Track vehicles in drone video")
    parser.add_argument("--video", required=True, help="Input video path")
    parser.add_argument("--model", default="models/visdrone_yolov8s_best.pt", help="YOLO weights")
    parser.add_argument("--output", default="outputs/tracked.mp4", help="Output video")
    parser.add_argument("--skip", type=int, default=3, help="Process every Nth frame")
    parser.add_argument("--conf", type=float, default=0.3, help="Detection confidence")
    args = parser.parse_args()

    model = YOLO(args.model)
    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps / args.skip, (w, h))

    all_ids = set()
    track_history = defaultdict(list)
    frame_idx = 0
    t0 = time.time()

    log.info("Processing %d frames (every %dth)...", total, args.skip)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % args.skip != 0:
            frame_idx += 1
            continue

        results = model.track(frame, persist=True, tracker="bytetrack.yaml",
                              conf=args.conf, verbose=False)

        if results[0].boxes.id is not None:
            ids = results[0].boxes.id.int().cpu().tolist()
            boxes = results[0].boxes.xyxy.cpu().tolist()
            classes = results[0].boxes.cls.int().cpu().tolist()

            for track_id, box, cls_id in zip(ids, boxes, classes):
                all_ids.add(track_id)
                x1, y1, x2, y2 = map(int, box)
                cx, cy = (x1+x2)//2, (y1+y2)//2

                track_history[track_id].append((cx, cy))
                if len(track_history[track_id]) > 30:
                    track_history[track_id] = track_history[track_id][-30:]

                cls_name = results[0].names[cls_id]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID:{track_id} {cls_name}", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

                pts = track_history[track_id]
                for j in range(1, len(pts)):
                    cv2.line(frame, pts[j-1], pts[j], (230, 230, 0), 1)

        cv2.putText(frame, f"Unique: {len(all_ids)} | Frame: {frame_idx}/{total}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        out.write(frame)

        if (frame_idx // args.skip) % 50 == 0:
            elapsed = time.time() - t0
            pct = frame_idx / total * 100
            log.info("  %.0f%% | Frame %d/%d | IDs: %d | %.0fs", pct, frame_idx, total, len(all_ids), elapsed)
            sys.stdout.flush()

        frame_idx += 1

    cap.release()
    out.release()
    log.info("Done. Unique vehicles: %d. Saved: %s", len(all_ids), args.output)


if __name__ == "__main__":
    main()
