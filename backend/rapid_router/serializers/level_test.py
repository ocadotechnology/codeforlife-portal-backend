"""
© Ocado Group
Created on 03/04/2024 at 11:41:36(+01:00).
"""

from codeforlife.tests import ModelSerializerTestCase

from ..models import Level
from .level import LevelSerializer

# pylint: disable=missing-class-docstring


class TestLevelSerializer(ModelSerializerTestCase[Level]):
    model_serializer_class = LevelSerializer
