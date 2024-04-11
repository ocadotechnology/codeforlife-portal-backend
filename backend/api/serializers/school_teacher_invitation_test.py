"""
© Ocado Group
Created on 13/02/2024 at 13:44:00(+00:00).
"""
import datetime
from unittest.mock import patch

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import AdminSchoolTeacherUser, User
from django.utils import timezone

from ..models import SchoolTeacherInvitation
from .school_teacher_invitation import SchoolTeacherInvitationSerializer


# pylint: disable-next=missing-class-docstring
class TestSchoolTeacherInvitationSerializer(
    ModelSerializerTestCase[User, SchoolTeacherInvitation]
):
    model_serializer_class = SchoolTeacherInvitationSerializer
    fixtures = ["school_1", "school_1_teacher_invitations"]

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )
        self.invitation = SchoolTeacherInvitation.objects.get(pk=1)

    @patch(
        "api.serializers.school_teacher_invitation.make_password",
        return_value="token",
    )
    def test_create(self, _):
        """Can successfully create."""
        now = timezone.now()
        with patch.object(timezone, "now", return_value=now):
            self.assert_create(
                {
                    "invited_teacher_first_name": "NewTeacher",
                    "invited_teacher_last_name": "NewTeacher",
                    "invited_teacher_email": "invited@teacher.com",
                    "invited_teacher_is_admin": False,
                },
                new_data={
                    "token": "token",
                    "school": self.admin_school_teacher_user.teacher.school,
                    "from_teacher": self.admin_school_teacher_user.teacher,
                    "expiry": now + datetime.timedelta(days=30),
                },
                context={
                    "request": self.request_factory.post(
                        user=self.admin_school_teacher_user
                    )
                },
            )

    def test_update(self):
        """Can successfully update."""
        now = timezone.now()
        with patch.object(timezone, "now", return_value=now):
            self.assert_update(
                self.invitation,
                {},
                new_data={
                    "expiry": now + datetime.timedelta(days=30),
                },
            )
