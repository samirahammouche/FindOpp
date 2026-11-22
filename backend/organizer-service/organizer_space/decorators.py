from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect, render
from rest_framework.exceptions import AuthenticationFailed

from organizer.authentication import decode_token
from organizer.models import Organization
from organizer.serializers import OrganizationSerializer


def remember_organization(request, organization):
    """Keeps the name and logo of the organization for the sidebar."""
    data = OrganizationSerializer(organization).data
    request.session["organization"] = {
        "name": data["name"], "logo_url": data["logo_url"], "is_verified": data["is_verified"],
    }


def organizer_required(view):
    """Protects a page of the organizer space.

    The session holds the JWT token given by the Auth service at login.
    It is checked locally (same JWT_SECRET), then the view receives
    `request.organization`, the profile of the connected organizer.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        login_url = f"/organizer/accounts/login/?next={request.path}"
        token = request.session.get("token")
        if not token:
            return redirect(login_url)
        try:
            payload = decode_token(token)
        except AuthenticationFailed:
            request.session.flush()
            messages.info(request, "Your session has expired. Please sign in again.")
            return redirect(login_url)
        if payload.get("role") != "organizer":
            request.session.flush()
            return redirect(login_url)
        try:
            request.organization = Organization.objects.get(user_id=payload["user_id"])
        except Organization.DoesNotExist:
            # The profile is created from the sign-up data (RabbitMQ event "organizer.registered").
            return render(request, "unavailable.html", {
                "message": "Your organizer profile is being created. Please try again in a few seconds.",
            }, status=503)
        if "organization" not in request.session:
            remember_organization(request, request.organization)
        return view(request, *args, **kwargs)

    return wrapper
