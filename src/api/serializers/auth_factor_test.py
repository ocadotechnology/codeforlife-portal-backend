"""
© Ocado Group
Created on 15/02/2024 at 15:44:25(+00:00).
"""

from unittest.mock import Mock, patch

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import (
    AuthFactor,
    OtpBypassToken,
    TeacherUser,
    User,
)

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

    def test_validate_otp__format(self):
        """OTP must be 6 digits."""
        self.assert_validate_field(
            name="otp",
            value="12345",
            error_code="format",
        )

    @patch("codeforlife.user.models.user.TOTP.verify", return_value=False)
    def test_validate_otp__invalid(self, totp__verify: Mock):
        """Cannot enable the OTP without providing the current OTP."""
        user = TeacherUser.objects.filter(
            # TODO: make otp_secret non-nullable
            userprofile__otp_secret__isnull=False
        ).first()
        assert user

        value = "123456"

        self.assert_validate_field(
            name="otp",
            value=value,
            error_code="invalid",
            context={
                "request": self.request_factory.post(
                    user=self.multi_auth_factor_teacher_user
                )
            },
        )

        totp__verify.assert_called_once_with(value)

    def test_validate__otp__required(self):
        """Current OTP is required when enabling OTP."""
        self.assert_validate(
            attrs={"type": AuthFactor.Type.OTP.value},
            error_code="otp__required",
        )

    def test_create__otp(self):
        """Can successfully enable an auth factor."""
        user = TeacherUser.objects.exclude(
            auth_factors__type__in=["otp"]
        ).first()
        assert user

        self.assert_create(
            validated_data={"type": AuthFactor.Type.OTP, "otp": "123456"},
            non_model_fields={"otp"},
            new_data={"user": user.id},
            context={"request": self.request_factory.post(user=user)},
        )

        assert user.otp_bypass_tokens.count() == OtpBypassToken.max_count
