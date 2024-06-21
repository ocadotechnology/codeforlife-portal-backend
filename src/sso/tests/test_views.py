"""
© Ocado Group
Created on 01/12/2023 at 16:04:15(+00:00).
"""

import json
import typing as t
from unittest.mock import patch
from urllib.parse import unquote

import pyotp
from codeforlife.tests import Client, CronTestCase, TestCase
from codeforlife.user.models import AuthFactor, User
from django.core import management
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone


class TestLoginView(TestCase):
    """Test the login view."""

    client: Client
    client_class = Client

    def setUp(self):
        self.user = User.objects.get(id=2)

    def _get_session_metadata(self, response: HttpResponse):
        class SessionMetadata(t.NamedTuple):
            """The data contained in session cookie."""

            user_id: int
            auth_factors: t.List[str]
            user_type: t.Literal["teacher", "student", "indy"]
            otp_bypass_token_exists: bool

        return SessionMetadata(
            **json.loads(unquote(response.cookies["session_metadata"].value))
        )

    def test_post__otp(self):
        """Test posting an OTP token."""

        AuthFactor.objects.create(
            user=self.user,
            type=AuthFactor.Type.OTP,
        )

        response = self.client.post(
            reverse("session-login", kwargs={"form": "login-with-email"}),
            data=json.dumps(
                {
                    "email": self.user.email,
                    "password": "Password1",
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        session_metadata = self._get_session_metadata(response)
        assert session_metadata.user_id == self.user.id
        assert session_metadata.auth_factors == [AuthFactor.Type.OTP]

        self.user.userprofile.otp_secret = pyotp.random_base32()
        self.user.userprofile.save()

        totp = pyotp.TOTP(self.user.userprofile.otp_secret)

        now = timezone.now()
        with patch.object(timezone, "now", return_value=now):
            response = self.client.post(
                reverse("session-login", kwargs={"form": "login-with-otp"}),
                data=json.dumps({"otp": totp.at(now)}),
                content_type="application/json",
            )

        assert response.status_code == 200
        session_metadata = self._get_session_metadata(response)
        assert session_metadata.user_id == self.user.id
        assert session_metadata.auth_factors == []


class TestClearExpiredView(CronTestCase):
    """Test the clear-expired view."""

    def test_clear_expired_view(self):
        """Test the clear sessions command is called."""

        with patch.object(management, "call_command") as call_command:
            self.client.get(reverse("session-clear-expired"))
            call_command.assert_called_once_with("clearsessions")
