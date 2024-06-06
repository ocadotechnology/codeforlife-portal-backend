"""
© Ocado Group
Created on 30/01/2024 at 19:03:45(+00:00).
"""

from unittest.mock import patch

from codeforlife.tests import (
    ModelListSerializerTestCase,
    ModelSerializerTestCase,
)
from codeforlife.user.models import (
    Class,
    NonAdminSchoolTeacherUser,
    Student,
    StudentUser,
    User,
)
from django.contrib.auth.hashers import make_password

from .student import (
    BaseStudentListSerializer,
    BaseStudentPasswordSerializer,
    BaseStudentSerializer,
    CreateStudentSerializer,
    ReleaseStudentSerializer,
    ResetStudentPasswordSerializer,
    TransferStudentSerializer,
)

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


# ------------------------------------------------------------------------------
# Base serializers
# ------------------------------------------------------------------------------


class TestBaseStudentListSerializer(ModelListSerializerTestCase[User, Student]):
    model_serializer_class = BaseStudentSerializer
    model_list_serializer_class = BaseStudentListSerializer
    # fixtures = ["school_1"]

    def setUp(self):
        student_user = StudentUser.objects.first()
        assert student_user
        self.student_user = student_user

    def test_validate__first_name__data__not_unique_per_class(self):
        """Cannot provide a first name more than once per class in data."""
        self.assert_validate(
            attrs=[
                {
                    "class_field": {"access_code": "AAAAA"},
                    "new_user": {"first_name": "Stefan"},
                },
                {
                    "class_field": {"access_code": "AAAAA"},
                    "new_user": {"first_name": "stefan"},
                },
            ],
            error_code="first_name__data__not_unique_per_class",
        )

    def test_validate__first_name__data__exists_in_class(self):
        """
        Cannot provide a first name in data for class if it already exists in
        that class.
        """
        self.assert_validate(
            attrs=[
                {
                    "class_field": {
                        "access_code": (
                            self.student_user.student.class_field.access_code
                        )
                    },
                    "new_user": {"first_name": self.student_user.first_name},
                }
            ],
            error_code="first_name__data__exists_in_class",
        )

    def test_validate__first_name__db__exists_in_class(self):
        """
        Cannot transfer a student to another class if their first name already
        exists in that class.
        """
        self.assert_validate(
            attrs=[
                {
                    "class_field": {
                        "access_code": (
                            self.student_user.student.class_field.access_code
                        )
                    }
                }
            ],
            error_code="first_name__db__exists_in_class",
            instance=[self.student_user.student],
        )


class TestBaseStudentSerializer(ModelSerializerTestCase[User, Student]):
    model_serializer_class = BaseStudentSerializer
    fixtures = ["school_1", "school_2"]

    def setUp(self):
        self.non_admin_school_teacher_user = (
            NonAdminSchoolTeacherUser.objects.get(email="teacher@school1.com")
        )

    def test_validate_klass__does_not_exist(self):
        """
        Requesting teacher cannot assign a student to a class that doesn't
        exist.
        """
        user = self.non_admin_school_teacher_user
        self.assert_validate_field(
            name="klass",
            value="",
            error_code="does_not_exist",
            context={"request": self.request_factory.post(user=user)},
        )

    def test_validate_klass__teacher_not_in_same_school(self):
        """
        Requesting teacher cannot assign a student to a class if they're not in
        the same school.
        """
        user = self.non_admin_school_teacher_user
        klass = Class.objects.exclude(
            teacher__school=user.teacher.school
        ).first()
        assert klass

        self.assert_validate_field(
            name="klass",
            value=klass.access_code,
            error_code="teacher_not_in_same_school",
            context={"request": self.request_factory.post(user=user)},
        )

    def test_validate_klass__teacher_not_admin_or_class_owner(self):
        """
        Requesting teacher cannot assign a student to a class if they're not an
        admin or they don't own the class.
        """
        user = self.non_admin_school_teacher_user
        klass = (
            # TODO: replace with school.classes in new data schema.
            Class.objects.filter(teacher__school=user.teacher.school)
            .exclude(teacher=user.teacher)
            .first()
        )
        assert klass

        self.assert_validate_field(
            name="klass",
            value=klass.access_code,
            error_code="teacher_not_admin_or_class_owner",
            context={"request": self.request_factory.post(user=user)},
        )


