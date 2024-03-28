"""
© Ocado Group
Created on 29/01/2024 at 10:13:58(+00:00).
"""
import typing as t

from codeforlife.types import DataDict
from codeforlife.user.models import (
    AdminSchoolTeacher,
    SchoolTeacher,
    Teacher,
    TeacherUser,
    teacher_as_type,
)
from codeforlife.user.serializers import TeacherSerializer
from rest_framework import serializers

from .user import BaseUserSerializer

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors
# pylint: disable=missing-function-docstring


class CreateTeacherSerializer(TeacherSerializer[Teacher]):
    class UserSerializer(BaseUserSerializer):
        add_to_newsletter = serializers.BooleanField(write_only=True)

        class Meta(BaseUserSerializer.Meta):
            fields = [
                *BaseUserSerializer.Meta.fields,
                "password",
                "add_to_newsletter",
            ]
            extra_kwargs = {
                **BaseUserSerializer.Meta.extra_kwargs,
                "first_name": {"min_length": 1},
                "last_name": {"min_length": 1},
                "password": {"write_only": True},
                "email": {"read_only": False},
            }

    user = UserSerializer(source="new_user")

    class Meta(TeacherSerializer.Meta):
        fields = [*TeacherSerializer.Meta.fields, "user"]

    def create(self, validated_data):
        user_fields = t.cast(DataDict, validated_data["new_user"])
        add_to_newsletter: bool = user_fields.pop("add_to_newsletter")

        teacher_user = TeacherUser.objects.create_user(**user_fields)
        if add_to_newsletter:
            teacher_user.add_contact_to_dot_digital()

        # TODO: send verification email.

        return teacher_user.teacher


class RemoveTeacherFromSchoolSerializer(TeacherSerializer[SchoolTeacher]):
    def validate(self, attrs):
        if self.non_none_instance.classes.exists():
            raise serializers.ValidationError(
                "Cannot leave school when you have classes assigned to you.",
                code="has_classes",
            )

        if (
            self.non_none_instance.is_admin
            and teacher_as_type(
                self.non_none_instance, AdminSchoolTeacher
            ).is_last_admin
        ):
            raise serializers.ValidationError(
                "There must be at least one admin teacher in the school.",
                code="last_admin",
            )

        return attrs

    def update(self, instance, validated_data):
        instance.school = None
        instance.save(update_fields=["school"])
        return instance


class SetSchoolTeacherAdminAccessSerializer(TeacherSerializer[SchoolTeacher]):
    class Meta(TeacherSerializer.Meta):
        extra_kwargs = {
            **TeacherSerializer.Meta.extra_kwargs,
            "is_admin": {"read_only": False},
        }

    def validate_is_admin(self, value: bool):
        if (
            not value
            and self.non_none_instance.is_admin
            and teacher_as_type(
                self.non_none_instance, AdminSchoolTeacher
            ).is_last_admin
        ):
            raise serializers.ValidationError(
                "There must be at least one admin teacher in the school.",
                code="last",
            )

        return value
