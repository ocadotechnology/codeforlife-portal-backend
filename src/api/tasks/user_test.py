"""
© Ocado Group
Created on 31/03/2025 at 18:31:33(+01:00).
"""

from datetime import timedelta
from unittest.mock import call, patch

from codeforlife.tests import CeleryTestCase
from codeforlife.user.models import (
    GoogleUser,
    IndependentUser,
    School,
    Student,
    StudentUser,
    Teacher,
    TeacherUser,
    User,
    UserProfile,
)
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .user import (
    independents_login,
    login_shares,
    student_logins,
    teacher_logins,
    total_registrations,
)

# pylint: disable=missing-class-docstring


class TestUser(CeleryTestCase):
    fixtures = ["school_1", "google_users"]

    def send_inactivity_email_reminder(self, days: int, campaign_name: str):
        """Test an inactivity email reminder is sent under conditions."""

        def test(_days: int, mail_sent: bool):
            date_joined = timezone.now() - timedelta(_days, hours=12)
            last_login = timezone.now() - timedelta(_days, hours=12)

            assert StudentUser.objects.update(date_joined=date_joined)

            TeacherUser.objects.update(date_joined=date_joined, last_login=None)
            IndependentUser.objects.update(last_login=last_login)

            teacher_users = list(TeacherUser.objects.all())
            assert teacher_users
            indy_users = list(IndependentUser.objects.all())
            assert indy_users

            with patch("src.api.tasks.user.send_mail") as send_mail_mock:
                self.apply_task(
                    "src.api.tasks.user.send_inactivity_email_reminder",
                    kwargs={"days": days, "campaign_name": campaign_name},
                )

                if mail_sent:
                    send_mail_mock.assert_has_calls(
                        [
                            call(
                                campaign_id=(
                                    settings.DOTDIGITAL_CAMPAIGN_IDS[
                                        campaign_name
                                    ]
                                ),
                                to_addresses=[user.email],
                            )
                            for user in teacher_users + indy_users
                        ],
                        any_order=True,
                    )
                else:
                    send_mail_mock.assert_not_called()

        test(_days=days - 1, mail_sent=False)
        test(_days=days, mail_sent=True)
        test(_days=days + 1, mail_sent=False)

    def test_send_1st_inactivity_email_reminder(self):
        """Can send the 1st inactivity email reminder."""
        self.send_inactivity_email_reminder(
            days=730, campaign_name="Inactive users on website - first reminder"
        )

    def test_send_2nd_inactivity_email_reminder(self):
        """Can send the 2nd inactivity email reminder."""
        self.send_inactivity_email_reminder(
            days=973,
            campaign_name="Inactive users on website - second reminder",
        )

    def test_send_final_inactivity_email_reminder(self):
        """Can send the final inactivity email reminder."""
        self.send_inactivity_email_reminder(
            days=1065,
            campaign_name="Inactive users on website - final reminder",
        )

    def send_verify_email_reminder(self, days: int, campaign_name: str):
        """Test a verify email reminder is sent under conditions."""

        def test(_days: int, is_verified: bool, mail_sent: bool):
            date_joined = timezone.now() - timedelta(_days, hours=12)

            assert StudentUser.objects.update(date_joined=date_joined)

            teacher_users = list(TeacherUser.objects.all())
            assert teacher_users
            indy_users = list(IndependentUser.objects.all())
            assert indy_users
            for user in teacher_users + indy_users:
                user.date_joined = date_joined
                user.save()
                user.userprofile.is_verified = is_verified
                user.userprofile.save()

            with patch(
                # pylint: disable-next=line-too-long
                "src.api.tasks.user.email_verification_token_generator.make_token",
                side_effect=lambda user_id, email: user_id,
            ) as make_token:
                with patch("src.api.tasks.user.send_mail") as send_mail_mock:
                    self.apply_task(
                        "src.api.tasks.user.send_verify_email_reminder",
                        kwargs={"days": days, "campaign_name": campaign_name},
                    )

                    if mail_sent:
                        make_token.assert_has_calls(
                            [
                                call(user.id, user.email)
                                for user in teacher_users + indy_users
                            ],
                            any_order=True,
                        )
                        send_mail_mock.assert_has_calls(
                            [
                                call(
                                    campaign_id=(
                                        settings.DOTDIGITAL_CAMPAIGN_IDS[
                                            campaign_name
                                        ]
                                    ),
                                    to_addresses=[user.email],
                                    personalization_values={
                                        # pylint: disable-next=line-too-long
                                        "VERIFICATION_LINK": (
                                            settings.SERVICE_BASE_URL
                                            + reverse(
                                                "user-verify-email-address",
                                                kwargs={
                                                    "pk": user.id,
                                                    "token": user.id,
                                                },
                                            )
                                        )
                                    },
                                )
                                for user in teacher_users + indy_users
                            ],
                            any_order=True,
                        )
                    else:
                        make_token.assert_not_called()
                        send_mail_mock.assert_not_called()

        test(_days=days - 1, is_verified=False, mail_sent=False)
        test(_days=days, is_verified=False, mail_sent=True)
        test(_days=days, is_verified=True, mail_sent=False)
        test(_days=days + 1, is_verified=False, mail_sent=False)

    def test_send_1st_verify_email_reminder(self):
        """Can send the 1st verify email reminder."""
        self.send_verify_email_reminder(
            days=7, campaign_name="Verify new user email - first reminder"
        )

    def test_send_2nd_verify_email_reminder(self):
        """Can send the 2nd verify email reminder."""
        self.send_verify_email_reminder(
            days=14, campaign_name="Verify new user email - second reminder"
        )

    def test_anonymize_users_with_unverified_emails(self):
        """Can anonymize users with unverified emails."""

        def check_anonymized(user: User):
            """Check if a user is anonymized.

            Args:
                user: The user to check.
            """
            user.refresh_from_db()
            return (
                user.first_name == ""
                and user.last_name == ""
                and user.email == ""
                and not user.is_active
            )

        def test(days: int, is_verified: bool, is_anonymized: bool):
            date_joined = timezone.now() - timedelta(days=days, hours=12)

            assert StudentUser.objects.update(date_joined=date_joined)

            # Create teacher user.
            teacher_user = User.objects.create(
                first_name="Unverified",
                last_name="Teacher",
                username="unverified.teacher@codeforlife.com",
                email="unverified.teacher@codeforlife.com",
                date_joined=date_joined,
            )
            teacher_user_profile = UserProfile.objects.create(
                user=teacher_user,
                is_verified=is_verified,
            )
            Teacher.objects.create(
                user=teacher_user_profile,
                new_user=teacher_user,
                school=School.objects.get(name="School 1"),
            )

            # Create independent user.
            indy_user = User.objects.create(
                first_name="Unverified",
                last_name="IndependentStudent",
                username="unverified.independentstudent@codeforlife.com",
                email="unverified.independentstudent@codeforlife.com",
                date_joined=date_joined,
            )
            indy_user_profile = UserProfile.objects.create(
                user=indy_user,
                is_verified=is_verified,
            )
            Student.objects.create(
                user=indy_user_profile,
                new_user=indy_user,
            )

            self.apply_task("src.api.tasks.user.anonymize_unverified_emails")

            for student_user in StudentUser.objects.all():
                assert not check_anonymized(student_user)

            assert is_anonymized == check_anonymized(teacher_user)
            assert is_anonymized == check_anonymized(indy_user)

            teacher_user.delete()
            indy_user.delete()

        test(days=18, is_verified=False, is_anonymized=False)
        test(days=19, is_verified=False, is_anonymized=True)
        test(days=19, is_verified=True, is_anonymized=False)
        test(days=20, is_verified=False, is_anonymized=True)

    def test_sync_google_users(self):
        """Can sync all Google-users."""
        with patch.object(GoogleUser.objects, "sync") as sync:
            self.apply_task("src.api.tasks.user.sync_google_users")

            sync.assert_has_calls(
                [
                    call(id=user_id)
                    for user_id in GoogleUser.objects.values_list(
                        "id", flat=True
                    )
                ]
            )

    # data warehouse tasks

    def test_teacher_logins(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=teacher_logins)

    def test_independents_login(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=independents_login)

    def test_student_logins(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=student_logins)

    def test_total_registrations(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=total_registrations)

    def test_login_shares(self):
        """Assert the queryset returns the expected fields."""
        self.assert_data_warehouse_task(task=login_shares)
