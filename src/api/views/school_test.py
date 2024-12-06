"""
© Ocado Group
Created on 02/02/2024 at 15:31:21(+00:00).
"""

import typing as t
from unittest.mock import PropertyMock, patch

from codeforlife.permissions import OR, AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    Class,
    NonSchoolTeacherUser,
    School,
    StudentUser,
    Teacher,
    User,
)
from codeforlife.user.permissions import IsIndependent, IsStudent, IsTeacher

from .school import SchoolViewSet


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class TestSchoolViewSet(ModelViewSetTestCase[User, School]):
    basename = "school"
    model_view_set_class = SchoolViewSet
    fixtures = ["non_school_teacher", "school_1"]

    def setUp(self):
        self.non_school_teacher_user = NonSchoolTeacherUser.objects.get(
            email="teacher@noschool.com"
        )
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )

    # test: get permissions

    def test_get_permissions__bulk(self):
        """No one is allowed to perform bulk actions."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="bulk",
        )

    def test_get_permissions__list(self):
        """No one is allowed to list schools."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="list",
        )

    def test_get_permissions__create(self):
        """Only teachers not in a school can create a school."""
        self.assert_get_permissions(
            permissions=[IsTeacher(in_school=False)],
            action="create",
        )

    def test_get_permissions__partial_update(self):
        """Only admin-teachers in a school can update a school."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="partial_update",
        )

    def test_get_permissions__retrieve(self):
        """Anyone in a school can retrieve a school."""
        self.assert_get_permissions(
            permissions=[
                OR(
                    OR(IsStudent(), IsTeacher(in_school=True)),
                    IsIndependent(is_requesting_to_join_class=True),
                )
            ],
            action="retrieve",
        )

    def test_get_permissions__destroy(self):
        """Only admin-teachers in a school can destroy a school."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="destroy",
        )

    # test: actions

    def test_create(self):
        """Can successfully create a school."""
        self.client.login_as(self.non_school_teacher_user)
        self.client.create(
            {
                "name": "ExampleSchool",
                "uk_county": "Surrey",
                "country": "GB",
            },
        )

    def test_partial_update(self):
        """Can successfully update a school."""
        user = self.admin_school_teacher_user

        self.client.login_as(user)
        self.client.partial_update(
            user.teacher.school,
            {
                "name": "NewSchoolName",
                "uk_county": "Surrey",
                "country": "GB",
            },
        )

    def test_destroy(self):
        """
        Can successfully anonymize a school, including all of its students,
        teachers and classes.
        """

        def assert_user_is_anonymized(user: User):
            assert user.first_name == ""
            assert user.last_name == ""
            assert user.email == ""
            assert user.username == ""
            assert not user.is_active

        user = self.admin_school_teacher_user
        school = user.teacher.school
        teachers: t.List[Teacher] = list(school.teacher_school.all())

        self.client.login_as(user)

        anonymized_name = "abc"
        with patch(
            "uuid.UUID.hex",
            new_callable=PropertyMock,
            return_value=anonymized_name,
        ):
            self.client.destroy(school)

        school.refresh_from_db()
        assert school.name == anonymized_name
        assert not school.is_active

        for klass in Class.objects.filter(teacher__school=school):
            for student_user in StudentUser.objects.filter(
                new_student__class_field=klass
            ):
                assert_user_is_anonymized(student_user)

            assert klass.name == anonymized_name
            assert klass.access_code == ""
            assert not klass.is_active

        for teacher in teachers:
            teacher.refresh_from_db()
            assert not teacher.school

        school.anonymise()
