"""
© Ocado Group
Created on 24/01/2024 at 09:47:04(+00:00).
"""

from unittest.mock import patch

from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import OtpBypassToken, User
from rest_framework import status

from .otp_bypass_token import OtpBypassTokenViewSet


# pylint: disable-next=missing-class-docstring
class TestOtpBypassTokenViewSet(ModelViewSetTestCase[OtpBypassToken]):
    basename = "otp-bypass-token"
    model_view_set_class = OtpBypassTokenViewSet

    def setUp(self):
        self.user = User.objects.get(email="alberteinstein@codeforlife.com")
        assert not self.user.otp_bypass_tokens.exists()

        self.otp_bypass_tokens = OtpBypassToken.objects.bulk_create(
            [
                OtpBypassToken(user=self.user, token=token)
                for token in OtpBypassToken.generate_tokens()
            ]
        )

    def test_generate(self):
        """
        Generate max number of OTP bypass tokens.
        """

        user = self.client.login_teacher(
            email="alberteinstein@codeforlife.com",
            password="Password1",
        )
        assert user == self.user

        tokens = {
            "aaaaaaaa",
            "bbbbbbbb",
            "cccccccc",
            "dddddddd",
            "eeeeeeee",
            "ffffffff",
            "gggggggg",
            "hhhhhhhh",
            "iiiiiiii",
            "jjjjjjjj",
        }
        assert len(tokens) == OtpBypassToken.max_count

        with patch.object(
            OtpBypassToken, "generate_tokens", return_value=tokens
        ) as generate_tokens:
            response = self.client.post(
                self.reverse_action("generate"),
                status_code_assertion=status.HTTP_201_CREATED,
            )

            generate_tokens.assert_called_once()

        # We received the expected tokens.
        assert set(response.json()) == tokens

        # The user's pre-existing tokens were deleted.
        assert (
            OtpBypassToken.objects.filter(
                pk__in=[
                    otp_bypass_token.pk
                    for otp_bypass_token in self.otp_bypass_tokens
                ]
            ).count()
            == 0
        )

        # The new tokens all check out.
        for otp_bypass_token in OtpBypassToken.objects.filter(user=user):
            found_token = False
            for token in tokens.copy():
                found_token = otp_bypass_token.check_token(token)
                if found_token:
                    tokens.remove(token)
                    break

            assert found_token
