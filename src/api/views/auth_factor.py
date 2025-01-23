"""
© Ocado Group
Created on 23/01/2024 at 11:04:44(+00:00).
"""

import pyotp
from codeforlife.permissions import NOT, AllowNone
from codeforlife.request import Request
from codeforlife.response import Response
from codeforlife.user.models import AuthFactor, User
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet, action

from ..filters import AuthFactorFilterSet
from ..permissions import HasAuthFactor
from ..serializers import (
    AuthFactorSerializer,
    CheckIfAuthFactorExistsSerializer,
)


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class AuthFactorViewSet(ModelViewSet[User, AuthFactor]):
    request_user_class = User
    model_class = AuthFactor
    http_method_names = ["get", "post", "delete"]
    filterset_class = AuthFactorFilterSet

    # pylint: disable-next=missing-function-docstring
    def get_serializer_class(self):
        if self.action == "check_if_exists":
            return CheckIfAuthFactorExistsSerializer

        return AuthFactorSerializer

    # pylint: disable-next=missing-function-docstring
    def get_queryset(self):
        queryset = AuthFactor.objects.all()
        user = self.request.teacher_user

        if (
            self.action in ["list", "destroy", "check_if_exists"]
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
        if self.action == "get_otp_secret":
            return [IsTeacher(), NOT(HasAuthFactor(AuthFactor.Type.OTP))]

        return [IsTeacher()]

    @action(detail=False, methods=["post"])
    def check_if_exists(self, request: Request[User]):
        """Check if an auth factor exists for the requesting user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "auth_factor_exists": self.get_queryset()
                .filter(**serializer.validated_data)
                .exists()
            }
        )

    @action(detail=False, methods=["get"])
    def get_otp_secret(self, request: Request[User]):
        """Get the secret for the user's one-time-password."""
        # TODO: make otp_secret non-nullable and delete code block
        user = request.auth_user
        if not user.userprofile.otp_secret:
            user.userprofile.otp_secret = pyotp.random_base32()
            user.userprofile.save(update_fields=["otp_secret"])

        return Response(
            {
                "secret": user.totp.secret,
                "provisioning_uri": user.totp_provisioning_uri,
            }
        )
