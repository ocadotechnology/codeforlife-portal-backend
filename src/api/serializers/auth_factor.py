"""
© Ocado Group
Created on 23/01/2024 at 11:05:37(+00:00).
"""

from codeforlife.serializers import ModelSerializer
from codeforlife.user.models import AuthFactor, OtpBypassToken, User
from rest_framework import serializers

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class AuthFactorSerializer(ModelSerializer[User, AuthFactor]):
    otp = serializers.CharField(
        required=False,
        write_only=True,
        validators=AuthFactor.otp_validators,
    )

    class Meta:
        model = AuthFactor
        fields = [
            "id",
            "type",
            "otp",
            "user",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "user": {"read_only": True},
        }

    # pylint: disable-next=missing-function-docstring
    def validate_type(self, value: str):
        if AuthFactor.objects.filter(
            user=self.request.auth_user, type=value
        ).exists():
            raise serializers.ValidationError(
                "You already have this authentication factor enabled.",
                code="already_exists",
            )

        return value

    # pylint: disable-next=missing-function-docstring
    def validate_otp(self, value: str):
        if not self.request.auth_user.totp.verify(value):
            raise serializers.ValidationError("Invalid OTP.", code="invalid")

        return value

    def validate(self, attrs):
        if attrs["type"] == "otp" and "otp" not in attrs:
            raise serializers.ValidationError(
                "Current OTP required to enable OTP.",
                code="otp__required",
            )

        return attrs

    def create(self, validated_data):
        validated_data["user_id"] = self.request.auth_user.id
        validated_data.pop("otp", None)
        auth_factor = super().create(validated_data)

        if auth_factor.type == AuthFactor.Type.OTP:
            OtpBypassToken.objects.bulk_create(auth_factor.user)

        return auth_factor
