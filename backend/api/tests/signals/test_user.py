from codeforlife.user.models import User, UserProfile
from django.test import TestCase


class TestUser(TestCase):
    def test_pre_save__otp_secret(self):
        """
        Creating a new user sets their OTP secret.
        """

        user = User.objects.create_user(
            username="john.doe@codeforlife.com",
            email="john.doe@codeforlife.com",
            password="password",
            first_name="John",
            last_name="Doe",
        )

        profile = UserProfile.objects.create(user=user)

        assert profile.otp_secret is not None

    def test_pre_save__email(self):
        """
        Updating the email field also updates the username field.
        """

        user = User.objects.first()
        assert user is not None

        email = "example@codeforelife.com"
        assert user.username != email

        user.email = email
        user.save()
        assert user.username == email

    def test_post_save__email(self):
        """
        Updating the email field sends a verification email.
        """

        raise NotImplementedError()  # TODO: implement
