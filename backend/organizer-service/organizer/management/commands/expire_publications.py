"""python manage.py expire_publications  (run once a day, e.g. with cron)"""
from django.core.management.base import BaseCommand

from organizer.services import expire_publications


class Command(BaseCommand):
    help = "Approved publications whose application deadline is passed become 'expired'."

    def handle(self, *args, **options):
        count = expire_publications()
        self.stdout.write(self.style.SUCCESS(f"{count} publication(s) expired"))
