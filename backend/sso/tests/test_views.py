"""
© Ocado Group
Created on 01/12/2023 at 16:04:15(+00:00).
"""

import json
import typing as t
from unittest.mock import patch

import pyotp
from codeforlife.tests import CronTestCase
from codeforlife.user.models import AuthFactor, User
from django.core import management
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


class TestLoginView(TestCase):
    """Test the login view."""

    def setUp(self):
        self.user = User.objects.get(id=2)

    def _get_session(self, response: HttpResponse):
        class Session(t.NamedTuple):
            """The data contained in session cookie."""

            user_id: int
            auth_factors: t.List[str]

        return Session(
            **json.loads(response.cookies["sessionid_httponly_false"].value)
        )

    def test_post__otp(self):
        """Test posting an OTP token."""

        AuthFactor.objects.create(
            user=self.user,
            type=AuthFactor.Type.OTP,
        )

        response = self.client.post(
            reverse("login", kwargs={"form": "email"}),
            data={
                "email": self.user.email,
                "password": "Password1",
            },
        )

        assert response.status_code == 200
        session = self._get_session(response)
        assert session.user_id == self.user.id
        assert session.auth_factors == [AuthFactor.Type.OTP]

        self.user.userprofile.otp_secret = pyotp.random_base32()
        self.user.userprofile.save()

        totp = pyotp.TOTP(self.user.userprofile.otp_secret)

        now = timezone.now()
        with patch.object(timezone, "now", return_value=now):
            response = self.client.post(
                reverse("login", kwargs={"form": "otp"}),
                data={"otp": totp.at(now)},
            )

        assert response.status_code == 200
        session = self._get_session(response)
        assert session.user_id == self.user.id
        assert session.auth_factors == []


class TestClearExpiredView(CronTestCase):
    """Test the clear-expired view."""

    def test_clear_expired_view(self):
        """Test the clear sessions command is called."""

        with patch.object(management, "call_command") as call_command:
            self.client.get(reverse("clear-expired-sessions"))
            call_command.assert_called_once_with("clearsessions")
