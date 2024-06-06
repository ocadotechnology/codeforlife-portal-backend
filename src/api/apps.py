"""
© Ocado Group
Created on 04/12/2023 at 12:46:47(+00:00).
"""

from django.apps import AppConfig


# pylint: disable-next=missing-class-docstring
class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel,unused-import
        from . import signals
