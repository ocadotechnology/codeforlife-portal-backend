"""
© Ocado Group
Created on 09/02/2024 at 17:02:00(+00:00).

All signals for the SchoolTeacherInvitation model.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from ..models import SchoolTeacherInvitation


# pylint: disable=unused-argument
@receiver(post_save, sender=SchoolTeacherInvitation)
def school_teacher_invitation__post_save(
    sender, instance: SchoolTeacherInvitation, *args, **kwargs
):
    """Send invitation email to invited teacher."""

    # instance._token  TODO: send email to invited teacher with differing
    # content based on whether the email is already linked to an account or not.
