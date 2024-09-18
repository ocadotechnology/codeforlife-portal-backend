"""
© Ocado Group
Created on 01/12/2023 at 16:00:24(+00:00).
"""

from codeforlife.user.models import User
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.validators import RegexValidator


class BaseLoginForm(forms.Form):
    """
    Base login form that all other login forms must inherit.
    """

    user: User

    def __init__(self, request: WSGIRequest, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        """Authenticates a user.

        Raises:
            ValidationError: If there are form errors.
            ValidationError: If the user's credentials were incorrect.
            ValidationError: If the user's account is deactivated.

        Returns:
            The cleaned form data.
        """

        if self.errors:
            raise ValidationError(
                "Found form errors. Skipping authentication.",
                code="form_errors",
            )

        user = authenticate(
            self.request,
            **{key: self.cleaned_data[key] for key in self.fields.keys()}
        )
        if user is None:
            raise ValidationError(
                self.get_invalid_login_error_message(),
                code="invalid_login",
            )
        if not isinstance(user, User):
            raise ValidationError(
                "Incorrect user class.",
                code="incorrect_user_class",
            )
        self.user = user

        if not user.is_active:
            raise ValidationError(
                "User is not active",
                code="user_not_active",
            )

        return self.cleaned_data

    def get_invalid_login_error_message(self) -> str:
        """Returns the error message if the user failed to login.

        Raises:
            NotImplementedError: If message is not set.
        """
        raise NotImplementedError()


class EmailLoginForm(BaseLoginForm):
    """Log in with an email address."""

    email = forms.EmailField()
    password = forms.CharField(strip=False)

    def get_invalid_login_error_message(self):
        return (
            "Please enter a correct email and password. Note that both"
            " fields are case-sensitive."
        )


class OtpLoginForm(BaseLoginForm):
    """Log in with an OTP code."""

    otp = forms.CharField(
        validators=[
            RegexValidator(r"^[0-9]{6}$", "Must be 6 digits"),
        ],
    )

    def get_invalid_login_error_message(self):
        return "Please enter the correct one-time password."


class OtpBypassTokenLoginForm(BaseLoginForm):
    """Log in with an OTP-bypass token."""

    token = forms.CharField(min_length=8, max_length=8)

    def get_invalid_login_error_message(self):
        return "Must be exactly 8 characters. A token can only be used once."


class StudentLoginForm(BaseLoginForm):
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


class StudentAutoLoginForm(BaseLoginForm):
    """Log in with the user's id."""

    student_id = forms.IntegerField(min_value=1)
    auto_gen_password = forms.CharField(strip=False)

    def get_invalid_login_error_message(self):
        return (
            "Your login link is invalid. Please contact your teacher or the"
            " Code for Life team for support."
        )
