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
from codeforlife.user.models import School, Teacher
from codeforlife.user.signals import teacher_receiver
from django.conf import settings
from django.db.models import signals

# pylint: disable=unused-argument


@teacher_receiver(signals.pre_save)
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

    if (
        update_fields_includes(update_fields, {"school"})
        and instance.school is None
        and pre_save.check_previous_values(
            instance, {"school": lambda value: value is not None}
        )
    ):
        pre_save.set_previous_values(instance, {"school"})


@teacher_receiver(signals.post_save)
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

    if update_fields_includes(update_fields, {"school"}):
        if instance.school is None and post_save.check_previous_values(
            instance, {"school": lambda value: value is not None}
        ):
            previous_school = post_save.get_previous_value(
                instance, "school", School
            )

            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS[
                    "Teacher released from school"
                ],
                to_addresses=[instance.new_user.email],
                personalization_values={
                    "SCHOOL_CLUB_NAME": previous_school.name,
                },
            )
