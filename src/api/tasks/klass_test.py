"""
© Ocado Group
Created on 23/10/2025 at 16:37:07(+01:00).
"""

from codeforlife.tests import CeleryTestCase

from .klass import common_class, students_per_class

# pylint: disable=missing-class-docstring


class TestClass(CeleryTestCase):
    fixtures = ["school_1"]

    def test_students_per_class(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=students_per_class)

    def test_common_class(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=common_class)
