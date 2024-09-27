"""
© Ocado Group
Created on 03/04/2024 at 11:25:40(+01:00).
"""

import typing as t

from codeforlife.permissions import OR, AllowAny
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import Class, SchoolTeacherUser
from codeforlife.user.permissions import IsTeacher

from ..models import Level, User
from ..serializers import (
    ListLevelSerializer,
    LockLevelSerializer,
    RetrieveLevelSerializer,
)
from .level import LevelViewSet


# pylint: disable-next=too-many-ancestors,missing-class-docstring
class TestLevelViewSet(ModelViewSetTestCase[User, Level]):
    basename = "level"
    model_view_set_class = LevelViewSet
    fixtures = ["school_1", "custom_levels"]

    def setUp(self):
        self.level_1 = Level.objects.get(name="1")
        self.level_2 = Level.objects.get(name="2")
        self.school_teacher_user = SchoolTeacherUser.objects.get(
            email="teacher@school1.com"
        )

        user_with_custom_and_shared_levels = User.objects.filter(
            userprofile__levels__isnull=False,
            shared__isnull=False,
        ).first()
        assert user_with_custom_and_shared_levels
        self.user_with_custom_and_shared_levels = (
            user_with_custom_and_shared_levels
        )

    # test: get permissions

    def test_get_permissions__lock(self):
        """Only admin-teachers or class-teachers can lock levels for classes."""
        self.assert_get_permissions(
            permissions=[
                OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))
            ],
            action="lock",
        )

    def test_get_permissions__list(self):
        """Anyone can list levels."""
        self.assert_get_permissions(
            permissions=[AllowAny()],
            action="list",
        )

    def test_get_permissions__retrieve(self):
        """Anyone can retrieve a level."""
        self.assert_get_permissions(
            permissions=[AllowAny()],
            action="retrieve",
        )

    # test: get queryset

    def test_get_queryset__lock(self):
        """Only default levels can be locked for classes."""
        self.assert_get_queryset(
            values=Level.objects.filter(default=True).order_by("pk"),
            action="lock",
        )

    def test_get_queryset__list(self):
        """
        Only default levels, custom levels owned by the requesting user and
        levels shared with the requesting user can be listed.
        """
        user = self.user_with_custom_and_shared_levels

        self.assert_get_queryset(
            values=(
                Level.objects.filter(default=True)
                | user.shared_levels.all()
                | user.levels.all()
            ).order_by("pk"),
            action="list",
            request=self.client.request_factory.get(user=user),
        )

    def test_get_queryset__retrieve(self):
        """
        Only default levels, custom levels owned by the requesting user and
        levels shared with the requesting user can be retrieved.
        """
        user = self.user_with_custom_and_shared_levels

        self.assert_get_queryset(
            values=(
                Level.objects.filter(default=True)
                | user.shared_levels.all()
                | user.levels.all()
            ).order_by("pk"),
            action="retrieve",
            request=self.client.request_factory.get(user=user),
        )

    # test: get serializer class

    def test_get_serializer_class__lock(self):
        """Locking levels has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=LockLevelSerializer,
            action="lock",
        )

    def test_get_serializer_class__list(self):
        """Listing levels has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=ListLevelSerializer,
            action="list",
        )

    def test_get_serializer_class__retrieve(self):
        """Retrieving a level has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=RetrieveLevelSerializer,
            action="retrieve",
        )

    # test: actions

    def test_lock(self):
        """Can successfully lock levels for a class."""
        user = self.school_teacher_user
        klass = t.cast(t.Optional[Class], user.teacher.class_teacher.first())
        assert klass
        assert self.level_1.default
        assert self.level_2.default
        levels = [self.level_1, self.level_2]

        self.client.login_as(user)
        self.client.bulk_update(
            models=levels,
            data=[
                {"locked_for_class": [klass.access_code]}
                for _ in range(len(levels))
            ],
            action="lock",
        )

    def test_list(self):
        """Can successfully list levels."""
        user = self.user_with_custom_and_shared_levels

        self.client.login(email=user.email, password="Password1")
        self.client.list(
            models=(
                Level.objects.filter(default=True)
                | user.shared_levels.all()
                | user.levels.all()
            ).order_by("pk"),
        )

    def test_list__default(self):
        """Can successfully list only default levels."""
        user = self.user_with_custom_and_shared_levels

        self.client.login(email=user.email, password="Password1")
        self.client.list(
            models=Level.objects.filter(default=True).order_by("pk"),
            filters={"default": "true"},
        )

    def test_retrieve(self):
        """Can successfully retrieve a level."""
        user = self.user_with_custom_and_shared_levels
        level = user.levels.first()
        assert level

        self.client.login(email=user.email, password="Password1")
        self.client.retrieve(model=level)
