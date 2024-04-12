"""
© Ocado Group
Created on 08/02/2024 at 13:01:42(+00:00).
"""

from unittest.mock import Mock, patch

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import (
    AdminSchoolTeacher,
    SchoolTeacher,
    Teacher,
    TeacherUser,
    User,
)
from django.contrib.auth.hashers import make_password

from .teacher import (
    CreateTeacherSerializer,
    RemoveTeacherFromSchoolSerializer,
    SetSchoolTeacherAdminAccessSerializer,
)

# pylint: disable=missing-class-docstring


class TestCreateTeacherSerializer(ModelSerializerTestCase[User, Teacher]):
    model_serializer_class = CreateTeacherSerializer

    @patch.object(TeacherUser, "add_contact_to_dot_digital")
    def test_create(self, add_contact_to_dot_digital: Mock):
        """Can successfully create a teacher."""
        password = "N3wPassword!"

        with patch(
            "django.contrib.auth.models.make_password",
            return_value=make_password(password),
        ) as user_make_password:
            self.assert_create(
                validated_data={
                    "new_user": {
                        "first_name": "Luke",
                        "last_name": "Skywalker",
                        "password": password,
                        "email": "luke.skywalker@jedi.academy",
                        "add_to_newsletter": True,
                    }
                },
                new_data={
                    "new_user": {"password": user_make_password.return_value}
                },
                non_model_fields={"new_user": ["add_to_newsletter"]},
            )

            user_make_password.assert_called_once_with(password)
        add_contact_to_dot_digital.assert_called_once()


class TestRemoveTeacherFromSchoolSerializer(
    ModelSerializerTestCase[User, SchoolTeacher]
):
    model_serializer_class = RemoveTeacherFromSchoolSerializer
    fixtures = ["school_1", "school_3"]

    def setUp(self):
        self.admin_school_1_teacher = AdminSchoolTeacher.objects.get(
            new_user__email="admin.teacher@school1.com"
        )
        self.admin_school_3_teacher = AdminSchoolTeacher.objects.get(
            new_user__email="admin.teacher@school3.com"
        )

    def test_validate__has_classes(self):
        """A teacher with classes cannot leave the school."""
        teacher = self.admin_school_1_teacher
        assert teacher.classes.exists()

        self.assert_validate(
            attrs={},
            error_code="has_classes",
            instance=teacher,
        )

    def test_validate__last_admin(self):
        """The last admin in a school cannot leave the school."""
        teacher = self.admin_school_3_teacher
        assert (
            not AdminSchoolTeacher.objects.exclude(pk=teacher.pk)
            .filter(school=teacher.school)
            .exists()
        )

        self.assert_validate(
            attrs={},
            error_code="last_admin",
            instance=teacher,
        )

    def test_update(self):
        """A teacher can be successfully removed from a school."""
        self.assert_update(
            instance=self.admin_school_1_teacher,
            validated_data={},
            new_data={"school": None},
        )


class TestSetSchoolTeacherAdminAccessSerializer(
    ModelSerializerTestCase[User, SchoolTeacher]
):
    model_serializer_class = SetSchoolTeacherAdminAccessSerializer
    fixtures = ["school_1"]

    def setUp(self):
        self.admin_school_teacher = AdminSchoolTeacher.objects.get(
            new_user__email="admin.teacher@school1.com"
        )

    def test_validate_is_admin__last(self):
        """There must be at least one admin in a school."""
        teacher = self.admin_school_teacher
        assert (
            not AdminSchoolTeacher.objects.exclude(pk=teacher.pk)
            .filter(school=teacher.school)
            .exists()
        )
        self.assert_validate_field(
            name="is_admin",
            value=False,
            error_code="last",
            instance=teacher,
        )
