"""Evaluate a YOLO model on Autel MAX 4T V2 xe RGB video directory.

Samples frames at a configurable interval across all .MP4 files in the
given directory and records per-frame detections.

Usage:
  python scripts/eval_autel.py \\
    --video-dir data/autel_20260612/video/rgb \\
    --model     models/visdrone_yolov8s_1280_best.pt \\
    --output    outputs/evaluation/autel_eval.json

Output (JSON):
  Dict keyed by filename, each value a list of per-sample records.
  See docs-site/schemas.md for full schema.
"""
from __future__ import annotations

import cv2
import json
import os
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
os.chdir(Path(__file__).parent.parent)

from ultralytics import YOLO
from logging_utils import get_logger

log = get_logger(__name__)


def run_video(
    video_path: str,
    model: object,
    interval: float = 2.0,
    conf: float = 0.20,
    imgsz: int = 1280,
) -> list[dict]:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(fps * interval))
    n_samples = total_frames // step

    results = []
    for i, fi in enumerate(range(0, total_frames, step)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, frame = cap.read()
        if not ret:
            break

        r = model(frame, conf=conf, imgsz=imgsz, verbose=False)[0]  # type: ignore[operator]
        classes: dict[str, int] = {}
        for b in r.boxes:
            name = r.names[int(b.cls)]
            classes[name] = classes.get(name, 0) + 1

        results.append({
            'frame': fi,
            'time_s': round(fi / fps, 2),
            'dets': classes,
            'total_dets': len(r.boxes),
        })

    cap.release()
    return results


def run(
    video_dir: str,
    model_path: str,
    output: str,
    interval: float = 2.0,
    conf: float = 0.20,
    imgsz: int = 1280,
) -> dict[str, list[dict]]:
    model = YOLO(model_path)
    log.info("Model: %s", model_path)

    video_files = sorted(Path(video_dir).glob('*.MP4'))
    if not video_files:
        log.warning("No .MP4 files found in %s", video_dir)
        return {}

    log.info("Found %d video files in %s", len(video_files), video_dir)

    all_results: dict[str, list[dict]] = {}
    t0 = time.time()

    for vpath in video_files:
        log.info("Processing %s ...", vpath.name)
        results = run_video(str(vpath), model, interval=interval, conf=conf, imgsz=imgsz)
        all_results[vpath.name] = results
        total_dets = sum(r['total_dets'] for r in results)
        log.info("  %s: %d samples, %d total detections", vpath.name, len(results), total_dets)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w') as f:
        json.dump(all_results, f, indent=2)

    elapsed = time.time() - t0
    total_samples = sum(len(v) for v in all_results.values())
    log.info("Done: %d videos, %d total samples in %.0fs. Saved: %s",
             len(all_results), total_samples, elapsed, output)
    return all_results


def main() -> None:
    parser = argparse.ArgumentParser(description='Evaluate YOLO on Autel MAX 4T V2 xe RGB videos')
    parser.add_argument('--video-dir', required=True, help='Directory containing .MP4 files')
    parser.add_argument('--model',     default='models/visdrone_yolov8s_1280_best.pt')
    parser.add_argument('--output',    default='outputs/evaluation/autel_eval.json')
    parser.add_argument('--interval',  type=float, default=2.0, help='Sample interval in seconds')
    parser.add_argument('--conf',      type=float, default=0.20, help='Detection confidence threshold')
    parser.add_argument('--imgsz',     type=int,   default=1280, help='Inference image size')
    args = parser.parse_args()

    run(
        video_dir=args.video_dir,
        model_path=args.model,
        output=args.output,
        interval=args.interval,
        conf=args.conf,
        imgsz=args.imgsz,
    )


if __name__ == '__main__':
    main()
