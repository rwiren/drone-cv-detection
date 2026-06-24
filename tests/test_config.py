"""Sanity checks for src/config.py constants."""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import (
    OBJECT_HEIGHTS,
    AUTEL_RGB,
    AUTEL_THERMAL,
    M2EA_RGB,
    M2EA_THERMAL,
    MQTT_THERMAL_CALIB,
    MQTT_RGB_FOV_SCALE,
    COCO_VEHICLE_CLASSES,
    VISDRONE_CLASSES,
    CONF_DEFAULT,
    CONF_PERSON,
    CONF_VEHICLE,
    CONF_AERIAL,
)


class TestObjectHeights:
    def test_all_heights_positive(self):
        for label, h in OBJECT_HEIGHTS.items():
            assert h > 0, f"OBJECT_HEIGHTS[{label!r}] = {h} is not positive"

    def test_person_height_plausible(self):
        assert 1.5 <= OBJECT_HEIGHTS['pedestrian'] <= 2.0, \
            f"Pedestrian height {OBJECT_HEIGHTS['pedestrian']} outside plausible range"


class TestSensorSpecs:
    def test_autel_rgb_dimensions_consistent(self):
        """Pixel pitch derived from sensor width / image width should be consistent."""
        pixel_pitch_mm = AUTEL_RGB['sensor_width_mm'] / AUTEL_RGB['image_width_px']
        assert pixel_pitch_mm == pytest.approx(AUTEL_RGB['sensor_height_mm'] / AUTEL_RGB['image_height_px'], rel=0.1)

    def test_autel_thermal_pixel_pitch(self):
        """640×512 @ 12μm pitch: sensor dims should be ~7.68mm × 6.14mm."""
        expected_w = 640 * 0.012  # mm
        expected_h = 512 * 0.012
        assert AUTEL_THERMAL['sensor_width_mm'] == pytest.approx(expected_w, rel=0.02)
        assert AUTEL_THERMAL['sensor_height_mm'] == pytest.approx(expected_h, rel=0.02)

    def test_fov_values_positive(self):
        for spec in [AUTEL_RGB, AUTEL_THERMAL, M2EA_RGB]:
            assert spec['fov_h_deg'] > 0
        # M2EA_THERMAL may not have fov_h_deg — check what keys it has
        assert M2EA_THERMAL.get('fov_h_deg', 1) > 0

    def test_image_dimensions_positive(self):
        for spec in [AUTEL_RGB, AUTEL_THERMAL, M2EA_RGB, M2EA_THERMAL]:
            assert spec['image_width_px'] > 0
            assert spec['image_height_px'] > 0


class TestMqttCalibration:
    def test_thermal_calib_scale_in_range(self):
        """x_scale should be between 0.5 and 1.0 (compression, not expansion)."""
        assert 0.5 < MQTT_THERMAL_CALIB['x_scale'] < 1.0

    def test_thermal_calib_offsets_finite(self):
        import math
        assert math.isfinite(MQTT_THERMAL_CALIB['x_offset'])
        assert math.isfinite(MQTT_THERMAL_CALIB['y_offset'])

    def test_rgb_fov_scale_positive(self):
        assert MQTT_RGB_FOV_SCALE['sx'] > 0
        assert MQTT_RGB_FOV_SCALE['sy'] > 0


class TestClassMaps:
    def test_coco_vehicle_int_keys(self):
        for k in COCO_VEHICLE_CLASSES:
            assert isinstance(k, int), f"Expected int key, got {type(k)}"

    def test_visdrone_int_keys(self):
        for k in VISDRONE_CLASSES:
            assert isinstance(k, int), f"Expected int key, got {type(k)}"


class TestConfidenceThresholds:
    def test_all_between_zero_and_one(self):
        for name, val in [
            ('CONF_DEFAULT', CONF_DEFAULT),
            ('CONF_PERSON', CONF_PERSON),
            ('CONF_VEHICLE', CONF_VEHICLE),
            ('CONF_AERIAL', CONF_AERIAL),
        ]:
            assert 0.0 < val < 1.0, f"{name}={val} not in (0,1)"
