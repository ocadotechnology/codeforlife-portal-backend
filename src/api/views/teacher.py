"""
© Ocado Group
Created on 18/03/2024 at 16:11:19(+00:00).
"""

from codeforlife.permissions import AllowAny
from codeforlife.user.models import (
    AdminSchoolTeacher,
    Class,
    SchoolTeacher,
    StudentUser,
    Teacher,
    User,
    teacher_as_type,
)
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from ..serializers import (
    CreateTeacherSerializer,
    RemoveTeacherFromSchoolSerializer,
    SetSchoolTeacherAdminAccessSerializer,
)


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class TeacherViewSet(ModelViewSet[User, Teacher]):
    http_method_names = ["post", "put", "delete"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action == "destroy":
            return [IsTeacher()]
        if self.action == "remove_from_school":
            return [IsTeacher(in_school=True)]

        return [IsTeacher(is_admin=True)]  # action == "set_admin_access"

    def get_queryset(self):
        teacher = self.request.teacher_user.teacher
        if self.action == "set_admin_access":
            return teacher_as_type(teacher, AdminSchoolTeacher).school_teachers
        if self.action == "remove_from_school":
            return (
                teacher_as_type(teacher, AdminSchoolTeacher).school_teachers
                if teacher.is_admin
                else SchoolTeacher.objects.filter(pk=teacher.pk)
            )

        return Teacher.objects.filter(pk=teacher.pk)  # action == "destroy"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "create":
            context["user_type"] = "teacher"

        return context

    def get_serializer_class(self):
        if self.action == "remove_from_school":
            return RemoveTeacherFromSchoolSerializer
        if self.action == "set_admin_access":
            return SetSchoolTeacherAdminAccessSerializer

        return CreateTeacherSerializer  # action == "create"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        # pylint: disable=duplicate-code
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as error:
            codes = error.get_codes()
            assert isinstance(codes, dict)
            user_codes = codes.get("user", {})
            assert isinstance(user_codes, dict)
            email_codes = user_codes.get("email", [])
            assert isinstance(email_codes, list)
            if any(code == "already_exists" for code in email_codes):
                # NOTE: Always return a 201 here - a noticeable change in
                # behaviour would allow email enumeration.
                return Response(status=status.HTTP_201_CREATED)

            raise error
        # pylint: enable=duplicate-code

        self.perform_create(serializer)

        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        teacher = self.get_object()

        def anonymize_user(user: User):
            user.first_name = ""
            user.last_name = ""
            user.email = ""
            user.is_active = False
            user.save(
                update_fields=[
                    "first_name",
                    "last_name",
                    "email",
                    "username",
                    "is_active",
                ]
            )

        if teacher.school:
            if (
                not SchoolTeacher.objects.filter(school=teacher.school)
                .exclude(pk=teacher.pk)
                .exists()
            ):
                teacher.school.anonymise()
            elif (
                teacher.is_admin
                and teacher_as_type(teacher, AdminSchoolTeacher).is_last_admin
            ):
                return Response(status=status.HTTP_409_CONFLICT)

        klass: Class  # TODO: delete in new data schema
        for klass in teacher.class_teacher.all():
            for student_user in StudentUser.objects.filter(
                new_student__class_field=klass
            ):
                anonymize_user(student_user)

            klass.anonymise()

        anonymize_user(teacher.new_user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    remove_from_school = ModelViewSet.update_action("remove_from_school")
    set_admin_access = ModelViewSet.update_action("set_admin_access")
