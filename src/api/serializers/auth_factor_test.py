"""
© Ocado Group
Created on 15/02/2024 at 15:44:25(+00:00).
"""

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import AuthFactor, TeacherUser, User

from ..views import AuthFactorViewSet
from .auth_factor import AuthFactorSerializer

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class TestAuthFactorSerializer(ModelSerializerTestCase[User, AuthFactor]):
    model_serializer_class = AuthFactorSerializer
    fixtures = ["school_2", "non_school_teacher"]

    def setUp(self):
        self.multi_auth_factor_teacher_user = TeacherUser.objects.get(
            email="teacher@school2.com"
        )
        assert self.multi_auth_factor_teacher_user.auth_factors.exists()

        self.uni_auth_factor_teacher_user = TeacherUser.objects.get(
            email="teacher@noschool.com"
        )
        assert not self.uni_auth_factor_teacher_user.auth_factors.exists()

    # test: validate

    def test_validate_type__already_exists(self):
        """Cannot enable an already enabled auth factor."""
        auth_factor = self.multi_auth_factor_teacher_user.auth_factors.first()
        assert auth_factor

        self.assert_validate_field(
            name="type",
            value=auth_factor.type,
            error_code="already_exists",
            context={
                "request": self.request_factory.post(
                    user=self.multi_auth_factor_teacher_user
                )
            },
        )

    # test: create

    def test_create(self):
        """Enabling OTP will ensure the user's OTP-secret is set."""
        user = self.uni_auth_factor_teacher_user
        assert user.otp_secret

        self.assert_create(
            validated_data={"type": AuthFactor.Type.OTP},
            context={"request": self.request_factory.post(user=user)},
            new_data={
                "user": {
                    "id": user.id,
                    "userprofile": {"otp_secret": user.otp_secret},
                },
            },
        )

    # test: to representation

    def test_to_representation(self):
        """User's TOTP provisioning URI is returned when enabling OTP."""
        assert self.multi_auth_factor_teacher_user.otp_secret

        self.assert_to_representation(
            instance=AuthFactor(type=AuthFactor.Type.OTP),
            new_data={
                "totp_provisioning_uri": (
                    self.multi_auth_factor_teacher_user.totp_provisioning_uri
                ),
            },
            context={
                "view": AuthFactorViewSet(action="create"),
                "request": self.request_factory.post(
                    user=self.multi_auth_factor_teacher_user
                ),
            },
            non_model_fields={"totp_provisioning_uri"},
        )
