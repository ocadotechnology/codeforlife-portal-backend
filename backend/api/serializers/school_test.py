"""
© Ocado Group
Created on 02/02/2024 at 15:38:51(+00:00).
"""

from codeforlife.tests import ModelSerializerTestCase
from codeforlife.user.models import School, User

from ..views.school import SchoolViewSet
from .school import SchoolSerializer


# pylint: disable-next=missing-class-docstring
class TestSchoolSerializer(ModelSerializerTestCase[User, School]):
    model_serializer_class = SchoolSerializer
    fixtures = ["school_1"]

    def setUp(self):
        self.school_1 = School.objects.get(pk=2)

    def test_validate__country_ne_gb(self):
        """
        Setting a UK county raises an error if the country does not equal GB.
        """

        self.assert_validate(
            attrs={
                "uk_county": "Surrey",
                "country": "AF",
            },
            error_code="country_ne_gb",
            context={"view": SchoolViewSet(action="create")},
        )

    def test_validate_name__name_not_unique(self):
        """
        School names must be unique.
        """

        self.assert_validate_field(
            name="name",
            value=self.school_1.name,
            error_code="name_not_unique",
        )
