"""
© Ocado Group
Created on 23/01/2024 at 17:53:44(+00:00).
"""
from codeforlife.permissions import OR, AllowAny, AllowNone
from codeforlife.request import Request
from codeforlife.response import Response
from codeforlife.user.models import User
from codeforlife.user.permissions import IsIndependent, IsTeacher
from codeforlife.user.views import UserViewSet as _UserViewSet
from codeforlife.views import action
from rest_framework import status
from rest_framework.serializers import ValidationError

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

    reset_password = _UserViewSet.update_action("reset_password")
    handle_join_class_request = _UserViewSet.update_action(
        "handle_join_class_request"
    )
    verify_email_address = _UserViewSet.update_action("verify_email_address")
