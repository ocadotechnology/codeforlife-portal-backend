"""
© Ocado Group
Created on 23/01/2024 at 11:04:44(+00:00).
"""

import pyotp
from codeforlife.permissions import AllowNone
from codeforlife.request import Request
from codeforlife.response import Response
from codeforlife.user.models import AuthFactor, User
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet, action

from ..serializers import AuthFactorSerializer


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class AuthFactorViewSet(ModelViewSet[User, AuthFactor]):
    request_user_class = User
    model_class = AuthFactor
    http_method_names = ["get", "post", "delete"]
    serializer_class = AuthFactorSerializer

    # pylint: disable-next=missing-function-docstring
    def get_queryset(self):
        queryset = AuthFactor.objects.all()
        user = self.request.teacher_user

        if (
            self.action in ["list", "destroy"]
            and user.teacher.school
            and user.teacher.is_admin
        ):
            return queryset.filter(
                user__new_teacher__school=user.teacher.school
            )

        return queryset.filter(user=user)

    # pylint: disable-next=missing-function-docstring
    def get_permissions(self):
        if self.action in ["retrieve", "bulk"]:
            return [AllowNone()]

        return [IsTeacher()]

    @action(detail=False, methods=["post"])
    def generate_otp_provisioning_uri(self, request: Request[User]):
        """Generate a time-based one-time-password provisioning URI."""
        # TODO: make otp_secret non-nullable and delete code block
        user = request.auth_user
        if not user.userprofile.otp_secret:
            user.userprofile.otp_secret = pyotp.random_base32()
            user.userprofile.save(update_fields=["otp_secret"])

        return Response(user.totp_provisioning_uri, content_type="text/plain")
