"""
© Ocado Group
Created on 13/02/2024 at 13:44:00(+00:00).
"""

from datetime import timedelta
from unittest.mock import Mock, patch

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    NonSchoolTeacherUser,
    TeacherUser,
    User,
)
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from ..models import SchoolTeacherInvitation
from .school_teacher_invitation import (
    AcceptSchoolTeacherInvitationSerializer,
    RefreshSchoolTeacherInvitationSerializer,
    SchoolTeacherInvitationSerializer,
)

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class TestSchoolTeacherInvitationSerializer(
    ModelSerializerTestCase[User, SchoolTeacherInvitation]
):
    model_serializer_class = SchoolTeacherInvitationSerializer
    fixtures = ["school_1"]

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )

    @patch(
        "src.api.serializers.school_teacher_invitation.make_password",
        return_value="token",
    )
    def test_create(self, invitation_make_password: Mock):
        """Can successfully create."""
        now = timezone.now()
        with patch.object(timezone, "now", return_value=now):
            self.assert_create(
                validated_data={
                    "invited_teacher_first_name": "NewTeacher",
                    "invited_teacher_last_name": "NewTeacher",
                    "invited_teacher_email": "invited@teacher.com",
                    "invited_teacher_is_admin": False,
                },
                new_data={
                    "token": invitation_make_password.return_value,
                    "school": self.admin_school_teacher_user.teacher.school,
                    "from_teacher": self.admin_school_teacher_user.teacher,
                    "expiry": now + timedelta(days=30),
                },
                context={
                    "request": self.request_factory.post(
                        user=self.admin_school_teacher_user
                    )
                },
            )

        invitation_make_password.assert_called_once()


class TestRefreshSchoolTeacherInvitationSerializer(
    ModelSerializerTestCase[User, SchoolTeacherInvitation]
):
    model_serializer_class = RefreshSchoolTeacherInvitationSerializer
    fixtures = ["school_1", "school_1_teacher_invitations"]

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )
        self.invitation = SchoolTeacherInvitation.objects.get(pk=1)

    def test_update(self):
        """Can successfully update."""
        now = timezone.now()
        with patch.object(timezone, "now", return_value=now):
            self.assert_update(
                instance=self.invitation,
                validated_data={},
                new_data={
                    "expiry": now + timedelta(days=30),
                },
            )


class TestAcceptSchoolTeacherInvitationSerializer(
    ModelSerializerTestCase[User, SchoolTeacherInvitation]
):
    model_serializer_class = AcceptSchoolTeacherInvitationSerializer
    fixtures = [
        "school_1",
        "school_1_teacher_invitations",
        "non_school_teacher",
    ]

    def setUp(self):
        self.invitation = SchoolTeacherInvitation.objects.get(pk=1)
        self.non_school_teacher_user = NonSchoolTeacherUser.objects.get(
            email="unverified.teacher@noschool.com"
        )

    def test_validate_user__cannot_update(self):
        """Cannot update an existing user."""
        self.assert_validate_field(
            name="user",
            error_code="cannot_update",
            context={"non_school_teacher_user": self.non_school_teacher_user},
        )

    @patch.object(TeacherUser, "add_contact_to_dot_digital")
    def test_update__new_user(self, add_contact_to_dot_digital: Mock):
        """Can accept an invitation for a new user."""
        user_fields = {
            "first_name": self.invitation.invited_teacher_first_name,
            "last_name": self.invitation.invited_teacher_last_name,
            "password": "password",
            "add_to_newsletter": True,
        }

        with patch(
            "django.contrib.auth.models.make_password",
            return_value=make_password(user_fields["password"]),
        ) as user_make_password:
            self.assert_update(
                instance=self.invitation,
                validated_data={"user": user_fields},
                context={"non_school_teacher_user": None},
                non_model_fields={"user"},
            )

            user_make_password.assert_called_once_with(user_fields["password"])
        add_contact_to_dot_digital.assert_called_once()

        user = TeacherUser.objects.get(
            email=self.invitation.invited_teacher_email
        )
        assert user.first_name == user_fields["first_name"]
        assert user.last_name == user_fields["last_name"]
        assert user.check_password(user_fields["password"])
        assert user.email == self.invitation.invited_teacher_email
        assert user.teacher.school == self.invitation.school
        assert user.teacher.is_admin == self.invitation.invited_teacher_is_admin
        assert user.userprofile.is_verified

    def test_update__existing_user(self):
        """Can accept an invitation for a existing user."""
        user = self.non_school_teacher_user
        assert not user.userprofile.is_verified

        invitation = SchoolTeacherInvitation.objects.get(
            invited_teacher_email=user.email
        )
        assert user.teacher.is_admin != invitation.invited_teacher_is_admin

        self.assert_update(
            instance=invitation,
            validated_data={},
            context={"non_school_teacher_user": user},
        )

        assert user.teacher.school == invitation.school
        assert user.teacher.is_admin == invitation.invited_teacher_is_admin
        assert user.userprofile.is_verified
