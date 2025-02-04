"""
© Ocado Group
Created on 23/01/2024 at 11:22:16(+00:00).
"""

import pyotp
from codeforlife.permissions import NOT, AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    AuthFactor,
    NonAdminSchoolTeacherUser,
    School,
    TeacherUser,
    User,
)
from codeforlife.user.permissions import IsTeacher
from django.db.models import Count

from ..permissions import HasAuthFactor
from .auth_factor import AuthFactorViewSet

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors
# pylint: disable=too-many-public-methods


class TestAuthFactorViewSet(ModelViewSetTestCase[User, AuthFactor]):
    basename = "auth-factor"
    model_view_set_class = AuthFactorViewSet
    fixtures = ["school_2", "non_school_teacher"]

    def setUp(self):
        self.mfa_non_admin_school_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school2.com")
        )
        assert self.mfa_non_admin_school_teacher_user.auth_factors.exists()

    # test: get queryset

    def test_get_queryset__list__admin(self):
        """
        Can list the author factors of all teachers in your school if you are
        an admin.
        """
        user = self.mfa_non_admin_school_teacher_user
        admin_school_teacher_user = AdminSchoolTeacherUser.objects.filter(
            new_teacher__school=user.teacher.school
        ).first()
        assert admin_school_teacher_user

        self.assert_get_queryset(
            action="list",
            values=list(
                user.auth_factors.all()
                | admin_school_teacher_user.auth_factors.all()
            ),
            request=self.client.request_factory.get(
                user=admin_school_teacher_user
            ),
        )

    def test_get_queryset__list__non_admin(self):
        """Can only list your own auth factors if you are not an admin."""
        user = self.mfa_non_admin_school_teacher_user

        self.assert_get_queryset(
            action="list",
            values=list(user.auth_factors.all()),
            request=self.client.request_factory.get(user=user),
        )

    def test_get_queryset__destroy__admin(self):
        """
        Can destroy the author factors of all teachers in your school if you are
        an admin.
        """
        user = self.mfa_non_admin_school_teacher_user
        admin_school_teacher_user = AdminSchoolTeacherUser.objects.filter(
            new_teacher__school=user.teacher.school
        ).first()
        assert admin_school_teacher_user

        self.assert_get_queryset(
            action="destroy",
            values=list(
                user.auth_factors.all()
                | admin_school_teacher_user.auth_factors.all()
            ),
            request=self.client.request_factory.get(
                user=admin_school_teacher_user
            ),
        )

    def test_get_queryset__destroy__non_admin(self):
        """Can only destroy your own auth factors if you are not an admin."""
        user = self.mfa_non_admin_school_teacher_user

        self.assert_get_queryset(
            action="destroy",
            values=list(user.auth_factors.all()),
            request=self.client.request_factory.get(user=user),
        )

    def test_get_queryset__get_otp_secret(self):
        """Can only get your own OTP secret."""
        user = self.mfa_non_admin_school_teacher_user

        self.assert_get_queryset(
            action="get_otp_secret",
            values=list(user.auth_factors.all()),
            request=self.client.request_factory.get(user=user),
        )

    def test_get_queryset__check_if_exists__admin(self):
        """
        Can check if a author factor exists for all teachers in your school if
        you are an admin.
        """
        user = self.mfa_non_admin_school_teacher_user
        admin_school_teacher_user = AdminSchoolTeacherUser.objects.filter(
            new_teacher__school=user.teacher.school
        ).first()
        assert admin_school_teacher_user

        self.assert_get_queryset(
            action="list",
            values=list(
                user.auth_factors.all()
                | admin_school_teacher_user.auth_factors.all()
            ),
            request=self.client.request_factory.get(
                user=admin_school_teacher_user
            ),
        )

    def test_get_queryset__check_if_exists__non_admin(self):
        """
        Can check if a author factor exists for only yourself if you are not an
        admin.
        """
        user = self.mfa_non_admin_school_teacher_user

        self.assert_get_queryset(
            action="list",
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

    def test_get_permissions__get_otp_secret(self):
        """Only a teacher-user can get an OTP secret."""
        self.assert_get_permissions(
            [IsTeacher(), NOT(HasAuthFactor(AuthFactor.Type.OTP))],
            action="get_otp_secret",
        )

    def test_get_permissions__check_if_exists(self):
        """Only a teacher-user can check if an auth factor exists."""
        self.assert_get_permissions([IsTeacher()], action="check_if_exists")

    # test: actions

    def test_list(self):
        """Can list enabled auth-factors."""
        user = self.mfa_non_admin_school_teacher_user

        self.client.login_as(user)
        self.client.list(user.auth_factors.all())

    def test_list__user(self):
        """Can list enabled auth-factors, filtered by a user's ID."""
        # Get a school that has at least:
        #  - one admin teacher;
        #  - two teachers with auth factors enabled.
        school = (
            School.objects.filter(
                id__in=School.objects.filter(
                    teacher_school__is_admin=True,
                ).values_list("id", flat=True)
            )
            .filter(teacher_school__new_user__auth_factors__isnull=False)
            .annotate(teacher_count=Count("teacher_school"))
            .filter(teacher_count__gte=2)
            .first()
        )
        assert school

        user = AdminSchoolTeacherUser.objects.filter(
            new_teacher__school=school
        ).first()
        assert user

        self.client.login_as(user)
        self.client.list(
            user.auth_factors.all(),
            filters={"user": str(user.pk)},
        )

    def test_list__type(self):
        """Can list enabled auth-factors, filtered by type."""
        user = self.mfa_non_admin_school_teacher_user
        auth_factor = user.auth_factors.first()
        assert auth_factor

        self.client.login_as(user)
        self.client.list(
            [auth_factor],
            filters={"type": auth_factor.type},
        )

    def test_create__otp(self):
        """Can enable OTP."""
        teacher_user = TeacherUser.objects.exclude(
            auth_factors__type__in=["otp"]
        ).first()
        assert teacher_user

        # TODO: make "otp_secret" non-nullable and delete code block
        teacher_user.userprofile.otp_secret = pyotp.random_base32()
        teacher_user.userprofile.save(update_fields=["otp_secret"])

        # TODO: set password="password" on all user fixtures
        self.client.login_as(teacher_user, password="abc123")
        self.client.create(
            {
                "type": AuthFactor.Type.OTP,
                "otp": teacher_user.totp.now(),
            }
        )

    def test_destroy(self):
        """Can disable an auth-factor."""
        user = self.mfa_non_admin_school_teacher_user
        auth_factor = user.auth_factors.first()
        assert auth_factor

        self.client.login_as(user)
        self.client.destroy(auth_factor)

    def test_get_otp_secret(self):
        """Can successfully generate a OTP provisioning URI."""
        user = TeacherUser.objects.exclude(
            auth_factors__type__in=[AuthFactor.Type.OTP]
        ).first()
        assert user

        # TODO: normalize password to "password"
        self.client.login_as(user, password="abc123")

        response = self.client.get(self.reverse_action("get_otp_secret"))

        self.assertDictEqual(
            response.json(),
            {
                "secret": user.totp.secret,
                "provisioning_uri": user.totp_provisioning_uri,
            },
        )
