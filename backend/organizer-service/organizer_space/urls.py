from django.urls import path

from . import views

app_name = "organizer_space"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="overview"),
    path("publications/", views.publication_list, name="publications"),
    path("publications/new/", views.publication_create, name="publication_create"),
    path("publications/<int:pk>/edit/", views.publication_edit, name="publication_edit"),
    path("publications/<int:pk>/<str:action>/", views.publication_action, name="publication_action"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("settings/", views.settings_redirect, name="settings"),
]
