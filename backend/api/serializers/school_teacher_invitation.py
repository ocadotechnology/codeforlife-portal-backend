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


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class SchoolTeacherInvitationSerializer(
    ModelSerializer[User, SchoolTeacherInvitation]
):
    first_name = serializers.CharField(source="invited_teacher_first_name")
    last_name = serializers.CharField(source="invited_teacher_last_name")
    email = serializers.EmailField(source="invited_teacher_email")
    is_admin = serializers.BooleanField(source="invited_teacher_is_admin")

    class Meta:
        model = SchoolTeacherInvitation
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "is_admin",
            "expiry",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "expiry": {"read_only": True},
        }

    def create(self, validated_data):
        user = self.request.admin_school_teacher_user

        token = get_random_string(length=32)
        validated_data["token"] = make_password(token)
        validated_data["school"] = user.teacher.school
        validated_data["from_teacher"] = user.teacher
        validated_data["expiry"] = timezone.now() + timedelta(days=30)

        invitation = super().create(validated_data)
        invitation._token = token
        return invitation

    def update(self, instance, validated_data):
        instance.expiry = timezone.now() + timedelta(days=30)
        instance.save()
        return instance
