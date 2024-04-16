"""
© Ocado Group
Created on 23/01/2024 at 17:54:08(+00:00).
"""

from codeforlife.permissions import AllowNone
from codeforlife.request import Request
from codeforlife.user.models import OtpBypassToken, User
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet, action
from rest_framework import status
from rest_framework.response import Response


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class OtpBypassTokenViewSet(ModelViewSet[User, OtpBypassToken]):
    http_method_names = ["post"]

    def get_queryset(self):
        return OtpBypassToken.objects.filter(user=self.request.teacher_user)

    def get_permissions(self):
        if self.action == "create":
            return [AllowNone()]

        return [IsTeacher()]

    # TODO: replace this custom action with bulk create and list serializer.
    @action(detail=False, methods=["post"])
    def generate(self, request: Request):
        """Generates some OTP bypass tokens for a user."""
        otp_bypass_tokens = OtpBypassToken.objects.bulk_create(
            request.auth_user
        )

        return Response(
            # pylint: disable-next=protected-access
            [otp_bypass_token._token for otp_bypass_token in otp_bypass_tokens],
            status.HTTP_201_CREATED,
        )
