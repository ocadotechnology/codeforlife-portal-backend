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

from codeforlife.urls import get_urlpatterns
from django.urls import include, path

from .api.urls import urlpatterns

urlpatterns = [
    path(
        "rapidrouter/",
        include("game.urls"),
        name="rapidrouter",
    ),
    *get_urlpatterns(urlpatterns, include_user_urls=False),
    path(
        "api/sso/",
        include("src.sso.urls"),
        name="sso",
    ),
    path(
        "api/rapid_router/",
        include("src.rapid_router.urls"),
        name="rapid-router",
    ),
]
