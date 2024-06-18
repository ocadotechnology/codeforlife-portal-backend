"""
© Ocado Group
Created on 17/06/2024 at 15:02:11(+01:00).

All signals for the Student model.
"""

from codeforlife.mail import send_mail
from codeforlife.models.signals import UpdateFields, update_fields_includes
from codeforlife.models.signals.pre_save import adding, check_previous_values
from codeforlife.user.models import Class, Student
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from ..auth import email_verification_token_generator

# pylint: disable=unused-argument


@receiver(pre_save, sender=Student)
def student__pre_save(
    sender,
    instance: Student,
    update_fields: UpdateFields,
    **kwargs,
):
    """Before a student is updated."""

    if (
        not adding(instance)
        and update_fields_includes(update_fields, {"class_field"})
        and check_previous_values(
            instance,
            {
                "class_field": lambda previous_klass, klass: (
                    previous_klass is not None and klass is None
                )
            },
        )
    ):
        # pylint: disable-next=protected-access
        instance._klass = Student.objects.get(pk=instance.pk).class_field


@receiver(post_save, sender=Student)
def student__post_save(
    sender,
    instance: Student,
    created: bool,
    update_fields: UpdateFields,
    **kwargs,
):
    """After a student is updated."""

    if (
        not created
        and update_fields_includes(update_fields, {"class_field"})
        and not instance.class_field
    ):
        # pylint: disable-next=protected-access
        klass: Class = instance._klass

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
                "SCHOOL_NAME": klass.teacher.school.name,
                "VERIFICATION_LINK": verify_email_address_link,
            },
        )
