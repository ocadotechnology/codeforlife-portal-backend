"""
© Ocado Group
Created on 03/04/2024 at 11:17:43(+01:00).
"""

import typing as t
from datetime import datetime

from codeforlife.serializers import ModelListSerializer, ModelSerializer
from codeforlife.user.models import Class
from common.models import DailyActivity
from django.db.models.query import QuerySet
from rest_framework import serializers

from ..models import Level, User

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-ancestors


class BaseLevelSerializer(ModelSerializer[User, Level]):
    class Meta:
        model = Level
        fields = ["id"]
        extra_kwargs = {"id": {"read_only": True}}


class LockLevelListSerializer(ModelListSerializer[User, Level]):
    def update(self, instance, validated_data):
        classes = {
            access_code: Class.objects.get(access_code=access_code)
            for access_code in {
                access_code
                for data in validated_data
                for access_code in data["locked_for_class"]
            }
        }

        for klass in classes.values():
            klass.locked_levels.clear()

        for level, data in zip(instance, validated_data):
            for access_code in data["locked_for_class"]:
                level.locked_for_class.add(classes[access_code])

        # TODO: use GA4 instead
        activity_today = DailyActivity.objects.get_or_create(
            date=datetime.now().date()
        )[0]
        activity_today.level_control_submits += 1
        activity_today.save()

        return instance


class LockedForClassField(serializers.ListField):
    child = serializers.CharField()

    def to_representation(
        self, data: QuerySet[Class]  # type: ignore[override]
    ):
        return list(data.values_list("access_code", flat=True))


class LockLevelSerializer(BaseLevelSerializer):
    locked_for_class = LockedForClassField()

    class Meta(BaseLevelSerializer.Meta):
        fields = [*BaseLevelSerializer.Meta.fields, "locked_for_class"]
        list_serializer_class = LockLevelListSerializer

    def validate_locked_for_class(self, value: t.List[str]):
        teacher = self.request.school_teacher_user.teacher
        for access_code in value:
            queryset = Class.objects.filter(access_code=access_code)

            if not queryset.filter(teacher__school=teacher.school).exists():
                raise serializers.ValidationError(
                    "Class is not in the teacher's school.",
                    code="not_in_school",
                )

            if (
                not teacher.is_admin
                and not queryset.filter(teacher=teacher).exists()
            ):
                raise serializers.ValidationError(
                    "Teacher is not an admin or the class teacher.",
                    code="not_class_teacher",
                )

        return value


class ListLevelSerializer(BaseLevelSerializer):
    locked_for_class = LockedForClassField()

    class Meta(BaseLevelSerializer.Meta):
        fields = [*BaseLevelSerializer.Meta.fields, "name", "locked_for_class"]


class RetrieveLevelSerializer(BaseLevelSerializer):
    class Meta(BaseLevelSerializer.Meta):
        # TODO: return require fields
        fields = [*BaseLevelSerializer.Meta.fields]
