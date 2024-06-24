"""
© Ocado Group
Created on 23/01/2024 at 17:53:44(+00:00).
"""
import logging
from datetime import timedelta

from codeforlife.mail import send_mail
from codeforlife.permissions import (
    OR,
    AllowAny,
    AllowNone,
    IsCronRequestFromGoogle,
)
from codeforlife.request import Request
from codeforlife.response import Response
from codeforlife.user.models import User
from codeforlife.user.permissions import IsIndependent, IsTeacher
from codeforlife.user.views import UserViewSet as _UserViewSet
from codeforlife.views import action, cron_job
from django.conf import settings
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.serializers import ValidationError

from ..auth import email_verification_token_generator
from ..serializers import (
    CreateUserSerializer,
    HandleIndependentUserJoinClassRequestSerializer,
    RequestUserPasswordResetSerializer,
    ResetUserPasswordSerializer,
    UpdateUserSerializer,
    VerifyUserEmailAddressSerializer,
)


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class UserViewSet(_UserViewSet):
    http_method_names = ["get", "post", "patch", "delete", "put"]

    # pylint: disable-next=too-many-return-statements
    def get_permissions(self):
        if self.action == "bulk":
            return [AllowNone()]
        if self.action in [
            "create",
            "request_password_reset",
            "reset_password",
            "verify_email_address",
        ]:
            return [AllowAny()]
        if self.action == "handle_join_class_request":
            return [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))]
        if self.action == "destroy" or (
            self.action == "partial_update"
            and "requesting_to_join_class" in self.request.data
        ):
            return [IsIndependent()]
        if self.action in [
            "send_1st_verify_email_reminder",
            "send_2nd_verify_email_reminder",
            "anonymize_unverified_accounts",
        ]:
            return [IsCronRequestFromGoogle()]

        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "create":
            context["user_type"] = "independent"

        return context

    # pylint: disable-next=too-many-return-statements
    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        if self.action == "partial_update":
            return UpdateUserSerializer
        if self.action == "request_password_reset":
            return RequestUserPasswordResetSerializer
        if self.action == "reset_password":
            return ResetUserPasswordSerializer
        if self.action == "handle_join_class_request":
            return HandleIndependentUserJoinClassRequestSerializer
        if self.action == "verify_email_address":
            return VerifyUserEmailAddressSerializer

        return super().get_serializer_class()

    def get_queryset(self, user_class=User):
        if self.action in ["reset_password", "verify_email_address"]:
            return User.objects.filter(pk=self.kwargs["pk"])
        if self.action == "handle_join_class_request":
            return self.request.school_teacher_user.teacher.indy_users

        queryset = super().get_queryset(user_class)
        if self.action == "destroy" or (
            self.action == "partial_update" and self.request.auth_user.student
        ):
            queryset = queryset.filter(pk=self.request.auth_user.pk)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as error:
            codes = error.get_codes()
            assert isinstance(codes, dict)
            email_codes = codes.get("email", [])
            assert isinstance(email_codes, list)
            if any(code == "already_exists" for code in email_codes):
                # NOTE: Always return a 201 here - a noticeable change in
                # behaviour would allow email enumeration.
                return Response(status=status.HTTP_201_CREATED)

            raise error

        self.perform_create(serializer)

        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        self.get_object().anonymize()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def request_password_reset(self, request: Request):
        """
        Generates a reset password URL to be emailed to the user if the
        given email address exists.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as error:
            codes = error.get_codes()
            assert isinstance(codes, dict)
            email_codes = codes.get("email", [])
            assert isinstance(email_codes, list)
            if any(code == "does_not_exist" for code in email_codes):
                # NOTE: Always return a 200 here - a noticeable change in
                # behaviour would allow email enumeration.
                return Response()

            raise error

        return Response()

    @action(
        detail=True,
        url_path="verify-email-address/(?P<token>.+)",
        methods=["get"],
    )
    def verify_email_address(self, request: Request, **url_params: str):
        """
        Verify a user's email address and redirect them back to the login page.

        NOTE: This should normally use HTTP PUT, not GET. However, GET is the
        default method used when users click on the link in their email.
        """
        user = self.get_object()

        serializer = self.get_serializer(
            instance=user, data={**request.data, "token": url_params["token"]}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            status=status.HTTP_303_SEE_OTHER,
            headers={
                "Location": settings.PAGE_TEACHER_LOGIN
                if user.teacher
                else settings.PAGE_INDY_LOGIN
            },
        )

    reset_password = _UserViewSet.update_action("reset_password")
    handle_join_class_request = _UserViewSet.update_action(
        "handle_join_class_request"
    )

    def _get_unverified_users(self, days: int, same_day: bool):
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

    def _send_verify_email_reminder(self, days: int, campaign_name: str):
        teacher_queryset, indy_queryset = self._get_unverified_users(
            days, same_day=True
        )

        user_queryset = teacher_queryset.union(indy_queryset)
        user_count = user_queryset.count()

        logging.info("%d emails unverified.", user_count)

        if user_count > 0:
            sent_email_count = 0
            for user_fields in user_queryset.values("id", "email").iterator(
                chunk_size=500
            ):
                url = settings.SERVICE_API_URL + reverse(
                    "user-verify-email-address",
                    kwargs={
                        "pk": user_fields["id"],
                        "token": email_verification_token_generator.make_token(
                            user_fields["id"]
                        ),
                    },
                )

                try:
                    send_mail(
                        campaign_id=settings.DOTDIGITAL_CAMPAIGN_IDS[
                            campaign_name
                        ],
                        to_addresses=[user_fields["email"]],
                        personalization_values={"VERIFICATION_LINK": url},
                    )

                    sent_email_count += 1
                # pylint: disable-next=broad-exception-caught
                except Exception as ex:
                    logging.exception(ex)

            logging.info("Sent %d/%d emails.", sent_email_count, user_count)

        return Response()

    @cron_job
    def send_1st_verify_email_reminder(self, request: Request):
        """
        Send the first reminder email to all users who have not verified their
        email address.
        """
        return self._send_verify_email_reminder(
            days=7, campaign_name="Verify new user email - first reminder"
        )

    @cron_job
    def send_2nd_verify_email_reminder(self, request: Request):
        """
        Send the second reminder email to all users who have not verified their
        email address.
        """
        return self._send_verify_email_reminder(
            days=14, campaign_name="Verify new user email - second reminder"
        )

    @cron_job
    def anonymize_unverified_accounts(self, request: Request):
        """Anonymize all users who have not verified their email address."""
        user_queryset = User.objects.filter(is_active=True)
        user_count = user_queryset.count()

        teacher_queryset, indy_queryset = self._get_unverified_users(
            days=int(request.query_params.get("days", 19)),
            same_day=False,
        )
        teacher_count = teacher_queryset.count()
        indy_count = indy_queryset.count()

        for user in teacher_queryset.union(indy_queryset).iterator(
            chunk_size=100
        ):
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

        return Response()
