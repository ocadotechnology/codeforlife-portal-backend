"""
© Ocado Group
Created on 02/04/2025 at 13:53:53(+01:00).
"""

from unittest.mock import Mock, patch

from codeforlife.tests import CeleryTestCase
from django.core.management import call_command as _call_command

# pylint: disable=missing-class-docstring


class TestSession(CeleryTestCase):
    @patch("src.sso.tasks.session.call_command", side_effect=_call_command)
    def test_clear_sessions(self, call_command: Mock):
        """Can clear all expired sessions."""
        self.apply_periodic_task("clear_sessions")
        call_command.assert_called_once_with("clearsessions")
