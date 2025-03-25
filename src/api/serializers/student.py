"""
© Ocado Group
Created on 29/01/2024 at 10:14:59(+00:00).
"""

import typing as t
from itertools import groupby

from codeforlife.serializers import ModelListSerializer
from codeforlife.types import DataDict
from codeforlife.user.models import (
    Class,
    Student,
    StudentUser,
    User,
    user_first_name_validators,
)
from codeforlife.user.serializers import StudentSerializer
from django.db.models.functions import Lower
from rest_framework import serializers

from .user import BaseUserSerializer

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors
# pylint: disable=missing-function-docstring


# ------------------------------------------------------------------------------
# Base serializers
# ------------------------------------------------------------------------------


class BaseStudentListSerializer(ModelListSerializer[User, Student]):
    """To be inherited by all student list serializers."""

    def _validate_first_names_are_unique_in_class(
        self, access_code: str, lower_first_names: t.List[str], code: str
    ):
        if (
            lower_first_names
            and StudentUser.objects.annotate(
                lower_first_name=Lower("first_name")
            )
            .filter(
                lower_first_name__in=lower_first_names,
                new_student__class_field__access_code=access_code,
            )
            .exists()
        ):
            raise serializers.ValidationError(
                "One or more first names is already taken in class"
                f" {access_code}.",
                code,
            )

    def validate(self, attrs):
        super().validate(attrs)

        def get_class_id(student_fields: DataDict):
            class_field: DataDict = student_fields.get("class_field", {})
            return t.cast(str, class_field.get("access_code", ""))

        def get_lower_first_name(student_fields: DataDict):
            new_user: DataDict = student_fields.get("new_user", {})
            return t.cast(str, new_user.get("first_name", "")).lower()

        # Copy list to preserve its original order.
        attrs_copy = attrs.copy()
        attrs_copy.sort(key=get_class_id)
        for access_code, group in groupby(attrs_copy, key=get_class_id):
            if not access_code:
                continue

            # Validate first name is not specified more than once in data.
            data = list(group)
            data.sort(key=get_lower_first_name)
            for first_name, group in groupby(data, key=get_lower_first_name):
                if first_name and len(list(group)) > 1:
                    raise serializers.ValidationError(
                        f'First name "{first_name}" is specified more than once'
                        f" in data for class {access_code}.",
                        code="first_name__data__not_unique_per_class",
                    )

            # Validate first names are not already taken in class.
            self._validate_first_names_are_unique_in_class(
                access_code,
                lower_first_names=[
                    first_name
                    for first_name in map(get_lower_first_name, data)
                    if first_name
                ],
                code="first_name__data__exists_in_class",
            )

            # Get students' first name from the db if it wasn't provided in the
            # request-data and validate they're unique in their new class.
            if self.instance:
                self._validate_first_names_are_unique_in_class(
                    access_code,
                    lower_first_names=[
                        student.new_user.first_name.lower()
                        for student_fields, student in zip(attrs, self.instance)
                        if not get_lower_first_name(student_fields)
                    ],
                    code="first_name__db__exists_in_class",
                )

        return attrs


class BaseStudentSerializer(StudentSerializer):
    def validate_klass(self, value: str):
        # Only teachers can manage students.
        teacher = self.request.school_teacher_user.teacher

        try:
            klass = Class.objects.get(access_code=value)
        except Class.DoesNotExist as ex:
            raise serializers.ValidationError(
                "Class does not exist.", code="does_not_exist"
            ) from ex

        if klass.teacher.school_id != teacher.school_id:
            raise serializers.ValidationError(
                "Class must belong to the same school as requesting teacher.",
                code="teacher_not_in_same_school",
            )
        if not teacher.is_admin and klass.teacher != teacher:
            raise serializers.ValidationError(
                "The requesting teacher must be an admin or own the class.",
                code="teacher_not_admin_or_class_owner",
            )

        return value


