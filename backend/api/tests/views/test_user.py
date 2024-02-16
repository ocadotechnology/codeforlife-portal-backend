"""
© Ocado Group
Created on 20/01/2024 at 10:58:52(+00:00).
"""

import typing as t

from codeforlife.permissions import OR
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    Class,
    SchoolTeacherUser,
    User,
)
from codeforlife.user.permissions import IsTeacher
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from rest_framework import status

from ...views import UserViewSet

# NOTE: type hint to help Intellisense.
default_token_generator: PasswordResetTokenGenerator = default_token_generator


# pylint: disable-next=missing-class-docstring
class TestUserViewSet(ModelViewSetTestCase[User]):
    basename = "user"
    model_view_set_class = UserViewSet
    fixtures = ["independent", "non_school_teacher", "school_1"]

    non_school_teacher_email = "teacher@noschool.com"
    school_teacher_email = "teacher@school1.com"
    indy_email = "indy@man.com"

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )

    def _login_non_admin_school_teacher(self):
        return self.client.login_non_admin_school_teacher(
            email=self.school_teacher_email,
            password="password",
        )

    def _get_pk_and_token_for_user(self, email: str):
        user = User.objects.get(email__iexact=email)
        token = default_token_generator.make_token(user)

        return user.pk, token

    # test: get permissions

    def test_get_permissions__bulk(self):
        """Only school-teachers can perform bulk actions."""
        self.assert_get_permissions(
            permissions=[
                OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))
            ],
            action="bulk",
        )

    def test_get_permissions__partial_update__teacher(self):
        """Only admin-school-teachers can update a teacher."""
        self.assert_get_permissions(
            permissions=[IsTeacher(is_admin=True)],
            action="partial_update",
            request=self.client.request_factory.patch(data={"teacher": {}}),
        )

    def test_get_permissions__partial_update__student(self):
        """Only school-teachers can update a student."""
        self.assert_get_permissions(
            permissions=[
                OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))
            ],
            action="partial_update",
            request=self.client.request_factory.patch(data={"student": {}}),
        )

    # test: get queryset

    def _test_get_queryset__bulk(self, request_method: str):
        assert User.objects.filter(
            new_teacher__school=self.admin_school_teacher_user.teacher.school
        ).exists()

        student_users = list(
            User.objects.filter(
                new_student__class_field__teacher__school=(
                    self.admin_school_teacher_user.teacher.school
                )
            )
        )
        assert student_users

        request = self.client.request_factory.generic(
            request_method, user=self.admin_school_teacher_user
        )

        self.assert_get_queryset(student_users, action="bulk", request=request)

    def test_get_queryset__bulk__patch(self):
        """Bulk partial-update can only target student-users."""
        self._test_get_queryset__bulk("patch")

    def test_get_queryset__bulk__delete(self):
        """Bulk destroy can only target student-users."""
        self._test_get_queryset__bulk("delete")

    # test: bulk actions

    def test_bulk_create__students(self):
        """Teacher can bulk create students."""
        user = self._login_non_admin_school_teacher()

        klass: t.Optional[Class] = user.teacher.class_teacher.first()
        assert klass is not None

        response = self.client.bulk_create(
            [
                {
                    "first_name": "Peter",
                    "student": {"klass": klass.access_code},
                },
                {
                    "first_name": "Mary",
                    "student": {"klass": klass.access_code},
                },
            ],
            make_assertions=False,
        )

        response.json()  # TODO: make custom assertions and check for password

    def test_bulk_destroy(self):
        """School-teacher can bulk anonymize students."""
        self.client.login_as(self.admin_school_teacher_user)

        student_user_queryset = User.objects.filter(
            new_student__class_field__teacher__school=(
                self.admin_school_teacher_user.teacher.school
            ),
        )
        student_user_ids = list(
            student_user_queryset.values_list("id", flat=True)
        )
        assert student_user_ids

        self.client.bulk_destroy(student_user_ids, make_assertions=False)

        assert (
            len(student_user_ids)
            == student_user_queryset.filter(
                first_name="", is_active=False
            ).count()
        )

    # test: reset password actions

    def test_request_password_reset__invalid_email(self):
        """
        Request password reset doesn't generate reset password URL if email
        is invalid but still returns a 200.
        """
        viewname = self.reverse_action("request-password-reset")

        response = self.client.post(
            viewname,
            data={"email": "nonexistent@email.com"},
            status_code_assertion=status.HTTP_200_OK,
        )

        assert response.data is None

    def test_request_password_reset__empty_email(self):
        """Email field is required."""
        viewname = self.reverse_action("request-password-reset")

        response = self.client.post(
            viewname, status_code_assertion=status.HTTP_400_BAD_REQUEST
        )

        assert response.data["email"] == ["Field is required."]

    def test_request_password_reset__valid_email(self):
        """
        Request password reset generates reset password URL for valid email.
        """
        viewname = self.reverse_action("request-password-reset")

        response = self.client.post(
            viewname, data={"email": self.non_school_teacher_email}
        )

        assert response.data["reset_password_url"] is not None
        assert response.data["pk"] is not None
        assert response.data["token"] is not None

    def test_reset_password__invalid_pk(self):
        """Reset password raises 400 on GET with invalid pk"""
        _, token = self._get_pk_and_token_for_user(
            self.non_school_teacher_email
        )

        viewname = self.reverse_action(
            "reset-password", kwargs={"pk": "whatever", "token": token}
        )

        response = self.client.get(
            viewname, status_code_assertion=status.HTTP_400_BAD_REQUEST
        )

        assert response.data["non_field_errors"] == [
            "No user found for given ID."
        ]

    def test_reset_password__invalid_token(self):
        """Reset password raises 400 on GET with invalid token"""
        pk, _ = self._get_pk_and_token_for_user(self.non_school_teacher_email)

        viewname = self.reverse_action(
            "reset-password", kwargs={"pk": pk, "token": "whatever"}
        )

        response = self.client.get(
            viewname, status_code_assertion=status.HTTP_400_BAD_REQUEST
        )

        assert response.data["non_field_errors"] == [
            "Token doesn't match given user."
        ]

    def test_reset_password__get(self):
        """Reset password GET succeeds."""
        pk, token = self._get_pk_and_token_for_user(
            self.non_school_teacher_email
        )

        viewname = self.reverse_action(
            "reset-password", kwargs={"pk": pk, "token": token}
        )

        self.client.get(viewname)

    def test_reset_password__patch__teacher(self):
        """Teacher can successfully update password."""
        pk, token = self._get_pk_and_token_for_user(
            self.non_school_teacher_email
        )

        viewname = self.reverse_action(
            "reset-password", kwargs={"pk": pk, "token": token}
        )

        self.client.patch(viewname, data={"password": "N3wPassword!"})
        self.client.login(
            email=self.non_school_teacher_email,
            password="N3wPassword!",
        )

    def test_reset_password__patch__indy(self):
        """Indy can successfully update password."""
        pk, token = self._get_pk_and_token_for_user(self.indy_email)

        viewname = self.reverse_action(
            "reset-password",
            kwargs={"pk": pk, "token": token},
        )

        self.client.patch(viewname, data={"password": "N3wPassword"})
        self.client.login(email=self.indy_email, password="N3wPassword")

    # test: generic actions

    def test_partial_update__teacher(self):
        """Admin-school-teacher can update another teacher's profile."""
        admin_school_teacher_user = self.client.login_admin_school_teacher(
            email="admin.teacher@school1.com",
            password="password",
        )

        other_school_teacher_user = (
            SchoolTeacherUser.objects.filter(
                new_teacher__school=admin_school_teacher_user.teacher.school
            )
            .exclude(pk=admin_school_teacher_user.pk)
            .first()
        )
        assert other_school_teacher_user

        self.client.partial_update(
            other_school_teacher_user,
            {
                "last_name": other_school_teacher_user.first_name,
                "teacher": {
                    "is_admin": not other_school_teacher_user.teacher.is_admin,
                },
            },
        )
