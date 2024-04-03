"""
© Ocado Group
Created on 23/01/2024 at 11:22:16(+00:00).
"""

from codeforlife.permissions import AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    AuthFactor,
    NonAdminSchoolTeacherUser,
    TeacherUser,
)
from codeforlife.user.permissions import IsTeacher

from .auth_factor import AuthFactorViewSet

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class TestAuthFactorViewSet(ModelViewSetTestCase[AuthFactor]):
    basename = "auth-factor"
    model_view_set_class = AuthFactorViewSet
    fixtures = ["school_2", "non_school_teacher"]

    def setUp(self):
        self.mfa_non_admin_school_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school2.com")
        )
        assert self.mfa_non_admin_school_teacher_user.auth_factors.exists()

    # test: get queryset

    def test_get_queryset__admin(self):
        """
        Can query the author factors of all teachers in your school if you are
        an admin.
        """
        user = self.mfa_non_admin_school_teacher_user
        admin_school_teacher_user = AdminSchoolTeacherUser.objects.filter(
            new_teacher__school=user.teacher.school
        ).first()
        assert admin_school_teacher_user

        self.assert_get_queryset(
            values=list(
                user.auth_factors.all()
                | admin_school_teacher_user.auth_factors.all()
            ),
            request=self.client.request_factory.get(
                user=admin_school_teacher_user
            ),
        )

    def test_get_queryset__non_admin(self):
        """Can only query your own auth factors if you are not an admin."""
        user = self.mfa_non_admin_school_teacher_user

        self.assert_get_queryset(
            values=list(user.auth_factors.all()),
            request=self.client.request_factory.get(user=user),
        )

    # test: get permissions

    def test_get_permissions__bulk(self):
        """Cannot perform any bulk action."""
        self.assert_get_permissions([AllowNone()], action="bulk")

    def test_get_permissions__retrieve(self):
        """Cannot retrieve a single auth factor."""
        self.assert_get_permissions([AllowNone()], action="retrieve")

    def test_get_permissions__list(self):
        """Only a teacher-user can list all auth factors."""
        self.assert_get_permissions([IsTeacher()], action="list")

    def test_get_permissions__create(self):
        """Only a teacher-user can enable an auth factor."""
        self.assert_get_permissions([IsTeacher()], action="create")

    def test_get_permissions__destroy(self):
        """Only a teacher-user can disable an auth factor."""
        self.assert_get_permissions([IsTeacher()], action="destroy")

    # test: generic actions

    def test_list(self):
        """Can list enabled auth-factors."""
        user = self.mfa_non_admin_school_teacher_user

        self.client.login_as(user)
        self.client.list(user.auth_factors.all())

    def test_create__otp(self):
        """Can enable OTP."""
        teacher_user = TeacherUser.objects.filter(
            auth_factors__isnull=True
        ).first()
        assert teacher_user

        # TODO: set password="password" on all user fixtures
        self.client.login_as(teacher_user, password="abc123")
        self.client.create({"type": "otp"})

    def test_destroy(self):
        """Can disable an auth-factor."""
        user = self.mfa_non_admin_school_teacher_user
        auth_factor = user.auth_factors.first()
        assert auth_factor

        self.client.login_as(user)
        self.client.destroy(auth_factor)
