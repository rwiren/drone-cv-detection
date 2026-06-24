"""Compare YOLO models on Avata 360 LRF footage.

Usage:
  python src/compare_models.py --video ~/DJI_20260612150146_0003_D.LRF --srt ~/DJI_20260612150146_0003_D.SRT

Once Colab model is ready, add it to models/ and re-run to compare.
"""
from __future__ import annotations

import cv2
import argparse
import time
from pathlib import Path
from ultralytics import YOLO
from avata360_monitor import extract_perspective, parse_avata_srt

from logging_utils import get_logger

log = get_logger(__name__)


def sample_frames(video_path, timestamps, fps):
    """Read specific frames from video."""
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    for t in timestamps:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if ret:
            frames.append((t, frame))
    cap.release()
    return frames


def evaluate_model(model_path, frames, imgsz=640):
    """Run model on perspective views extracted from dual-fisheye frames."""
    model = YOLO(str(model_path))
    total_dets = 0
    total_conf = 0.0
    t0 = time.time()

    for t, frame in frames:
        for yaw in range(0, 360, 45):
            view = extract_perspective(frame, fov_deg=90, yaw_deg=yaw, pitch_deg=50)
            r = model(view, conf=0.25, imgsz=imgsz, verbose=False)[0]
            n = len(r.boxes)
            total_dets += n
            if n > 0:
                total_conf += sum(float(b.conf) for b in r.boxes)

    elapsed = time.time() - t0
    avg_conf = total_conf / total_dets if total_dets > 0 else 0
    return total_dets, avg_conf, elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', required=True)
    parser.add_argument('--srt', required=True)
    parser.add_argument('--samples', type=int, default=5, help='Number of frames to test')
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps
    cap.release()

    # Sample evenly across the video
    timestamps = [duration * i / (args.samples + 1) for i in range(1, args.samples + 1)]
    log.info("Video: %.0fs, %.0ffps. Sampling %d frames.", duration, fps, len(timestamps))

    frames = sample_frames(args.video, timestamps, fps)

    # Find all models
    models_dir = Path(__file__).parent.parent / 'models'
    models = sorted(models_dir.glob('*.pt'))

    if not models:
        log.warning("No models found in models/")
        return

    log.info("%-40s %5s %8s %6s", 'Model', 'Dets', 'AvgConf', 'Time')
    log.info("=" * 65)

    for m in models:
        dets, conf, elapsed = evaluate_model(m, frames)
        log.info("%-40s %5d %8.3f %5.1fs", m.name, dets, conf, elapsed)

    log.info("(8 views × %d frames = %d inferences per model)", len(frames), 8 * len(frames))


if __name__ == '__main__':
    main()
