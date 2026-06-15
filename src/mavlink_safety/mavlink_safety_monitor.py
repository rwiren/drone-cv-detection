"""mavlink_safety_monitor.py — Patent WO2025034145A1 Claims 4,7,8,10 Proof-of-Concept

External communication device (claim 10) that:
- Receives MAVLink telemetry via MQTT (altitude, position, gimbal pitch)
- Runs CV detection on camera stream (claim 1: detect object from image)
- Extracts focal length from metadata (claim 4)
- Calculates lateral distance from bounding box geometry
- Compares with determined_value × altitude (1:1 rule, claim 6)
- Issues message to receiving unit (claim 1)
- Sends MAV_CMD back to drone to hold position if violated (claims 7,8)

Architecture:
  Pixhawk/ArduPilot → MAVProxy → MQTT broker
       ↕ (bidirectional)
  This script (external device) → CV detection → lateral distance calc
       → if violated: publishes MAV_CMD_NAV_LOITER via MQTT → MAVProxy → drone

Usage:
  python src/mavlink_safety/mavlink_safety_monitor.py \
    --broker mqtt://localhost:8883 \
    --telemetry-topic pixhawk/telemetry \
    --command-topic pixhawk/command \
    --camera rtsp://drone:8554/stream \
    --model models/visdrone_yolov8m_1280_best.pt \
    --safety-value 1.0
"""

import argparse
import json
import time
import math
import threading
from dataclasses import dataclass, field

import cv2
import numpy as np
import paho.mqtt.client as mqtt
from ultralytics import YOLO


@dataclass
class DroneState:
    """Current telemetry from MAVLink via MQTT."""
    altitude_m: float = 0.0
    lat: float = 0.0
    lon: float = 0.0
    gimbal_pitch_deg: float = -90.0  # nadir default
    heading_deg: float = 0.0
    speed_mps: float = 0.0
    timestamp: float = 0.0


@dataclass
class CameraConfig:
    """Camera parameters for lateral distance calculation (claim 4)."""
    focal_length_mm: float = 4.5  # default: typical drone wide camera
    sensor_width_mm: float = 6.4  # 1/2.3" sensor
    image_width_px: int = 1920

    @property
    def focal_length_px(self) -> float:
        """Focal length in pixels — claim 4: calculated from image width + sensor width."""
        return self.focal_length_mm * self.image_width_px / self.sensor_width_mm


def calculate_lateral_distance(bbox_height_px: float, gimbal_pitch_deg: float,
                                focal_length_px: float, person_height_m: float = 1.75,
                                fraction_x: float = 2.0) -> float:
    """Calculate lateral distance from UAV to detected person.

    Implements patent Eq. 1:
        d_H = (H_P / 2) * (x * f / H_y) * (sin θ + (f/H_y) * cos θ) * cos θ

    Args:
        bbox_height_px: Height of bounding box in pixels (H_y)
        gimbal_pitch_deg: Gimbal pitch angle in degrees (θ, 0=horizon, -90=nadir)
        focal_length_px: Focal length in pixels (f)
        person_height_m: Assumed person height in meters (H_P)
        fraction_x: Bounding box fraction (x=2 if centered)

    Returns:
        Lateral distance in meters (d_H)
    """
    theta = math.radians(abs(gimbal_pitch_deg))
    H_y = bbox_height_px
    f = focal_length_px
    H_P = person_height_m

    if H_y < 1:
        return float('inf')

    d_H = (H_P / 2.0) * (fraction_x * f / H_y) * (
        math.sin(theta) + (f / H_y) * math.cos(theta)
    ) * math.cos(theta)

    return d_H


