"""
© Ocado Group
Created on 03/04/2024 at 11:17:43(+01:00).
"""

from codeforlife.serializers import ModelListSerializer, ModelSerializer
from codeforlife.user.models import Class
from django.db.models.query import QuerySet
from rest_framework import serializers

from ..models import Level, User

# pylint: disable=missing-class-docstring
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

        for level, data in zip(instance, validated_data):
            for access_code in data["locked_for_class"]:
                level.locked_for_class.add(classes[access_code])

        return instance


class LockLevelSerializer(BaseLevelSerializer):
    class LockedForClassField(serializers.ListField):
        child = serializers.CharField()

        def to_representation(
            self, data: QuerySet[Class]  # type: ignore[override]
        ):
            return list(data.values_list("access_code", flat=True))

    locked_for_class = LockedForClassField()

    class Meta(BaseLevelSerializer.Meta):
        fields = [*BaseLevelSerializer.Meta.fields, "locked_for_class"]
        list_serializer_class = LockLevelListSerializer


class ListLevelSerializer(BaseLevelSerializer):
    class Meta(BaseLevelSerializer.Meta):
        fields = [*BaseLevelSerializer.Meta.fields, "name", "locked_for_class"]


class RetrieveLevelSerializer(BaseLevelSerializer):
    class Meta(BaseLevelSerializer.Meta):
        # TODO: return require fields
        fields = [*BaseLevelSerializer.Meta.fields]
