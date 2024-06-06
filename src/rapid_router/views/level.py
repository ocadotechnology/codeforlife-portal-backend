"""
© Ocado Group
Created on 03/04/2024 at 11:14:27(+01:00).
"""

from codeforlife.permissions import OR, AllowAny
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet

from ..filters import LevelFilterSet
from ..models import Level, User
from ..serializers import (
    ListLevelSerializer,
    LockLevelSerializer,
    RetrieveLevelSerializer,
)


# pylint: disable-next=too-many-ancestors,missing-class-docstring
class LevelViewSet(ModelViewSet[User, Level]):
    http_method_names = ["get", "put"]
    filterset_class = LevelFilterSet

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]

        # action == "lock"
        return [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))]

    def get_queryset(self):
        queryset = Level.objects.filter(default=True)
        if self.action in ["list", "retrieve"]:
            user = self.request.user
            if isinstance(user, User):
                return queryset | user.shared_levels.all() | user.levels.all()

        return queryset

    def get_serializer_class(self):
        if self.action == "lock":
            return LockLevelSerializer
        if self.action == "retrieve":
            return RetrieveLevelSerializer

        return ListLevelSerializer

    lock = ModelViewSet.bulk_update_action("lock")
