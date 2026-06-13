"""Real-time 1:1 lateral distance rule monitor for Autel MAX 4T V2 xe.

Subscribes to MQTT detection stream, calculates lateral distance to detected
persons, and triggers alerts when the 1:1 rule is violated.

Implements patent WO2025034145A1 claim: "issue a message to a receiving unit
if the lateral distance is less or equal to the determined value times the
altitude of the UAV."

Can run in:
  - Live mode: subscribes to MQTT broker
  - Replay mode: reads from saved JSONL files (for testing/demo)
"""

import json
import math
import argparse
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class RuleStatus:
    timestamp_utc: str
    altitude_m: float
    lateral_distance_m: float
    ratio: float
    violation: bool
    person_lat: float
    person_lon: float
    drone_lat: float
    drone_lon: float
    num_persons: int


def check_1to1_rule(drone_lat: float, drone_lon: float, drone_alt: float,
                    person_lat: float, person_lon: float,
                    safety_value: float = 1.0) -> RuleStatus:
    """Check 1:1 rule compliance for a single person detection.

    Patent WO2025034145A1: d_lateral >= determined_value × altitude
    """
    dlat = (person_lat - drone_lat) * 111320
    dlon = (person_lon - drone_lon) * 111320 * math.cos(math.radians(drone_lat))
    lateral = math.sqrt(dlat**2 + dlon**2)
    ratio = lateral / drone_alt if drone_alt > 1 else 0
    violation = ratio < safety_value

    return RuleStatus(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        altitude_m=drone_alt,
        lateral_distance_m=round(lateral, 2),
        ratio=round(ratio, 3),
        violation=violation,
        person_lat=person_lat,
        person_lon=person_lon,
        drone_lat=drone_lat,
        drone_lon=drone_lon,
        num_persons=1,
    )


def replay_from_jsonl(detections_path: str, osd_path: str, safety_value: float = 1.0):
    """Replay saved MQTT data and evaluate 1:1 rule for all person detections."""
    import bisect

    # Load drone OSD
    with open(osd_path) as f:
        osd = [json.loads(l) for l in f]
    osd_times = [r['arrival_ts'] for r in osd]

    # Process detections
    results = []
    with open(detections_path) as f:
        for line in f:
            r = json.loads(line)
            persons = [o for o in r['data']['objs'] if o['cls_id'] == 30]
            if not persons:
                continue

            # Get drone state at detection time
            idx = min(bisect.bisect_left(osd_times, r['arrival_ts']), len(osd) - 1)
            drone = osd[idx]['data']

            # Check rule against closest person
            min_status = None
            for p in persons:
                status = check_1to1_rule(
                    drone['latitude'], drone['longitude'], drone['height'],
                    p['pos']['latitude'], p['pos']['longitude'],
                    safety_value,
                )
                status.timestamp_utc = datetime.fromtimestamp(
                    r['arrival_ts'], tz=timezone.utc).isoformat()
                status.num_persons = len(persons)
                if min_status is None or status.lateral_distance_m < min_status.lateral_distance_m:
                    min_status = status

            if min_status:
                results.append(min_status)

    return results


def live_monitor(broker: str, port: int, safety_value: float):
    """Subscribe to MQTT and monitor 1:1 rule in real time.

    Expects Autel cloud MQTT topics:
      - thing/product/+/osd (drone position, 1Hz)
      - thing/product/+/state (detections with method=target_detect_result_report)
    """
    import paho.mqtt.client as mqtt

    drone_state = {'lat': 0, 'lon': 0, 'alt': 0}

    def on_connect(client, userdata, flags, rc, properties=None):
        print(f'Connected to {broker}:{port} (rc={rc})')
        client.subscribe('thing/product/+/osd')
        client.subscribe('thing/product/+/state')

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload)
        except json.JSONDecodeError:
            return

        topic = msg.topic

        # Drone OSD — update position
        if '/osd' in topic and 'latitude' in payload.get('data', {}):
            d = payload['data']
            drone_state['lat'] = d['latitude']
            drone_state['lon'] = d['longitude']
            drone_state['alt'] = d['height']

        # Detection report — check for persons
        if '/state' in topic and payload.get('method') == 'target_detect_result_report':
            persons = [o for o in payload['data'].get('objs', []) if o['cls_id'] == 30]
            if not persons or drone_state['alt'] < 2:
                return

            for p in persons:
                status = check_1to1_rule(
                    drone_state['lat'], drone_state['lon'], drone_state['alt'],
                    p['pos']['latitude'], p['pos']['longitude'], safety_value,
                )
                symbol = '🚨' if status.violation else '✅'
                print(f'{symbol} {status.timestamp_utc[11:19]} | '
                      f'alt={status.altitude_m:.0f}m | '
                      f'lateral={status.lateral_distance_m:.1f}m | '
                      f'ratio={status.ratio:.2f}x | '
                      f'persons={len(persons)}')

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f'1:1 Rule Live Monitor — Patent WO2025034145A1')
    print(f'  Broker: {broker}:{port} | Safety value: {safety_value}x')
    print(f'  Waiting for drone telemetry...')

    client.connect(broker, port)
    client.loop_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='1:1 Rule Monitor (Patent WO2025034145A1)')
    parser.add_argument('--detections', default='data/autel_mqtt_20260612/detections.jsonl')
    parser.add_argument('--osd', default='data/autel_mqtt_20260612/osd_drone.jsonl')
    parser.add_argument('--safety-value', type=float, default=1.0, help='Multiplier (>=1)')
    parser.add_argument('--summary', action='store_true', help='Print summary only')
    parser.add_argument('--live', action='store_true', help='Subscribe to MQTT broker')
    parser.add_argument('--broker', default='localhost', help='MQTT broker host')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    args = parser.parse_args()

    if args.live:
        live_monitor(args.broker, args.port, args.safety_value)
    else:
        results = replay_from_jsonl(args.detections, args.osd, args.safety_value)

        violations = [r for r in results if r.violation]
        passes = [r for r in results if not r.violation]

        if args.summary:
            print(f'1:1 Rule Monitor — Patent WO2025034145A1')
            print(f'  Safety value: {args.safety_value}x')
            print(f'  Measurements: {len(results)}')
            print(f'  Violations: {len(violations)} ({100*len(violations)/len(results):.0f}%)')
            print(f'  Passes: {len(passes)} ({100*len(passes)/len(results):.0f}%)')
            print(f'  Min lateral: {min(r.lateral_distance_m for r in results):.1f}m')
            print(f'  Max lateral: {max(r.lateral_distance_m for r in results):.1f}m')
            print(f'  Min ratio: {min(r.ratio for r in results):.2f}x')
        else:
            print(f'{"Time":>12} | {"Alt":>5} | {"Lat.Dist":>8} | {"Ratio":>6} | Status')
            print('-' * 52)
            last_ts = 0
            for r in results:
                ts = datetime.fromisoformat(r.timestamp_utc).timestamp()
                if ts - last_ts < 2:
                    continue
                last_ts = ts
                t = r.timestamp_utc[11:19]
                status = '✗ VIOL' if r.violation else '✓ PASS'
                print(f'{t:>12} | {r.altitude_m:>5.1f} | {r.lateral_distance_m:>7.1f}m | {r.ratio:>5.2f}x | {status}')
