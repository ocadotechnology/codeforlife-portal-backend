"""
© Ocado Group
Created on 03/04/2024 at 11:41:36(+01:00).
"""

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import Class

from ..models import Level, User
from .level import LockLevelSerializer

# pylint: disable=missing-class-docstring


class TestLockLevelSerializer(ModelSerializerTestCase[User, Level]):
    model_serializer_class = LockLevelSerializer

    def setUp(self):
        klass = Class.objects.first()
        assert klass
        self.klass = klass

        self.level_1 = Level.objects.get(pk=1)
        self.level_2 = Level.objects.get(pk=2)

    # TODO: test this once access_code is changed to id in new schema.
    # def test_update_many(self):
    #     """Locks the levels for a specified class."""
    #     levels = [self.level_1, self.level_2]

    #     self.assert_update_many(
    #         instance=levels,
    #         validated_data=[
    #             {"locked_for_class": [self.klass.access_code]}
    #             for _ in range(len(levels))
    #         ],
    #     )
