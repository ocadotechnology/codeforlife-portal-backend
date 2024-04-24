"""
© Ocado Group
Created on 09/02/2024 at 16:14:00(+00:00).
"""

from datetime import timedelta

from codeforlife.serializers import ModelSerializer
from codeforlife.user.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers

from ..models import SchoolTeacherInvitation

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-ancestors


class BaseSchoolTeacherInvitationSerializer(
    ModelSerializer[User, SchoolTeacherInvitation]
):
    class Meta:
        model = SchoolTeacherInvitation
        fields = ["id"]
        extra_kwargs = {"id": {"read_only": True}}


class SchoolTeacherInvitationSerializer(BaseSchoolTeacherInvitationSerializer):
    expires_at = serializers.DateTimeField(source="expiry", read_only=True)

    class Meta(BaseSchoolTeacherInvitationSerializer.Meta):
        fields = [
            *BaseSchoolTeacherInvitationSerializer.Meta.fields,
            "invited_teacher_first_name",
            "invited_teacher_last_name",
            "invited_teacher_email",
            "invited_teacher_is_admin",
            "expires_at",
        ]

    def create(self, validated_data):
        user = self.request.admin_school_teacher_user

        token = get_random_string(length=32)

        # TODO: move this logic to SchoolTeacherInvitation.objects.create
        invitation = SchoolTeacherInvitation.objects.create(
            **validated_data,
            token=make_password(token),
            school=user.teacher.school,
            from_teacher=user.teacher,
            expiry=timezone.now() + timedelta(days=30),
        )

        # pylint: disable-next=protected-access
        invitation._token = token

        return invitation


class RefreshSchoolTeacherInvitationSerializer(
    BaseSchoolTeacherInvitationSerializer
):
    expires_at = serializers.DateTimeField(source="expiry", read_only=True)

    class Meta(BaseSchoolTeacherInvitationSerializer.Meta):
        fields = [
            *BaseSchoolTeacherInvitationSerializer.Meta.fields,
            "expires_at",
        ]

    def update(self, instance, validated_data):
        instance.expiry = timezone.now() + timedelta(days=30)
        instance.save(update_fields=["expiry"])
        return instance
