from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"organizer/publications", views.PublicationViewSet, basename="publication")
router.register(r"internal/organizers", views.InternalOrganizationViewSet, basename="internal-organizer")

urlpatterns = [
    # Organizer space (JWT token of an organizer)
    path("organizer/dashboard/", views.dashboard, name="dashboard"),
    path("organizer/profile/", views.ProfileView.as_view(), name="profile"),
    path("organizer/settings/", views.SettingsView.as_view(), name="settings"),
    # Public site
    path("publications/<int:pk>/track/", views.track, name="track"),
    # Other microservices (header X-Internal-Key)
    path("internal/publications/<int:pk>/status/", views.internal_publication_status,
         name="internal-publication-status"),
    path("", include(router.urls)),
]
