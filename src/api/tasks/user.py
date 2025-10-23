"""
© Ocado Group
Created on 31/03/2025 at 18:06:49(+01:00).
"""

import logging
from datetime import timedelta

from codeforlife.mail import send_mail
from codeforlife.tasks import DataWarehouseTask, shared_task
from codeforlife.user.models import GoogleUser, User
from common.models import UserSession  # type: ignore[import-untyped]
from django.conf import settings
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from ..auth import email_verification_token_generator


@shared_task
def send_inactivity_email_reminder(days: int, campaign_name: str):
    """Send email reminders to teacher- and independent-users who haven't been
    active in a while.

    Args:
        days: How many days the user has been inactive for.
        campaign_name: The name of the email campaign to send them.
    """

    now = timezone.now()

    # All users who haven't logged in in X days OR who've never logged in
    # and registered over X days ago.
    user_queryset = (
        User.objects.filter(
            Q(
                last_login__isnull=False,
                last_login__lte=now - timedelta(days=days),
                last_login__gt=now - timedelta(days=days + 1),
            )
            | Q(
                last_login__isnull=True,
                date_joined__lte=now - timedelta(days=days),
                date_joined__gt=now - timedelta(days=days + 1),
            )
        )
        .exclude(email__isnull=True)
        .exclude(email="")
    )

    user_count = user_queryset.count()

    logging.info("%d inactive users after %d days.", user_count, days)

    if user_count > 0:
        sent_email_count = 0
        for email in user_queryset.values_list("email", flat=True).iterator(
            chunk_size=500
        ):
            try:
                send_mail(
                    campaign_id=settings.DOTDIGITAL_CAMPAIGN_IDS[campaign_name],
                    to_addresses=[email],
                )

                sent_email_count += 1
            except Exception as ex:  # pylint: disable=broad-exception-caught
                logging.exception(ex)

        logging.info(
            "Reminded %d/%d inactive users.", sent_email_count, user_count
        )


def _get_unverified_users(days: int, same_day: bool):
    now = timezone.now()

    # All expired unverified users.
    user_queryset = User.objects.filter(
        date_joined__lte=now - timedelta(days=days),
        userprofile__is_verified=False,
    )
    if same_day:
        user_queryset = user_queryset.filter(
            date_joined__gt=now - timedelta(days=days + 1)
        )

    teacher_queryset = user_queryset.filter(
        new_teacher__isnull=False,
        new_student__isnull=True,
    )
    independent_student_queryset = user_queryset.filter(
        new_teacher__isnull=True,
        new_student__class_field__isnull=True,
    )

    return teacher_queryset, independent_student_queryset


@shared_task
def send_verify_email_reminder(days: int, campaign_name: str):
    """Send email reminders to teacher- and independent-users who haven't
    verified their email in a while.

    Args:
        days: How many days the user hasn't verified their email for.
        campaign_name: The name of the email campaign to send them.
    """

    teacher_queryset, indy_queryset = _get_unverified_users(days, same_day=True)

    user_queryset = teacher_queryset.union(indy_queryset)
    user_count = user_queryset.count()

    logging.info("%d emails unverified.", user_count)

    if user_count > 0:
        sent_email_count = 0
        for user_fields in user_queryset.values("id", "email").iterator(
            chunk_size=500
        ):
            url = settings.SERVICE_BASE_URL + reverse(
                "user-verify-email-address",
                kwargs={
                    "pk": user_fields["id"],
                    "token": email_verification_token_generator.make_token(
                        user_fields["id"], user_fields["email"]
                    ),
                },
            )

            try:
                send_mail(
                    campaign_id=settings.DOTDIGITAL_CAMPAIGN_IDS[campaign_name],
                    to_addresses=[user_fields["email"]],
                    personalization_values={"VERIFICATION_LINK": url},
                )

                sent_email_count += 1
            # pylint: disable-next=broad-exception-caught
            except Exception as ex:
                logging.exception(ex)

        logging.info("Sent %d/%d emails.", sent_email_count, user_count)


@shared_task
def anonymize_unverified_emails():
    """Anonymize all users who have not verified their email address."""

    user_queryset = User.objects.filter(is_active=True)
    user_count = user_queryset.count()

    teacher_queryset, indy_queryset = _get_unverified_users(
        days=19, same_day=False
    )
    teacher_count = teacher_queryset.count()
    indy_count = indy_queryset.count()

    for user in teacher_queryset.union(indy_queryset).iterator(chunk_size=100):
        try:
            user.anonymize()
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            logging.error("Failed to anonymise user with id: %d", user.id)
            logging.exception(ex)

    logging.info(
        "%d unverified users anonymised.",
        user_count - user_queryset.count(),
    )

    # Use data warehouse in new system.
    # pylint: disable-next=import-outside-toplevel
    from common.models import (  # type: ignore[import-untyped]
        DailyActivity,
        TotalActivity,
    )

    activity_today = DailyActivity.objects.get_or_create(
        date=timezone.now().date()
    )[0]
    activity_today.anonymised_unverified_teachers = teacher_count
    activity_today.anonymised_unverified_independents = indy_count
    activity_today.save()
    TotalActivity.objects.update(
        anonymised_unverified_teachers=F("anonymised_unverified_teachers")
        + teacher_count,
        anonymised_unverified_independents=F(
            "anonymised_unverified_independents"
        )
        + indy_count,
    )


@shared_task
def sync_google_users():
    """Sync all users have linked their account with Google."""
    for user_id in GoogleUser.objects.values_list("id", flat=True).iterator(
        chunk_size=2000
    ):
        try:
            GoogleUser.objects.sync(id=user_id)
        # pylint: disable-next=broad-exception-caught
        except Exception as ex:
            logging.error("Failed to sync Google-user with id: %d", user_id)
            logging.exception(ex)


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="overwrite",
        chunk_size=1000,
        fields=["user_id", "school_id", "login_time", "country"],
        id_field="user_id",
    )
)
def teacher_logins():
    """
    Collects data from the UserSession table mainly. Used to report on login
    data for teachers (in annual report).

    https://console.cloud.google.com/bigquery?tc=europe:674837bb-0000-25c8-a14c-f40304387e64&project=decent-digit-629&ws=!1m0
    """
    return UserSession.objects.filter(user__new_teacher__isnull=False).annotate(
        country=F("school__country"),
    )


@DataWarehouseTask.shared(
    DataWarehouseTask.Settings(
        bq_table_write_mode="overwrite",
        chunk_size=1000,
        fields=["user_id", "login_time"],
        id_field="user_id",
    )
)
def independents_login():
    """
    Collects data from the UserSession table mainly. Used to report on login
    data for independents (in annual report).

    https://console.cloud.google.com/bigquery?tc=europe:67483b33-0000-25c8-a14c-f40304387e64&project=decent-digit-629&ws=!1m0
    """
    return UserSession.objects.filter(
        user__new_student__isnull=False,
        user__new_student__class_field__isnull=True,
    )
