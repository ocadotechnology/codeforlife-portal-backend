"""
© Ocado Group
Created on 09/02/2024 at 16:14:00(+00:00).
"""

import typing as t
from datetime import timedelta

from codeforlife.serializers import ModelSerializer
from codeforlife.types import DataDict
from codeforlife.user.models import (
    NonSchoolTeacherUser,
    SchoolTeacherUser,
    User,
)
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers

from ..models import SchoolTeacherInvitation
from .teacher import CreateTeacherSerializer

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-ancestors


class BaseSchoolTeacherInvitationSerializer(
    ModelSerializer[User, SchoolTeacherInvitation]
):
    expires_at = serializers.DateTimeField(source="expiry", read_only=True)

    class Meta:
        model = SchoolTeacherInvitation
        fields = ["id", "expires_at"]
        extra_kwargs = {"id": {"read_only": True}}


class SchoolTeacherInvitationSerializer(BaseSchoolTeacherInvitationSerializer):
    class Meta(BaseSchoolTeacherInvitationSerializer.Meta):
        fields = [
            *BaseSchoolTeacherInvitationSerializer.Meta.fields,
            "invited_teacher_first_name",
            "invited_teacher_last_name",
            "invited_teacher_email",
            "invited_teacher_is_admin",
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
    def update(self, instance, validated_data):
        instance.expiry = timezone.now() + timedelta(days=30)
        instance.save(update_fields=["expiry"])
        return instance


class AcceptSchoolTeacherInvitationSerializer(
    BaseSchoolTeacherInvitationSerializer
):
    @property
    def non_school_teacher_user(self) -> t.Optional[NonSchoolTeacherUser]:
        return self.context["non_school_teacher_user"]

    user = CreateTeacherSerializer.UserSerializer(required=False)

    class Meta(BaseSchoolTeacherInvitationSerializer.Meta):
        fields = [
            *BaseSchoolTeacherInvitationSerializer.Meta.fields,
            "user",
        ]

    def validate_user(self, value: DataDict):
        if self.non_school_teacher_user:
            raise serializers.ValidationError(
                "Cannot update existing teacher.",
                code="cannot_update",
            )

        return value

    def update(self, instance, validated_data):
        if self.non_school_teacher_user:
            self.non_school_teacher_user.teacher.is_admin = (
                instance.invited_teacher_is_admin
            )
            self.non_school_teacher_user.teacher.school = instance.school
            self.non_school_teacher_user.teacher.save(
                update_fields=["is_admin", "school"]
            )
            self.non_school_teacher_user.userprofile.is_verified = True
            self.non_school_teacher_user.userprofile.save(
                update_fields=["is_verified"]
            )
        else:
            user_fields = t.cast(DataDict, validated_data["user"])
            add_to_newsletter = user_fields.pop("add_to_newsletter")

            school_teacher_user = SchoolTeacherUser.objects.create_user(
                **user_fields,
                school=instance.school,
                is_admin=instance.invited_teacher_is_admin,
                email=instance.invited_teacher_email,
                is_verified=True,
            )

            if add_to_newsletter:
                school_teacher_user.add_contact_to_dot_digital()

        return instance
