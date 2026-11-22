"""JWT authentication for the Organizer service.

The login and the "Create account" page belong to the Auth service.
The Auth service gives a JWT token (HS256) that contains at least:
    {"user_id": 12, "role": "organizer", "email": "...", "exp": 1767225600}

This service does not call the Auth service for each request: it checks the
token signature locally with the shared secret (JWT_SECRET), as asked in the
WAMS project ("The API validates locally or via Auth Service").
Only the Python standard library is used, so no extra package is needed.
"""
import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from rest_framework import authentication, exceptions


def _b64url_decode(data):
    data += "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data)


def _b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def encode_token(payload, secret=None):
    """Create a HS256 token (used by the tests and the `make_dev_token` command)."""
    secret = (secret or settings.JWT_SECRET).encode()
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(json.dumps(payload).encode())
    signature = hmac.new(secret, f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(signature)}"


def decode_token(token, secret=None):
    secret = (secret or settings.JWT_SECRET).encode()
    try:
        header_b64, body_b64, signature_b64 = token.split(".")
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(body_b64))
        signature = _b64url_decode(signature_b64)
    except (ValueError, json.JSONDecodeError):
        raise exceptions.AuthenticationFailed("Malformed token.")

    if header.get("alg") != "HS256":
        raise exceptions.AuthenticationFailed("Unsupported token algorithm.")
    expected = hmac.new(secret, f"{header_b64}.{body_b64}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise exceptions.AuthenticationFailed("Invalid token signature.")
    if "exp" in payload and payload["exp"] < time.time():
        raise exceptions.AuthenticationFailed("Token has expired.")
    if "user_id" not in payload:
        raise exceptions.AuthenticationFailed("Token has no user_id.")
    return payload


class TokenUser:
    """Light user built from the token (users are stored in the Auth service)."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, payload):
        self.id = payload["user_id"]
        self.role = payload.get("role", "")
        self.email = payload.get("email", "")
        self.payload = payload

    def __str__(self):
        return f"{self.role}#{self.id}"


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode()
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed("Use: Authorization: Bearer <token>")
        payload = decode_token(parts[1])
        return TokenUser(payload), payload

    def authenticate_header(self, request):
        return self.keyword
