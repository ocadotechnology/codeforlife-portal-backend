"""
© Ocado Group
Created on 01/12/2023 at 16:00:24(+00:00).
"""

from codeforlife.forms import BaseLoginForm, BaseOAuth2LoginForm
from codeforlife.user.models import AuthFactor, OtpBypassToken, User
from codeforlife.user.models.klass import class_access_code_validators
from django import forms


class EmailLoginForm(BaseLoginForm[User]):
    """Log in with an email address."""

    email = forms.EmailField()
    password = forms.CharField(strip=False)

    def get_invalid_login_error_message(self):
        return (
            "Please enter a correct email and password. Note that both"
            " fields are case-sensitive."
        )


class OtpLoginForm(BaseLoginForm[User]):
    """Log in with an OTP code."""

    otp = forms.CharField(validators=AuthFactor.otp_validators)

    def get_invalid_login_error_message(self):
        return "Please enter the correct one-time password."


class OtpBypassTokenLoginForm(BaseLoginForm[User]):
    """Log in with an OTP-bypass token."""

    token = forms.CharField(validators=OtpBypassToken.validators)

    def get_invalid_login_error_message(self):
        return "Must be exactly 8 characters. A token can only be used once."


class StudentLoginForm(BaseLoginForm[User]):
    """Log in as a student."""

    first_name = forms.CharField()
    password = forms.CharField(strip=False)
    class_id = forms.CharField(validators=class_access_code_validators)

    def get_invalid_login_error_message(self):
        return (
            "Please enter a correct username and password for a class."
            " Double check your class ID is correct and remember that your"
            " username and password are case-sensitive."
        )


class StudentAutoLoginForm(BaseLoginForm[User]):
    """Log in with the user's id."""

    student_id = forms.IntegerField(min_value=1)
    auto_gen_password = forms.CharField(strip=False)

    def get_invalid_login_error_message(self):
        return (
            "Your login link is invalid. Please contact your teacher or the"
            " Code for Life team for support."
        )

class GoogleLoginForm(BaseOAuth2LoginForm[User]):
    """Log in with the user's Google account."""