class TestBaseStudentPasswordSerializer(ModelSerializerTestCase[User, Student]):
    model_serializer_class = BaseStudentPasswordSerializer
    # fixtures = ["school_1"]

    def setUp(self):
        student = Student.objects.first()
        assert student
        self.student = student

    # TODO: fix and implement test in new data schema
    # def test_to_representation(self):
    #     password, login_id = "password", "abcdefghijklmnopqrstuzwxyz"
    #     self.student.login_id = login_id
    #     self.student.new_user._password = password

    #     self.assert_to_representation(
    #         self.student,
    #         new_data={"user": {"password": password}, "login_id": login_id},
    #     )


# ------------------------------------------------------------------------------
# Action serializers
# ------------------------------------------------------------------------------


class TestCreateStudentSerializer(ModelSerializerTestCase[User, Student]):
    model_serializer_class = CreateStudentSerializer
    # fixtures = ["school_1"]

    def setUp(self):
        klass = Class.objects.first()
        assert klass
        self.klass = klass

    def test_create_many(self):
        """Can create many instances of the student model."""
        self.assert_create_many(
            validated_data=[
                {
                    "new_user": {"first_name": "Joshua"},
                    "class_field": {"access_code": self.klass.access_code},
                },
                {
                    "new_user": {"first_name": "Roxy"},
                    "class_field": {"access_code": self.klass.access_code},
                },
            ]
        )


class TestReleaseStudentSerializer(ModelSerializerTestCase[User, Student]):
    model_serializer_class = ReleaseStudentSerializer
    # fixtures = ["school_1"]

    def setUp(self):
        student = Student.objects.first()
        assert student
        self.student = student

    def test_update_many(self):
        """The student is converted to an independent."""
        self.assert_update_many(
            instance=[self.student],
            validated_data=[
                {
                    "new_user": {
                        "email": f"{self.student.pk}@gmail.com",
                        "first_name": "Indiana",
                    }
                }
            ],
            new_data=[
                {
                    "class_field": None,
                    "new_user": {"username": f"{self.student.pk}@gmail.com"},
                }
            ],
        )


class TestTransferStudentSerializer(ModelSerializerTestCase[User, Student]):
    model_serializer_class = TransferStudentSerializer
    fixtures = ["school_1"]

    def setUp(self):
        self.class_1 = Class.objects.get(name="Class 1 @ School 1")
        self.class_2 = Class.objects.get(name="Class 2 @ School 1")

    def test_update(self):
        """The student-user is transferred to another class."""
        assert self.class_1 != self.class_2
        students = self.class_1.students.all()

        self.assert_update_many(
            instance=list(students),
            validated_data=[
                {
                    "new_user": {"first_name": f"TransferStudent{student.pk}"},
                    "class_field": {"access_code": self.class_2.access_code},
                }
                for student in students
            ],
        )


class TestResetStudentPasswordSerializer(
    ModelSerializerTestCase[User, Student]
):
    model_serializer_class = ResetStudentPasswordSerializer
    # fixtures = ["school_1"]

    def setUp(self):
        student = Student.objects.first()
        assert student
        self.student = student

    def test_update_many(self):
        """The students' password is reset."""
        password = "password"
        assert not self.student.new_user.check_password(password)

        with patch(
            "django.contrib.auth.base_user.make_password",
            return_value=make_password(password),
        ) as user_make_password:
            with patch.object(
                StudentUser,
                "_get_random_login_id",
                # pylint: disable-next=protected-access
                return_value=StudentUser._get_random_login_id(),
            ) as get_random_login_id:
                self.assert_update_many(
                    instance=[self.student],
                    validated_data=[{"new_user": {"password": password}}],
                    new_data=[
                        {
                            "new_user": {
                                "password": user_make_password.return_value
                            },
                            "login_id": get_random_login_id.return_value,
                        }
                    ],
                )

                get_random_login_id.assert_called_once()
            user_make_password.assert_called_once_with(password)
