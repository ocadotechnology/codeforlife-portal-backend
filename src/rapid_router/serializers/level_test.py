"""
© Ocado Group
Created on 03/04/2024 at 11:41:36(+01:00).
"""

import typing as t

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import Class, NonAdminSchoolTeacherUser

from ..models import Level, User
from .level import LockLevelListSerializer, LockLevelSerializer

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class TestLockLevelSerializer(ModelSerializerTestCase[User, Level]):
    model_serializer_class = LockLevelSerializer
    fixtures = ["school_1"]

    def setUp(self):
        klass = Class.objects.first()
        assert klass
        self.klass = klass

        self.non_admin_school_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school1.com")
        )

        self.level_1 = Level.objects.get(pk=1)
        self.level_2 = Level.objects.get(pk=2)
        self.level_3 = Level.objects.get(pk=3)

    def test_validate_locked_for_class__not_in_school(self):
        """Cannot lock a class in another school."""
        user = self.non_admin_school_teacher_user
        klass = Class.objects.exclude(
            teacher__school=user.teacher.school
        ).first()
        assert klass

        self.assert_validate_field(
            name="locked_for_class",
            error_code="not_in_school",
            value=[klass.access_code],
            context={
                "request": self.request_factory.put(user=t.cast(User, user))
            },
        )

    def test_validate_locked_for_class__not_class_teacher(self):
        """Cannot lock a class if teacher is not an admin or its teacher."""
        user = self.non_admin_school_teacher_user
        klass = (
            Class.objects.filter(teacher__school=user.teacher.school)
            .exclude(teacher=user.teacher)
            .first()
        )
        assert klass

        self.assert_validate_field(
            name="locked_for_class",
            error_code="not_class_teacher",
            value=[klass.access_code],
            context={
                "request": self.request_factory.put(user=t.cast(User, user))
            },
        )

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

        self.level_3.locked_for_class.add(self.klass)

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

        assert not self.level_3.locked_for_class.filter(
            pk=self.klass.pk
        ).exists()
