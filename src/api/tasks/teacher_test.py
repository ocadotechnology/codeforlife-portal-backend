"""
© Ocado Group
Created on 23/10/2025 at 14:29:26(+01:00).
"""

from codeforlife.tests import CeleryTestCase

from .teacher import classes_per_teacher

# pylint: disable=missing-class-docstring


class TestTeacher(CeleryTestCase):
    fixtures = ["school_1"]

    def test_classes_per_teacher(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=classes_per_teacher)
