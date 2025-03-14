"""
© Ocado Group
Created on 18/01/2024 at 15:14:32(+00:00).
"""

import typing as t
from datetime import date, timedelta

from codeforlife.mail import send_mail
from codeforlife.types import DataDict
from codeforlife.user.models import (
    AnyUser,
    Class,
    ContactableUser,
    IndependentUser,
    SchoolTeacher,
    Student,
    StudentUser,
    Teacher,
    TeacherUser,
    User,
)
from codeforlife.user.serializers import (
    BaseUserSerializer as _BaseUserSerializer,
)
from codeforlife.user.serializers import ClassSerializer as _ClassSerializer
from codeforlife.user.serializers import TeacherSerializer as _TeacherSerializer
from codeforlife.user.serializers import UserSerializer as _UserSerializer
from codeforlife.validators import AlphaCharSetValidator
from django.conf import settings
from django.contrib.auth.password_validation import (
    validate_password as _validate_password,
)
from django.core.exceptions import ValidationError as CoreValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from ..auth import (
    email_verification_token_generator,
    password_reset_token_generator,
)

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors
# pylint: disable=missing-function-docstring


# ------------------------------------------------------------------------------
# Base serializers
# ------------------------------------------------------------------------------


class BaseUserSerializer(_BaseUserSerializer[AnyUser], t.Generic[AnyUser]):
    def validate_first_name(self, value: str):
        user = self.instance
        if user and user.student and user.student.class_field:
            if User.objects.filter(
                first_name=value,
                new_student__class_field=user.student.class_field,
            ).exists():
                raise serializers.ValidationError(
                    "A student in this class already has this name.",
                    code="student_name_in_class",
                )

        return value

    # TODO: make email unique in new models and remove this validation.
    def validate_email(self, value: str):
        user = User.objects.filter(email__iexact=value).first()
        if user:
            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS["User already registered"],
                to_addresses=[value],
                personalization_values={
                    "EMAIL": value,
                    "LOGIN_URL": (
                        settings.PAGE_TEACHER_LOGIN
                        if user.teacher
                        else settings.PAGE_INDY_LOGIN
                    ),
                },
            )

            raise serializers.ValidationError(
                "Already exists.", code="already_exists"
            )

        return value

    def validate_password(self, value: str):
        """Validate the new password depending on user type."""
        # If we're creating a new user, we do not yet have the user object.
        # Therefore, we need to create a dummy user and pass it to the password
        # validators so they know what type of user we have.
        user: t.Optional[User] = self.instance
        if not user:
            user = User()

            user_type: str = self.context["user_type"]
            if user_type == "teacher":
                Teacher(new_user=user)
            elif user_type == "student":
                Student(new_user=user, class_field=Class())
            elif user_type == "independent":
                Student(new_user=user)

        try:
            _validate_password(value, user)
        except CoreValidationError as ex:
            raise serializers.ValidationError(
                ex.messages, code="invalid_password"
            ) from ex

        return value

    def update(self, instance: AnyUser, validated_data: DataDict):
        password = validated_data.pop("password", None)
        if password is not None:
            instance.set_password(password)

        return super().update(instance, validated_data)


# ------------------------------------------------------------------------------
# Action serializers
# ------------------------------------------------------------------------------


class CreateUserSerializer(BaseUserSerializer[IndependentUser]):
    # pylint: disable=duplicate-code
    # TODO: add to model validators in new schema.
    first_name = serializers.CharField(
        validators=[AlphaCharSetValidator()],
        max_length=150,
        min_length=1,
    )
    # TODO: add to model validators in new schema.
    last_name = serializers.CharField(
        validators=[AlphaCharSetValidator()],
        max_length=150,
        min_length=1,
    )
    # pylint: enable=duplicate-code

    date_of_birth = serializers.DateField(write_only=True)
    add_to_newsletter = serializers.BooleanField(write_only=True)

    # pylint: disable=duplicate-code
    class Meta(BaseUserSerializer.Meta):
        fields = [
            *BaseUserSerializer.Meta.fields,
            "password",
            "date_of_birth",
            "add_to_newsletter",
        ]
        extra_kwargs = {
            **BaseUserSerializer.Meta.extra_kwargs,
            "first_name": {"min_length": 1},
            "last_name": {"min_length": 1},
            "password": {"write_only": True},
            "email": {"read_only": False},
        }

    # pylint: enable=duplicate-code

    def create(self, validated_data):
        add_to_newsletter: bool = validated_data.pop("add_to_newsletter")
        date_of_birth: date = validated_data.pop("date_of_birth")

        independent_user = IndependentUser.objects.create_user(**validated_data)
        if add_to_newsletter:
            independent_user.add_contact_to_dot_digital()

        verify_email_address_link = settings.SERVICE_BASE_URL + reverse(
            "user-verify-email-address",
            kwargs={
                "pk": independent_user.pk,
                "token": email_verification_token_generator.make_token(
                    independent_user.pk, validated_data["email"]
                ),
            },
        )

        # TODO: send in signal instead in new schema.
        if (
            date_of_birth
            <= (timezone.now() - timedelta(days=365.25 * 13)).date()
        ):
            independent_user.email_user(
                settings.DOTDIGITAL_CAMPAIGN_IDS["Verify new user email"],
                personalization_values={
                    "VERIFICATION_LINK": verify_email_address_link
                },
            )
        else:
            independent_user.email_user(
                settings.DOTDIGITAL_CAMPAIGN_IDS[
                    "Verify new user email - parents"
                ],
                personalization_values={
                    "ACTIVATION_LINK": verify_email_address_link,
                    "FIRST_NAME": independent_user.first_name,
                },
            )

        return independent_user


