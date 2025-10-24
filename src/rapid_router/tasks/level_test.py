"""
© Ocado Group
Created on 24/10/2025 at 14:03:00(+01:00).
"""

from codeforlife.tests import CeleryTestCase

from .level import (
    game_level_shared_with,
    level_control_submits,
    rapid_router_attempts,
)

# pylint: disable=missing-class-docstring


class TestLevel(CeleryTestCase):
    fixtures = ["school_1"]

    def test_rapid_router_attempts(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=rapid_router_attempts)

    def test_game_level_shared_with(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=game_level_shared_with)

    def test_level_control_submits(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=level_control_submits)
