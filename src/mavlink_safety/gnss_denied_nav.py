"""gnss_denied_nav.py — GNSS-denied navigation via optical flow + visual odometry.

Use Case 3: GNSS-denied navigation — the drone maintains position and executes
autonomous flight using only camera-based positioning (no satellite signals).

This script provides:
1. Optical flow velocity estimation from downward camera (BlueOS extension handles this)
2. Visual landmark matching for absolute position correction
3. Integration with the 1:1 safety monitor — works without GPS

Architecture on BlueOS:
  SIYI camera (downward) → BlueOS OpticalFlow Extension → MAVLink OPTICAL_FLOW → EKF3
  SIYI camera (forward)  → mavlink_safety_monitor.py → person detection + lateral dist

For GNSS-denied, ArduPilot's EKF3 fuses:
  - Optical flow (velocity)
  - Rangefinder (altitude)
  - IMU (attitude)
  → Position estimate without any satellite signal

This script adds visual-inertial odometry as a supplementary position source,
using ground features matched against a reference image/map.

Usage:
  # On BlueOS companion (runs alongside the optical flow extension):
  python src/mavlink_safety/gnss_denied_nav.py \
    --camera rtsp://192.168.144.25:8554/main.264 \
    --mav udp:127.0.0.1:14550 \
    --reference-image reference_site.jpg \
    --origin-lat 60.1316 --origin-lon 24.5126
"""

import argparse
import time
import math

import cv2
import numpy as np
from pymavlink import mavutil


