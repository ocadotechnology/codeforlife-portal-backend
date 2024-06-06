"""
© Ocado Group
Created on 01/12/2023 at 15:59:54(+00:00).
"""

from django.apps import AppConfig


# pylint: disable-next=missing-class-docstring
class SsoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sso"
