"""
© Ocado Group
Created on 03/04/2024 at 11:17:43(+01:00).
"""

from codeforlife.serializers import ModelSerializer

from ..models import Level

# pylint: disable=missing-class-docstring


class LevelSerializer(ModelSerializer[Level]):
    class Meta:
        model = Level
