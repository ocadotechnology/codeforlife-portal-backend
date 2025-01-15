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
    request_user_class = User
    model_class = OtpBypassToken
    http_method_names = ["post"]

    def get_permissions(self):
        if self.action in ["create", "bulk"]:
            return [AllowNone()]

        return [IsTeacher()]

    # TODO: replace this custom action with bulk create and list serializer.
    @action(detail=False, methods=["post"])
    def generate(self, request: Request):
        """
        Generates some OTP bypass tokens for a user.

        NOTE: Cannot use bulk_create action as it expects data fields to be
        passed.
        """
        otp_bypass_tokens = OtpBypassToken.objects.bulk_create(
            request.auth_user
        )

        return Response(
            # pylint: disable-next=protected-access
            [otp_bypass_token._token for otp_bypass_token in otp_bypass_tokens],
            status.HTTP_201_CREATED,
        )
