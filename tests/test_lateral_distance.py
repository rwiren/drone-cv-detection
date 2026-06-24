"""Unit tests for src/lateral_distance.py — pure math functions only."""
from __future__ import annotations

import sys
import os
import math
import pytest

# Allow importing from src/ without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lateral_distance import calculate_lateral_distance, parse_srt


# Common sensor parameters (Autel MAX 4T V2 xe RGB)
PARAMS = dict(
    image_width_px=4000,
    image_height_px=3000,
    focal_len_mm=9.1,
    sensor_width_mm=7.68,
    sensor_height_mm=5.76,
    altitude_m=50.0,
)


# ---------------------------------------------------------------------------
# calculate_lateral_distance
# ---------------------------------------------------------------------------

class TestCalculateLateralDistanceGSD:
    """Tests for GSD (near-nadir) path (|pitch| < 15°)."""

    def test_image_center_returns_near_zero(self):
        """Nadir camera pointing straight down, object at image centre → ~0 lateral."""
        dist, method = calculate_lateral_distance(
            bbox_center_x=2000.0,
            bbox_center_y=1500.0,
            gimbal_pitch_deg=0.0,
            **PARAMS,
        )
        assert method == 'GSD'
        assert dist == pytest.approx(0.0, abs=1.0)

    def test_altitude_scaling(self):
        """Doubling altitude should ~double the lateral distance (GSD path)."""
        base = dict(bbox_center_x=2500.0, bbox_center_y=1500.0, gimbal_pitch_deg=0.0,
                    image_width_px=4000, image_height_px=3000,
                    focal_len_mm=9.1, sensor_width_mm=7.68, sensor_height_mm=5.76)
        dist50, _ = calculate_lateral_distance(**base, altitude_m=50.0)
        dist100, _ = calculate_lateral_distance(**base, altitude_m=100.0)
        assert dist100 == pytest.approx(dist50 * 2, rel=0.05)

    def test_returns_positive_distance(self):
        """Lateral distance must always be non-negative."""
        for cx in [500, 1000, 2000, 3000, 3500]:
            dist, _ = calculate_lateral_distance(
                bbox_center_x=float(cx), bbox_center_y=1500.0,
                gimbal_pitch_deg=0.0, **PARAMS,
            )
            assert dist >= 0, f"Negative distance at cx={cx}: {dist}"

    def test_symmetric(self):
        """Object equidistant left/right from centre should give same distance."""
        left, _ = calculate_lateral_distance(
            bbox_center_x=2000.0 - 500.0, bbox_center_y=1500.0,
            gimbal_pitch_deg=0.0, **PARAMS,
        )
        right, _ = calculate_lateral_distance(
            bbox_center_x=2000.0 + 500.0, bbox_center_y=1500.0,
            gimbal_pitch_deg=0.0, **PARAMS,
        )
        assert left == pytest.approx(right, rel=0.01)


class TestCalculateLateralDistanceRay:
    """Tests for RAY fallback path (|pitch| >= 15°, no bbox_height_px)."""

    def test_ray_method_label(self):
        dist, method = calculate_lateral_distance(
            bbox_center_x=2000.0, bbox_center_y=1500.0,
            gimbal_pitch_deg=-45.0,
            **PARAMS,
        )
        assert method == 'RAY'

    def test_ray_positive_distance(self):
        dist, method = calculate_lateral_distance(
            bbox_center_x=2200.0, bbox_center_y=1600.0,
            gimbal_pitch_deg=-30.0,
            **PARAMS,
        )
        assert dist > 0
        assert math.isfinite(dist)


class TestCalculateLateralDistanceEQ10:
    """Tests for EQ10 (patent formula, |pitch| >= 15°, bbox_height provided)."""

    def test_eq10_method_label(self):
        dist, method = calculate_lateral_distance(
            bbox_center_x=2000.0, bbox_center_y=1500.0,
            gimbal_pitch_deg=-45.0,
            bbox_height_px=120.0,
            object_height_m=1.7,
            **PARAMS,
        )
        assert method == 'EQ10'

    def test_eq10_positive_distance(self):
        dist, _ = calculate_lateral_distance(
            bbox_center_x=2000.0, bbox_center_y=1500.0,
            gimbal_pitch_deg=-45.0,
            bbox_height_px=120.0,
            **PARAMS,
        )
        assert dist > 0
        assert math.isfinite(dist)


# ---------------------------------------------------------------------------
# parse_srt
# ---------------------------------------------------------------------------

SRT_SAMPLE = """\
1
00:00:00,033 --> 00:00:00,066
<font size="28">FrameCnt: 1, DiffTime: 33ms
2026-06-12 14:23:01.033
[focal_len:91] [latitude: 60.123456] [longitude: 24.567890] [rel_alt: 80.50] [Pitch:-90.0] [Yaw:45.0]</font>

2
00:00:00,066 --> 00:00:00,099
<font size="28">FrameCnt: 2, DiffTime: 33ms
2026-06-12 14:23:01.066
[focal_len:91] [latitude: 60.123460] [longitude: 24.567895] [rel_alt: 81.00] [Pitch:-89.0] [Yaw:46.0]</font>

"""


class TestParseSrt:
    def test_returns_list(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(SRT_SAMPLE)
        frames = parse_srt(str(srt_file))
        assert isinstance(frames, list)

    def test_correct_frame_count(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(SRT_SAMPLE)
        frames = parse_srt(str(srt_file))
        assert len(frames) == 2

    def test_fields_present(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(SRT_SAMPLE)
        frames = parse_srt(str(srt_file))
        f = frames[0]
        for field in ('lat', 'lon', 'altitude'):
            assert field in f, f"Missing field: {field}"

    def test_correct_values(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(SRT_SAMPLE)
        frames = parse_srt(str(srt_file))
        f = frames[0]
        assert f['lat'] == pytest.approx(60.123456, rel=1e-5)
        assert f['lon'] == pytest.approx(24.567890, rel=1e-5)
        assert f['altitude'] == pytest.approx(80.5, rel=1e-3)

    def test_empty_file(self, tmp_path):
        srt_file = tmp_path / "empty.SRT"
        srt_file.write_text("")
        frames = parse_srt(str(srt_file))
        assert frames == []