class BaseStudentPasswordSerializer(BaseStudentSerializer):
    """
    To be inherited by serializers that need to return the student's
    auto-generated password.
    """

    user = BaseUserSerializer[StudentUser](source="new_user")

    class Meta(BaseStudentSerializer.Meta):
        fields = [*BaseStudentSerializer.Meta.fields, "user"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Return student's auto-generated password.
        password = getattr(instance.new_user, "_password", None)
        auto_gen_password = getattr(instance.new_user, "_login_id", None)
        if password is not None and auto_gen_password is not None:
            representation["user"]["password"] = password
            representation["auto_gen_password"] = auto_gen_password

        return representation


# ------------------------------------------------------------------------------
# Action serializers
# ------------------------------------------------------------------------------


class CreateStudentListSerializer(BaseStudentListSerializer):
    def create(self, validated_data):
        classes = {
            klass.access_code: klass
            for klass in Class.objects.filter(
                access_code__in={
                    student_fields["class_field"]["access_code"]
                    for student_fields in validated_data
                }
            )
        }

        # TODO: replace this logic with bulk creates for each object when we
        #   switch to PostgreSQL.
        return [
            StudentUser.objects.create_user(
                first_name=student_fields["new_user"]["first_name"],
                klass=classes[student_fields["class_field"]["access_code"]],
            ).student
            for student_fields in validated_data
        ]


class CreateStudentSerializer(BaseStudentPasswordSerializer):
    """Create a student user."""

    class UserSerializer(BaseUserSerializer):
        # TODO: add to model validators in new schema.
        first_name = serializers.CharField(
            validators=user_first_name_validators,
            max_length=150,
            required=False,
        )

        class Meta(BaseUserSerializer.Meta):
            extra_kwargs = {
                **BaseUserSerializer.Meta.extra_kwargs,
                "first_name": {"read_only": False},
            }

    user = UserSerializer(source="new_user")
    klass = serializers.CharField(source="class_field.access_code")

    class Meta(BaseStudentPasswordSerializer.Meta):
        list_serializer_class = CreateStudentListSerializer


class ReleaseStudentListSerializer(BaseStudentListSerializer):
    def update(self, instance, validated_data):
        for student, data in zip(instance, validated_data):
            student.class_field = None
            student.save(update_fields=["class_field"])

            user_fields = t.cast(DataDict, data["new_user"])
            student.new_user.email = user_fields["email"]
            update_fields = ["email", "username"]
            if "first_name" in user_fields:
                student.new_user.first_name = user_fields["first_name"]
                update_fields.append("first_name")
            student.new_user.save(update_fields=update_fields)

        return instance


class ReleaseStudentSerializer(BaseStudentSerializer):
    """Convert a student to an independent learner."""

    class UserSerializer(BaseUserSerializer):
        # TODO: add to model validators in new schema.
        first_name = serializers.CharField(
            validators=user_first_name_validators,
            max_length=150,
            required=False,
        )

        class Meta(BaseUserSerializer.Meta):
            extra_kwargs = {
                **BaseUserSerializer.Meta.extra_kwargs,
                "first_name": {"required": False},
                "email": {"read_only": False},
            }

    user = UserSerializer(source="new_user")

    class Meta(BaseStudentSerializer.Meta):
        fields = [*BaseStudentSerializer.Meta.fields, "user"]
        list_serializer_class = ReleaseStudentListSerializer


class TransferStudentListSerializer(BaseStudentListSerializer):
    def update(self, instance, validated_data):
        classes = {
            data["class_field"]["access_code"]: Class.objects.get(
                access_code=data["class_field"]["access_code"]
            )
            for data in validated_data
        }

        for student, data in zip(instance, validated_data):
            student.class_field = classes[data["class_field"]["access_code"]]
            student.save(update_fields=["class_field"])

            user_fields = t.cast(DataDict, data.get("new_user", {}))
            if "first_name" in user_fields:
                student.new_user.first_name = user_fields["first_name"]
                student.new_user.save(update_fields=["first_name"])

        return instance


class TransferStudentSerializer(BaseStudentSerializer):
    """Transfer a student to another class."""

    class UserSerializer(BaseUserSerializer):
        # TODO: add to model validators in new schema.
        first_name = serializers.CharField(
            validators=user_first_name_validators,
            max_length=150,
            required=False,
        )

        class Meta(BaseUserSerializer.Meta):
            extra_kwargs = {
                **BaseUserSerializer.Meta.extra_kwargs,
                "first_name": {"required": False},
            }

    user = UserSerializer(source="new_user", required=False)
    klass = serializers.CharField(source="class_field.access_code")

    class Meta(BaseStudentSerializer.Meta):
        fields = [*BaseStudentSerializer.Meta.fields, "user"]
        list_serializer_class = TransferStudentListSerializer


class ResetStudentListPasswordSerializer(BaseStudentListSerializer):
    def update(self, instance, validated_data):
        for student, data in zip(instance, validated_data):
            # TODO: use proxy in new model and replace with student.user
            student_user = StudentUser(
                pk=student.new_user.pk,
                new_student=student,  # type: ignore[misc]
            )

            user_fields = t.cast(DataDict, data.get("new_user", {}))
            student_user.set_password(user_fields.get("password"))
            student.save(update_fields=["login_id"])

            # Save deletes the raw password.
            # Need to preserve it and return it to the teacher.
            # pylint: disable=protected-access
            password = student.new_user._password
            student.new_user.save(update_fields=["password"])
            student.new_user._password = password
            # pylint: enable=protected-access

        return instance


class ResetStudentPasswordSerializer(BaseStudentPasswordSerializer):
    class UserSerializer(BaseUserSerializer):
        class Meta(BaseUserSerializer.Meta):
            fields = [*BaseUserSerializer.Meta.fields, "password"]
            extra_kwargs = {
                **BaseUserSerializer.Meta.extra_kwargs,
                "password": {"write_only": True, "required": False},
            }

    user = UserSerializer(source="new_user", required=False)

    class Meta(BaseStudentPasswordSerializer.Meta):
        list_serializer_class = ResetStudentListPasswordSerializer
