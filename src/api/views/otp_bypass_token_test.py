"""
© Ocado Group
Created on 24/01/2024 at 09:47:04(+00:00).
"""

from unittest.mock import call, patch

from codeforlife.permissions import AllowNone
from codeforlife.tests import ModelViewSetTestCase
from codeforlife.user.models import AuthFactor, OtpBypassToken, User
from codeforlife.user.permissions import IsTeacher
from rest_framework import status

from ..permissions import HasAuthFactor
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

    # test: get permissions

    def test_get_permissions__retrieve(self):
        """No one can retrieve a single otp-bypass-token."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="retrieve",
        )

    def test_get_permissions__list(self):
        """
        Only teachers who have enabled OTP as an auth factor can list
        otp-bypass-tokens.
        """
        self.assert_get_permissions(
            permissions=[IsTeacher(), HasAuthFactor(AuthFactor.Type.OTP)],
            action="list",
        )

    def test_get_permissions__create(self):
        """No one can create a single otp-bypass-token."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="create",
        )

    def test_get_permissions__bulk(self):
        """No one can bulk-create many otp-bypass-tokens."""
        self.assert_get_permissions(
            permissions=[AllowNone()],
            action="bulk",
        )

    def test_get_permissions__generate(self):
        """
        Only teachers who have enabled OTP as an auth factor can generate
        otp-bypass-tokens.
        """
        self.assert_get_permissions(
            permissions=[IsTeacher(), HasAuthFactor(AuthFactor.Type.OTP)],
            action="generate",
        )

    # test: get queryset

    def test_get_queryset__list(self):
        """Users can only list their own OTP bypass tokens."""
        self.assert_get_queryset(
            values=self.user.otp_bypass_tokens.all(),
            action="list",
            request=self.client.request_factory.get(user=self.user),
        )

    # test: actions

    def test_list(self):
        """Can list a user's OTP bypass tokens."""
        self.client.login(email=self.user.email, password="password")
        self.client.list(self.user.otp_bypass_tokens.all())

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
        response_json = response.json()
        assert isinstance(response_json, list) and tokens == {
            otp_bypass_token["token"]
            for otp_bypass_token in response_json
            if isinstance(otp_bypass_token, dict)
        }

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
