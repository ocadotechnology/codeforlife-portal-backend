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

from ..serializers import (
    CreateTeacherSerializer,
    RemoveTeacherFromSchoolSerializer,
    SetSchoolTeacherAdminAccessSerializer,
)


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class TeacherViewSet(ModelViewSet[Teacher]):
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
