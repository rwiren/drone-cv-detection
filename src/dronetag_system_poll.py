"""
DroneTag System Telemetry Poller
Polls REST API for device diagnostics (LTE, GNSS, battery) alongside MQTT position data.

Usage:
  export DRONETAG_API_TOKEN="your-token-here"
  python dronetag_system_poll.py --device-id 1596F28F3E7548C3E849 --interval 5 --duration 300
"""
from __future__ import annotations

import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime

from logging_utils import get_logger

log = get_logger(__name__)


def poll_device_telemetry(api_token, device_id):
    """Poll DroneTag REST API for system telemetry."""
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"https://api.dronetag.com/v1/devices/{device_id}/telemetry"
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": resp.status_code, "msg": resp.text[:200]}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="DroneTag System Telemetry Poller")
    parser.add_argument("--device-id", default="1596F28F3E7548C3E849")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval seconds")
    parser.add_argument("--duration", type=int, default=300, help="Total duration seconds")
    parser.add_argument("--output", default="/tmp/dronetag_system_telemetry.json")
    args = parser.parse_args()

    api_token = os.environ.get("DRONETAG_API_TOKEN")
    if not api_token:
        log.error("Set DRONETAG_API_TOKEN environment variable")
        log.error("  Get token from: https://app.dronetag.cz → Developer → API Keys")
        sys.exit(1)

    records = []
    start = time.time()
    log.info("Polling device %s every %ds for %ds", args.device_id, args.interval, args.duration)

    while time.time() - start < args.duration:
        data = poll_device_telemetry(api_token, args.device_id)
        record = {"poll_ts": time.time(), "poll_iso": datetime.utcnow().isoformat(), "data": data}
        records.append(record)

        if "error" not in data:
            lte = data.get("lte", {})
            gnss = data.get("gnss", {})
            batt = data.get("battery", {})
            log.info("[%s] GNSS: %s sats | LTE: RSRP=%s RSRQ=%s SNR=%s | Batt: %s%%",
                     datetime.now().strftime('%H:%M:%S'),
                     gnss.get('satellites', '?'),
                     lte.get('rsrp', '?'), lte.get('rsrq', '?'), lte.get('snr', '?'),
                     batt.get('percentage', '?'))
        else:
            log.warning("[%s] Error: %s", datetime.now().strftime('%H:%M:%S'), data)

        time.sleep(args.interval)

    with open(args.output, 'w') as f:
        json.dump(records, f, indent=2)
    log.info("Saved %d records to %s", len(records), args.output)


if __name__ == "__main__":
    main()
