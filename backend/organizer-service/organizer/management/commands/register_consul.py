"""python manage.py register_consul  [--deregister]

Registers this instance in Consul (service registry), with a health check
on /health/. The "traefik.*" tags let Traefik discover the service and
send it the requests whose path matches TRAEFIK_RULE (with load balancing
when several instances of the same service are registered).
"""
import json
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Register (or deregister) this service instance in Consul."

    def add_arguments(self, parser):
        parser.add_argument("--deregister", action="store_true")

    def handle(self, *args, **options):
        if not settings.CONSUL_URL:
            raise CommandError("Set CONSUL_URL, e.g. http://consul:8500")
        name = settings.SERVICE_NAME
        service_id = f"{name}-{settings.SERVICE_HOST}-{settings.SERVICE_PORT}"

        if options["deregister"]:
            url, body = f"{settings.CONSUL_URL}/v1/agent/service/deregister/{service_id}", None
        else:
            url = f"{settings.CONSUL_URL}/v1/agent/service/register"
            body = json.dumps({
                "ID": service_id,
                "Name": name,
                "Address": settings.SERVICE_HOST,
                "Port": settings.SERVICE_PORT,
                "Tags": [
                    "traefik.enable=true",
                    f"traefik.http.routers.{name}.rule={settings.TRAEFIK_RULE}",
                    f"traefik.http.routers.{name}.priority={settings.TRAEFIK_PRIORITY}",
                    f"traefik.http.services.{name}.loadbalancer.healthcheck.path=/health/",
                ],
                "Check": {
                    "HTTP": f"http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/health/",
                    "Interval": "10s",
                    "Timeout": "3s",
                    "DeregisterCriticalServiceAfter": "1m",
                },
            }).encode()

        request = urllib.request.Request(url, data=body, method="PUT",
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=5) as response:
            response.read()
        verb = "deregistered from" if options["deregister"] else "registered in"
        self.stdout.write(self.style.SUCCESS(f"{service_id} {verb} Consul"))
