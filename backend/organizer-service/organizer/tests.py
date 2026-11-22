import time
from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .authentication import encode_token
from .models import Organization, Publication

INTERNAL = {"HTTP_X_INTERNAL_KEY": "test-key"}


def token(user_id=1, role="organizer", **extra):
    return encode_token({"user_id": user_id, "role": role, "exp": int(time.time()) + 3600, **extra})


@override_settings(JWT_SECRET="test-secret", INTERNAL_API_KEY="test-key", RABBITMQ_URL="")
class OrganizerSpaceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(
            user_id=1, name="Club Robotique USTHB", org_type="club", city="Alger",
            contact_email="bureau@clubrobotique.example",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token(1)}")
        self.in_30_days = (timezone.localdate() + timedelta(days=30)).isoformat()

    def full_publication(self, **extra):
        data = {
            "category": "hackathon",
            "title": "Robotics Hackathon 2027",
            "short_description": "A weekend to design the robotics projects of tomorrow.",
            "full_description": "Imagine, build and test your prototype as a team.",
            "location": "Alger · Campus",
            "application_link": "https://clubrobotique.example/candidature",
            "study_levels": ["bachelor", "master"],
            "fields_of_study": ["Computer science", "Robotics"],
            "funding_type": "prize",
            "amount": "150000",
            "application_deadline": self.in_30_days,
        }
        data.update(extra)
        return data

    # ---------- authentication
    def test_no_token_is_refused(self):
        self.assertEqual(APIClient().get("/api/organizer/profile/").status_code, 401)

    def test_bad_signature_is_refused(self):
        bad = encode_token({"user_id": 1, "role": "organizer"}, secret="other")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {bad}")
        self.assertEqual(client.get("/api/organizer/profile/").status_code, 401)

    def test_student_token_is_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token(1, role='student')}")
        self.assertEqual(self.client.get("/api/organizer/profile/").status_code, 403)

    # ---------- profile / settings
    def test_profile_comes_from_create_account(self):
        response = APIClient().post("/api/internal/organizers/", {
            "user_id": 7, "name": "GDG Alger", "org_type": "club", "city": "Alger",
            "contact_email": "gdg@example.com",
        }, format="json", **INTERNAL)
        self.assertEqual(response.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token(7)}")
        profile = self.client.get("/api/organizer/profile/").json()
        self.assertEqual(profile["name"], "GDG Alger")
        self.assertEqual(profile["verification_status"], "pending")

    def test_organizer_cannot_verify_himself(self):
        self.client.patch("/api/organizer/profile/", {"verification_status": "verified", "city": "Oran"},
                          format="json")
        self.org.refresh_from_db()
        self.assertEqual(self.org.city, "Oran")
        self.assertEqual(self.org.verification_status, "pending")

    def test_settings_toggle_notifications(self):
        response = self.client.patch("/api/organizer/settings/", {"notify_status_changes": False}, format="json")
        self.assertEqual(response.status_code, 200)
        self.org.refresh_from_db()
        self.assertFalse(self.org.notify_status_changes)

    # ---------- publications
    def test_create_draft_then_submit(self):
        created = self.client.post("/api/organizer/publications/", self.full_publication(), format="json")
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(created.json()["status"], "draft")
        submitted = self.client.post(f"/api/organizer/publications/{created.json()['id']}/submit/")
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.json()["status"], "pending")

    def test_incomplete_draft_cannot_be_submitted(self):
        created = self.client.post("/api/organizer/publications/",
                                   {"category": "event", "title": "Summit"}, format="json")
        response = self.client.post(f"/api/organizer/publications/{created.json()['id']}/submit/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("application_link", response.json())

    def test_wrong_dates_are_refused(self):
        start = timezone.localdate() + timedelta(days=10)
        response = self.client.post("/api/organizer/publications/", self.full_publication(
            start_date=start.isoformat(), end_date=(start - timedelta(days=1)).isoformat()), format="json")
        self.assertEqual(response.status_code, 400)

    def test_status_is_read_only(self):
        response = self.client.post("/api/organizer/publications/",
                                    self.full_publication(status="approved"), format="json")
        self.assertEqual(response.json()["status"], "draft")

    def test_organizer_only_sees_his_publications(self):
        other = Organization.objects.create(user_id=2, name="Other", org_type="ngo", city="Oran",
                                            contact_email="o@example.com")
        Publication.objects.create(organization=other, category="event", title="Not mine")
        Publication.objects.create(organization=self.org, category="event", title="Mine")
        titles = [p["title"] for p in self.client.get("/api/organizer/publications/").json()["results"]]
        self.assertEqual(titles, ["Mine"])

    def test_filters_and_counts(self):
        Publication.objects.create(organization=self.org, category="event", title="A", status="approved")
        Publication.objects.create(organization=self.org, category="club", title="B", status="draft")
        Publication.objects.create(organization=self.org, category="club", title="C", status="draft")
        response = self.client.get("/api/organizer/publications/?status=draft&category=club")
        self.assertEqual(response.json()["count"], 2)
        counts = self.client.get("/api/organizer/publications/counts/").json()
        self.assertEqual((counts["all"], counts["draft"], counts["approved"]), (3, 2, 1))

    def test_moderation_by_admin_service_sends_email(self):
        pub = Publication.objects.create(organization=self.org, category="event", title="Summit",
                                         status="pending")
        response = APIClient().post(f"/api/internal/publications/{pub.id}/status/",
                                    {"status": "rejected", "reason": "Add the dates."},
                                    format="json", **INTERNAL)
        self.assertEqual(response.status_code, 200)
        pub.refresh_from_db()
        self.assertEqual((pub.status, pub.rejection_reason), ("rejected", "Add the dates."))
        self.assertEqual(len(mail.outbox), 1)

    def test_internal_endpoint_needs_key(self):
        pub = Publication.objects.create(organization=self.org, category="event", title="X", status="pending")
        response = APIClient().post(f"/api/internal/publications/{pub.id}/status/",
                                    {"status": "approved"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_editing_approved_publication_goes_back_to_review(self):
        pub = Publication.objects.create(organization=self.org, category="event", title="Summit",
                                         status="approved")
        self.client.patch(f"/api/organizer/publications/{pub.id}/", {"title": "Summit 2027"}, format="json")
        pub.refresh_from_db()
        self.assertEqual(pub.status, "pending")

    # ---------- dashboard
    def test_dashboard_kpis_and_chart(self):
        pub = Publication.objects.create(organization=self.org, category="event", title="Summit",
                                         status="approved", application_deadline=timezone.localdate()
                                         + timedelta(days=5), published_at=timezone.now())
        Publication.objects.create(organization=self.org, category="club", title="P", status="pending")
        for _ in range(3):
            APIClient().post(f"/api/publications/{pub.id}/track/", {"event": "view"}, format="json")
        APIClient().post(f"/api/publications/{pub.id}/track/", {"event": "save"}, format="json")

        data = self.client.get("/api/organizer/dashboard/").json()
        self.assertEqual(data["kpis"]["live_publications"], 1)
        self.assertEqual(data["kpis"]["pending_publications"], 1)
        self.assertEqual(data["kpis"]["total_views"], 3)
        self.assertEqual(data["kpis"]["saves"], 1)
        self.assertEqual(len(data["views_chart"]["points"]), 30)
        self.assertEqual(data["views_chart"]["points"][-1]["views"], 3)
