"""
© Ocado Group
Created on 20/01/2024 at 11:39:26(+00:00).

All signals for the User model.
"""

import pyotp
from codeforlife.models.signals import (
    UpdateFields,
    assert_update_fields_includes,
)
from codeforlife.models.signals.pre_save import (
    adding,
    previous_values_are_unequal,
)
from codeforlife.user.models import StudentUser, TeacherUser, User, UserProfile
from codeforlife.user.signals import user_receiver
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from ..auth import email_verification_token_generator

# pylint: disable=unused-argument


@receiver(pre_save, sender=UserProfile)
def user__pre_save__otp_secret(
    sender, instance: UserProfile, update_fields: UpdateFields, *args, **kwargs
):
    """Set the OTP secret for new users."""
    # TODO: move this to User.otp_secret.default when restructuring.
    if adding(instance):
        assert_update_fields_includes(update_fields, {"otp_secret"})
        instance.otp_secret = pyotp.random_base32()


@user_receiver(pre_save)
def user__pre_save__email(
    sender, instance: User, update_fields: UpdateFields, *args, **kwargs
):
    """Before a user's email field is updated."""
    if (update_fields and "email" in update_fields) or (
        instance.email and previous_values_are_unequal(instance, {"email"})
    ):
        assert_update_fields_includes(update_fields, {"email", "username"})
        # TODO: remove this logic in new data schema. needed for anonymization.
        instance.username = (
            StudentUser.get_random_username()
            if instance.email == ""
            else instance.email
        )


@receiver(post_save, sender=User)
def user__post_save__email(
    sender, instance: User, created: bool, *args, **kwargs
):
    """After a user's email field is updated."""

    if created:
        if instance.teacher:
            verify_email_address_link = settings.SERVICE_BASE_URL + reverse(
                "user-verify-email-address",
                kwargs={
                    "pk": instance.pk,
                    "token": email_verification_token_generator.make_token(
                        instance.pk
                    ),
                },
            )

            teacher_user = instance.as_type(TeacherUser)
            teacher_user.email_user(
                settings.DOTDIGITAL_CAMPAIGN_IDS["Verify new user email"],
                personalization_values={
                    "VERIFICATION_LINK": verify_email_address_link
                },
            )

        # TODO: add nullable date_of_birth field to user model and send
        #   verification email to independents in new schema.
