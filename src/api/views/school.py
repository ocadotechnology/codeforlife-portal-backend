"""
© Ocado Group
Created on 23/01/2024 at 17:53:50(+00:00).
"""

from codeforlife.permissions import AllowNone
from codeforlife.response import Response
from codeforlife.user.models import Class, StudentUser, Teacher
from codeforlife.user.permissions import IsTeacher
from codeforlife.user.views import SchoolViewSet as _SchoolViewSet
from rest_framework import status

from ..serializers import SchoolSerializer


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class SchoolViewSet(_SchoolViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = SchoolSerializer

    def get_permissions(self):
        # Bulk actions not allowed for schools.
        if self.action == "bulk":
            return [AllowNone()]
        # Only teachers not in a school can create a school.
        if self.action == "create":
            return [IsTeacher(in_school=False)]
        # Only admin-teachers in a school can update or delete a school.
        if self.action in ["partial_update", "destroy"]:
            return [IsTeacher(is_admin=True)]

        return super().get_permissions()

    # pylint: disable-next=missing-function-docstring
    def destroy(self, request, *args, **kwargs):
        school = self.get_object()

        for klass in Class.objects.filter(teacher__school=school):
            for student_user in StudentUser.objects.filter(
                new_student__class_field=klass
            ):
                student_user.anonymize()

            klass.anonymise()

        Teacher.objects.filter(school=school).update(school=None)

        school.anonymise()

        return Response(status=status.HTTP_204_NO_CONTENT)