class MAVLinkSafetyMonitor:
    """External communication device implementing patent claims 1,4,7,8,10."""

    def __init__(self, broker_host: str, broker_port: int,
                 telemetry_topic: str, command_topic: str,
                 camera_source: str, model_path: str,
                 safety_value: float = 1.0, person_height: float = 1.75,
                 use_tls: bool = True, username: str = None, password: str = None):
        self.telemetry_topic = telemetry_topic
        self.command_topic = command_topic
        self.camera_source = camera_source
        self.safety_value = safety_value
        self.person_height = person_height
        self.drone_state = DroneState()
        self.camera_config = CameraConfig()
        self.model = YOLO(model_path)
        self.running = False
        self.violation_active = False

        # MQTT client (claim 10: external communication device)
        self.client = mqtt.Client()
        if username:
            self.client.username_pw_set(username, password)
        if use_tls:
            self.client.tls_set()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(broker_host, broker_port, 60)

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Connected (rc={rc}), subscribing to {self.telemetry_topic}")
        client.subscribe(self.telemetry_topic)

    def _on_message(self, client, userdata, msg):
        """Receive MAVLink telemetry via MQTT."""
        try:
            data = json.loads(msg.payload)
            self.drone_state.altitude_m = data.get("alt_rel", data.get("altitude", 0))
            self.drone_state.lat = data.get("lat", 0)
            self.drone_state.lon = data.get("lon", 0)
            self.drone_state.gimbal_pitch_deg = data.get("gimbal_pitch", -90)
            self.drone_state.heading_deg = data.get("heading", 0)
            self.drone_state.speed_mps = data.get("groundspeed", 0)
            self.drone_state.timestamp = time.time()

            # Update camera config from telemetry if available (claim 4: from metadata)
            if "focal_length_mm" in data:
                self.camera_config.focal_length_mm = data["focal_length_mm"]
            if "image_width" in data:
                self.camera_config.image_width_px = data["image_width"]
            if "sensor_width_mm" in data:
                self.camera_config.sensor_width_mm = data["sensor_width_mm"]
        except (json.JSONDecodeError, KeyError):
            pass

    def _send_hold_command(self):
        """Claim 7+8: Prevent UAV from moving further toward detected object.

        Sends MAV_CMD_NAV_LOITER_UNLIM equivalent via MQTT to MAVProxy bridge.
        The receiving unit (MAVProxy/GCS) initiates the prevention (claim 8).
        """
        command = {
            "command": "GUIDED_LOITER",
            "reason": "1:1_rule_violation",
            "lat": self.drone_state.lat,
            "lon": self.drone_state.lon,
            "alt": self.drone_state.altitude_m,
            "timestamp": time.time()
        }
        self.client.publish(self.command_topic, json.dumps(command), qos=1)
        print(f"[SAFETY] ⚠️  HOLD COMMAND SENT — 1:1 rule violated")

    def _send_clear_command(self):
        """Resume normal flight when violation clears."""
        command = {
            "command": "RESUME",
            "reason": "1:1_rule_clear",
            "timestamp": time.time()
        }
        self.client.publish(self.command_topic, json.dumps(command), qos=1)
        print(f"[SAFETY] ✅ CLEAR — resuming normal flight")

    def _issue_message(self, lateral_distance: float, altitude: float, num_persons: int):
        """Claim 1: Issue message to receiving unit if d_H <= value × altitude."""
        message = {
            "type": "SAFETY_ALERT",
            "lateral_distance_m": round(lateral_distance, 2),
            "altitude_m": round(altitude, 2),
            "safety_ratio": round(lateral_distance / max(altitude, 0.1), 3),
            "threshold": self.safety_value,
            "violated": lateral_distance <= self.safety_value * altitude,
            "persons_detected": num_persons,
            "timestamp": time.time()
        }
        self.client.publish(f"{self.command_topic}/safety_alert", json.dumps(message), qos=1)
        return message["violated"]

    def process_frame(self, frame: np.ndarray) -> dict:
        """Full pipeline: detect → calculate → compare → issue/prevent."""
        results = self.model(frame, classes=[0], conf=0.3, verbose=False)  # class 0 = person
        detections = results[0].boxes if results else []

        if len(detections) == 0:
            if self.violation_active:
                self.violation_active = False
                self._send_clear_command()
            return {"persons": 0, "violated": False}

        # Calculate lateral distance for each detected person
        altitude = self.drone_state.altitude_m
        gimbal_pitch = self.drone_state.gimbal_pitch_deg
        f_px = self.camera_config.focal_length_px
        distances = []

        for box in detections:
            bbox_h = (box.xyxy[0][3] - box.xyxy[0][1]).item()
            d_h = calculate_lateral_distance(
                bbox_height_px=bbox_h,
                gimbal_pitch_deg=gimbal_pitch,
                focal_length_px=f_px,
                person_height_m=self.person_height
            )
            distances.append(d_h)

        # Claim 5: Select shortest lateral distance
        shortest = min(distances)

        # Claim 1: Compare and issue message
        violated = self._issue_message(shortest, altitude, len(distances))

        # Claims 7+8: Prevent further approach
        if violated and not self.violation_active:
            self.violation_active = True
            self._send_hold_command()
        elif not violated and self.violation_active:
            self.violation_active = False
            self._send_clear_command()

        return {
            "persons": len(distances),
            "shortest_distance_m": round(shortest, 2),
            "altitude_m": round(altitude, 2),
            "ratio": round(shortest / max(altitude, 0.1), 3),
            "violated": violated
        }

    def run(self):
        """Main loop: read camera, process frames, enforce safety."""
        self.running = True
        self.client.loop_start()

        cap = cv2.VideoCapture(self.camera_source)
        if not cap.isOpened():
            print(f"[ERROR] Cannot open camera: {self.camera_source}")
            return

        print(f"[START] Safety monitor active — value={self.safety_value}, "
              f"camera={self.camera_source}")

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                result = self.process_frame(frame)
                if result["persons"] > 0:
                    print(f"[DETECT] {result['persons']} person(s), "
                          f"closest={result['shortest_distance_m']}m, "
                          f"alt={result['altitude_m']}m, "
                          f"ratio={result['ratio']}, "
                          f"violated={result['violated']}")

                time.sleep(0.5)  # 2 Hz processing
        except KeyboardInterrupt:
            pass
        finally:
            cap.release()
            self.client.loop_stop()
            print("[STOP] Safety monitor stopped")


def main():
    parser = argparse.ArgumentParser(description="MAVLink 1:1 Safety Monitor (Patent WO2025034145A1)")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=8883, help="MQTT broker port")
    parser.add_argument("--telemetry-topic", default="pixhawk/telemetry")
    parser.add_argument("--command-topic", default="pixhawk/command")
    parser.add_argument("--camera", default="0", help="Camera source (RTSP URL, device index, or video file)")
    parser.add_argument("--model", default="models/visdrone_yolov8m_1280_best.pt")
    parser.add_argument("--safety-value", type=float, default=1.0, help="Multiplier for 1:1 rule (≥1.0)")
    parser.add_argument("--person-height", type=float, default=1.75, help="Assumed person height (m)")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--no-tls", action="store_true")
    args = parser.parse_args()

    camera = int(args.camera) if args.camera.isdigit() else args.camera

    monitor = MAVLinkSafetyMonitor(
        broker_host=args.broker,
        broker_port=args.port,
        telemetry_topic=args.telemetry_topic,
        command_topic=args.command_topic,
        camera_source=camera,
        model_path=args.model,
        safety_value=args.safety_value,
        person_height=args.person_height,
        use_tls=not args.no_tls,
        username=args.username,
        password=args.password
    )
    monitor.run()


if __name__ == "__main__":
    main()
