"""
© Ocado Group
Created on 31/01/2024 at 16:07:32(+00:00).
"""
from datetime import date
from unittest.mock import Mock, patch

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    Class,
    IndependentUser,
    StudentUser,
    User,
)
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)

from ...serializers.user import (
    BaseUserSerializer,
    CreateUserSerializer,
    RequestUserPasswordResetSerializer,
    ResetUserPasswordSerializer,
    UpdateUserSerializer,
)

# NOTE: type hint to help Intellisense.
password_reset_token_generator: PasswordResetTokenGenerator = (
    default_token_generator
)


# pylint: disable=missing-class-docstring


class TestBaseUserSerializer(ModelSerializerTestCase[User]):
    model_serializer_class = BaseUserSerializer[User]
    # fixtures = ["school_1"]

    def test_validate_email__already_exists(self):
        """Cannot assign a user an email that already exists."""
        user_fields = User.objects.values("email").first()
        assert user_fields

        self.assert_validate_field(
            name="email",
            value=user_fields["email"],
            error_code="already_exists",
        )

    def test_validate_password(self):
        """
        Password is validated using django's installed password-validators.
        """
        raise NotImplementedError()  # TODO

    def test_update(self):
        """Updating a user's password saves the password's hash."""
        raise NotImplementedError()  # TODO


class TestCreateTeacherSerializer(ModelSerializerTestCase[IndependentUser]):
    model_serializer_class = CreateUserSerializer

    @patch.object(IndependentUser, "add_contact_to_dot_digital")
    def test_create(self, add_contact_to_dot_digital: Mock):
        """Can successfully create an independent user."""
        password = "N3wPassword!"

        with patch(
            "django.contrib.auth.models.make_password",
            return_value=make_password(password),
        ) as user_make_password:
            self.assert_create(
                validated_data={
                    "first_name": "Anakin",
                    "last_name": "Skywalker",
                    "password": password,
                    "email": "anakin.skywalker@jedi.academy",
                    "add_to_newsletter": True,
                    "date_of_birth": date(419, 10, 31),
                },
                new_data={"password": user_make_password.return_value},
                non_model_fields={"add_to_newsletter", "date_of_birth"},
            )

            user_make_password.assert_called_once_with(password)
        add_contact_to_dot_digital.assert_called_once()


class TestUpdateUserSerializer(ModelSerializerTestCase[User]):
    model_serializer_class = UpdateUserSerializer
    fixtures = ["independent", "school_1"]

    def setUp(self):
        self.independent = IndependentUser.objects.get(
            email="indy.requester@email.com"
        )
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com",
        )
        self.student_user = StudentUser.objects.get(first_name="Student1")
        self.class_2 = Class.objects.get(name="Class 2 @ School 1")
        self.class_3 = Class.objects.get(name="Class 3 @ School 1")

    def test_validate__current_password__required(self):
        """
        Cannot update credential fields without providing the current password.
        """
        self.assert_validate(
            attrs={"email": ""},
            error_code="current_password__required",
            instance=self.admin_school_teacher_user,
        )

    def test_validate_current_password__user_does_not_exist(self):
        """
        Cannot validate the current password of a user that does not exist.
        """
        self.assert_validate_field(
            name="current_password",
            error_code="user_does_not_exist",
        )

    def test_validate_current_password__does_not_match(self):
        """
        Cannot provide a password that does not match the current password.
        """
        self.assert_validate_field(
            name="current_password",
            value="",
            error_code="does_not_match",
            instance=self.admin_school_teacher_user,
        )

    def test_validate_requesting_to_join_class__does_not_exist(self):
        """Student cannot request to join a class which doesn't exist."""
        self.assert_validate_field(
            name="requesting_to_join_class",
            value="AAAAA",
            error_code="does_not_exist",
        )

    def test_validate_requesting_to_join_class__does_not_accept_requests(self):
        """
        Student cannot request to join a class which doesn't accept requests.
        """
        self.assert_validate_field(
            name="requesting_to_join_class",
            value=self.class_2.access_code,
            error_code="does_not_accept_requests",
        )

    def test_validate_requesting_to_join_class__no_longer_accepts_requests(
        self,
    ):
        """
        Student cannot request to join a class which no longer accepts requests.
        """
        self.assert_validate_field(
            name="requesting_to_join_class",
            value=self.class_3.access_code,
            error_code="no_longer_accepts_requests",
        )


class TestRequestUserPasswordResetSerializer(ModelSerializerTestCase[User]):
    model_serializer_class = RequestUserPasswordResetSerializer
    fixtures = ["independent", "school_1"]

    def setUp(self):
        self.indy_user = IndependentUser.objects.get(
            email="indy.requester@email.com"
        )
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com",
        )

    def test_validate_email(self):
        """Returns a user by their email."""
        user = self.indy_user
        serializer = RequestUserPasswordResetSerializer()
        assert serializer.validate_email(user.email) == user

    def test_validate_email__does_not_exist(self):
        """Cannot get an email that does not exist."""
        self.assert_validate_field(
            name="email",
            error_code="does_not_exist",
            value="does.not.exist@email.com",
        )

    def _test_create(self, user: User):
        serializer = RequestUserPasswordResetSerializer()

        token = password_reset_token_generator.make_token(user)
        with patch.object(
            password_reset_token_generator, "make_token", return_value=token
        ) as make_token:
            serializer.create(validated_data={"email": user})
            make_token.assert_called_once_with(user)

            # TODO: assert the reset-password url includes the user's type.
            # pylint: disable-next=unused-variable
            user_type = "teacher" if user.teacher else "independent"
            # TODO: assert the reset-password url includes the user's pk.
            # TODO: assert the reset-password url includes the token.
            # TODO: assert the reset-password url is included in a sent email.

    def test_create__teacher(self):
        """Sends an email to a teacher with a link to reset their password."""
        self._test_create(self.admin_school_teacher_user)

    def test_create__indy(self):
        """Sends an email to an indy with a link to reset their password."""
        self._test_create(self.indy_user)


class TestResetUserPasswordSerializer(ModelSerializerTestCase[User]):
    model_serializer_class = ResetUserPasswordSerializer
    # fixtures = ["school_1"]

    def setUp(self):
        user = User.objects.first()
        assert user
        self.user = user

    def test_validate_token__user_does_not_exist(self):
        """Cannot validate the token of a user that does not exist."""
        self.assert_validate_field(
            name="token",
            error_code="user_does_not_exist",
        )

    def test_validate_token__does_not_match(self):
        """The token must match the user's tokens."""
        self.assert_validate_field(
            name="token",
            error_code="does_not_match",
            value="invalid-token",
            instance=self.user,
        )

    def test_update(self):
        """Can successfully reset a user's password."""
        password = "new-password"
        assert not self.user.check_password(password)

        with patch(
            "django.contrib.auth.base_user.make_password",
            return_value=make_password(password),
        ) as user_make_password:
            self.assert_update(
                instance=self.user,
                validated_data={"password": password},
                new_data={"password": user_make_password.return_value},
            )

            user_make_password.assert_called_once_with(password)
        assert self.user.check_password(password)
