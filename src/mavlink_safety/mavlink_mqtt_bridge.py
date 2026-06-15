"""mavlink_mqtt_bridge.py — Bidirectional MAVLink ↔ MQTT bridge.

Connects to ArduPilot via MAVProxy UDP and bridges telemetry + commands over MQTT.
Enables external communication device (patent claim 10) to receive telemetry
and send flight commands back to the drone (claims 7, 8).

Telemetry flow:  MAVLink → MQTT (pixhawk/telemetry)
Command flow:    MQTT (pixhawk/command) → MAVLink

Requires: pymavlink, paho-mqtt
"""

import argparse
import json
import time
import threading

from pymavlink import mavutil
import paho.mqtt.client as mqtt


class MAVLinkMQTTBridge:
    def __init__(self, mav_connection: str, broker_host: str, broker_port: int,
                 telemetry_topic: str = "pixhawk/telemetry",
                 command_topic: str = "pixhawk/command",
                 username: str = None, password: str = None, use_tls: bool = True):
        self.telemetry_topic = telemetry_topic
        self.command_topic = command_topic

        # MAVLink connection
        print(f"[MAV] Connecting to {mav_connection}...")
        self.mav = mavutil.mavlink_connection(mav_connection)
        self.mav.wait_heartbeat()
        print(f"[MAV] Connected (sysid={self.mav.target_system}, comp={self.mav.target_component})")

        # MQTT connection
        self.client = mqtt.Client()
        if username:
            self.client.username_pw_set(username, password)
        if use_tls:
            self.client.tls_set()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_command
        self.client.connect(broker_host, broker_port, 60)

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Connected, subscribing to {self.command_topic}")
        client.subscribe(f"{self.command_topic}/#")

    def _on_command(self, client, userdata, msg):
        """Receive commands from external safety monitor and send to drone."""
        try:
            cmd = json.loads(msg.payload)
            command = cmd.get("command", "")

            if command == "GUIDED_LOITER":
                # Claim 7+8: prevent further approach — switch to GUIDED + loiter
                print(f"[CMD] HOLD POSITION — reason: {cmd.get('reason')}")
                self.mav.set_mode_apm(15)  # GUIDED mode
                self.mav.mav.command_long_send(
                    self.mav.target_system, self.mav.target_component,
                    mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM, 0,
                    0, 0, 0, 0,
                    int(cmd.get("lat", 0) * 1e7),
                    int(cmd.get("lon", 0) * 1e7),
                    cmd.get("alt", 10)
                )

            elif command == "RESUME":
                print(f"[CMD] RESUME FLIGHT — reason: {cmd.get('reason')}")
                # Return to AUTO or previous mode
                self.mav.set_mode_apm(10)  # AUTO mode

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[CMD] Error parsing command: {e}")

    def _publish_telemetry(self):
        """Read MAVLink messages and publish as MQTT telemetry."""
        while True:
            msg = self.mav.recv_match(type=['GLOBAL_POSITION_INT', 'ATTITUDE',
                                            'VFR_HUD', 'MOUNT_STATUS'],
                                     blocking=True, timeout=1)
            if msg is None:
                continue

            msg_type = msg.get_type()

            if msg_type == 'GLOBAL_POSITION_INT':
                telemetry = {
                    "lat": msg.lat / 1e7,
                    "lon": msg.lon / 1e7,
                    "alt_rel": msg.relative_alt / 1000.0,
                    "altitude": msg.relative_alt / 1000.0,
                    "heading": msg.hdg / 100.0,
                    "vx": msg.vx / 100.0,
                    "vy": msg.vy / 100.0,
                    "vz": msg.vz / 100.0,
                    "groundspeed": (msg.vx**2 + msg.vy**2)**0.5 / 100.0,
                    "timestamp": time.time()
                }
                self.client.publish(self.telemetry_topic, json.dumps(telemetry))

            elif msg_type == 'MOUNT_STATUS':
                gimbal = {
                    "gimbal_pitch": msg.pointing_a / 100.0,
                    "gimbal_roll": msg.pointing_b / 100.0,
                    "gimbal_yaw": msg.pointing_c / 100.0,
                    "timestamp": time.time()
                }
                self.client.publish(f"{self.telemetry_topic}/gimbal", json.dumps(gimbal))

    def run(self):
        self.client.loop_start()
        print("[BRIDGE] Running MAVLink ↔ MQTT bridge...")
        try:
            self._publish_telemetry()
        except KeyboardInterrupt:
            pass
        finally:
            self.client.loop_stop()
            print("[BRIDGE] Stopped")


def main():
    parser = argparse.ArgumentParser(description="MAVLink ↔ MQTT Bridge")
    parser.add_argument("--mav", default="udp:127.0.0.1:14550", help="MAVLink connection string")
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=8883)
    parser.add_argument("--telemetry-topic", default="pixhawk/telemetry")
    parser.add_argument("--command-topic", default="pixhawk/command")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--no-tls", action="store_true")
    args = parser.parse_args()

    bridge = MAVLinkMQTTBridge(
        mav_connection=args.mav,
        broker_host=args.broker,
        broker_port=args.port,
        telemetry_topic=args.telemetry_topic,
        command_topic=args.command_topic,
        username=args.username,
        password=args.password,
        use_tls=not args.no_tls
    )
    bridge.run()


if __name__ == "__main__":
    main()
