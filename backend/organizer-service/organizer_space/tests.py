"""Tests of the pages of the organizer space (real database, token like the Auth service's)."""
import time
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from organizer.authentication import encode_token
from organizer.models import Organization, Publication


@override_settings(JWT_SECRET="test-secret", RABBITMQ_URL="", AUTH_API_URL="", DEMO_LOGIN=True)
class OrganizerPagesTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(user_id=1, name="Club Robotique USTHB", org_type="club",
                                               city="Alger", contact_email="bureau@club.dz",
                                               verification_status="verified")
        self.deadline = (timezone.localdate() + timedelta(days=40)).isoformat()

    def login(self, role="organizer", user_id=1):
        token = encode_token({"user_id": user_id, "role": role, "exp": int(time.time()) + 3600})
        return self.client.post("/organizer/accounts/token/", {"token": token})

    def test_pages_need_login(self):
        response = self.client.get("/organizer/")
        self.assertRedirects(response, "/organizer/accounts/login/?next=/organizer/", fetch_redirect_response=False)

    def test_token_login_refuses_other_roles(self):
        self.login(role="admin")
        response = self.client.get("/organizer/")
        self.assertEqual(response.status_code, 302)

    def test_demo_login(self):
        response = self.client.post("/organizer/accounts/demo/")
        self.assertRedirects(response, "/organizer/", fetch_redirect_response=False)
        self.assertContains(self.client.get("/organizer/"), "Hello, Club Robotique USTHB")

    def test_overview(self):
        Publication.objects.create(organization=self.org, category="event", title="Web Summit", status="approved",
                                   application_deadline=timezone.localdate() + timedelta(days=5),
                                   published_at=timezone.now())
        self.login()
        response = self.client.get("/organizer/")
        self.assertContains(response, "Live publications")
        self.assertContains(response, "Web Summit")

    def test_list_filters_and_tabs(self):
        Publication.objects.create(organization=self.org, category="club", title="Creators Club", status="approved")
        Publication.objects.create(organization=self.org, category="hackathon", title="Robotics", status="draft")
        self.login()
        response = self.client.get("/organizer/publications/?status=draft")
        self.assertContains(response, "Robotics")
        self.assertNotContains(response, "Creators Club")
        self.assertContains(response, "Drafts · 1")

    def test_create_and_submit(self):
        self.login()
        response = self.client.post("/organizer/publications/new/", {
            "category": "hackathon", "title": "Robotics Hackathon 2027",
            "short_description": "A weekend to design robots.", "full_description": "Build as a team.",
            "location": "Alger", "application_link": "https://club.dz/apply", "study_levels": ["bachelor"],
            "fields_of_study": "Computer science, Robotics", "funding_type": "prize", "amount": "150000",
            "currency": "DZD", "application_deadline": self.deadline, "action": "submit",
        })
        self.assertRedirects(response, "/organizer/publications/", fetch_redirect_response=False)
        publication = Publication.objects.get()
        self.assertEqual(publication.status, "pending")
        self.assertEqual(publication.fields_of_study, ["Computer science", "Robotics"])

    def test_incomplete_submit_stays_a_draft(self):
        self.login()
        response = self.client.post("/organizer/publications/new/", {
            "category": "event", "title": "Summit", "currency": "DZD", "action": "submit"})
        self.assertContains(response, "is required before submitting")
        self.assertEqual(Publication.objects.get().status, "draft")

    def test_cannot_edit_another_organizer_publication(self):
        other = Organization.objects.create(user_id=2, name="Other", org_type="ngo", city="Oran",
                                            contact_email="o@o.dz")
        publication = Publication.objects.create(organization=other, category="event", title="Not mine")
        self.login()
        self.assertEqual(self.client.get(f"/organizer/publications/{publication.pk}/edit/").status_code, 404)

    def test_duplicate_and_delete(self):
        publication = Publication.objects.create(organization=self.org, category="event", title="Summit")
        self.login()
        self.client.post(f"/organizer/publications/{publication.pk}/duplicate/")
        self.assertTrue(Publication.objects.filter(title="Summit (copy)").exists())
        self.client.post(f"/organizer/publications/{publication.pk}/delete/")
        self.assertFalse(Publication.objects.filter(pk=publication.pk).exists())

    def test_profile_and_settings_on_one_page(self):
        self.login()
        response = self.client.get("/organizer/profile/")
        self.assertContains(response, "Organization <em>profile</em>", html=False)
        self.assertContains(response, "Space <em>settings</em>", html=False)
        self.client.post("/organizer/profile/", {"section": "notifications"})
        self.org.refresh_from_db()
        self.assertFalse(self.org.notify_status_changes)

    def test_edit_profile(self):
        self.login()
        self.client.post("/organizer/profile/edit/", {"name": "Club Robotique", "org_type": "club",
                                                       "city": "Boumerdès"})
        self.org.refresh_from_db()
        self.assertEqual((self.org.name, self.org.city), ("Club Robotique", "Boumerdès"))
        self.assertEqual(self.org.verification_status, "verified")   # cannot be changed by the organizer
