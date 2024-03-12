"""
© Ocado Group
Created on 20/01/2024 at 10:58:52(+00:00).
"""
import typing as t

from codeforlife.permissions import OR, AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.types import JsonDict
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    Class,
    IndependentUser,
    NonAdminSchoolTeacherUser,
    NonSchoolTeacherUser,
    SchoolTeacherUser,
    Student,
    StudentUser,
    TypedUser,
    User,
)
from codeforlife.user.permissions import IsIndependent, IsTeacher
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.db.models.query import QuerySet
from rest_framework import status

from ...views import UserViewSet

# NOTE: type hint to help Intellisense.
default_token_generator: PasswordResetTokenGenerator = default_token_generator


# pylint: disable-next=missing-class-docstring,too-many-public-methods
class TestUserViewSet(ModelViewSetTestCase[User]):
    basename = "user"
    model_view_set_class = UserViewSet
    fixtures = ["independent", "non_school_teacher", "school_1", "school_2"]

    def setUp(self):
        self.non_school_teacher_user = NonSchoolTeacherUser.objects.get(
            email="teacher@noschool.com"
        )

        self.admin_school_1_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )
        self.non_admin_school_1_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school1.com")
        )
        self.admin_school_2_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school2.com"
        )

        self.indy_user = IndependentUser.objects.get(email="indy@email.com")
        self.indy_user_requesting_to_join_class = IndependentUser.objects.get(
            email="indy.requester@email.com"
        )

        self.class_1_at_school_1 = Class.objects.get(name="Class 1 @ School 1")

    def _get_pk_and_token_for_user(self, email: str):
        user = User.objects.get(email__iexact=email)
        token = default_token_generator.make_token(user)

        return user.pk, token

    # test: get permissions

    def test_get_permissions__bulk(self):
        """No one can perform bulk actions."""
        self.assert_get_permissions([AllowNone()], action="bulk")

    def test_get_permissions__partial_update__teacher(self):
        """Only admin-teachers can update a teacher."""
        self.assert_get_permissions(
            [IsTeacher(is_admin=True)],
            action="partial_update",
            request=self.client.request_factory.patch(data={"teacher": {}}),
        )

    def test_get_permissions__partial_update__student(self):
        """Only admin-teachers or class-teachers can update a student."""
        self.assert_get_permissions(
            [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))],
            action="partial_update",
            request=self.client.request_factory.patch(data={"student": {}}),
        )

    def test_get_permissions__partial_update__requesting_to_join_class(
        self,
    ):
        """Only independents can update their class join request."""
        self.assert_get_permissions(
            [IsIndependent()],
            action="partial_update",
            request=self.client.request_factory.patch(
                data={"requesting_to_join_class": ""}
            ),
        )

    def test_get_permissions__independents__handle_join_class_request(self):
        """
        Only school-teachers can handle an independent's class join request.
        """
        self.assert_get_permissions(
            [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))],
            action="independents__handle_join_class_request",
            request=self.client.request_factory.patch(data={"accept": False}),
        )

    def test_get_permissions__destroy(self):
        """Only independents or teachers can destroy a user."""
        self.assert_get_permissions(
            [OR(IsTeacher(), IsIndependent())],
            action="destroy",
        )

    # test: get queryset

    def _test_get_queryset__independents__handle_join_class_request(
        self, user: SchoolTeacherUser
    ):
        request = self.client.request_factory.patch(user=user)

        indy_users = list(user.teacher.indy_users)
        assert indy_users

        self.assert_get_queryset(
            indy_users,
            action="independents__handle_join_class_request",
            request=request,
        )

    def test_get_queryset__independents__handle_join_class_request__admin(self):
        """Handling a join class request can only target the independent
        students who made a request to any class in the teacher's school."""
        self._test_get_queryset__independents__handle_join_class_request(
            user=self.admin_school_1_teacher_user
        )

    def test_get_queryset__independents__handle_join_class_request__non_admin(
        self,
    ):
        """Handling a join class request can only target the independent
        students who made a request to one of the teacher's classes."""
        self._test_get_queryset__independents__handle_join_class_request(
            user=self.non_admin_school_1_teacher_user
        )

    def test_get_queryset__destroy(self):
        """Destroying a user can only target the user making the request."""
        self.assert_get_queryset(
            [self.admin_school_1_teacher_user],
            action="destroy",
            request=self.client.request_factory.delete(
                user=self.admin_school_1_teacher_user
            ),
        )

    def test_get_queryset__partial_update__student(self):
        """Updating a student can only target the user making the request if
        the user is a student."""
        return self.assert_get_queryset(
            [self.indy_user],
            action="partial_update",
            request=self.client.request_factory.patch(user=self.indy_user),
        )

    # test: class join request actions

    def test_independents__handle_join_class_request__accept(self):
        """Teacher can successfully accept a class join request."""
        indy_user = self.indy_user_requesting_to_join_class

        self.client.login_as(self.admin_school_1_teacher_user)
        self.client.patch(
            path=self.reverse_action(
                "independents--handle-join-class-request",
                kwargs={"pk": indy_user.pk},
            ),
            data={"accept": True},
        )

        pending_class_request = indy_user.student.pending_class_request
        username = indy_user.username
        indy_user.refresh_from_db()
        assert indy_user.student.pending_class_request is None
        assert indy_user.student.class_field == pending_class_request
        assert indy_user.last_name == ""
        assert indy_user.email == ""
        assert indy_user.username != username

    def test_independents__handle_join_class_request__reject(self):
        """Teacher can successfully reject a class join request."""
        indy_user = self.indy_user_requesting_to_join_class

        self.client.login_as(self.admin_school_1_teacher_user)
        self.client.patch(
            path=self.reverse_action(
                "independents--handle-join-class-request",
                kwargs={"pk": indy_user.pk},
            ),
            data={"accept": False},
        )

        indy_user.refresh_from_db()
        assert indy_user.student.pending_class_request is None
        assert indy_user.student.class_field is None

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
            viewname, data={"email": self.non_school_teacher_user.email}
        )

        assert response.data["reset_password_url"] is not None
        assert response.data["pk"] is not None
        assert response.data["token"] is not None

    def test_reset_password__invalid_pk(self):
        """Reset password raises 400 on GET with invalid pk"""
        _, token = self._get_pk_and_token_for_user(
            self.non_school_teacher_user.email
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
        pk, _ = self._get_pk_and_token_for_user(
            self.non_school_teacher_user.email
        )

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
            self.non_school_teacher_user.email
        )

        viewname = self.reverse_action(
            "reset-password", kwargs={"pk": pk, "token": token}
        )

        self.client.get(viewname)

    def test_reset_password__patch__teacher(self):
        """Teacher can successfully update password."""
        pk, token = self._get_pk_and_token_for_user(
            self.non_school_teacher_user.email
        )

        viewname = self.reverse_action(
            "reset-password", kwargs={"pk": pk, "token": token}
        )

        self.client.patch(viewname, data={"password": "N3wPassword!"})
        self.client.login_as(
            self.non_school_teacher_user, password="N3wPassword!"
        )

    def test_reset_password__patch__indy(self):
        """Indy can successfully update password."""
        pk, token = self._get_pk_and_token_for_user(self.indy_user.email)

        viewname = self.reverse_action(
            "reset-password", kwargs={"pk": pk, "token": token}
        )

        self.client.patch(viewname, data={"password": "N3wPassword"})
        self.client.login_as(self.indy_user, password="N3wPassword")

    # test: generic actions

    # TODO: move this logic and test to TeacherViewSet
    def test_partial_update__teacher(self):
        """Admin-school-teacher can update another teacher's profile."""
        self.client.login_as(self.admin_school_1_teacher_user)

        other_school_teacher_user = (
            SchoolTeacherUser.objects.filter(
                new_teacher__school=self.admin_school_1_teacher_user.teacher.school
            )
            .exclude(pk=self.admin_school_1_teacher_user.pk)
            .first()
        )
        assert other_school_teacher_user

        self.client.partial_update(
            other_school_teacher_user,
            {
                "last_name": other_school_teacher_user.first_name,
                "teacher": {
                    "is_admin": not other_school_teacher_user.teacher.is_admin
                },
            },
        )

    def test_partial_update__indy__send_join_request(self):
        """Independent user can request to join a class."""
        self.client.login_as(self.indy_user)

        self.client.partial_update(
            self.indy_user,
            {"requesting_to_join_class": self.class_1_at_school_1.access_code},
        )

    def test_partial_update__indy__revoke_join_request(self):
        """Independent user can revoke their request to join a class."""
        self.client.login_as(self.indy_user)

        self.client.partial_update(
            self.indy_user, {"requesting_to_join_class": None}
        )

    def assert_user_is_anonymized(self, user: User):
        """Assert user has been anonymized.

        Args:
            user: The user to assert.
        """
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.email == ""
        assert not user.is_active

    def assert_classes_are_anonymized(
        self,
        school_teacher_user: SchoolTeacherUser,
        class_names: t.Iterable[str],
    ):
        """Assert the classes and their students have been anonymized.

        Args:
            school_teacher_user: The user the classes belong to.
            class_names: The original class names.
        """
        # TODO: remove when using new data strategy
        queryset = QuerySet(
            model=Class.objects.model,
            using=Class.objects._db,
            hints=Class.objects._hints,
        ).filter(teacher=school_teacher_user.teacher)

        for klass, name in zip(queryset, class_names):
            assert klass.name != name
            assert klass.access_code == ""
            assert not klass.is_active

            student: Student  # TODO: delete in new data schema
            for student in klass.students.all():
                self.assert_user_is_anonymized(student.new_user)

    def _test_destroy(
        self,
        user: TypedUser,
        status_code_assertion: int = status.HTTP_204_NO_CONTENT,
    ):
        self.client.login_as(user)
        self.client.destroy(
            user,
            status_code_assertion=status_code_assertion,
            make_assertions=False,
        )

    def test_destroy__class_teacher(self):
        """Class-teacher-users can anonymize themselves and their classes."""
        user = self.non_admin_school_1_teacher_user
        assert user.teacher.class_teacher.exists()
        class_names = list(
            user.teacher.class_teacher.values_list("name", flat=True)
        )

        self._test_destroy(user)
        user.refresh_from_db()
        self.assert_user_is_anonymized(user)
        self.assert_classes_are_anonymized(user, class_names)

    def test_destroy__school_teacher__last_teacher(self):
        """
        School-teacher-users can anonymize themselves and their school if they
        are the last teacher.
        """
        user = self.admin_school_1_teacher_user
        assert user.teacher.class_teacher.exists()
        class_names = list(
            user.teacher.class_teacher.values_list("name", flat=True)
        )
        school_name = user.teacher.school.name

        SchoolTeacherUser.objects.filter(
            new_teacher__school=user.teacher.school
        ).exclude(pk=user.pk).delete()

        self._test_destroy(user)
        user.refresh_from_db()
        self.assert_user_is_anonymized(user)
        self.assert_classes_are_anonymized(user, class_names)
        assert user.teacher.school.name != school_name
        assert not user.teacher.school.is_active

    def test_destroy__school_teacher__last_admin_teacher(self):
        """
        School-teacher-users cannot anonymize themselves if they are the last
        admin teachers.
        """
        self._test_destroy(
            self.admin_school_1_teacher_user,
            status_code_assertion=status.HTTP_409_CONFLICT,
        )

    def test_destroy__independent(self):
        """Independent-users can anonymize themselves."""
        user = self.indy_user
        self._test_destroy(user)
        user.refresh_from_db()
        self.assert_user_is_anonymized(user)
