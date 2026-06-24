"""Unified CLI for drone-cv-detection.

Usage:
  python src/cli.py detect   --input video.mp4 --model models/yolov8s.pt
  python src/cli.py track    --video video.mp4 --model models/yolov8s.pt
  python src/cli.py rule     --detections data/detections.jsonl --osd data/osd.jsonl
  python src/cli.py parking  --video rgb.mp4 --thermal thermal.mp4
  python src/cli.py avata    --video flight.LRF --srt flight.SRT
  python src/cli.py compare  --video flight.LRF --srt flight.SRT
  python src/cli.py map      --osd data/osd.jsonl --timeline outputs/timeline.csv
  python src/cli.py dronetag --device-id <ID> --interval 5 --duration 300
  python src/cli.py counter
"""
from __future__ import annotations

import sys
import importlib


COMMANDS: dict[str, tuple[str, str]] = {
    "detect":   ("detect",              "main"),
    "track":    ("vehicle_tracker",     "main"),
    "rule":     ("rule_monitor",        "__main__"),
    "parking":  ("parking_monitor",     "main"),
    "avata":    ("avata360_monitor",    "main"),
    "compare":  ("compare_models",      "main"),
    "map":      ("flight_map",          "main"),
    "dronetag": ("dronetag_system_poll", "main"),
    "counter":  ("yolo_car_counter",    "main"),
}

HELP = """drone-cv — aerial computer vision toolkit (Patent WO2025034145A1)

Commands:
  detect    Run YOLO detection on an image or video
  track     ByteTrack persistent ID tracking on drone video
  rule      Evaluate 1:1 lateral distance rule (replay or live MQTT)
  parking   Two-stream RGB+Thermal parking occupancy monitor
  avata     DJI Avata 360 omnidirectional person detection
  compare   Compare YOLO models on Avata 360 LRF footage
  map       Generate interactive Folium flight map
  dronetag  Poll DroneTag REST API for device telemetry
  counter   YOLO car counter on traffic video

Run `python src/cli.py <command> --help` for per-command options.
"""


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(HELP)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd!r}")
        print("Available commands:", ", ".join(COMMANDS))
        sys.exit(1)

    module_name, entry = COMMANDS[cmd]

    # Remove cli.py and command name so the target module sees a clean sys.argv
    sys.argv = [module_name + ".py"] + sys.argv[2:]

    # rule_monitor uses if __name__ == '__main__' directly; run it via runpy
    if entry == "__main__":
        import runpy
        runpy.run_module(module_name, run_name="__main__", alter_sys=True)
    else:
        module = importlib.import_module(module_name)
        getattr(module, entry)()


if __name__ == "__main__":
    main()
