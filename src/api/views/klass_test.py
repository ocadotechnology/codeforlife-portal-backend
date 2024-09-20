"""
© Ocado Group
Created on 05/02/2024 at 16:13:46(+00:00).
"""

import typing as t
from datetime import timedelta

from codeforlife.permissions import OR, AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import AdminSchoolTeacherUser, Class, Teacher, User
from codeforlife.user.permissions import IsStudent, IsTeacher
from django.utils import timezone
from rest_framework import status

from ..serializers import ReadClassSerializer, WriteClassSerializer
from .klass import ClassViewSet


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class TestClassViewSet(ModelViewSetTestCase[User, Class]):
    basename = "class"
    model_view_set_class = ClassViewSet
    fixtures = ["school_1"]

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )
        self.empty_class = Class.objects.get(name="Class 3 @ School 1")

    # test: get permissions

    def test_get_permissions__bulk__create(self):
        """No one is allowed to bulk create."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="bulk",
            request=self.client.request_factory.post(),
        )

    def test_get_permissions__bulk__partial_update(self):
        """Only admin-teachers or class-teachers can bulk partial-update."""
        self.assert_get_permissions(
            permissions=[
                OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))
            ],
            action="bulk",
            request=self.client.request_factory.patch(),
        )

    def test_get_permissions__bulk__destroy(self):
        """No one is allowed to bulk destroy."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="bulk",
            request=self.client.request_factory.delete(),
        )

    def test_get_permissions__create(self):
        """Only school-teachers can create a class."""
        self.assert_get_permissions(
            permissions=[IsTeacher(in_school=True)],
            action="create",
        )

    def test_get_permissions__partial_update(self):
        """Only admin-teachers or class-teachers can update a class."""
        self.assert_get_permissions(
            permissions=[
                OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))
            ],
            action="partial_update",
        )

    def test_get_permissions__destroy(self):
        """Only admin-teachers or class-teachers can destroy a class."""
        self.assert_get_permissions(
            permissions=[
                OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))
            ],
            action="destroy",
        )

    def test_get_permissions__list(self):
        """Only admin-teachers and class-teachers can list classes."""
        self.assert_get_permissions(
            permissions=[IsTeacher(in_school=True)],
            action="list",
        )

    def test_get_permissions__retrieve(self):
        """
        Only students, admin-teachers or class-teachers can retrieve a class.
        """
        self.assert_get_permissions(
            permissions=[OR(IsStudent(), IsTeacher(in_school=True))],
            action="retrieve",
        )

    # test: get serializer class

    def test_get_serializer_class__create(self):
        """Creating a class has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=WriteClassSerializer,
            action="create",
        )

    def test_get_serializer_class__partial_update(self):
        """Partially updating a class has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=WriteClassSerializer,
            action="partial_update",
        )

    def test_get_serializer_class__retrieve(self):
        """Retrieving a class has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=ReadClassSerializer,
            action="retrieve",
        )

    def test_get_serializer_class__list(self):
        """Listing classes has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=ReadClassSerializer,
            action="list",
        )

    # test: default actions

    def test_create__self(self):
        """Teacher can create a class with themselves as the class owner."""
        user = self.admin_school_teacher_user

        self.client.login_as(user)
        self.client.create(
            {
                "name": "ExampleClass",
                "school": user.teacher.school.id,
                "read_classmates_data": False,
                "receive_requests_until": timezone.now() + timedelta(days=1),
            },
        )

    def test_create__other(self):
        """
        Admin-teacher can create a class with another teacher as the class
        owner.
        """
        user = self.admin_school_teacher_user
        teacher = (
            Teacher.objects.filter(school=user.teacher.school)
            .exclude(pk=user.teacher.pk)
            .first()
        )
        assert teacher

        self.client.login_as(user)
        self.client.create(
            {
                "name": "ExampleClass",
                "school": user.teacher.school.id,
                "read_classmates_data": False,
                "receive_requests_until": timezone.now() + timedelta(days=1),
                "teacher": teacher.id,
            },
        )

    def test_partial_update__teacher(self):
        """Teacher can transfer a class to another teacher."""
        user = self.admin_school_teacher_user
        klass = t.cast(t.Optional[Class], user.teacher.class_teacher.first())
        assert klass

        teacher = t.cast(
            Teacher,
            user.teacher.school.teacher_school.exclude(
                pk=user.teacher.pk
            ).first(),
        )
        assert teacher

        self.client.login_as(user)
        self.client.partial_update(model=klass, data={"teacher": teacher.pk})

    def test_destroy__has_students(self):
        """Teacher cannot delete a class that still has students."""
        user = self.admin_school_teacher_user
        klass = user.teacher.class_teacher.first()
        assert klass

        self.client.login_as(user)
        self.client.destroy(
            model=klass, status_code_assertion=status.HTTP_409_CONFLICT
        )

    def test_destroy(self):
        """Teacher can delete a class that has no students."""
        self.client.login_as(self.admin_school_teacher_user)
        self.client.destroy(model=self.empty_class)
