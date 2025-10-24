"""
© Ocado Group
Created on 24/10/2025 at 14:03:00(+01:00).
"""

from codeforlife.tests import CeleryTestCase

from .level import rapid_router_attempts

# pylint: disable=missing-class-docstring


class TestClass(CeleryTestCase):
    fixtures = ["school_1"]

    def test_rapid_router_attempts(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=rapid_router_attempts)
