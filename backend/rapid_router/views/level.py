"""
© Ocado Group
Created on 03/04/2024 at 11:14:27(+01:00).
"""

from codeforlife.views import ModelViewSet

from ..models import Level
from ..serializers import LevelSerializer


# pylint: disable-next=too-many-ancestors,missing-class-docstring
class LevelViewSet(ModelViewSet[Level]):
    def get_serializer_class(self):
        return LevelSerializer
