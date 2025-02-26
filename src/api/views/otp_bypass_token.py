"""
© Ocado Group
Created on 23/01/2024 at 17:54:08(+00:00).
"""

from codeforlife.permissions import AllowNone
from codeforlife.request import Request
from codeforlife.user.models import AuthFactor, OtpBypassToken, User
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet, action
from rest_framework import status
from rest_framework.response import Response

from ..permissions import HasAuthFactor
from ..serializers import OtpBypassTokenSerializer


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class OtpBypassTokenViewSet(ModelViewSet[User, OtpBypassToken]):
    request_user_class = User
    model_class = OtpBypassToken
    serializer_class = OtpBypassTokenSerializer
    http_method_names = ["get", "post"]

    # pylint: disable-next=missing-function-docstring
    def get_permissions(self):
        if self.action in ["retrieve", "create", "bulk"]:
            return [AllowNone()]

        return [IsTeacher(), HasAuthFactor(AuthFactor.Type.OTP)]

    # pylint: disable-next=missing-function-docstring
    def get_queryset(self):
        return OtpBypassToken.objects.filter(user=self.request.auth_user)

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
        serializer = self.serializer_class(otp_bypass_tokens, many=True)

        return Response(serializer.data, status.HTTP_201_CREATED)
