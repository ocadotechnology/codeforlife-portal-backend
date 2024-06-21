"""
© Ocado Group
Created on 03/04/2024 at 14:44:42(+01:00).
"""

from unittest.mock import Mock, call, patch

from codeforlife.user.models import TeacherUser, User, UserProfile
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from ..auth import email_verification_token_generator


# pylint: disable-next=missing-class-docstring
class TestUser(TestCase):
    def test_user_profile__pre_save(self):
        """Creating a new user sets their OTP secret."""
        user = User.objects.create_user(
            username="john.doe@codeforlife.com",
            email="john.doe@codeforlife.com",
            password="password",
            first_name="John",
            last_name="Doe",
        )

        profile = UserProfile.objects.create(user=user)

        assert profile.otp_secret is not None

    def test_pre_save__username(self):
        """Updating the email field also updates the username field."""
        user = TeacherUser.objects.first()
        assert user

        email = "example@codeforelife.com"
        assert user.username != email
        user.email = email

        user.save()
        assert user.username == email

    @patch("src.api.signals.user.send_mail")
    def test_post_save__email_change_notification(self, send_mail: Mock):
        """Updating the email field sends a verification email."""
        user = TeacherUser.objects.first()
        assert user

        previous_email = user.email
        email = "example@codeforelife.com"
        assert previous_email != email
        user.email = email

        with patch.object(
            email_verification_token_generator,
            "make_token",
            return_value=email_verification_token_generator.make_token(user),
        ) as make_token:
            user.save()

            make_token.assert_called_once_with(user.pk)

            send_mail.assert_has_calls(
                [
                    call(
                        settings.DOTDIGITAL_CAMPAIGN_IDS[
                            "Email change notification"
                        ],
                        to_addresses=[previous_email],
                        personalization_values={"NEW_EMAIL_ADDRESS": email},
                    ),
                    call(
                        settings.DOTDIGITAL_CAMPAIGN_IDS[
                            "Verify changed user email"
                        ],
                        to_addresses=[email],
                        personalization_values={
                            "VERIFICATION_LINK": (
                                settings.SERVICE_API_URL
                                + reverse(
                                    "user-verify-email-address",
                                    kwargs={
                                        "pk": user.pk,
                                        "token": make_token.return_value,
                                    },
                                )
                            )
                        },
                    ),
                ]
            )
