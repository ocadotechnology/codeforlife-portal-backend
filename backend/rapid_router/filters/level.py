"""
© Ocado Group
Created on 03/04/2024 at 16:37:39(+01:00).
"""

from django_filters import rest_framework as filters

from ..models import Level


# pylint: disable-next=missing-class-docstring
class LevelFilterSet(filters.FilterSet):
    default = filters.BooleanFilter()

    class Meta:
        model = Level
        fields = ["default"]
