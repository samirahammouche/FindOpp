"""Organizer microservice: the pages of the organizer space AND their REST API.

    /organizer/                 pages (Django templates)  -> organizer_space app
    /organizer/accounts/        sign in / sign out        -> accounts app
    /api/organizer/...          REST API (DRF)            -> organizer app
    /health/                    Consul + Traefik health check
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

from organizer.views import health

urlpatterns = [
    path("", RedirectView.as_view(url="/organizer/")),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/", include("organizer.urls")),
    path("organizer/accounts/", include("accounts.urls")),
    path("organizer/", include("organizer_space.urls")),
    # Uploaded images (logo, covers)
    re_path(r"^organizer-media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
