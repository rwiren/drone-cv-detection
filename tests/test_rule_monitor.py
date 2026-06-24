"""Unit tests for src/rule_monitor.py — pure math functions only."""
from __future__ import annotations

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rule_monitor import check_1to1_rule, RuleStatus


class TestCheck1to1Rule:
    """Tests for check_1to1_rule(drone_lat, drone_lon, drone_alt, person_lat, person_lon, ...)."""

    # Reference location: Jorvas, Finland
    DRONE_LAT = 60.1234
    DRONE_LON = 24.5678
    ALT = 50.0

    def test_person_at_drone_position_is_violation(self):
        """Person directly below drone → lateral=0 → ratio=0 → violation."""
        status = check_1to1_rule(
            self.DRONE_LAT, self.DRONE_LON, self.ALT,
            self.DRONE_LAT, self.DRONE_LON,
        )
        assert status.violation is True
        assert status.lateral_distance_m == pytest.approx(0.0, abs=0.1)
        assert status.ratio == pytest.approx(0.0, abs=0.01)

    def test_person_far_away_is_pass(self):
        """Person 100 m away at 50 m altitude → ratio=2.0 → not a violation."""
        # ~100 m north  ≈  100 / 111320 degrees latitude
        person_lat = self.DRONE_LAT + (100.0 / 111320)
        status = check_1to1_rule(
            self.DRONE_LAT, self.DRONE_LON, self.ALT,
            person_lat, self.DRONE_LON,
        )
        assert status.violation is False
        assert status.lateral_distance_m == pytest.approx(100.0, rel=0.02)

    def test_boundary_equal_ratio(self):
        """Lateral == altitude → ratio == 1.0 → exactly at boundary → NOT a violation."""
        # Place person exactly altitude metres away
        person_lat = self.DRONE_LAT + (self.ALT / 111320)
        status = check_1to1_rule(
            self.DRONE_LAT, self.DRONE_LON, self.ALT,
            person_lat, self.DRONE_LON,
        )
        # ratio ≈ 1.0, violation = (ratio < 1.0) → False
        assert status.ratio == pytest.approx(1.0, abs=0.02)
        assert status.violation is False

    def test_custom_safety_value(self):
        """With safety_value=1.5 a person 60 m away at 50 m alt should violate."""
        person_lat = self.DRONE_LAT + (60.0 / 111320)
        status = check_1to1_rule(
            self.DRONE_LAT, self.DRONE_LON, self.ALT,
            person_lat, self.DRONE_LON,
            safety_value=1.5,
        )
        # ratio = 60/50 = 1.2 < 1.5 → violation
        assert status.violation is True
        assert status.ratio == pytest.approx(1.2, rel=0.02)

    def test_returns_rulestatus(self):
        """Return type must be RuleStatus."""
        status = check_1to1_rule(
            self.DRONE_LAT, self.DRONE_LON, self.ALT,
            self.DRONE_LAT, self.DRONE_LON,
        )
        assert isinstance(status, RuleStatus)

    def test_near_zero_altitude_does_not_crash(self):
        """Altitude < 1 m should return ratio=0 and not raise ZeroDivisionError."""
        status = check_1to1_rule(
            self.DRONE_LAT, self.DRONE_LON, 0.5,
            self.DRONE_LAT + (10.0 / 111320), self.DRONE_LON,
        )
        assert status.ratio == pytest.approx(0.0, abs=0.01)
