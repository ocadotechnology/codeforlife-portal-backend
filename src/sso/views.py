"""
© Ocado Group
Created on 01/12/2023 at 16:03:08(+00:00).

Because there are so few views in the SSO service, all views have been placed
into one folder. If in the future the number of views grows, it's recommended to
split these views into multiple files.
"""

import json
import logging
import typing as t
from urllib.parse import quote_plus

from codeforlife.mixins import CronMixin
from codeforlife.request import HttpRequest
from common.models import UserSession  # type: ignore
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as _LoginView
from django.contrib.sessions.models import Session, SessionManager
from django.core import management
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import (
    BaseLoginForm,
    EmailLoginForm,
    OtpBypassTokenLoginForm,
    OtpLoginForm,
    StudentAutoLoginForm,
    StudentLoginForm,
)


# pylint: disable-next=too-many-ancestors
class LoginView(_LoginView):
    """
    Extends Django's login view to allow a user to log in using one of the
    approved forms.

    WARNING: It's critical that to inherit Django's login view as it implements
        industry standard security measures that a login view should have.
    """

    request: HttpRequest

    def get_form_class(self):
        form = self.kwargs["form"]
        if form == "login-with-email":
            return EmailLoginForm
        if form == "login-with-otp":
            return OtpLoginForm
        if form == "login-with-otp-bypass-token":
            return OtpBypassTokenLoginForm
        if form == "login-as-student":
            return StudentLoginForm
        if form == "auto-login-as-student":
            return StudentAutoLoginForm

        raise NameError(f'Unsupported form: "{form}".')

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["data"] = json.loads(self.request.body)

        return form_kwargs

    def form_valid(self, form: BaseLoginForm):  # type: ignore
        user = form.user

        # Clear expired sessions.
        self.request.session.clear_expired(user.pk)

        # Create session (without data).
        login(self.request, user)

        # TODO: use google analytics
        user_session: t.Dict[str, t.Any] = {"user": user}
        if self.get_form_class() in [StudentAutoLoginForm, StudentLoginForm]:
            user_session[
                "class_field"
            ] = user.new_student.class_field  # type: ignore[attr-defined]
            user_session["login_type"] = (
                "direct" if "user_id" in self.request.POST else "classform"
            )
        UserSession.objects.create(**user_session)

        # Save session (with data).
        self.request.session.save()

        user_type = "indy"
        if user.teacher:
            user_type = "teacher"
        elif user.student and user.student.class_field:
            user_type = "student"

        # Get session metadata.
        session_metadata = {
            "user_id": user.id,
            "user_type": user_type,
            "auth_factors": list(
                user.session.auth_factors.values_list(
                    "auth_factor__type", flat=True
                )
            ),
            "otp_bypass_token_exists": user.otp_bypass_tokens.exists(),
        }

        # Return session metadata in response and a non-HTTP-only cookie.
        response = JsonResponse(session_metadata)
        response.set_cookie(
            key=settings.SESSION_METADATA_COOKIE_NAME,
            value=quote_plus(
                json.dumps(
                    session_metadata,
                    separators=(",", ":"),
                    indent=None,
                )
            ),
            max_age=(
                None
                if settings.SESSION_EXPIRE_AT_BROWSER_CLOSE
                else settings.SESSION_COOKIE_AGE
            ),
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=t.cast(
                t.Optional[t.Literal["Lax", "Strict", "None", False]],
                settings.SESSION_COOKIE_SAMESITE,
            ),
            domain=settings.SESSION_COOKIE_DOMAIN,
            httponly=False,
        )

        return response

    def form_invalid(self, form: BaseLoginForm):  # type: ignore
        return JsonResponse(form.errors, status=status.HTTP_400_BAD_REQUEST)


class ClearExpiredView(CronMixin, APIView):  # type: ignore
    """Clear all expired sessions."""

    def get(self, request):
        # objects is missing type SessionManager
        session_objects: SessionManager = Session.objects

        before_session_count = session_objects.count()
        logging.info("Session count before clearance: %d", before_session_count)

        # Clears expired sessions.
        # https://docs.djangoproject.com/en/3.2/ref/django-admin/#clearsessions
        management.call_command("clearsessions")

        after_session_count = session_objects.count()
        logging.info("Session count after clearance: %d", after_session_count)
        session_clearance_count = before_session_count - after_session_count
        logging.info("Session clearance count: %d", session_clearance_count)

        return Response()
