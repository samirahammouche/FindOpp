"""Calls to the team's Auth service (login and password belong to it).

Expected API of the Auth service (AUTH_API_URL):
    POST /api/auth/login/            {"email", "password"}           -> {"access": "<JWT>", ...}
    POST /api/auth/change-password/  {"old_password", "new_password"} (header Authorization: Bearer <JWT>)
The JWT must be HS256-signed with the shared JWT_SECRET and contain "user_id" and "role".
"""
import json
import urllib.error
import urllib.request

from django.conf import settings


class AuthServiceError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(errors)


def _post(path, body, token=None):
    if not settings.AUTH_API_URL:
        raise AuthServiceError({"__all__": ["The Auth service is not configured (AUTH_API_URL)."]})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{settings.AUTH_API_URL}{path}", data=json.dumps(body).encode(),
                                     headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=settings.API_TIMEOUT) as response:
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        try:
            data = json.loads(error.read() or b"{}")
        except ValueError:
            data = {}
        if error.code in (400, 401):
            raise AuthServiceError(data or {"__all__": ["Wrong email or password."]})
        raise AuthServiceError({"__all__": ["The Auth service had a problem. Please try again."]})
    except (urllib.error.URLError, TimeoutError):
        raise AuthServiceError({"__all__": ["The Auth service is unreachable. Please try again."]})


def login(email, password):
    """Returns the JWT token given by the Auth service."""
    data = _post("/api/auth/login/", {"email": email, "password": password})
    token = data.get("access") or data.get("token")
    if not token:
        raise AuthServiceError({"__all__": ["The Auth service did not return a token."]})
    return token


def change_password(token, old_password, new_password):
    return _post("/api/auth/change-password/", {"old_password": old_password, "new_password": new_password},
                 token=token)
