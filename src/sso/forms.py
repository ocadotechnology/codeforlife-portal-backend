"""
© Ocado Group
Created on 01/12/2023 at 16:00:24(+00:00).
"""

from codeforlife.forms import BaseLoginForm
from codeforlife.user.models import User
from django import forms
from django.core.validators import RegexValidator


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

    otp = forms.CharField(
        validators=[
            RegexValidator(r"^[0-9]{6}$", "Must be 6 digits"),
        ],
    )

    def get_invalid_login_error_message(self):
        return "Please enter the correct one-time password."


class OtpBypassTokenLoginForm(BaseLoginForm[User]):
    """Log in with an OTP-bypass token."""

    token = forms.CharField(min_length=8, max_length=8)

    def get_invalid_login_error_message(self):
        return "Must be exactly 8 characters. A token can only be used once."


class StudentLoginForm(BaseLoginForm[User]):
    """Log in as a student."""

    first_name = forms.CharField()
    password = forms.CharField(strip=False)
    class_id = forms.CharField(
        validators=[
            RegexValidator(
                r"^[A-Z]{2}([0-9]{3}|[A-Z]{3})$",
                (
                    "Must be 5 upper case letters or 2 upper case letters"
                    " followed by 3 digits"
                ),
            ),
        ],
    )

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
