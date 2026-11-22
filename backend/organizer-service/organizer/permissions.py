from django.conf import settings
from rest_framework import permissions


class IsOrganizer(permissions.BasePermission):
    """The token must belong to an organizer account."""

    message = "This space is reserved for organizers."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", "") == "organizer")


class IsInternalService(permissions.BasePermission):
    """Calls coming from the other microservices (Auth, Admin), with a shared key."""

    message = "Internal endpoint."

    def has_permission(self, request, view):
        key = request.headers.get("X-Internal-Key", "")
        return bool(settings.INTERNAL_API_KEY) and key == settings.INTERNAL_API_KEY
