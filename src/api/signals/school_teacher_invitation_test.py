"""
© Ocado Group
Created on 09/02/2024 at 19:45:00(+00:00).
"""

from django.test import TestCase


# pylint: disable-next=missing-class-docstring
class TestSchoolTeacherInvitation(TestCase):
    def test_post_save(self):
        """Creating a teacher invitation sends a verification email."""
        # raise NotImplementedError()  # TODO: implement
