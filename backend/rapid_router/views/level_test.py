"""
© Ocado Group
Created on 03/04/2024 at 11:25:40(+01:00).
"""

from codeforlife.tests import ModelViewSetTestCase

from ..models import Level
from ..serializers import LevelSerializer
from .level import LevelViewSet


# pylint: disable-next=too-many-ancestors,missing-class-docstring
class TestLevelViewSet(ModelViewSetTestCase[Level]):
    basename = "level"
    model_view_set_class = LevelViewSet

    def test_get_serializer_class__(self):
        self.assert_get_serializer_class(
            serializer_class=LevelSerializer,
            action="",
        )
