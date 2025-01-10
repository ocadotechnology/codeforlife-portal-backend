"""
© Ocado Group
Created on 02/02/2024 at 15:38:51(+00:00).
"""

import typing as t

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    NonSchoolTeacherUser,
    School,
    User,
)

from ..views.school import SchoolViewSet
from .school import SchoolSerializer

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class TestSchoolSerializer(ModelSerializerTestCase[User, School]):
    model_serializer_class = SchoolSerializer
    fixtures = ["school_1", "non_school_teacher"]

    def setUp(self):
        self.school_1 = School.objects.get(pk=2)

        non_school_teacher_user = NonSchoolTeacherUser.objects.first()
        assert non_school_teacher_user
        self.non_school_teacher_user = non_school_teacher_user

    def test_validate__country_ne_gb(self):
        """
        Setting a UK county raises an error if the country does not equal GB.
        """

        self.assert_validate(
            attrs={
                "uk_county": "Surrey",
                "country": "AF",
            },
            error_code="country_ne_gb",
            context={"view": SchoolViewSet(action="create")},
        )

    def test_validate_name__name_not_unique(self):
        """
        School names must be unique.
        """

        self.assert_validate_field(
            name="name",
            value=self.school_1.name,
            error_code="name_not_unique",
        )

    def test_create(self):
        """Can successfully create a school."""
        user = self.non_school_teacher_user

        self.assert_create(
            validated_data={
                "name": "Test School",
                "country": "CY",
            },
            context={"request": self.request_factory.post(user=user)},
            new_data={"county": None},
        )

        user = t.cast(AdminSchoolTeacherUser, user)  # type: ignore[assignment]
        user.teacher.refresh_from_db()
        assert user.teacher.school
        assert user.teacher.is_admin
