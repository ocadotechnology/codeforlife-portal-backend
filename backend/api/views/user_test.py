"""
© Ocado Group
Created on 20/01/2024 at 10:58:52(+00:00).
"""
import typing as t

from codeforlife.permissions import OR, AllowAny, AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    Class,
    IndependentUser,
    NonAdminSchoolTeacherUser,
    NonSchoolTeacherUser,
    SchoolTeacherUser,
    TypedUser,
    User,
)
from codeforlife.user.permissions import IsIndependent, IsTeacher
from codeforlife.user.serializers import UserSerializer
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)

from ..auth import email_verification_token_generator
from ..serializers import (
    CreateUserSerializer,
    HandleIndependentUserJoinClassRequestSerializer,
    RequestUserPasswordResetSerializer,
    ResetUserPasswordSerializer,
    UpdateUserSerializer,
)
from .user import UserViewSet

# NOTE: type hint to help Intellisense.
default_token_generator: PasswordResetTokenGenerator = default_token_generator


# pylint: disable-next=missing-class-docstring,too-many-public-methods,too-many-ancestors
class TestUserViewSet(ModelViewSetTestCase[User, User]):
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

    # test: get permissions

    def test_get_permissions__bulk(self):
        """No one can perform bulk actions."""
        self.assert_get_permissions(permissions=[AllowNone()], action="bulk")

    def test_get_permissions__partial_update__requesting_to_join_class(
        self,
    ):
        """Only independents can update their class join request."""
        self.assert_get_permissions(
            permissions=[IsIndependent()],
            action="partial_update",
            request=self.client.request_factory.patch(
                data={"requesting_to_join_class": ""}
            ),
        )

    def test_get_permissions__handle_join_class_request(self):
        """
        Only school-teachers can handle an independent's class join request.
        """
        self.assert_get_permissions(
            permissions=[
                OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))
            ],
            action="handle_join_class_request",
            request=self.client.request_factory.patch(data={"accept": False}),
        )

    def test_get_permissions__create(self):
        """Anyone can create an independent-user."""
        self.assert_get_permissions(permissions=[AllowAny()], action="create")

    def test_get_permissions__destroy(self):
        """Only independents can destroy."""
        self.assert_get_permissions(
            permissions=[IsIndependent()],
            action="destroy",
        )

    def test_get_permissions__request_password_reset(self):
        """Anyone can request to reset their password."""
        self.assert_get_permissions(
            permissions=[AllowAny()],
            action="request_password_reset",
        )

    def test_get_permissions__reset_password(self):
        """Anyone can reset their password."""
        self.assert_get_permissions(
            permissions=[AllowAny()],
            action="reset_password",
        )

    # test: get queryset

    def _test_get_queryset__handle_join_class_request(
        self, user: SchoolTeacherUser
    ):
        request = self.client.request_factory.patch(user=user)

        indy_users = list(user.teacher.indy_users)
        assert indy_users

        self.assert_get_queryset(
            indy_users,
            action="handle_join_class_request",
            request=request,
        )

    def test_get_queryset__handle_join_class_request__admin(self):
        """Handling a join class request can only target the independent
        students who made a request to any class in the teacher's school."""
        self._test_get_queryset__handle_join_class_request(
            user=self.admin_school_1_teacher_user
        )

    def test_get_queryset__handle_join_class_request__non_admin(
        self,
    ):
        """Handling a join class request can only target the independent
        students who made a request to one of the teacher's classes."""
        self._test_get_queryset__handle_join_class_request(
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

    def test_get_queryset__reset_password(self):
        """
        Resetting a password can only target the user whose password is being
        reset.
        """
        self.assert_get_queryset(
            values=[self.indy_user],
            kwargs={"pk": self.indy_user.pk},
            action="reset_password",
        )

    # test: get serializer context

    def test_get_serializer_context__create(self):
        """Need to give context to the type of user being created."""
        self.assert_get_serializer_context(
            serializer_context={"user_type": "independent"},
            action="create",
        )

    # test: get serializer class

    def test_get_serializer_class__request_password_reset(self):
        """Requesting a password reset has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=RequestUserPasswordResetSerializer,
            action="request_password_reset",
        )

    def test_get_serializer_class__reset_password(self):
        """Resetting a password has a dedicated serializer."""
        self.assert_get_serializer_class(
            serializer_class=ResetUserPasswordSerializer,
            action="reset_password",
        )

    def test_get_serializer_class__handle_join_class_request(
        self,
    ):
        """
        Handling independents' join-class request has a dedicated serializer.
        """
        self.assert_get_serializer_class(
            serializer_class=HandleIndependentUserJoinClassRequestSerializer,
            action="handle_join_class_request",
        )

    def test_get_serializer_class__create(self):
        """Creating a user uses the create user serializer."""
        self.assert_get_serializer_class(
            serializer_class=CreateUserSerializer,
            action="create",
        )

    def test_get_serializer_class__partial_update(self):
        """Partially updating a user uses the general serializer."""
        self.assert_get_serializer_class(
            serializer_class=UpdateUserSerializer,
            action="partial_update",
        )

    def test_get_serializer_class__retrieve(self):
        """Retrieving a user uses the general serializer."""
        self.assert_get_serializer_class(
            serializer_class=UserSerializer,
            action="retrieve",
        )

    def test_get_serializer_class__list(self):
        """Listing users uses the general serializer."""
        self.assert_get_serializer_class(
            serializer_class=UserSerializer,
            action="list",
        )

    # test: class join request actions

    def test_handle_join_class_request__accept(self):
        """Teacher can successfully accept a class join request."""
        user = self.indy_user_requesting_to_join_class

        self.client.login_as(self.admin_school_1_teacher_user)
        self.client.put(
            path=self.reverse_action("handle-join-class-request", user),
            data={"accept": True},
        )

        pending_class_request = user.student.pending_class_request
        username = user.username
        user.refresh_from_db()
        assert user.student.pending_class_request is None
        assert user.student.class_field == pending_class_request
        assert user.last_name == ""
        assert user.email == ""
        assert user.username != username

    def test_handle_join_class_request__reject(self):
        """Teacher can successfully reject a class join request."""
        user = self.indy_user_requesting_to_join_class

        self.client.login_as(self.admin_school_1_teacher_user)
        self.client.put(
            path=self.reverse_action("handle-join-class-request", user),
            data={"accept": False},
        )

        user.refresh_from_db()
        assert user.student.pending_class_request is None
        assert user.student.class_field is None

    # test: reset password actions

    def test_request_password_reset(self):
        """Can successfully request a password reset email."""
        path = self.reverse_action("request-password-reset")

        response = self.client.post(
            path, data={"email": self.non_school_teacher_user.email}
        )

        email = "nonexistent@email.com"
        assert not User.objects.filter(email__iexact=email).exists()

        # Need to assert non-existent email returns the same status code.
        self.client.post(
            path,
            data={"email": email},
            status_code_assertion=response.status_code,
        )

    def _test_reset_password(
        self, user: TypedUser, password: t.Optional[str] = None
    ):
        data = {"token": default_token_generator.make_token(user)}
        if password is not None:
            data["password"] = password

        self.client.update(user, data=data, action="reset_password")

    def test_reset_password__token(self):
        """Can check the user's reset-password token."""
        self._test_reset_password(self.indy_user)

    def test_reset_password__token_and_password(self):
        """Can reset the user's password."""
        user = self.indy_user
        password = "N3wPassword!"

        self._test_reset_password(user, password)
        self.client.login_as(user, password)

    def test_verify_email_address(self):
        """Can verify the user's email address."""
        user = User.objects.filter(userprofile__is_verified=False).first()
        assert user

        self.client.update(
            user,
            action="verify_email_address",
            data={"token": email_verification_token_generator.make_token(user)},
        )

        user.refresh_from_db()
        assert user.userprofile.is_verified

    # test: generic actions

    def test_partial_update(self):
        """Can successfully update a user."""
        user = self.admin_school_1_teacher_user
        password = "N3wPassword!"
        assert not user.check_password(password)
        email = "new@email.com"
        assert user.email.lower() != email.lower()

        self.client.login_as(user)
        self.client.partial_update(
            user,
            data={
                "email": email,
                "password": password,
                "current_password": "password",
            },
        )
        self.client.login_as(user, password)

    # TODO: move this logic and test to TeacherViewSet
    def test_partial_update__teacher(self):
        """Admin-school-teacher can update another teacher's profile."""
        self.client.login_as(self.admin_school_1_teacher_user)

        other_school_teacher_user = (
            SchoolTeacherUser.objects.filter(
                new_teacher__school=(
                    self.admin_school_1_teacher_user.teacher.school
                )
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

    def test_destroy(self):
        """Independent-users can anonymize themselves."""
        user = self.indy_user

        self.client.login_as(user)
        self.client.destroy(user, make_assertions=False)

        user.refresh_from_db()
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.email == ""
        assert not user.is_active
