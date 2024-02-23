"""
© Ocado Group
Created on 18/01/2024 at 15:14:32(+00:00).
"""

import typing as t
from itertools import groupby

from codeforlife.serializers import ModelListSerializer
from codeforlife.user.models import (
    Class,
    Student,
    StudentUser,
    Teacher,
    User,
    UserProfile,
)
from codeforlife.user.serializers import UserSerializer as _UserSerializer
from django.contrib.auth.password_validation import (
    validate_password as _validate_password,
)
from rest_framework import serializers

from .student import StudentSerializer
from .teacher import TeacherSerializer

# pylint: disable=missing-class-docstring,too-many-ancestors


class UserListSerializer(ModelListSerializer[User]):
    def create(self, validated_data):
        classes = {
            klass.access_code: klass
            for klass in Class.objects.filter(
                access_code__in={
                    user_fields["new_student"]["class_field"]["access_code"]
                    for user_fields in validated_data
                }
            )
        }

        # TODO: replace this logic with bulk creates for each object when we
        #   switch to PostgreSQL.
        return [
            StudentUser.objects.create_user(
                first_name=user_fields["first_name"],
                klass=classes[
                    user_fields["new_student"]["class_field"]["access_code"]
                ],
            )
            for user_fields in validated_data
        ]

    def validate(self, attrs):
        super().validate(attrs)

        def get_access_code(user_fields: t.Dict[str, t.Any]):
            return user_fields["new_student"]["class_field"]["access_code"]

        def get_first_name(user_fields: t.Dict[str, t.Any]):
            return user_fields["first_name"]

        attrs.sort(key=get_access_code)
        for access_code, group in groupby(attrs, key=get_access_code):
            # Validate first name is not specified more than once in data.
            data = list(group)
            data.sort(key=get_first_name)
            for first_name, group in groupby(data, key=get_first_name):
                if len(list(group)) > 1:
                    raise serializers.ValidationError(
                        f'First name "{first_name}" is specified more than once'
                        f" in data for class {access_code}.",
                        code="first_name_not_unique_per_class_in_data",
                    )

            # Validate first names are not already taken in class.
            if User.objects.filter(
                first_name__in=list(map(get_first_name, data)),
                new_student__class_field__access_code=access_code,
            ).exists():
                raise serializers.ValidationError(
                    "One or more first names is already taken in class"
                    f" {access_code}.",
                    code="first_name_not_unique_per_class_in_db",
                )

        return attrs


class UserSerializer(_UserSerializer[User]):
    student = StudentSerializer(source="new_student", required=False)
    teacher = TeacherSerializer(source="new_teacher", required=False)
    current_password = serializers.CharField(
        write_only=True,
        required=False,
    )

    class Meta(_UserSerializer.Meta):
        fields = [
            *_UserSerializer.Meta.fields,
            "student",
            "teacher",
            "password",
            "current_password",
        ]
        extra_kwargs = {
            **_UserSerializer.Meta.extra_kwargs,
            "first_name": {"read_only": False},
            "last_name": {
                "read_only": False,
                "required": False,
                "min_length": 1,
            },
            "email": {"read_only": False},
            "password": {"write_only": True, "required": False},
        }
        list_serializer_class = UserListSerializer

    def validate(self, attrs):
        if self.instance is not None and self.view.action != "reset-password":
            # TODO: make current password required when changing self-profile.
            pass

        if "new_teacher" in attrs and "last_name" not in attrs:
            raise serializers.ValidationError(
                "Last name is required.", code="last_name_required"
            )

        return attrs

    def validate_password(self, value: str):
        """
        Validate the new password depending on user type.
        """

        # If we're creating a new user, we do not yet have the user object.
        # Therefore, we need to create a dummy user and pass it to the password
        # validators so they know what type of user we have.
        instance = self.instance
        if not instance:
            instance = User()

            user_type: str = self.context["user_type"]
            if user_type == "teacher":
                Teacher(new_user=instance)
            elif user_type == "student":
                Student(new_user=instance)

        _validate_password(value, instance)

        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data.get("last_name"),
        )

        user_profile = UserProfile.objects.create(
            user=user,
            is_verified=self.context.get("is_verified", False),
        )

        if "new_teacher" in validated_data:
            Teacher.objects.create(
                user=user_profile,
                new_user=user,
                is_admin=validated_data["new_teacher"]["is_admin"],
                school=self.context.get("school"),
            )
        elif "new_student" in validated_data:
            pass  # TODO

        # TODO: Handle signing new user up to newsletter if checkbox ticked

        return user

    def update(self, instance, validated_data):
        password = validated_data.get("password")

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance

    def to_representation(self, instance: User):
        representation = super().to_representation(instance)

        # Return student's auto-generated password.
        if (
            representation["student"] is not None
            and self.request.auth_user.teacher is not None
        ):
            # pylint: disable-next=protected-access
            password = instance._password
            if password is not None:
                representation["password"] = password

        return representation


class ReleaseStudentUserListSerializer(ModelListSerializer[StudentUser]):
    def update(self, instance, validated_data):
        for student_user, data in zip(instance, validated_data):
            student_user.student.class_field = None
            student_user.student.save(update_fields=["class_field"])

            student_user.email = data["email"]
            student_user.save(update_fields=["email"])

        return instance


class ReleaseStudentUserSerializer(_UserSerializer[StudentUser]):
    """Convert a student to an independent learner."""

    class Meta(_UserSerializer.Meta):
        extra_kwargs = {
            "first_name": {
                "min_length": 1,
                "read_only": False,
                "required": False,
            },
            "email": {"read_only": False},
        }
        list_serializer_class = ReleaseStudentUserListSerializer

    # pylint: disable-next=missing-function-docstring
    def validate_email(self, value: str):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Already exists.", code="already_exists"
            )

        return value
