
from django.urls import path
from .views import (
    OrganizerOnlyView,
    RegisterView,
    LoginView,
    MeView,
    RefreshTokenView,
    LogoutView,
    ChangePasswordView,
)
from .views import AdminOnlyView, OrganizerOnlyView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path(
        "password/change/",
        ChangePasswordView.as_view(),
        name="change-password"
    ),
    path("admin-only/", AdminOnlyView.as_view(), name="admin-only"),
    path("organizer-only/", OrganizerOnlyView.as_view(), name="organizer-only"),
]
