"""
© Ocado Group
Created on 08/03/2024 at 11:59:41(+00:00).
"""

import typing as t

from codeforlife.permissions import OR, AllowNone
from codeforlife.response import Response
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import (
    AdminSchoolTeacherUser,
    Class,
    NonAdminSchoolTeacherUser,
    SchoolTeacherUser,
    Student,
    User,
)
from codeforlife.user.permissions import IsTeacher

from ..serializers import (
    CreateStudentSerializer,
    ReleaseStudentSerializer,
    ResetStudentPasswordSerializer,
    TransferStudentSerializer,
)
from .student import StudentViewSet

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors
# pylint: disable=too-many-public-methods


class TestStudentViewSet(ModelViewSetTestCase[User, Student]):
    basename = "student"
    model_view_set_class = StudentViewSet
    fixtures = ["school_1"]

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            email="admin.teacher@school1.com"
        )
        self.non_admin_school_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school1.com")
        )
        self.class_1 = Class.objects.get(name="Class 1 @ School 1")
        self.class_2 = Class.objects.get(name="Class 2 @ School 1")

    # test: assertions

    def assert_passwords(
        self,
        response: Response,
        students: t.Optional[t.List[Student]] = None,
        are_valid: bool = True,
    ):
        # pylint: disable=line-too-long
        """Assert the student's password and login_id are valid.

        Args:
            response: The response after setting the student's password.
            students: The students who were updated. If not provided, they will be fetched from the DB.
            are_valid: Assert whether or not the password and login_id are valid.
        """
        # pylint: enable=line-too-long
        response_json = response.json()
        assert isinstance(response_json, list) and response_json

        student_lookup: t.Dict[int, Student] = {}
        if students is None:
            for student_fields in response_json:
                assert isinstance(student_fields, dict)

                student_id = student_fields["id"]
                assert isinstance(student_id, int)

                student_lookup[student_id] = Student.objects.get(id=student_id)
        else:
            student_lookup = {student.id: student for student in students}

        for student_fields in response_json:
            assert isinstance(student_fields, dict)

            login_id = student_fields["login_id"]
            assert isinstance(login_id, str) and login_id

            student_id = student_fields["id"]
            assert isinstance(student_id, int)
            student = student_lookup[student_id]

            login_id_is_valid = student.login_id == login_id
            if are_valid:
                assert login_id_is_valid
            else:
                assert not login_id_is_valid

            student_user_fields = student_fields["user"]
            assert isinstance(student_user_fields, dict)

            password = student_user_fields["password"]
            assert isinstance(password, str)

            password_is_valid = student.new_user.check_password(password)
            if are_valid:
                assert password_is_valid
            else:
                assert not password_is_valid

    # test: get permissions

    def test_get_permissions__create(self):
        """No one is allowed to create a single student."""
        self.assert_get_permissions([AllowNone()], action="create")

    def test_get_permissions__release(self):
        """Only admin-teachers or class-teachers can release students."""
        self.assert_get_permissions(
            [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))],
            action="release",
        )

    def test_get_permissions__transfer(self):
        """Only admin-teachers or class-teachers can transfer students."""
        self.assert_get_permissions(
            [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))],
            action="transfer",
        )

    def test_get_permissions__reset_password(self):
        """
        Only admin-teachers or class-teachers can reset students' password.
        """
        self.assert_get_permissions(
            [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))],
            action="reset_password",
        )

    def test_get_permissions__bulk(self):
        """Only admin-teachers or class-teachers can perform bulk actions."""
        self.assert_get_permissions(
            [OR(IsTeacher(is_admin=True), IsTeacher(in_class=True))],
            action="bulk",
        )

    # test: get queryset

    def _test_get_queryset(
        self, user: SchoolTeacherUser, action: str, request_method: str
    ):
        self.assert_get_queryset(
            user.teacher.students.order_by("pk"),
            action=action,
            request=self.client.request_factory.generic(
                request_method, user=user
            ),
        )

    def test_get_queryset__release__admin(self):
        """An admin-school-teacher can release all students in their school."""
        self._test_get_queryset(
            self.admin_school_teacher_user,
            action="release",
            request_method="put",
        )

    def test_get_queryset__release__non_admin(self):
        """
        A non-admin-school-teacher can release all students in their class.
        """
        self._test_get_queryset(
            self.non_admin_school_teacher_user,
            action="release",
            request_method="put",
        )

    def test_get_queryset__transfer__admin(self):
        """An admin-school-teacher can transfer all students in their school."""
        self._test_get_queryset(
            self.admin_school_teacher_user,
            action="transfer",
            request_method="put",
        )

    def test_get_queryset__transfer__non_admin(self):
        """
        A non-admin-school-teacher can transfer all students in their class.
        """
        self._test_get_queryset(
            self.non_admin_school_teacher_user,
            action="transfer",
            request_method="put",
        )

    def test_get_queryset__reset_password__admin(self):
        """
        An admin-school-teacher can reset all students' password in their
        school.
        """
        self._test_get_queryset(
            self.admin_school_teacher_user,
            action="reset_password",
            request_method="put",
        )

    def test_get_queryset__reset_password__non_admin(self):
        """
        A non-admin-school-teacher can reset all students' password in their
        class.
        """
        self._test_get_queryset(
            self.non_admin_school_teacher_user,
            action="reset_password",
            request_method="put",
        )

    # test: get serializer class

    def test_get_serializer_class__release(self):
        """The action for releasing students has a dedicated serializer."""
        self.assert_get_serializer_class(
            ReleaseStudentSerializer, action="release"
        )

    def test_get_serializer_class__transfer(self):
        """The action for transferring students has a dedicated serializer."""
        self.assert_get_serializer_class(
            TransferStudentSerializer, action="transfer"
        )

    def test_get_serializer_class__reset_password(self):
        """
        The action for resetting students' password has a dedicated serializer.
        """
        self.assert_get_serializer_class(
            ResetStudentPasswordSerializer, action="reset_password"
        )

    def test_get_serializer_class__bulk(self):
        """The action for bulk creating students has a dedicated serializer."""
        self.assert_get_serializer_class(CreateStudentSerializer, action="bulk")

    # test: actions

    def test_release(self):
        """
        Admin-teacher or class-teacher can convert their students to independent
        learners.
        """
        user = self.admin_school_teacher_user
        students = user.teacher.students

        self.client.login_as(user)
        self.client.bulk_update(
            models=students,
            data=[
                {"user": {"email": f"{student.id}@email.com"}}
                for student in students
            ],
            action="release",
        )

    def test_transfer(self):
        """
        Admin-teacher or class-teacher can successfully transfer students to
        another class.
        """
        user = self.admin_school_teacher_user
        students = user.teacher.students.filter(class_field=self.class_1)

        self.client.login_as(user)
        self.client.bulk_update(
            models=students,
            data=[
                {"klass": self.class_2.access_code}
                for _ in range(len(students))
            ],
            action="transfer",
        )

    def test_reset_password(self):
        """Teacher can bulk reset students' password."""
        user = self.admin_school_teacher_user
        students = list(user.teacher.students)

        self.client.login_as(user)
        response = self.client.bulk_update(
            models=students,
            data=[{} for _ in range(len(students))],
            action="reset_password",
            make_assertions=False,
        )

        self.assert_passwords(response, students, are_valid=False)
        self.assert_passwords(response)

    def test_bulk__create(self):
        """Teacher can bulk create students."""
        user = self.non_admin_school_teacher_user
        self.client.login_as(user)

        klass: t.Optional[Class] = user.teacher.class_teacher.first()
        assert klass is not None

        response = self.client.bulk_create(
            [
                {
                    "klass": klass.access_code,
                    "user": {"first_name": "Peter"},
                },
                {
                    "klass": klass.access_code,
                    "user": {"first_name": "Mary"},
                },
            ],
            make_assertions=False,
        )

        self.assert_passwords(response)

    def test_bulk_destroy(self):
        """School-teacher can bulk anonymize students."""
        user = self.admin_school_teacher_user
        students = user.teacher.students
        student_ids = list(students.values_list("id", flat=True))
        assert student_ids

        self.client.login_as(user)
        self.client.bulk_destroy(student_ids, make_assertions=False)

        assert (
            len(student_ids)
            == students.filter(
                new_user__first_name="", new_user__is_active=False
            ).count()
        )
