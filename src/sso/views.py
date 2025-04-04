"""
© Ocado Group
Created on 01/12/2023 at 16:03:08(+00:00).

Because there are so few views in the SSO service, all views have been placed
into one folder. If in the future the number of views grows, it's recommended to
split these views into multiple files.
"""

import typing as t

from codeforlife.request import HttpRequest
from codeforlife.user.models import User
from codeforlife.views import BaseLoginView
from common.models import UserSession  # type: ignore

from .forms import (
    EmailLoginForm,
    OtpBypassTokenLoginForm,
    OtpLoginForm,
    StudentAutoLoginForm,
    StudentLoginForm,
)


# pylint: disable-next=too-many-ancestors
class LoginView(BaseLoginView[HttpRequest[User], User]):
    """
    Extends Django's login view to allow a user to log in using one of the
    approved forms.

    WARNING: It's critical that to inherit Django's login view as it implements
        industry standard security measures that a login view should have.
    """

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

    def get_session_metadata(self, user):
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

        user_type = "indy"
        if user.teacher:
            user_type = "teacher"
        elif user.student and user.student.class_field:
            user_type = "student"

        return {
            "user_id": user.id,
            "user_type": user_type,
            "auth_factors": list(
                user.session.auth_factors.values_list(
                    "auth_factor__type", flat=True
                )
            ),
            "otp_bypass_token_exists": user.otp_bypass_tokens.exists(),
        }
