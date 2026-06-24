"""Unit tests for src/avata360_monitor.py — pure numpy/cv2 functions only."""
from __future__ import annotations

import sys
import os
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import only pure functions — do NOT import YOLO-dependent entry points
from avata360_monitor import extract_perspective, parse_avata_srt


# ---------------------------------------------------------------------------
# extract_perspective
# ---------------------------------------------------------------------------

class TestExtractPerspective:
    """Tests for extract_perspective(dual_fisheye, ...) — pure numpy/cv2."""

    @pytest.fixture
    def dummy_frame(self):
        """1920×960 synthetic dual-fisheye frame (uniform noise)."""
        rng = np.random.default_rng(42)
        return rng.integers(0, 255, (960, 1920, 3), dtype=np.uint8)

    def test_output_shape_default(self, dummy_frame):
        """Default out_size=(640,480) → output must be (480, 640, 3)."""
        view = extract_perspective(dummy_frame)
        assert view.shape == (480, 640, 3)

    def test_output_shape_custom(self, dummy_frame):
        """Custom out_size is respected."""
        view = extract_perspective(dummy_frame, out_size=(320, 240))
        assert view.shape == (240, 320, 3)

    def test_output_dtype_uint8(self, dummy_frame):
        """Output must be uint8 (same as OpenCV frame)."""
        view = extract_perspective(dummy_frame)
        assert view.dtype == np.uint8

    def test_all_yaw_angles(self, dummy_frame):
        """All yaw angles 0–315° in 45° steps should produce a valid frame."""
        for yaw in range(0, 360, 45):
            view = extract_perspective(dummy_frame, yaw_deg=yaw)
            assert view.shape[2] == 3, f"yaw={yaw} produced non-3-channel output"

    def test_left_lens(self, dummy_frame):
        """Left lens (zenith) extraction should produce a valid frame."""
        view = extract_perspective(dummy_frame, lens='left')
        assert view.shape == (480, 640, 3)

    def test_right_lens(self, dummy_frame):
        """Right lens (nadir) extraction should produce a valid frame."""
        view = extract_perspective(dummy_frame, lens='right')
        assert view.shape == (480, 640, 3)


# ---------------------------------------------------------------------------
# parse_avata_srt
# ---------------------------------------------------------------------------

AVATA_SRT_SAMPLE = """\
1
00:00:00,000 --> 00:00:00,016
<font size="28">FrameCnt: 0, DiffTime: 16ms
2026-06-12 15:01:00.000
[iso: 400] [shutter: 1/2000] [fnum: 2.8] [ev: 0] [ct: 5500] [color_md: default] [focal_len: 0] [latitude: 60.123456] [longitude: 24.567890] [rel_alt: 50.000 abs_alt: 130.000] [gb_yaw: 45.0 gb_pitch: -70.0 gb_roll: 0.0]</font>

2
00:00:00,016 --> 00:00:00,033
<font size="28">FrameCnt: 1, DiffTime: 16ms
2026-06-12 15:01:00.016
[iso: 400] [shutter: 1/2000] [fnum: 2.8] [ev: 0] [ct: 5500] [color_md: default] [focal_len: 0] [latitude: 60.123460] [longitude: 24.567895] [rel_alt: 50.100 abs_alt: 130.100] [gb_yaw: 45.5 gb_pitch: -70.5 gb_roll: 0.0]</font>

"""


class TestParseAvataSrt:
    def test_returns_list(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(AVATA_SRT_SAMPLE)
        frames = parse_avata_srt(str(srt_file))
        assert isinstance(frames, list)

    def test_correct_frame_count(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(AVATA_SRT_SAMPLE)
        frames = parse_avata_srt(str(srt_file))
        assert len(frames) == 2

    def test_fields_present(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(AVATA_SRT_SAMPLE)
        frames = parse_avata_srt(str(srt_file))
        f = frames[0]
        for field in ('lat', 'lon', 'altitude'):
            assert field in f, f"Missing field: {field}"

    def test_correct_values(self, tmp_path):
        srt_file = tmp_path / "test.SRT"
        srt_file.write_text(AVATA_SRT_SAMPLE)
        frames = parse_avata_srt(str(srt_file))
        f = frames[0]
        assert f['lat'] == pytest.approx(60.123456, rel=1e-5)
        assert f['altitude'] == pytest.approx(50.0, rel=1e-3)

    def test_empty_file(self, tmp_path):
        srt_file = tmp_path / "empty.SRT"
        srt_file.write_text("")
        frames = parse_avata_srt(str(srt_file))
        assert frames == []
