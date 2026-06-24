"""Evaluate a YOLO model on DJI M2EA video + SRT telemetry.

Samples frames at a configurable interval and records per-frame detections.

Usage:
  python scripts/eval_m2ea.py \\
    --video data/DJI_0398_W.MP4 \\
    --srt   data/DJI_0398_W.SRT \\
    --model models/visdrone_yolov8s_1280_best.pt \\
    --output outputs/evaluation/m2ea_DJI_0398_W_eval.json

Output (JSON):
  List of per-sample records — see docs-site/schemas.md for full schema.
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

from lateral_distance import parse_srt
from ultralytics import YOLO
from logging_utils import get_logger

log = get_logger(__name__)


def run(
    video: str,
    srt: str,
    model_path: str,
    output: str,
    interval: float = 1.0,
    conf: float = 0.20,
    imgsz: int = 1280,
) -> list[dict]:
    telem = parse_srt(srt)
    log.info("Loaded %d SRT frames", len(telem))

    model = YOLO(model_path)
    log.info("Model: %s", model_path)

    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(fps * interval))
    n_samples = total_frames // step
    log.info("Video: %.0f fps, %d frames, ~%d samples", fps, total_frames, n_samples)

    results = []
    t0 = time.time()

    for i, fi in enumerate(range(0, total_frames, step)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, frame = cap.read()
        if not ret:
            break

        srt_idx = min(fi, len(telem) - 1)
        srt_frame = telem[srt_idx] if telem else {}
        alt = srt_frame.get('altitude', 0.0)

        r = model(frame, conf=conf, imgsz=imgsz, verbose=False)[0]
        classes: dict[str, int] = {}
        for b in r.boxes:
            name = r.names[int(b.cls)]
            classes[name] = classes.get(name, 0) + 1

        results.append({
            'frame': fi,
            'time_s': round(fi / fps, 2),
            'alt_m': round(alt, 2),
            'dets': classes,
            'total_dets': len(r.boxes),
        })

        if i % 20 == 0:
            elapsed = time.time() - t0
            pct = i / max(n_samples, 1) * 100
            log.info("[%5.1f%%] frame %d/%d t=%.1fs alt=%.1fm dets=%d  (%.0fs elapsed)",
                     pct, i, n_samples, fi / fps, alt, len(r.boxes), elapsed)

    cap.release()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)

    total_dets = sum(r['total_dets'] for r in results)
    log.info("Done: %d frames sampled, %d total detections. Saved: %s",
             len(results), total_dets, output)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description='Evaluate YOLO on DJI M2EA video + SRT')
    parser.add_argument('--video',    required=True, help='Path to .MP4 file')
    parser.add_argument('--srt',      required=True, help='Path to .SRT telemetry file')
    parser.add_argument('--model',    default='models/visdrone_yolov8s_1280_best.pt')
    parser.add_argument('--output',   default='outputs/evaluation/m2ea_eval.json')
    parser.add_argument('--interval', type=float, default=1.0, help='Sample interval in seconds')
    parser.add_argument('--conf',     type=float, default=0.20, help='Detection confidence threshold')
    parser.add_argument('--imgsz',    type=int,   default=1280, help='Inference image size')
    args = parser.parse_args()

    run(
        video=args.video,
        srt=args.srt,
        model_path=args.model,
        output=args.output,
        interval=args.interval,
        conf=args.conf,
        imgsz=args.imgsz,
    )


if __name__ == '__main__':
    main()
