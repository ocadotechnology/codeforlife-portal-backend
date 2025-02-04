"""
© Ocado Group
Created on 20/01/2025 at 18:52:16(+00:00).
"""

from codeforlife.permissions import IsAuthenticated
from codeforlife.user.models import AuthFactor, User


class HasAuthFactor(IsAuthenticated):
    """Request's user must have a auth factor enabled."""

    def __init__(self, t: AuthFactor.Type):
        super().__init__()

        self.t = t

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.t == other.t

    def has_permission(self, request, view):
        user = request.user
        return (
            super().has_permission(request, view)
            and isinstance(user, User)
            and user.auth_factors.filter(type=self.t).exists()
        )
