"""
© Ocado Group
Created on 09/02/2024 at 16:14:00(+00:00).
"""

import typing as t

from codeforlife.mail import send_mail
from codeforlife.permissions import AllowNone
from codeforlife.request import Request
from codeforlife.response import Response
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    NonSchoolTeacherUser,
    User,
)
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet, action
from rest_framework import status
from rest_framework.serializers import ValidationError

from ..models import SchoolTeacherInvitation
from ..permissions import IsInvitedSchoolTeacher
from ..serializers import (
    AcceptSchoolTeacherInvitationSerializer,
    RefreshSchoolTeacherInvitationSerializer,
    SchoolTeacherInvitationSerializer,
)


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class SchoolTeacherInvitationViewSet(
    ModelViewSet[User, SchoolTeacherInvitation]
):
    request_user_class = User
    model_class = SchoolTeacherInvitation
    http_method_names = ["get", "post", "put", "delete"]

    # pylint: disable-next=missing-function-docstring
    def get_permissions(self):
        if self.action in ["accept", "reject"]:
            return [IsInvitedSchoolTeacher()]
        if self.action in [
            "retrieve",
            "list",
            "create",
            "refresh",
            "destroy",
        ]:
            return [IsTeacher(is_admin=True)]
        if self.action == "bulk":
            return [AllowNone()]

        return super().get_permissions()

    # pylint: disable-next=missing-function-docstring
    def get_queryset(self):
        queryset = SchoolTeacherInvitation.objects.all()
        if self.action in ["accept", "reject"]:
            return queryset.filter(pk=self.kwargs["pk"])

        return queryset.filter(
            school=self.request.admin_school_teacher_user.teacher.school
        )

    # pylint: disable-next=missing-function-docstring
    def get_serializer_class(self):
        if self.action == "accept":
            return AcceptSchoolTeacherInvitationSerializer
        if self.action == "refresh":
            return RefreshSchoolTeacherInvitationSerializer

        return SchoolTeacherInvitationSerializer

    refresh = ModelViewSet.update_action("refresh")

    @action(detail=True, methods=["delete"])
    def accept(self, request: Request, **kwargs: str):
        """The invited teacher accepts the invitation."""
        invitation = self.get_object()
        if invitation.is_expired:
            return Response(status=status.HTTP_410_GONE)

        try:
            user = User.objects.get(
                email__iexact=invitation.invited_teacher_email
            )
        except User.DoesNotExist:
            # Inform the FE to display the new-user form.
            if "user" not in request.json_dict:
                return Response(status=status.HTTP_404_NOT_FOUND)

            user = None

        if user:
            if not user.teacher:
                return Response(
                    "You're already registered as a non-teacher user. You'll"
                    " need to delete the existing user before accepting this"
                    " invite.",
                    status=status.HTTP_409_CONFLICT,
                )

            if user.teacher.school:
                return Response(
                    "You're already in a school. You'll need to leave your"
                    " current school before accepting this invite.",
                    status=status.HTTP_409_CONFLICT,
                )

            user = user.as_type(NonSchoolTeacherUser)

        serializer = self.get_serializer(
            invitation,
            data=request.data,
            context={
                **self.get_serializer_context(),
                "non_school_teacher_user": user,
                "user_type": "teacher",
            },
        )

        # pylint: disable=duplicate-code
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as error:
            codes = error.get_codes()
            assert isinstance(codes, dict)
            user_codes = codes.get("user", {})
            assert isinstance(user_codes, dict)
            email_codes = user_codes.get("email", [])
            assert isinstance(email_codes, list)
            if any(code == "already_exists" for code in email_codes):
                # NOTE: Always return a 204 here - a noticeable change in
                # behaviour would allow email enumeration.
                return Response(status=status.HTTP_204_NO_CONTENT)

            raise error
        # pylint: enable=duplicate-code

        serializer.save()

        invitation.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["delete"])
    def reject(self, request: Request, **kwargs: str):
        """The invited teacher rejects the invitation."""
        invitation = self.get_object()

        to_addresses = [invitation.from_teacher.new_user.email]
        # TODO: set max admin teacher count per school <= 10
        # TODO: create the following properties on the school model:
        # - school.teacher_users
        # - school.admin_teachers
        # - school.admin_teacher_users
        # - school.non_admin_teachers
        # - school.non_admin_teacher_users
        cc_addresses: t.List[str] = list(
            AdminSchoolTeacherUser.objects.filter(
                new_teacher__school=invitation.school
            )
            .exclude(id=invitation.from_teacher.new_user_id)
            .values_list("email", flat=True)
        )
        # TODO: set the correct bindings.
        personalization_values = {
            "invited_teacher_email": invitation.invited_teacher_email,
            "invited_teacher_first_name": (
                invitation.invited_teacher_first_name
            ),
            "invited_teacher_last_name": (invitation.invited_teacher_last_name),
        }

        invitation.delete()

        send_mail(
            # TODO: create email template to explain invitation was rejected.
            campaign_id=0,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            personalization_values=personalization_values,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