class UpdateUserSerializer(BaseUserSerializer[User], _UserSerializer):
    requesting_to_join_class = serializers.CharField(
        source="new_student.pending_class_request",
        allow_null=True,
    )
    current_password = serializers.CharField(write_only=True)

    class Meta(_UserSerializer.Meta):
        fields = [*_UserSerializer.Meta.fields, "password", "current_password"]
        extra_kwargs = {
            **_UserSerializer.Meta.extra_kwargs,
            "first_name": {"min_length": 1},
            "last_name": {"min_length": 1},
            "email": {},
            "password": {"write_only": True},
        }

    def validate_requesting_to_join_class(self, value: str):
        # NOTE: Error message is purposefully ambiguous to prevent class
        # enumeration.
        error_message = "Class does not exist or does not accept join requests."

        if value is not None:
            try:
                klass = Class.objects.get(access_code=value)
            except Class.DoesNotExist as ex:
                raise serializers.ValidationError(
                    error_message, code="does_not_exist"
                ) from ex

            if klass.accept_requests_until is None:
                raise serializers.ValidationError(
                    error_message, code="does_not_accept_requests"
                )

            if klass.accept_requests_until < timezone.now():
                raise serializers.ValidationError(
                    error_message, code="no_longer_accepts_requests"
                )

        return value

    def validate_current_password(self, value: str):
        if not self.instance:
            raise serializers.ValidationError(
                "Can only check the password of an existing user.",
                code="user_does_not_exist",
            )
        if not self.instance.check_password(value):
            raise serializers.ValidationError(
                "Does not match the current password.",
                code="does_not_match",
            )

        return value

    def validate(self, attrs):
        if (
            self.instance
            and any(field in attrs for field in self.instance.credential_fields)
            and "current_password" not in attrs
        ):
            raise serializers.ValidationError(
                "Current password is required when updating fields: "
                f"{', '.join(self.instance.credential_fields)}.",
                code="current_password__required",
            )

        return attrs

    def update(self, instance, validated_data):
        if "new_student" in validated_data:
            new_student = t.cast(DataDict, validated_data.pop("new_student"))
            if "pending_class_request" in new_student:
                pending_class_request: t.Optional[str] = new_student[
                    "pending_class_request"
                ]
                student = t.cast(IndependentUser, instance).student
                student.pending_class_request = (
                    None
                    if pending_class_request is None
                    else Class.objects.get(access_code=pending_class_request)
                )
                student.save(update_fields=["pending_class_request"])

                # TODO: Send email in signal to indy user confirming successful
                #  join request.
                # TODO: Send email in signal to teacher of selected class to
                #  notify them of join request.

        email = validated_data.pop("email", None)
        if email is not None and email.lower() != instance.email.lower():
            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS["Email will change"],
                to_addresses=[instance.email],
                personalization_values={"NEW_EMAIL_ADDRESS": email},
            )

            # pylint: disable-next=duplicate-code
            verify_email_address_link = settings.SERVICE_BASE_URL + reverse(
                "user-verify-email-address",
                kwargs={
                    "pk": instance.pk,
                    "token": email_verification_token_generator.make_token(
                        instance.pk, email
                    ),
                },
            )

            send_mail(
                settings.DOTDIGITAL_CAMPAIGN_IDS["Verify changed user email"],
                to_addresses=[email],
                personalization_values={
                    "VERIFICATION_LINK": verify_email_address_link
                },
            )

        return super().update(instance, validated_data)


