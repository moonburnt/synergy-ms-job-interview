from django.contrib import admin
from django.urls import path, include
from referal.utils import get_default_router

router = get_default_router()

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/", include("rest_framework.urls")),
]
