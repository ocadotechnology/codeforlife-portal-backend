"""
© Ocado Group
Created on 03/04/2024 at 10:49:07(+01:00).
"""

from rest_framework.routers import DefaultRouter

from .views import LevelViewSet

router = DefaultRouter()
router.register(
    "levels",
    LevelViewSet,
    basename="level",
)

urlpatterns = router.urls
