"""
© Ocado Group
Created on 09/02/2024 at 17:02:00(+00:00).

All signals for the SchoolTeacherInvitation model.
"""

from codeforlife.mail import send_mail
from codeforlife.user.models import User
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver

from ..models import SchoolTeacherInvitation

# pylint: disable=unused-argument


@receiver(signals.post_save, sender=SchoolTeacherInvitation)
def school_teacher_invitation__post_save(
    sender,
    instance: SchoolTeacherInvitation,
    created: bool,
    **kwargs,
):
    """Send invitation email to invited teacher."""

    if not created:
        return

    if User.objects.filter(
        email__iexact=instance.invited_teacher_email
    ).exists():
        send_mail(
            settings.DOTDIGITAL_CAMPAIGN_IDS["Invite teacher - account exists"],
            to_addresses=[instance.invited_teacher_email],
            personalization_values={
                "SCHOOL_NAME": instance.school.name,
                "REGISTRATION_LINK": settings.PAGE_REGISTER,
            },
        )
    else:
        send_mail(
            settings.DOTDIGITAL_CAMPAIGN_IDS[
                "Invite teacher - account doesn't exist"
            ],
            to_addresses=[instance.invited_teacher_email],
            personalization_values={
                "SCHOOL_NAME": instance.school.name,
                "REGISTRATION_LINK": settings.PAGE_REGISTER,
            },
        )
