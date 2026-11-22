"""Sign in / sign out of the organizer space.

Accounts and passwords belong to the Auth service (made by another team member).
This service only receives the JWT token and keeps it in the session:
  - login_view:  email + password sent to the Auth service -> token
  - token_login: the team's login page can send the token directly (POST "token")
  - demo_login:  development only, signs in as the demo organizer without the Auth service
"""
import time

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.exceptions import AuthenticationFailed

from organizer.authentication import decode_token, encode_token
from organizer.models import Organization

from . import auth_client
from .forms import LoginForm

HOME = "/organizer/"


def _safe_next(request, url):
    return url if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}) else HOME


def _start_session(request, token):
    """Checks the token and opens the session. Returns an error message or None."""
    try:
        payload = decode_token(token)
    except AuthenticationFailed as error:
        return str(error.detail)
    if payload.get("role") != "organizer":
        return "This space is reserved for organizers."
    request.session.cycle_key()  # new session id after login
    request.session.update({"token": token, "role": "organizer", "user_id": payload["user_id"],
                            "email": payload.get("email", "")})
    request.session.pop("organization", None)
    return None


def login_view(request):
    next_url = _safe_next(request, request.GET.get("next") or request.POST.get("next"))
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            token = auth_client.login(form.cleaned_data["email"], form.cleaned_data["password"])
            error = _start_session(request, token)
            if not error:
                return redirect(next_url)
            form.add_error(None, error)
        except auth_client.AuthServiceError as error:
            form.add_error(None, " ".join(str(e) for v in error.errors.values()
                                          for e in (v if isinstance(v, list) else [v])))
    return render(request, "accounts/login.html", {
        "form": form, "next": next_url, "demo_login": settings.DEMO_LOGIN,
    })


@csrf_exempt  # called by the team's login page (another service), the token itself is the proof
@require_POST
def token_login(request):
    """POST /organizer/accounts/token/  token=<JWT>  -> opens the organizer space."""
    error = _start_session(request, request.POST.get("token", ""))
    if error:
        messages.error(request, error)
        return redirect("accounts:login")
    return redirect(_safe_next(request, request.POST.get("next")))


@require_POST
def demo_login(request):
    if not settings.DEMO_LOGIN:
        raise Http404
    organization = Organization.objects.order_by("id").first()
    if organization is None:
        messages.error(request, "No organizer yet. Run: python manage.py seed_demo")
        return redirect("accounts:login")
    token = encode_token({"user_id": organization.user_id, "role": "organizer",
                          "email": organization.contact_email, "exp": int(time.time()) + 8 * 3600})
    _start_session(request, token)
    return redirect(_safe_next(request, request.POST.get("next")))


@require_POST
def logout_view(request):
    request.session.flush()
    messages.info(request, "You are signed out.")
    return redirect("accounts:login")
