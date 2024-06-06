"""
© Ocado Group
Created on 23/01/2024 at 17:53:37(+00:00).
"""
from codeforlife.permissions import OR, AllowNone
from codeforlife.user.permissions import IsTeacher
from codeforlife.user.views import ClassViewSet as _ClassViewSet
from rest_framework import status
from rest_framework.response import Response

from ..serializers import ClassSerializer


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class ClassViewSet(_ClassViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = ClassSerializer

    def get_permissions(self):
        # Bulk actions not allowed for classes.
        if self.action == "bulk":
            return (
                [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))]
                if self.request.method == "PATCH"
                else [AllowNone()]
            )
        if self.action == "create":
            return [IsTeacher(in_school=True)]
        if self.action in ["partial_update", "destroy"]:
            return [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))]

        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        klass = self.get_object()

        if klass.has_students():
            return Response(status=status.HTTP_409_CONFLICT)

        klass.anonymise()

        return Response(status=status.HTTP_204_NO_CONTENT)
