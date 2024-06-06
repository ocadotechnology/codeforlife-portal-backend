"""
© Ocado Group
Created on 24/04/2024 at 11:57:38(+01:00).
"""

import typing as t

from codeforlife.permissions import BasePermission
from django.contrib.auth.hashers import check_password
from rest_framework.viewsets import ModelViewSet

from ..models import SchoolTeacherInvitation


class IsInvitedSchoolTeacher(BasePermission):
    """The request is being made by the teacher invited to join a school."""

    def has_permission(  # type: ignore[override]
        self, request, view: ModelViewSet
    ):
        pk: t.Optional[str] = view.kwargs.get(
            view.lookup_url_kwarg or view.lookup_field
        )

        token: t.Optional[str] = request.data.get("token")

        if pk is not None and token is not None:
            invitation = SchoolTeacherInvitation.objects.get(pk=int(pk))

            return check_password(token, invitation.token)

        return False
