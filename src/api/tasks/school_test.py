"""
© Ocado Group
Created on 23/10/2025 at 17:13:51(+01:00).
"""

from codeforlife.tests import CeleryTestCase

from .school import common_school, teachers_per_school

# pylint: disable=missing-class-docstring


class TestSchool(CeleryTestCase):
    fixtures = ["school_1"]

    def test_common_school(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=common_school)

    def test_teachers_per_school(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=teachers_per_school)
