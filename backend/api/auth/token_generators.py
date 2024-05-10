"""
© Ocado Group
Created on 10/05/2024 at 14:37:36(+01:00).
"""

from datetime import timedelta

import jwt
from codeforlife.user.models import User
from django.conf import settings
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.utils import timezone

# NOTE: type hint to help Intellisense.
password_reset_token_generator: PasswordResetTokenGenerator = (
    default_token_generator
)


class EmailVerificationTokenGenerator:
    """Custom token generator used to verify a user's email address."""

    def _get_audience(self, user: User):
        return f"user:{user.pk}"

    def make_token(self, user: User):
        """Generate a token used to verify user's email address.

        https://pyjwt.readthedocs.io/en/stable/usage.html

        Args:
            user: The user to generate a token for.

        Returns:
            A token used to verify user's email address.
        """
        return jwt.encode(
            payload={
                "exp": (
                    timezone.now()
                    + timedelta(seconds=settings.EMAIL_VERIFICATION_TIMEOUT)
                ),
                "aud": [self._get_audience(user)],
            },
            key=settings.SECRET_KEY,
            algorithm="HS256",
        )

    def check_token(self, user: User, token: str):
        """Check the token belongs to the user and has not expired.

        Args:
            user: The user to check.
            token: The token to check.

        Returns:
            A flag designating whether the token belongs to the user and has not
            expired.
        """
        try:
            jwt.decode(
                jwt=token,
                key=settings.SECRET_KEY,
                audience=self._get_audience(user),
                algorithms=["HS256"],
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidAudienceError):
            return False

        return True


email_verification_token_generator = EmailVerificationTokenGenerator()
