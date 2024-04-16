"""
© Ocado Group
Created on 01/12/2023 at 16:02:53(+00:00).
"""

from django.urls import include, path, re_path

from .views import ClearExpiredView, LoginOptionsView, LoginView

urlpatterns = [
    path(
        "session/",
        include(
            [
                path(
                    "login/",
                    include(
                        [
                            path(
                                "options/",
                                LoginOptionsView.as_view(),
                                name="login-options",
                            ),
                            re_path(
                                # pylint: disable-next=line-too-long
                                r"^(?P<form>email|username|user-id|otp|otp-bypass-token)/$",
                                LoginView.as_view(),
                                name="login",
                            ),
                        ]
                    ),
                ),
                path(
                    "clear-expired/",
                    ClearExpiredView.as_view(),
                    name="clear-expired-sessions",
                ),
            ]
        ),
    ),
]