class HandleIndependentUserJoinClassRequestSerializer(
    BaseUserSerializer[IndependentUser]
):
    """
    Handles an independent user's request to join a class. If "accept" is
    True, convert the independent user to a student user and add them to the
    class in question. First name validation is also done to avoid duplicate
    first names within the class (case-insensitive).
    """

    # TODO: add to model validators in new schema.
    first_name = serializers.CharField(
        validators=[AlphaCharSetValidator()],
        max_length=150,
        min_length=1,
        required=False,
    )

    accept = serializers.BooleanField(write_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = [*BaseUserSerializer.Meta.fields, "accept"]
        extra_kwargs = {
            **BaseUserSerializer.Meta.extra_kwargs,
            "first_name": {"min_length": 1, "required": False},
        }

    def validate_first_name(self, value: str):
        if StudentUser.objects.filter(
            new_student__class_field=(
                self.non_none_instance.student.pending_class_request
            ),
            first_name__iexact=value,
        ).exists():
            raise serializers.ValidationError(
                "This name already exists in the class. "
                "Please choose a different name.",
                code="already_in_class",
            )

        return value

    def update(self, instance: IndependentUser, validated_data):
        if validated_data["accept"]:
            instance.username = StudentUser.get_random_username()
            instance.first_name = validated_data.get(
                "first_name", instance.first_name
            )
            instance.last_name = ""
            instance.email = ""
            instance.save(
                update_fields=["username", "first_name", "last_name", "email"]
            )

            instance.student.class_field = (
                instance.student.pending_class_request
            )
            instance.student.pending_class_request = None
            instance.student.save(
                update_fields=["class_field", "pending_class_request"]
            )
        else:
            instance.student.pending_class_request = None
            instance.student.save(update_fields=["pending_class_request"])

        return instance


class RequestUserPasswordResetSerializer(_UserSerializer[ContactableUser]):
    class Meta(_UserSerializer.Meta):
        extra_kwargs = {
            **_UserSerializer.Meta.extra_kwargs,
            "email": {"read_only": False},
        }

    def validate_email(self, value: str):
        try:
            return ContactableUser.objects.get(email__iexact=value)
        except ContactableUser.DoesNotExist as ex:
            raise serializers.ValidationError(code="does_not_exist") from ex

    def create(self, validated_data: DataDict):
        user: ContactableUser = validated_data["email"]

        # Generate reset-password url for the frontend.
        # pylint: disable-next=unused-variable
        reset_password_url = "/".join(
            [
                settings.SERVICE_SITE_URL,
                "reset-password",
                "teacher" if user.teacher else "independent",  # user type
                str(user.pk),
                password_reset_token_generator.make_token(user),
            ]
        )

        user.email_user(
            settings.DOTDIGITAL_CAMPAIGN_IDS["Reset password"],
            personalization_values={"RESET_PASSWORD_LINK": reset_password_url},
        )

        return user


class ResetUserPasswordSerializer(BaseUserSerializer[User], _UserSerializer):
    token = serializers.CharField(write_only=True)

    class Meta(_UserSerializer.Meta):
        fields = [*_UserSerializer.Meta.fields, "password", "token"]
        extra_kwargs = {
            **_UserSerializer.Meta.extra_kwargs,
            "password": {"write_only": True, "required": False},
        }

    def validate_token(self, value: str):
        if not self.instance:
            raise serializers.ValidationError(
                "Can only reset the password of an existing user.",
                code="user_does_not_exist",
            )
        if not password_reset_token_generator.check_token(self.instance, value):
            raise serializers.ValidationError(
                "Does not match the given user.",
                code="does_not_match",
            )

        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password is not None:
            instance.set_password(password)
            instance.save(update_fields=["password"])

        return instance


class VerifyUserEmailAddressSerializer(_UserSerializer[User]):
    token = serializers.CharField(write_only=True)

    class Meta(_UserSerializer.Meta):
        fields = [*_UserSerializer.Meta.fields, "token"]

    def validate_token(self, value: str):
        if not self.instance:
            raise serializers.ValidationError(
                "Can only verify the email address of an existing user.",
                code="user_does_not_exist",
            )

        token = email_verification_token_generator.check_token(
            self.instance, value
        )
        if token is None:
            raise serializers.ValidationError(
                "Does not match the given user.",
                code="does_not_match",
            )

        return token

    def update(self, instance, validated_data):
        instance.userprofile.is_verified = True
        instance.userprofile.save(update_fields=["is_verified"])

        email = validated_data["token"]["email"]
        if email.lower() != instance.email.lower():
            instance.email = email
            instance.username = email
            instance.save(update_fields=["email", "username"])

        return instance


class RegisterEmailToNewsletter(_BaseUserSerializer[ContactableUser]):
    class Meta(_BaseUserSerializer.Meta):
        fields = ["email"]
        extra_kwargs = {"email": {"write_only": True}}

    def create(self, validated_data):
        # NOTE: this user instance is not (and should not) be saved to the db.
        user = ContactableUser(email=validated_data["email"])
        user.add_contact_to_dot_digital()

        return user


class ReadUserSerializer(_UserSerializer[User]):
    class ClassSerializer(_ClassSerializer):
        class TeacherSerializer(_TeacherSerializer[SchoolTeacher]):
            user = _BaseUserSerializer[TeacherUser](
                source="new_user", read_only=True
            )

            class Meta(_TeacherSerializer.Meta):
                fields = [*_TeacherSerializer.Meta.fields, "user"]

        teacher = TeacherSerializer(read_only=True)

    requesting_to_join_class = ClassSerializer(  # type: ignore[assignment]
        source="new_student.pending_class_request",
        read_only=True,
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            if (
                instance.new_student
                and instance.new_student.pending_class_request
            ):
                representation["requesting_to_join_class"] = (
                    self.ClassSerializer(
                        instance.new_student.pending_class_request
                    ).data
                )
        except Student.DoesNotExist:
            pass

        return representation
