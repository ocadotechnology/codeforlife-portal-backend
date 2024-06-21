"""
© Ocado Group
Created on 22/03/2024 at 13:48:22(+00:00).
"""

import typing as t
from unittest.mock import Mock, patch

from codeforlife.permissions import AllowAny
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    Class,
    NonAdminSchoolTeacherUser,
    SchoolTeacherUser,
    Student,
    Teacher,
    TeacherUser,
    User,
)
from codeforlife.user.permissions import IsTeacher
from django.contrib.auth.hashers import make_password
from django.db.models.query import QuerySet
from rest_framework import status

from ..serializers import (
    CreateTeacherSerializer,
    RemoveTeacherFromSchoolSerializer,
    SetSchoolTeacherAdminAccessSerializer,
)
from .teacher import TeacherViewSet

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors
# pylint: disable=too-many-public-methods


class TestTeacherViewSet(ModelViewSetTestCase[User, Teacher]):
    basename = "teacher"
    model_view_set_class = TeacherViewSet
    fixtures = ["school_1", "school_3"]

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )
        self.non_admin_school_1_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school1.com")
        )
        self.non_admin_school_3_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school3.com")
        )

    # assertion helpers

    def assert_user_is_anonymized(self, user: TeacherUser):
        """Assert user has been anonymized.

        Args:
            user: The user to assert.
        """
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.email == ""
        assert not user.is_active

    def assert_classes_are_anonymized(
        self,
        school_teacher_user: SchoolTeacherUser,
        class_names: t.Iterable[str],
    ):
        """Assert the classes and their students have been anonymized.

        Args:
            school_teacher_user: The user the classes belong to.
            class_names: The original class names.
        """
        # TODO: remove when using new data strategy
        queryset = QuerySet(
            model=Class.objects.model,
            # pylint: disable-next=protected-access
            using=Class.objects._db,
            # pylint: disable-next=protected-access
            hints=Class.objects._hints,
        ).filter(teacher=school_teacher_user.teacher)

        for klass, name in zip(queryset, class_names):
            assert klass.name != name
            assert klass.access_code == ""
            assert not klass.is_active

            student: Student  # TODO: delete in new data schema
            for student in klass.students.all():
                self.assert_user_is_anonymized(student.new_user)

    # test: get permissions

    def test_get_permissions__create(self):
        """Anyone can create a teacher-user."""
        self.assert_get_permissions(
            permissions=[AllowAny()],
            action="create",
        )

    def test_get_permissions__destroy(self):
        """Only teachers can destroy a teacher."""
        self.assert_get_permissions(
            permissions=[IsTeacher()],
            action="destroy",
        )

    def test_get_permissions__remove_from_school(self):
        """Only school-teachers can be removed from a school."""
        self.assert_get_permissions(
            permissions=[IsTeacher(in_school=True)],
            action="remove_from_school",
        )

    def test_get_permissions__set_admin_access(self):
        """Only admin-teachers can set a teacher's admin access."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="set_admin_access",
        )

    # test: get queryset

    def test_get_queryset__destroy(self):
        """Teachers can only delete themselves."""
        user = self.admin_school_teacher_user
        self.assert_get_queryset(
            values=[user.teacher],
            action="destroy",
            request=self.client.request_factory.delete(user=user),
        )

    def test_get_queryset__remove_from_school__admin(self):
        """Admin-teachers can remove all other teachers from their school."""
        user = self.admin_school_teacher_user
        self.assert_get_queryset(
            values=user.teacher.school_teachers,
            action="remove_from_school",
            request=self.client.request_factory.put(user=user),
        )

    def test_get_queryset__remove_from_school__non_admin(self):
        """Non-admin-teachers can only remove themselves from their school."""
        user = self.non_admin_school_1_teacher_user
        self.assert_get_queryset(
            values=[user.teacher],
            action="remove_from_school",
            request=self.client.request_factory.put(user=user),
        )

    def test_get_queryset__set_admin_access(self):
        """
        Admin-teachers can set the admin access of all other teachers in their
        school.
        """
        user = self.admin_school_teacher_user
        self.assert_get_queryset(
            values=user.teacher.school_teachers,
            action="set_admin_access",
            request=self.client.request_factory.put(user=user),
        )

    # test: get serializer context

    def test_get_serializer_context__create(self):
        """Need to give context to the type of user being created."""
        self.assert_get_serializer_context(
            serializer_context={"user_type": "teacher"},
            action="create",
        )

    # test: get serializer class

    def test_get_serializer_class__create(self):
        """Creating a teacher has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=CreateTeacherSerializer,
            action="create",
        )

    def test_get_serializer_class__remove_from_school(self):
        """Removing a teacher from a school has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=RemoveTeacherFromSchoolSerializer,
            action="remove_from_school",
        )

    def test_get_serializer_class__set_admin_access(self):
        """Setting a teacher's admin access has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=SetSchoolTeacherAdminAccessSerializer,
            action="set_admin_access",
        )

    # test: actions

    @patch.object(TeacherUser, "add_contact_to_dot_digital")
    def test_create(self, add_contact_to_dot_digital: Mock):
        """Can create a teacher."""
        password = "N3wPassword!"

        with patch(
            "django.contrib.auth.models.make_password",
            return_value=make_password(password),
        ) as user_make_password:
            self.client.create(
                data={
                    "user": {
                        "first_name": "Peter",
                        "last_name": "Parker",
                        "password": password,
                        "email": "peter.parker@spider.man",
                        "add_to_newsletter": True,
                    }
                },
                make_assertions=False,
            )

            user_make_password.assert_called_once_with(password)
        add_contact_to_dot_digital.assert_called_once()

    def test_remove_from_school(self):
        """Can remove a teacher from a school."""
        user = self.non_admin_school_3_teacher_user

        self.client.login_as(user)
        self.client.update(user.teacher, action="remove_from_school")

        assert user.teacher.school is None

    def test_set_admin_access(self):
        """Can set the admin access of a teacher in the same school."""
        admin_school_teacher = self.admin_school_teacher_user.teacher
        non_admin_school_teacher = self.non_admin_school_1_teacher_user.teacher
        assert admin_school_teacher.school == non_admin_school_teacher.school

        self.client.login_as(admin_school_teacher.new_user)
        self.client.update(
            non_admin_school_teacher,
            data={"is_admin": True},
            action="set_admin_access",
        )

        assert non_admin_school_teacher.is_admin

    def _test_destroy(
        self,
        user: TeacherUser,
        status_code_assertion: int = status.HTTP_204_NO_CONTENT,
    ):
        self.client.login_as(user)
        self.client.destroy(
            user.teacher,
            status_code_assertion=status_code_assertion,
            make_assertions=False,
        )

    def test_destroy(self):
        """Class-teachers can anonymize themselves and their classes."""
        user = self.non_admin_school_1_teacher_user
        assert user.teacher.class_teacher.exists()
        class_names = list(
            user.teacher.class_teacher.values_list("name", flat=True)
        )

        self._test_destroy(user)
        user.refresh_from_db()
        self.assert_user_is_anonymized(user)
        self.assert_classes_are_anonymized(user, class_names)

    def test_destroy__last_teacher(self):
        """
        School-teacher-users can anonymize themselves and their school if they
        are the last teacher.
        """
        user = self.admin_school_teacher_user
        assert user.teacher.class_teacher.exists()
        class_names = list(
            user.teacher.class_teacher.values_list("name", flat=True)
        )
        school_name = user.teacher.school.name

        SchoolTeacherUser.objects.filter(
            new_teacher__school=user.teacher.school
        ).exclude(pk=user.pk).delete()

        self._test_destroy(user)
        user.refresh_from_db()
        self.assert_user_is_anonymized(user)
        self.assert_classes_are_anonymized(user, class_names)
        assert user.teacher.school.name != school_name
        assert not user.teacher.school.is_active

    def test_destroy__last_admin_teacher(self):
        """
        School-teacher-users cannot anonymize themselves if they are the last
        admin teachers.
        """
        self._test_destroy(
            self.admin_school_teacher_user,
            status_code_assertion=status.HTTP_409_CONFLICT,
        )
