"""
© Ocado Group
Created on 20/01/2024 at 11:39:26(+00:00).

All signals for the User model.
"""

import pyotp
from codeforlife.mail import send_mail
from codeforlife.models.signals import (
    UpdateFields,
    post_save,
    pre_save,
    update_fields_includes,
)
from codeforlife.user.models import StudentUser, TeacherUser, User, UserProfile
from codeforlife.user.signals import user_receiver
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from django.urls import reverse

from ..auth import email_verification_token_generator

# pylint: disable=unused-argument


@receiver(signals.pre_save, sender=UserProfile)
def user_profile__pre_save(
    sender,
    instance: UserProfile,
    update_fields: UpdateFields,
    **kwargs,
):
    """Set the OTP secret for new users."""
    # TODO: move this to User.otp_secret.default when restructuring.
    if pre_save.adding(instance):
        if update_fields:
            assert update_fields_includes(update_fields, {"otp_secret"})
        instance.otp_secret = pyotp.random_base32()


@user_receiver(signals.pre_save)
def user__pre_save(
    sender,
    instance: User,
    update_fields: UpdateFields,
    **kwargs,
):
    """Before a user is saved."""

    if update_fields_includes(update_fields, {"email"}) or (
        instance.email
        and pre_save.previous_values_are_unequal(instance, {"email"})
    ):
        if update_fields:
            assert update_fields_includes(update_fields, {"email", "username"})

        if not pre_save.adding(instance):
            pre_save.set_previous_values(instance, {"email"})

        # TODO: remove this logic in new data schema. needed for anonymization.
        instance.username = (
            StudentUser.get_random_username()
            if instance.email == ""
            else instance.email
        )


@user_receiver(signals.post_save)
def user__post_save(
    sender,
    instance: User,
    created: bool,
    update_fields: UpdateFields,
    **kwargs,
):
    """After a user is saved."""

    if created:
        if isinstance(instance, User) and instance.teacher:
            verify_email_address_link = settings.SERVICE_API_URL + reverse(
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

    elif instance.email != "":
        if post_save.check_previous_values(
            instance,
            {
                "email": lambda value: (
                    isinstance(value, str)
                    and value.lower() not in ["", instance.email.lower()]
                )
            },
        ):
            previous_email = post_save.get_previous_value(
                instance, "email", str
            )

            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS["Email change notification"],
                to_addresses=[previous_email],
                personalization_values={"NEW_EMAIL_ADDRESS": instance.email},
            )

            verify_email_address_link = settings.SERVICE_API_URL + reverse(
                "user-verify-email-address",
                kwargs={
                    "pk": instance.pk,
                    "token": email_verification_token_generator.make_token(
                        instance.pk
                    ),
                },
            )

            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS["Verify changed user email"],
                to_addresses=[instance.email],
                personalization_values={
                    "VERIFICATION_LINK": verify_email_address_link
                },
            )
    # TODO: remove in new schema
    elif (
        instance.email == ""
        and isinstance(instance, User)
        and (not instance.student or not instance.student.class_field)
        and post_save.previous_values_are_unequal(instance, {"email"})
    ):
        send_mail(
            settings.DOTDIGITAL_CAMPAIGN_IDS["Account deletion"],
            to_addresses=[instance.email],
        )


@user_receiver(signals.post_delete)
def user__post_delete(sender, instance: User, **kwargs):
    """After a user is deleted."""
    send_mail(
        settings.DOTDIGITAL_CAMPAIGN_IDS["Account deletion"],
        to_addresses=[instance.email],
    )
