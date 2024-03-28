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
from codeforlife.user.models import StudentUser, User, UserProfile
from codeforlife.user.signals import user_receiver
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

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
def user__post_save__email(sender, instance: User, *args, **kwargs):
    """After a user's email field is updated."""
    # TODO: send verification email
    # TODO: ensure that the correct verification email is sent depending on
    #  the user's age if they're independent
