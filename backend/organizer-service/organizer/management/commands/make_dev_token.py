"""python manage.py make_dev_token --user-id 1

For testing only, while the Auth service is not ready: prints a token
signed with JWT_SECRET, exactly like the one the Auth service will give.
"""
import time

from django.core.management.base import BaseCommand

from organizer.authentication import encode_token


class Command(BaseCommand):
    help = "Create a test JWT token for an organizer."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, default=1)
        parser.add_argument("--role", default="organizer")
        parser.add_argument("--hours", type=int, default=24)

    def handle(self, *args, **options):
        token = encode_token({
            "user_id": options["user_id"],
            "role": options["role"],
            "exp": int(time.time()) + options["hours"] * 3600,
        })
        self.stdout.write(token)
