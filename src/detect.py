"""
Simple YOLO detection on drone video/image.
"""
import cv2
import argparse
from pathlib import Path
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Detect objects in aerial imagery")
    parser.add_argument("--input", required=True, help="Image or video path")
    parser.add_argument("--model", default="models/visdrone_yolov8s_best.pt")
    parser.add_argument("--conf", type=float, default=0.3)
    parser.add_argument("--output", default="outputs/detection.jpg")
    args = parser.parse_args()

    model = YOLO(args.model)
    results = model(args.input, conf=args.conf, verbose=False)

    plotted = results[0].plot()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(args.output, plotted)

    names = results[0].names
    for box in results[0].boxes:
        cls = names[int(box.cls[0])]
        conf = float(box.conf[0])
        print(f"  {cls}: {conf:.2f}")
    print(f"\n{len(results[0].boxes)} objects. Saved: {args.output}")


if __name__ == "__main__":
    main()
