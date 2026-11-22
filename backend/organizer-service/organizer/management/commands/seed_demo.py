"""python manage.py seed_demo

Creates the demo data shown on the Figma page: "Club Robotique USTHB"
(user_id = 1) with its 12 publications and 30 days of views.
"""
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from organizer.models import DailyStat, Organization, Publication

S = Publication.Status
C = Publication.Category

PUBLICATIONS = [
    ("Robotics Hackathon 2027", C.HACKATHON, S.DRAFT, date(2027, 1, 15)),
    ("Mobility Scholarship 2027", C.SCHOLARSHIP, S.PENDING, date(2026, 12, 18)),
    ("Web Development Summit", C.EVENT, S.APPROVED, date(2026, 12, 2)),
    ("Entrepreneurship Forum 2026", C.EVENT, S.APPROVED, date(2026, 11, 28)),
    ("Creators Club", C.CLUB, S.APPROVED, date(2026, 11, 30)),
    ("Impact Challenge", C.HACKATHON, S.REJECTED, None),
    ("AI Night Hackathon", C.HACKATHON, S.APPROVED, date(2026, 12, 20)),
    ("Women in Tech Meetup", C.EVENT, S.APPROVED, date(2026, 12, 12)),
    ("Arduino Workshop Series", C.CLUB, S.APPROVED, date(2027, 1, 5)),
    ("Research Excellence Grant", C.SCHOLARSHIP, S.PENDING, date(2027, 2, 1)),
    ("Drone Design Challenge", C.HACKATHON, S.DRAFT, None),
    ("Open Source Days 2025", C.EVENT, S.EXPIRED, date(2025, 11, 10)),
]


class Command(BaseCommand):
    help = "Create the Club Robotique USTHB demo data."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, default=1,
                            help="id of the demo account in the Auth service")

    def handle(self, *args, **options):
        organization, _ = Organization.objects.update_or_create(
            user_id=options["user_id"],
            defaults=dict(
                name="Club Robotique USTHB",
                org_type=Organization.Type.CLUB,
                city="Alger",
                description=(
                    "We bring together people with a passion for robotics, programming and making things. "
                    "Our workshops, challenges and events help ideas grow through teamwork."
                ),
                contact_email="bureau@clubrobotique.example",
                website="https://clubrobotique.example",
                linkedin="https://www.linkedin.com/company/clubrobotique",
                instagram="https://www.instagram.com/clubrobotique",
                verification_status=Organization.Verification.VERIFIED,
            ),
        )
        organization.publications.all().delete()
        today = timezone.localdate()
        random.seed(42)

        # created from the last to the first, so the list (newest first) looks like the design
        for title, category, status, deadline in reversed(PUBLICATIONS):
            publication = Publication.objects.create(
                organization=organization,
                title=title,
                category=category,
                status=status,
                short_description="A weekend to design the robotics projects of tomorrow.",
                full_description="Imagine, build and test your prototype as a team.",
                location="Alger · Campus",
                application_link="https://clubrobotique.example/candidature",
                study_levels=["bachelor", "master"],
                fields_of_study=["Computer science", "Robotics", "Design"],
                eligible_region="Algeria",
                funding_type=Publication.Funding.PRIZE,
                amount=150000,
                application_deadline=deadline,
                rejection_reason="Please add the full prize details." if status == S.REJECTED else "",
                published_at=timezone.now() - timedelta(days=random.randint(1, 40))
                if status in (S.APPROVED, S.EXPIRED) else None,
            )
            if status in (S.APPROVED, S.EXPIRED):
                total_views = total_saves = 0
                for i in range(60):   # 60 days: the dashboard compares with the previous 30 days
                    views = random.randint(15, 45) + i * 2
                    saves = random.randint(0, 8)
                    DailyStat.objects.create(publication=publication, date=today - timedelta(days=59 - i),
                                             views=views, saves=saves)
                    total_views += views
                    total_saves += saves
                publication.views_count = total_views
                publication.saves_count = total_saves
                publication.save()

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {organization.name} (user_id={organization.user_id}), {len(PUBLICATIONS)} publications"
        ))
