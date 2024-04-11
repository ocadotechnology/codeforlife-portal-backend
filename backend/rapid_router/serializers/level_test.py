"""
© Ocado Group
Created on 03/04/2024 at 11:41:36(+01:00).
"""

import typing as t

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import Class

from ..models import Level, User
from .level import LockLevelListSerializer, LockLevelSerializer

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

    def test_update_many(self):
        """Locks the levels for a specified class."""
        levels = [self.level_1, self.level_2]
        for level in levels:
            assert not level.locked_for_class.filter(
                access_code=self.klass.access_code
            ).exists()

        serializer = t.cast(
            LockLevelListSerializer,
            LockLevelSerializer(instance=levels, many=True),
        )

        models = serializer.update(
            instance=levels,
            validated_data=[
                {"locked_for_class": [self.klass.access_code]}
                for _ in range(len(levels))
            ],
        )
        assert len(models) == len(levels)
        for level, model in zip(levels, models):
            assert level == model
            assert model.locked_for_class.filter(
                access_code=self.klass.access_code
            ).exists()
