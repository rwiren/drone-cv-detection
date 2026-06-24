"""Evaluate a YOLO model on DJI Avata 360 LRF footage.

Extracts perspective views (configurable yaw×pitch sweep) and records
best detection confidence per second.

Usage:
  python scripts/eval_avata360.py \\
    --video ~/DJI_20260612150146_0003_D.LRF \\
    --srt   ~/DJI_20260612150146_0003_D.SRT \\
    --model models/visdrone_yolov8s_1280_best.pt \\
    --output outputs/evaluation/avata360_eval.json

Output (JSON):
  List of per-second records — see docs-site/schemas.md for full schema.
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

from avata360_monitor import extract_perspective, parse_avata_srt
from ultralytics import YOLO
from logging_utils import get_logger

log = get_logger(__name__)


def run(
    video: str,
    srt: str,
    model_path: str,
    output: str,
    interval: float = 1.0,
    pitches: list[int] | None = None,
    conf: float = 0.20,
    imgsz: int = 1280,
) -> list[dict]:
    if pitches is None:
        pitches = [30, 50, 70]

    telem = parse_avata_srt(srt)
    log.info("Loaded %d SRT frames", len(telem))

    model = YOLO(model_path)
    log.info("Model: %s", model_path)

    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(total_frames / fps)
    log.info("Video: %.0f fps, %ds duration", fps, duration)

    results = []
    t0 = time.time()

    for t in range(0, duration, max(1, int(interval))):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if not ret:
            break

        srt_idx = min(int(t * fps), len(telem) - 1)
        srt_frame = telem[srt_idx]
        alt = srt_frame.get('rel_alt', srt_frame.get('altitude', 0))

        best_conf, best_yaw, best_pitch = 0.0, 0, 0
        for pitch in pitches:
            for yaw in range(0, 360, 45):
                view = extract_perspective(frame, fov_deg=90, yaw_deg=yaw, pitch_deg=pitch)
                r = model(view, conf=conf, classes=[0, 1], imgsz=imgsz, verbose=False)[0]
                if len(r.boxes) > 0:
                    c = max(float(b.conf) for b in r.boxes)
                    if c > best_conf:
                        best_conf, best_yaw, best_pitch = c, yaw, pitch

        results.append({
            't': t,
            'alt': round(alt, 2),
            'conf': round(best_conf, 3),
            'yaw': best_yaw,
            'pitch': best_pitch,
        })

        if t % 10 == 0:
            pct = t / max(duration, 1) * 100
            eta = (time.time() - t0) / max(t, 1) * (duration - t) / 60
            marker = "✓" if best_conf > 0.25 else "·"
            log.info("[%5.1f%%] t=%3ds alt=%5.1fm conf=%.2f %s  ETA: %.0fmin",
                     pct, t, alt, best_conf, marker, eta)

    cap.release()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)

    detected = sum(1 for r in results if r['conf'] > 0.25)
    log.info("Done: %d seconds scanned, %d with detection. Saved: %s",
             len(results), detected, output)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description='Evaluate YOLO on Avata 360 LRF footage')
    parser.add_argument('--video', required=True, help='Path to .LRF or .MP4 file')
    parser.add_argument('--srt',   required=True, help='Path to .SRT telemetry file')
    parser.add_argument('--model', default='models/visdrone_yolov8s_1280_best.pt')
    parser.add_argument('--output', default='outputs/evaluation/avata360_eval.json')
    parser.add_argument('--interval', type=float, default=1.0, help='Sample interval in seconds')
    parser.add_argument('--pitches', nargs='+', type=int, default=[30, 50, 70],
                        help='Pitch angles to sweep (degrees)')
    parser.add_argument('--conf', type=float, default=0.20, help='Detection confidence threshold')
    parser.add_argument('--imgsz', type=int, default=1280, help='Inference image size')
    args = parser.parse_args()

    run(
        video=args.video,
        srt=args.srt,
        model_path=args.model,
        output=args.output,
        interval=args.interval,
        pitches=args.pitches,
        conf=args.conf,
        imgsz=args.imgsz,
    )


if __name__ == '__main__':
    main()
