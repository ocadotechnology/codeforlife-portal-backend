"""
© Ocado Group
Created on 23/01/2024 at 11:05:37(+00:00).
"""

import pyotp
from codeforlife.serializers import ModelSerializer
from codeforlife.user.models import AuthFactor, User
from rest_framework import serializers


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class AuthFactorSerializer(ModelSerializer[User, AuthFactor]):
    class Meta:
        model = AuthFactor
        fields = ["id", "type", "user"]
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

    def create(self, validated_data):
        user = self.request.auth_user
        if not user.userprofile.otp_secret:
            user.userprofile.otp_secret = pyotp.random_base32()
            user.userprofile.save()

        validated_data["user"] = user
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if (
            self.view.action == "create"
            and instance.type == AuthFactor.Type.OTP
        ):
            representation["totp_provisioning_uri"] = (
                self.request.auth_user.totp_provisioning_uri
            )

        return representation
