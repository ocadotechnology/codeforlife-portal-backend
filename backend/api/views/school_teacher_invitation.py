"""
© Ocado Group
Created on 09/02/2024 at 16:14:00(+00:00).
"""
from codeforlife.permissions import AllowAny, AllowNone
from codeforlife.request import Request
from codeforlife.user.models import User
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet, action
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.response import Response

from ..models import SchoolTeacherInvitation
from ..serializers import (
    CreateTeacherSerializer,
    SchoolTeacherInvitationSerializer,
)


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class SchoolTeacherInvitationViewSet(
    ModelViewSet[User, SchoolTeacherInvitation]
):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = SchoolTeacherInvitationSerializer

    def get_permissions(self):
        if self.action == "accept":
            return [AllowAny()]
        if self.action in [
            "retrieve",
            "list",
            "create",
            "partial_update",
            "destroy",
        ]:
            return [IsTeacher(is_admin=True)]
        if self.action == "bulk":
            return [AllowNone()]

        return super().get_permissions()

    def get_queryset(self):
        queryset = SchoolTeacherInvitation.objects.all()
        if self.action == "accept":
            return queryset

        return queryset.filter(
            school=self.request.admin_school_teacher_user.teacher.school
        )

    # TODO: use serializer and custom update (HTTP PUT) action
    @action(
        detail=True, methods=["get", "post"], url_path="accept/(?P<token>.+)"
    )
    def accept(self, request: Request, token: str, **kwargs: str):
        """
        Handles accepting a teacher's invitation to join their school. On GET,
        checks validity of the invitation token. On PATCH, rechecks this
        param, performs password validation and creates the new Teacher.
        """
        invitation = self.get_object()

        if not check_password(token, invitation.token):
            return Response(
                {"non_field_errors": ["Incorrect token."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.is_expired:
            return Response(
                {"non_field_errors": ["The invitation has expired."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(
            email__iexact=invitation.invited_teacher_email
        ).exists():
            return Response(
                {
                    "non_field_errors": [
                        "It looks like an account is already registered with "
                        "this email address. You will need to delete the other "
                        "account first or change the email associated with it "
                        "in order to proceed. You will then be able to access "
                        "this page."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            context = self.get_serializer_context()
            context["is_verified"] = True
            context["user_type"] = "teacher"
            context["school"] = invitation.school

            data = {
                "first_name": invitation.invited_teacher_first_name,
                "last_name": invitation.invited_teacher_last_name,
                "email": invitation.invited_teacher_email,
                **request.data,
                "teacher": {
                    "is_admin": invitation.invited_teacher_is_admin,
                    **request.data.get("teacher", {}),
                },
            }

            serializer = CreateTeacherSerializer(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            invitation.delete()

        return Response()
