"""
© Ocado Group
Created on 24/01/2024 at 09:47:04(+00:00).
"""

from unittest.mock import call, patch

from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import OtpBypassToken, User
from rest_framework import status

from .otp_bypass_token import OtpBypassTokenViewSet


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class TestOtpBypassTokenViewSet(ModelViewSetTestCase[User, OtpBypassToken]):
    basename = "otp-bypass-token"
    model_view_set_class = OtpBypassTokenViewSet
    fixtures = ["school_2"]

    def setUp(self):
        user = User.objects.filter(otp_bypass_tokens__isnull=False).first()
        assert user
        self.user = user

    def test_generate(self):
        """Generate max number of OTP bypass tokens."""
        otp_bypass_token_pks = list(
            self.user.otp_bypass_tokens.values_list("pk", flat=True)
        )

        self.client.login(email=self.user.email, password="password")

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

        with patch(
            "codeforlife.user.models.otp_bypass_token.get_random_string",
            side_effect=list(tokens),
        ) as get_random_string:
            response = self.client.post(
                self.reverse_action("generate"),
                status_code_assertion=status.HTTP_201_CREATED,
            )

            get_random_string.assert_has_calls(
                [
                    call(
                        OtpBypassToken.length,
                        OtpBypassToken.allowed_chars,
                    )
                    for _ in range(len(tokens))
                ]
            )

        # We received the expected tokens.
        assert set(response.json()) == tokens

        # The user's pre-existing tokens were deleted.
        assert not OtpBypassToken.objects.filter(
            pk__in=otp_bypass_token_pks
        ).exists()

        # The new tokens all check out.
        for otp_bypass_token in self.user.otp_bypass_tokens.all():
            found_token = False
            for token in tokens.copy():
                found_token = otp_bypass_token.check_token(token)
                if found_token:
                    tokens.remove(token)
                    break

            assert found_token
