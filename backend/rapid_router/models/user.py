"""
© Ocado Group
Created on 05/04/2024 at 12:40:10(+01:00).

User proxy for Rapid Router app.
"""

import typing as t

from codeforlife.user.models import User as _User
from django.db.models.query import QuerySet
from django_stubs_ext.db.models import TypedModelMeta

if t.TYPE_CHECKING:
    from .level import Level


class User(_User):
    """A Rapid Router user."""

    shared: QuerySet["Level"]

    class Meta(TypedModelMeta):
        proxy = True

    @property
    def shared_levels(self):
        """Rename poorly named related levels."""
        return self.shared

    @property
    def levels(self) -> QuerySet["Level"]:
        """Shortcut to related levels."""
        return self.userprofile.levels
