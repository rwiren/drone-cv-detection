"""Unit tests for src/autel_telemetry.py — pure math functions only."""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from autel_telemetry import correct_mqtt_bbox
from config import MQTT_THERMAL_CALIB


def bbox(x: float, y: float, w: float, h: float) -> dict:
    return {'x': x, 'y': y, 'w': w, 'h': h}


class TestCorrectMqttBbox:
    """Tests for correct_mqtt_bbox(bbox, target)."""

    def test_thermal_center_point(self):
        """Thermal detection at image centre should map near centre after correction."""
        cx, cy, w, h = correct_mqtt_bbox(bbox(0.5, 0.5, 0.1, 0.1), target='thermal')
        # cx = x_scale * 0.5 + x_offset
        assert cx == pytest.approx(MQTT_THERMAL_CALIB['x_scale'] * 0.5 + MQTT_THERMAL_CALIB['x_offset'], abs=0.01)
        # cy = y + y_offset
        assert cy == pytest.approx(0.5 + MQTT_THERMAL_CALIB['y_offset'], abs=0.01)

    def test_thermal_bbox_width_scales(self):
        """Thermal correction scales bbox width by x_scale."""
        _, _, w, h = correct_mqtt_bbox(bbox(0.5, 0.5, 0.2, 0.15), target='thermal')
        assert w == pytest.approx(0.2 * MQTT_THERMAL_CALIB['x_scale'], abs=0.01)
        assert h == pytest.approx(0.15, abs=0.01)

    def test_rgb_target(self):
        """RGB target should apply IR→RGB FOV scale correction and stay in [0,1]."""
        cx, cy, w, h = correct_mqtt_bbox(bbox(0.5, 0.5, 0.1, 0.1), target='rgb')
        assert 0.0 <= cx <= 1.0
        assert 0.0 <= cy <= 1.0

    def test_unknown_target_passthrough(self):
        """Unknown target should return original coordinates unchanged."""
        cx, cy, w, h = correct_mqtt_bbox(bbox(0.4, 0.6, 0.1, 0.08), target='unknown')
        assert cx == pytest.approx(0.4, abs=0.001)
        assert cy == pytest.approx(0.6, abs=0.001)
        assert w == pytest.approx(0.1, abs=0.001)
        assert h == pytest.approx(0.08, abs=0.001)

    def test_left_edge_shifts_right(self):
        """Thermal x near left edge: affine correction shifts x."""
        x_in = 0.1
        cx, _, _, _ = correct_mqtt_bbox(bbox(x_in, 0.5, 0.05, 0.05), target='thermal')
        expected = MQTT_THERMAL_CALIB['x_scale'] * x_in + MQTT_THERMAL_CALIB['x_offset']
        assert cx == pytest.approx(expected, abs=0.01)

    def test_right_edge_corrected(self):
        """Thermal x near right edge: scale < 1 means corrected x < original for large x."""
        x_in = 0.9
        cx, _, _, _ = correct_mqtt_bbox(bbox(x_in, 0.5, 0.05, 0.05), target='thermal')
        expected = MQTT_THERMAL_CALIB['x_scale'] * x_in + MQTT_THERMAL_CALIB['x_offset']
        assert cx == pytest.approx(expected, abs=0.01)
        assert cx < x_in, f"Right edge should compress: cx={cx:.3f} x_in={x_in}"
