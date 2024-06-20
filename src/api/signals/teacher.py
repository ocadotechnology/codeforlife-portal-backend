"""
© Ocado Group
Created on 20/06/2024 at 15:36:58(+01:00).

All signals for the Teacher model.
"""

from codeforlife.mail import send_mail
from codeforlife.models.signals import (
    UpdateFields,
    post_save,
    pre_save,
    update_fields_includes,
)
from codeforlife.user.models import Teacher
from codeforlife.user.signals import teacher_receiver
from django.conf import settings
from django.db.models.signals import post_save as post_save_signal
from django.db.models.signals import pre_save as pre_save_signal

# pylint: disable=unused-argument


@teacher_receiver(pre_save_signal)
def teacher__pre_save(
    sender,
    instance: Teacher,
    update_fields: UpdateFields,
    **kwargs,
):
    """Before a teacher is saved."""

    if pre_save.adding(instance):
        return

    if update_fields_includes(update_fields, {"is_admin"}) and instance.school:
        pre_save.set_previous_values(instance, {"is_admin"})


@teacher_receiver(post_save_signal)
def teacher__post_save(
    sender,
    instance: Teacher,
    created: bool,
    update_fields: UpdateFields,
    **kwargs,
):
    """After a teacher is saved."""

    if created:
        return

    if update_fields_includes(update_fields, {"is_admin"}) and instance.school:
        if instance.is_admin:
            if post_save.check_previous_values(
                instance, {"is_admin": lambda value: not value}
            ):
                send_mail(
                    settings.DOTDIGITAL_CAMPAIGN_IDS["Admin given"],
                    to_addresses=[instance.new_user.email],
                    personalization_values={
                        "SCHOOL_CLUB_NAME": instance.school.name,
                        "MANAGEMENT_LINK": (
                            settings.PAGE_TEACHER_DASHBOARD_SCHOOL
                        ),
                    },
                )
        elif post_save.check_previous_values(
            instance, {"is_admin": lambda value: value}
        ):
            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS["Admin revoked"],
                to_addresses=[instance.new_user.email],
                personalization_values={
                    "SCHOOL_CLUB_NAME": instance.school.name,
                },
            )
