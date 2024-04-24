"""
© Ocado Group
Created on 24/04/2024 at 11:57:38(+01:00).
"""

import typing as t

from codeforlife.permissions import BasePermission
from django.contrib.auth.hashers import check_password

from ..models import SchoolTeacherInvitation


class IsInvitedSchoolTeacher(BasePermission):
    """The request is being made by the teacher invited to join a school."""

    def has_permission(self, request, view):
        pk = t.cast(t.Optional[int], request.query_params.get("pk"))
        token: t.Optional[str] = request.data.get("token")

        if pk is not None and token is not None:
            invitation = SchoolTeacherInvitation.objects.get(pk=pk)

            return check_password(token, invitation.token)

        return False
