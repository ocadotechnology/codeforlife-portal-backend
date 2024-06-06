"""service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from aimmo import urls as aimmo_urls  # type: ignore[import-untyped]
from codeforlife.urls import service_urlpatterns
from django.urls import include, path
from portal.views.aimmo.dashboard import (  # type: ignore[import-untyped]
    StudentAimmoDashboard,
    TeacherAimmoDashboard,
)

urlpatterns = [
    path(
        "rapidrouter/",
        include("game.urls"),
        name="rapidrouter",
    ),
    path(
        "teach/kurono/dashboard/",
        TeacherAimmoDashboard.as_view(),
        name="teacher_aimmo_dashboard",
    ),
    path(
        "play/kurono/dashboard/",
        StudentAimmoDashboard.as_view(),
        name="student_aimmo_dashboard",
    ),
    path(
        "kurono/",
        include(aimmo_urls),
        name="kurono",
    ),
    *service_urlpatterns(
        api_urls_path="src.api.urls",
        frontend_template_name="portal.html",  # TODO: update, removed bundling
        include_user_urls=False,
    ),
    path(
        "api/",
        include("src.sso.urls"),
        name="sso",
    ),
    path(
        "api/rapid_router/",
        include("src.rapid_router.urls"),
        name="rapid-router",
    ),
]