class VisualOdometry:
    """Simple feature-based visual odometry for position correction.

    Uses ORB features + homography to estimate frame-to-frame translation.
    When a reference image is provided, estimates absolute position via
    feature matching against the known reference.
    """

    def __init__(self, reference_image_path: str = None,
                 reference_gsd: float = 0.05):
        """
        Args:
            reference_image_path: Path to georeferenced nadir image of the site
            reference_gsd: Ground sampling distance of reference (m/pixel)
        """
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.prev_frame = None
        self.prev_kp = None
        self.prev_desc = None
        self.reference_gsd = reference_gsd

        # Load reference image if provided
        self.ref_kp = None
        self.ref_desc = None
        if reference_image_path:
            ref = cv2.imread(reference_image_path, cv2.IMREAD_GRAYSCALE)
            if ref is not None:
                self.ref_kp, self.ref_desc = self.orb.detectAndCompute(ref, None)
                self.ref_shape = ref.shape
                print(f"[VO] Reference loaded: {ref.shape}, {len(self.ref_kp)} features")

    def estimate_displacement(self, frame: np.ndarray, altitude_m: float) -> dict:
        """Estimate displacement from previous frame using optical flow features.

        Args:
            frame: Current grayscale frame (downward camera)
            altitude_m: Current altitude from rangefinder/barometer

        Returns:
            dict with dx_m, dy_m (displacement in meters), confidence
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        kp, desc = self.orb.detectAndCompute(gray, None)

        result = {"dx_m": 0.0, "dy_m": 0.0, "confidence": 0.0, "matches": 0}

        if self.prev_desc is not None and desc is not None and len(kp) > 10:
            matches = self.bf.match(self.prev_desc, desc)
            matches = sorted(matches, key=lambda x: x.distance)[:50]

            if len(matches) >= 8:
                src_pts = np.float32([self.prev_kp[m.queryIdx].pt for m in matches])
                dst_pts = np.float32([kp[m.trainIdx].pt for m in matches])

                H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                if H is not None:
                    # Translation from homography (pixels)
                    dx_px = H[0, 2]
                    dy_px = H[1, 2]

                    # Convert to meters using GSD at current altitude
                    # GSD = altitude / focal_length_px (approximation)
                    gsd = altitude_m / (gray.shape[1] / 2)  # rough estimate
                    result["dx_m"] = -dx_px * gsd  # negative = camera moved right
                    result["dy_m"] = -dy_px * gsd
                    result["confidence"] = float(np.sum(mask)) / len(mask)
                    result["matches"] = int(np.sum(mask))

        self.prev_frame = gray
        self.prev_kp = kp
        self.prev_desc = desc
        return result

    def match_reference(self, frame: np.ndarray, altitude_m: float) -> dict:
        """Match current frame against reference image for absolute position.

        Returns position offset from reference image center in meters.
        """
        if self.ref_desc is None:
            return {"error": "no reference image"}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        kp, desc = self.orb.detectAndCompute(gray, None)

        if desc is None or len(kp) < 10:
            return {"confidence": 0}

        matches = self.bf.match(self.ref_desc, desc)
        matches = sorted(matches, key=lambda x: x.distance)[:100]

        if len(matches) < 15:
            return {"confidence": 0, "matches": len(matches)}

        src_pts = np.float32([self.ref_kp[m.queryIdx].pt for m in matches])
        dst_pts = np.float32([kp[m.trainIdx].pt for m in matches])

        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if H is None:
            return {"confidence": 0}

        # Center of current frame in reference image coordinates
        h, w = gray.shape
        center = np.array([[[w / 2, h / 2]]], dtype=np.float32)
        ref_center = cv2.perspectiveTransform(center, np.linalg.inv(H))

        # Offset from reference center in pixels
        ref_cx = self.ref_shape[1] / 2
        ref_cy = self.ref_shape[0] / 2
        offset_px_x = ref_center[0][0][0] - ref_cx
        offset_px_y = ref_center[0][0][1] - ref_cy

        # Convert to meters using reference GSD
        return {
            "offset_east_m": offset_px_x * self.reference_gsd,
            "offset_north_m": -offset_px_y * self.reference_gsd,  # image Y is south
            "confidence": float(np.sum(mask)) / len(mask),
            "matches": int(np.sum(mask))
        }


def send_vision_position(mav, x_m: float, y_m: float, z_m: float, timestamp_us: int):
    """Send VISION_POSITION_ESTIMATE to ArduPilot EKF3.

    This provides an external position source when GPS is unavailable.
    ArduPilot fuses this with IMU + optical flow for navigation.
    """
    mav.mav.vision_position_estimate_send(
        timestamp_us,
        x_m, y_m, z_m,  # NED position
        0, 0, 0,  # roll, pitch, yaw (not used)
        [0] * 21,  # covariance (not used)
        0  # reset counter
    )


def main():
    parser = argparse.ArgumentParser(description="GNSS-Denied Visual Navigation")
    parser.add_argument("--camera", default="rtsp://192.168.144.25:8554/main.264")
    parser.add_argument("--mav", default="udp:127.0.0.1:14550")
    parser.add_argument("--reference-image", help="Georeferenced nadir image of flight site")
    parser.add_argument("--reference-gsd", type=float, default=0.05, help="Reference image GSD (m/px)")
    parser.add_argument("--origin-lat", type=float, default=0)
    parser.add_argument("--origin-lon", type=float, default=0)
    parser.add_argument("--rate-hz", type=float, default=10)
    args = parser.parse_args()

    # Connect to ArduPilot
    mav = mavutil.mavlink_connection(args.mav)
    mav.wait_heartbeat()
    print(f"[MAV] Connected (sysid={mav.target_system})")

    # Set EKF origin if provided (required for non-GPS flight)
    if args.origin_lat != 0:
        mav.mav.set_gps_global_origin_send(
            mav.target_system,
            int(args.origin_lat * 1e7),
            int(args.origin_lon * 1e7),
            0  # alt mm
        )
        print(f"[NAV] Origin set: {args.origin_lat}, {args.origin_lon}")

    # Initialize visual odometry
    vo = VisualOdometry(args.reference_image, args.reference_gsd)

    # Open camera
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera: {args.camera}")
        return

    print(f"[NAV] GNSS-denied navigation active at {args.rate_hz} Hz")

    pos_x, pos_y, pos_z = 0.0, 0.0, 0.0  # accumulated position (NED, meters)
    interval = 1.0 / args.rate_hz

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # Get altitude from rangefinder/barometer via MAVLink
            msg = mav.recv_match(type='RANGEFINDER', blocking=False)
            alt = msg.distance if msg else 2.0  # default 2m if no rangefinder

            # Estimate displacement
            disp = vo.estimate_displacement(frame, alt)

            if disp["confidence"] > 0.3:
                pos_x += disp["dy_m"]  # north
                pos_y += disp["dx_m"]  # east
                pos_z = -alt  # down (NED)

                # Send to EKF3
                send_vision_position(mav, pos_x, pos_y, pos_z,
                                     int(time.time() * 1e6))

            # Periodically correct against reference if available
            if args.reference_image and int(time.time()) % 5 == 0:
                ref_match = vo.match_reference(frame, alt)
                if ref_match.get("confidence", 0) > 0.5:
                    pos_x = ref_match["offset_north_m"]
                    pos_y = ref_match["offset_east_m"]

            time.sleep(interval)

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        print("[NAV] Stopped")


if __name__ == "__main__":
    main()
