from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import ReferalUserViewSet
import logging

log = logging.getLogger(__name__)

router = DefaultRouter()
router.register("users", ReferalUserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/", include("rest_framework.urls")),
]
