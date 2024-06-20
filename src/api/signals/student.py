"""
© Ocado Group
Created on 17/06/2024 at 15:02:11(+01:00).

All signals for the Student model.
"""

from codeforlife.mail import send_mail
from codeforlife.models.signals import (
    UpdateFields,
    post_save,
    pre_save,
    update_fields_includes,
)
from codeforlife.user.models import Class, Student
from django.conf import settings
from django.db.models.signals import post_save as post_save_signal
from django.db.models.signals import pre_save as pre_save_signal
from django.dispatch import receiver
from django.urls import reverse

from ..auth import email_verification_token_generator

# pylint: disable=unused-argument


@receiver(pre_save_signal, sender=Student)
def student__pre_save(
    sender,
    instance: Student,
    update_fields: UpdateFields,
    **kwargs,
):
    """Before a student is updated."""

    if pre_save.adding(instance):
        return

    if (
        update_fields_includes(update_fields, {"class_field"})
        and instance.class_field is None
        and pre_save.check_previous_values(
            instance, {"class_field": lambda value: value is not None}
        )
    ):
        pre_save.set_previous_values(instance, {"class_field"})

    if update_fields_includes(update_fields, {"pending_class_request"}):
        pre_save.set_previous_values(instance, {"pending_class_request"})


@receiver(post_save_signal, sender=Student)
def student__post_save(
    sender,
    instance: Student,
    created: bool,
    update_fields: UpdateFields,
    **kwargs,
):
    """After a student is updated."""

    if created:
        return

    if (
        update_fields_includes(update_fields, {"class_field"})
        and instance.class_field is None
        and post_save.check_previous_values(
            instance, {"class_field": lambda value: value is not None}
        )
    ):
        previous_class_field = post_save.get_previous_value(
            instance, "class_field", Class
        )

        verify_email_address_link = settings.SERVICE_BASE_URL + reverse(
            "user-verify-email-address",
            kwargs={
                "pk": instance.new_user.pk,
                "token": email_verification_token_generator.make_token(
                    instance.new_user.pk
                ),
            },
        )

        # TODO: user student.user.email_user() in new schema.
        send_mail(
            settings.DOTDIGITAL_CAMPAIGN_IDS["Verify released student email"],
            to_addresses=[instance.new_user.email],
            personalization_values={
                "SCHOOL_NAME": previous_class_field.teacher.school.name,
                "VERIFICATION_LINK": verify_email_address_link,
            },
        )

    if update_fields_includes(update_fields, {"pending_class_request"}):
        if instance.pending_class_request is None:
            if post_save.check_previous_values(
                instance,
                {"pending_class_request": lambda value: value is None},
            ):
                return

            previous_pending_class_request = post_save.get_previous_value(
                instance, "pending_class_request", Class
            )

            if instance.class_field is None:
                # TODO: user student.user.email_user() in new schema.
                send_mail(
                    settings.DOTDIGITAL_CAMPAIGN_IDS[
                        "Student join request rejected"
                    ],
                    to_addresses=[instance.new_user.email],
                    personalization_values={
                        "SCHOOL_NAME": (
                            previous_pending_class_request.teacher.school.name
                        ),
                        "ACCESS_CODE": (
                            previous_pending_class_request.access_code
                        ),
                    },
                )
            else:
                pass
                # TODO: user student.user.email_user() in new schema.
                # send_mail(
                #     settings.DOTDIGITAL_CAMPAIGN_IDS[
                #         "Student join request accepted"
                #     ],
                #     to_addresses=[instance.new_user.email],
                #     personalization_values={
                #         "SCHOOL_NAME": klass.teacher.school.name,
                #         "ACCESS_CODE": klass.access_code,
                #     },
                # )
        else:
            # TODO: user student.user.email_user() in new schema.
            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS[
                    "Student join request notification"
                ],
                to_addresses=[
                    instance.pending_class_request.teacher.new_user.email
                ],
                personalization_values={
                    "USERNAME": instance.new_user.first_name,
                    "EMAIL": instance.new_user.email,
                    "ACCESS_CODE": (instance.pending_class_request.access_code),
                },
            )
