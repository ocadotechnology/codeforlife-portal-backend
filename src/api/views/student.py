"""
© Ocado Group
Created on 08/03/2024 at 09:23:26(+00:00).
"""

from codeforlife.permissions import OR, AllowNone
from codeforlife.user.models import Student, User
from codeforlife.user.permissions import IsTeacher
from codeforlife.views import ModelViewSet

from ..serializers import (
    CreateStudentSerializer,
    ReleaseStudentSerializer,
    ResetStudentPasswordSerializer,
    TransferStudentSerializer,
)


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class StudentViewSet(ModelViewSet[User, Student]):
    http_method_names = ["post", "put", "delete"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowNone()]

        return [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))]

    def get_queryset(self):
        return self.request.school_teacher_user.teacher.students

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()
        if self.action == "reset_password":
            serializer_context["user_type"] = "student"

        return serializer_context

    def get_serializer_class(self):
        if self.action == "release":
            return ReleaseStudentSerializer
        if self.action == "reset_password":
            return ResetStudentPasswordSerializer
        if self.action == "transfer":
            return TransferStudentSerializer

        return CreateStudentSerializer  # action == "bulk"

    release = ModelViewSet.bulk_update_action("release")
    transfer = ModelViewSet.bulk_update_action("transfer")
    reset_password = ModelViewSet.bulk_update_action("reset_password")

    def perform_bulk_destroy(self, queryset):
        for student in queryset:
            student.new_user.first_name = ""
            student.new_user.is_active = False
            student.new_user.save(update_fields=["first_name", "is_active"])
