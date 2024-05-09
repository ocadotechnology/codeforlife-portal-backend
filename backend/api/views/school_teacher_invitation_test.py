"""
© Ocado Group
Created on 09/02/2024 at 17:18:00(+00:00).
"""

import typing as t
from datetime import timedelta
from unittest.mock import Mock, patch

from codeforlife.permissions import AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    School,
    SchoolTeacherUser,
    User,
)
from codeforlife.user.permissions import IsTeacher
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework import status

from ..models import SchoolTeacherInvitation
from ..permissions import IsInvitedSchoolTeacher
from ..serializers import (
    AcceptSchoolTeacherInvitationSerializer,
    RefreshSchoolTeacherInvitationSerializer,
    SchoolTeacherInvitationSerializer,
)
from .school_teacher_invitation import SchoolTeacherInvitationViewSet


# pylint: disable-next=missing-class-docstring,too-many-ancestors,too-many-public-methods
class TestSchoolTeacherInvitationViewSet(
    ModelViewSetTestCase[User, SchoolTeacherInvitation]
):
    basename = "school-teacher-invitation"
    model_view_set_class = SchoolTeacherInvitationViewSet
    fixtures = [
        "independent",
        "non_school_teacher",
        "school_1",
        "school_1_teacher_invitations",
        "school_2",
        "school_2_teacher_invitations",
    ]

    def invited_user_exists(self, invitation: SchoolTeacherInvitation):
        """Check if the invited user exists.

        Args:
            invitation: The invitation sent to the user.

        Returns:
            A flag designating whether the user exists.
        """
        return User.objects.filter(
            email__iexact=invitation.invited_teacher_email
        ).exists()

    def setUp(self):
        self.school = School.objects.get(name="School 1")
        self.school_teacher_user = SchoolTeacherUser.objects.get(
            email="teacher@school1.com"
        )
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )

        self.expired_invitation = SchoolTeacherInvitation.objects.get(pk=1)
        assert self.expired_invitation.is_expired

        self.new_user_invitation = SchoolTeacherInvitation.objects.get(pk=2)
        assert not self.new_user_invitation.is_expired
        assert not self.invited_user_exists(self.new_user_invitation)

        self.existing_indy_user_invitation = (
            SchoolTeacherInvitation.objects.get(
                invited_teacher_email="indy@email.com"
            )
        )
        assert self.invited_user_exists(self.existing_indy_user_invitation)

        self.existing_school_teacher_invitation = (
            SchoolTeacherInvitation.objects.get(
                invited_teacher_email="teacher@school1.com"
            )
        )
        assert self.invited_user_exists(self.existing_school_teacher_invitation)

        self.existing_non_school_teacher_invitation = (
            SchoolTeacherInvitation.objects.get(
                invited_teacher_email="unverified.teacher@noschool.com"
            )
        )
        assert self.invited_user_exists(
            self.existing_non_school_teacher_invitation
        )

    # test: get permissions

    def test_get_permissions__bulk(self):
        """No one is allowed to perform bulk actions."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="bulk",
        )

    def test_get_permissions__create(self):
        """Only admin-teachers can create an invitation."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="create",
        )

    def test_get_permissions__refresh(self):
        """Only admin-teachers can refresh an invitation."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="refresh",
        )

    def test_get_permissions__retrieve(self):
        """Only admin-teachers can retrieve an invitation."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="retrieve",
        )

    def test_get_permissions__list(self):
        """Only admin-teachers can list invitations."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="list",
        )

    def test_get_permissions__destroy(self):
        """Only admin-teachers can destroy an invitation."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="destroy",
        )

    def test_get_permissions__accept(self):
        """Only the invited teacher can accept the invitation."""
        self.assert_get_permissions(
            permissions=[IsInvitedSchoolTeacher()],
            action="accept",
        )

    def test_get_permissions__reject(self):
        """Only the invited teacher can reject the invitation."""
        self.assert_get_permissions(
            permissions=[IsInvitedSchoolTeacher()],
            action="reject",
        )

    # test: get queryset

    def test_get_queryset__refresh(self):
        """Can target only target the invitations in the school."""
        self.assert_get_queryset(
            values=list(self.school.teacher_invitations.all()),
            action="refresh",
            request=self.client.request_factory.put(
                user=self.school_teacher_user
            ),
        )

    def test_get_queryset__retrieve(self):
        """Can target only target the invitations in the school."""
        self.assert_get_queryset(
            values=list(self.school.teacher_invitations.all()),
            action="retrieve",
            request=self.client.request_factory.put(
                user=self.school_teacher_user
            ),
        )

    def test_get_queryset__list(self):
        """Can target only target the invitations in the school."""
        self.assert_get_queryset(
            values=list(self.school.teacher_invitations.all()),
            action="list",
            request=self.client.request_factory.put(
                user=self.school_teacher_user
            ),
        )

    def test_get_queryset__destroy(self):
        """Can target only target the invitations in the school."""
        self.assert_get_queryset(
            values=list(self.school.teacher_invitations.all()),
            action="destroy",
            request=self.client.request_factory.put(
                user=self.school_teacher_user
            ),
        )

    def test_get_queryset__accept(self):
        """Can target the invitation the invited teacher has permissions for."""
        invitation = self.new_user_invitation

        self.assert_get_queryset(
            values=[invitation],
            action="accept",
            kwargs={"pk": invitation.pk},
        )

    def test_get_queryset__reject(self):
        """Can target the invitation the invited teacher has permissions for."""
        invitation = self.new_user_invitation

        self.assert_get_queryset(
            values=[invitation],
            action="reject",
            kwargs={"pk": invitation.pk},
        )

    # test: get serializer class

    def test_get_serializer_class__accept(self):
        """Accepting an invitation has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=AcceptSchoolTeacherInvitationSerializer,
            action="accept",
        )

    def test_get_serializer_class__refresh(self):
        """Refreshing an invitation has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=RefreshSchoolTeacherInvitationSerializer,
            action="refresh",
        )

    def test_get_serializer_class__retrieve(self):
        """Retrieving an invitation uses the general serializer."""
        self.assert_get_serializer_class(
            serializer_class=SchoolTeacherInvitationSerializer,
            action="retrieve",
        )

    def test_get_serializer_class__list(self):
        """Listing the invitations uses the general serializer."""
        self.assert_get_serializer_class(
            serializer_class=SchoolTeacherInvitationSerializer,
            action="list",
        )

    def test_get_serializer_class__create(self):
        """Creating an invitation uses the general serializer."""
        self.assert_get_serializer_class(
            serializer_class=SchoolTeacherInvitationSerializer,
            action="create",
        )

    # test: actions

    def test_create(self):
        """Can successfully create an invitation."""
        user = self.admin_school_teacher_user
        self.client.login_as(user)

        self.client.create(
            {
                "invited_teacher_first_name": "Invited",
                "invited_teacher_last_name": "Teacher",
                "invited_teacher_email": "invited@teacher.com",
                "invited_teacher_is_admin": False,
            },
        )

    def test_list(self):
        """Can successfully list invitations."""
        user = self.admin_school_teacher_user
        self.client.login_as(user)

        self.client.list(models=user.teacher.school.teacher_invitations.all())

    def test_retrieve(self):
        """Can successfully retrieve an invitation."""
        user = self.admin_school_teacher_user
        self.client.login_as(user)

        invitation = t.cast(
            t.Optional[SchoolTeacherInvitation],
            user.teacher.school.teacher_invitations.first(),
        )
        assert invitation

        self.client.retrieve(model=invitation)

    def test_refresh(self):
        """Can successfully refresh an invitation."""
        user = self.admin_school_teacher_user
        self.client.login_as(user)

        invitation = self.expired_invitation

        now = timezone.now()
        with patch.object(timezone, "now", return_value=now):
            self.client.put(self.reverse_action("refresh", invitation))

        invitation.refresh_from_db()
        assert invitation.expiry == now + timedelta(days=30)

    def test_destroy(self):
        """Can successfully destroy an invitation."""
        user = self.admin_school_teacher_user
        self.client.login_as(user)

        invitation = t.cast(
            t.Optional[SchoolTeacherInvitation],
            user.teacher.school.teacher_invitations.first(),
        )
        assert invitation

        self.client.destroy(model=invitation)

        with self.assertRaises(invitation.DoesNotExist):
            invitation.refresh_from_db()

    def test_accept__invalid_token(self):
        """Return 403 status code when user provides an invalid token."""
        invitation = self.new_user_invitation

        self.client.delete(
            self.reverse_action("accept", invitation),
            data={"token": "invalid_token"},
            status_code_assertion=status.HTTP_403_FORBIDDEN,
        )

    def test_accept__expired(self):
        """Return 410 status code when the invitation has expired."""
        invitation = self.expired_invitation

        self.client.delete(
            self.reverse_action("accept", invitation),
            data={"token": "token"},
            status_code_assertion=status.HTTP_410_GONE,
        )

    def test_accept__non_teacher(self):
        """
        Return 409 status code when the invited user already exists as a
        non-teacher.
        """
        invitation = self.existing_indy_user_invitation

        response = self.client.delete(
            self.reverse_action("accept", invitation),
            data={"token": "token"},
            status_code_assertion=status.HTTP_409_CONFLICT,
        )

        assert t.cast(str, response.data).startswith(
            "You're already registered as a non-teacher user."
        )

    def test_accept__in_school(self):
        """
        Return 409 status code when the invited user is already a
        school-teacher.
        """
        invitation = self.existing_school_teacher_invitation

        response = self.client.delete(
            self.reverse_action("accept", invitation),
            data={"token": "token"},
            status_code_assertion=status.HTTP_409_CONFLICT,
        )

        assert t.cast(str, response.data).startswith(
            "You're already in a school."
        )

    def test_accept__user_does_not_exist(self):
        """
        Return 404 status code when the invited user does not exist and no new
        user was specified.
        """
        invitation = self.new_user_invitation

        self.client.delete(
            self.reverse_action("accept", invitation),
            data={"token": "token"},
            status_code_assertion=status.HTTP_404_NOT_FOUND,
        )

    def test_accept__existing_non_school_teacher(self):
        """An existing non-school-teacher accepts the invite."""
        invitation = self.existing_non_school_teacher_invitation

        self.client.delete(
            self.reverse_action("accept", invitation),
            data={"token": "token"},
        )

        user = SchoolTeacherUser.objects.get(
            email=invitation.invited_teacher_email
        )
        assert user.teacher.school == invitation.school
        assert user.teacher.is_admin == invitation.invited_teacher_is_admin
        assert user.userprofile.is_verified

        with self.assertRaises(SchoolTeacherInvitation.DoesNotExist):
            invitation.refresh_from_db()

    @patch.object(SchoolTeacherUser, "add_contact_to_dot_digital")
    def test_accept__create_new_user(self, add_contact_to_dot_digital: Mock):
        """A new user accepts the invite to become a school-teacher."""
        invitation = self.new_user_invitation

        user_fields = {
            "first_name": invitation.invited_teacher_first_name,
            "last_name": invitation.invited_teacher_last_name,
            "password": "Hn87954y97695!@$%&",
            "add_to_newsletter": True,
        }

        with patch(
            "django.contrib.auth.models.make_password",
            return_value=make_password(user_fields["password"]),
        ) as user_make_password:
            self.client.delete(
                self.reverse_action("accept", invitation),
                data={"token": "token", "user": user_fields},
            )

            user_make_password.assert_called_once_with(user_fields["password"])
        add_contact_to_dot_digital.assert_called_once()

        user = SchoolTeacherUser.objects.get(
            email=invitation.invited_teacher_email
        )
        assert user.first_name == user_fields["first_name"]
        assert user.last_name == user_fields["last_name"]
        assert user.check_password(user_fields["password"])
        assert user.email == invitation.invited_teacher_email
        assert user.teacher.school == invitation.school
        assert user.teacher.is_admin == invitation.invited_teacher_is_admin
        assert user.userprofile.is_verified

        with self.assertRaises(SchoolTeacherInvitation.DoesNotExist):
            invitation.refresh_from_db()

    @patch("api.views.school_teacher_invitation.send_mail")
    def test_reject(self, send_mail: Mock):
        """The invited person can reject the invitation."""
        invitation = self.new_user_invitation

        self.client.delete(
            self.reverse_action("reject", invitation),
            data={"token": "token"},
        )

        send_mail.assert_called_once_with(
            campaign_id=0,
            to_addresses=[invitation.from_teacher.new_user.email],
            cc_addresses=list(
                AdminSchoolTeacherUser.objects.filter(
                    new_teacher__school=invitation.school
                )
                .exclude(id=invitation.from_teacher.new_user_id)
                .values_list("email", flat=True)
            ),
            personalization_values={
                "invited_teacher_email": invitation.invited_teacher_email,
                "invited_teacher_first_name": (
                    invitation.invited_teacher_first_name
                ),
                "invited_teacher_last_name": (
                    invitation.invited_teacher_last_name
                ),
            },
        )

        with self.assertRaises(SchoolTeacherInvitation.DoesNotExist):
            invitation.refresh_from_db()
