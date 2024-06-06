"""
© Ocado Group
Created on 05/02/2024 at 15:31:59(+00:00).
"""

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import (
    Class,
    SchoolTeacher,
    SchoolTeacherUser,
    User,
)

from .klass import ClassSerializer

# pylint: disable=missing-class-docstring


class TestClassSerializer(ModelSerializerTestCase[User, Class]):
    model_serializer_class = ClassSerializer
    fixtures = ["school_1", "school_2"]

    def setUp(self):
        self.school_teacher_user = SchoolTeacherUser.objects.get(
            email="teacher@school1.com"
        )
        self.klass = Class.objects.get(name="Class 1 @ School 1")

    def test_validate_name__name_not_unique(self):
        """Class names must be unique per school."""
        user = self.school_teacher_user
        assert user.teacher.school == self.klass.teacher.school

        self.assert_validate_field(
            name="name",
            value=self.klass.name,
            error_code="name_not_unique",
            context={"request": self.request_factory.post(user=user)},
        )

    def test_validate_teacher__not_in_school(self):
        """Teacher must be in school."""
        user = self.school_teacher_user
        school_teacher = SchoolTeacher.objects.exclude(
            school=user.teacher.school
        ).first()
        assert school_teacher

        self.assert_validate_field(
            name="teacher",
            value=school_teacher,
            error_code="not_in_school",
            context={"request": self.request_factory.post(user=user)},
        )

    def test_update_many(self):
        """Can bulk update many classes."""
        school_teacher = self.school_teacher_user.teacher
        other_school_teacher = (
            SchoolTeacher.objects.filter(school=school_teacher.school)
            .exclude(pk=school_teacher.pk)
            .first()
        )
        assert other_school_teacher
        classes = school_teacher.classes.all()

        self.assert_update_many(
            instance=list(classes),
            validated_data=[
                {
                    "name": f"NewClassName{klass.pk}",
                    "teacher": other_school_teacher,
                }
                for klass in classes
            ],
        )

    def test_create__teacher(self):
        """Can successfully create with setting the teacher field."""
        self.assert_create(
            {
                "name": "ExampleClass",
                "teacher": self.school_teacher_user.teacher,
                "classmates_data_viewable": False,
            }
        )

    def test_create__no_teacher(self):
        """Can successfully create without setting the teacher field."""
        user = self.school_teacher_user

        self.assert_create(
            {
                "name": "ExampleClass",
                "classmates_data_viewable": False,
            },
            new_data={"teacher": user.teacher},
            context={"request": self.request_factory.post(user=user)},
        )
