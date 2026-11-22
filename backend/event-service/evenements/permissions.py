from rest_framework.permissions import BasePermission


def get_role(user):
    # Role lu dans le jeton JWT (None si visiteur non connecte)
    token = getattr(user, 'token', None)
    if token is None:
        return None
    return token.get('role')


class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and get_role(request.user) == 'ORGANIZER')


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and get_role(request.user) == 'ADMIN')


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.organisateurId == int(request.user.id)