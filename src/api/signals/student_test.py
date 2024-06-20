"""
© Ocado Group
Created on 17/06/2024 at 15:02:15(+01:00).
"""

from unittest.mock import Mock, patch

from codeforlife.user.models import Student
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from ..auth import email_verification_token_generator


# pylint: disable-next=missing-class-docstring
class TestStudent(TestCase):
    fixtures = ["school_1"]

    def test_pre_save(self):
        """Releasing a student from a class sets the class' previous value."""
        student = Student.objects.filter(class_field__isnull=False).first()
        assert student

        klass = student.class_field

        student.class_field = None
        student.save(update_fields=["class_field"])

        assert student.previous_class_field == klass

    @patch("src.api.signals.student.send_mail")
    def test_post_save(self, send_mail: Mock):
        """Releasing a student from a class sends them an email."""
        student = Student.objects.filter(class_field__isnull=False).first()
        assert student

        klass = student.class_field
        student.class_field = None

        email_verification_token = (
            email_verification_token_generator.make_token(student.new_user.pk)
        )

        with patch.object(
            email_verification_token_generator,
            "make_token",
            return_value=email_verification_token,
        ) as make_token:
            student.save(update_fields=["class_field"])

            make_token.assert_called_once_with(student.new_user.pk)

        send_mail.assert_called_once_with(
            settings.DOTDIGITAL_CAMPAIGN_IDS["Verify released student email"],
            to_addresses=[student.new_user.email],
            personalization_values={
                "SCHOOL_NAME": klass.teacher.school.name,
                "VERIFICATION_LINK": settings.SERVICE_BASE_URL
                + reverse(
                    "user-verify-email-address",
                    kwargs={
                        "pk": student.new_user.pk,
                        "token": email_verification_token,
                    },
                ),
            },
        )
