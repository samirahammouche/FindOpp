from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Organization, User


class OrganizerRegistrationTests(APITestCase):
    registration_url = "/api/auth/register/"
    password = "OrganizerPass!729"

    def registration_data(self, filename="verification.pdf", content=b"%PDF-1.4 test"):
        return {
            "email": "organizer@example.com",
            "first_name": "Amina",
            "last_name": "Benali",
            "password": self.password,
            "organization_name": "Algeria Startup Hub",
            "organization_type": Organization.Type.COMPANY,
            "city": "Alger",
            "website": "https://example.com",
            "official_document": SimpleUploadedFile(
                filename,
                content,
                content_type="application/pdf",
            ),
        }

    def test_registration_creates_pending_organizer_and_organization(self):
        response = self.client.post(
            self.registration_url,
            self.registration_data(),
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="organizer@example.com")
        organization = Organization.objects.get(organizer=user)
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, User.Role.ORGANIZER)
        self.assertEqual(organization.name, "Algeria Startup Hub")
        self.assertEqual(
            organization.verification_status,
            Organization.VerificationStatus.PENDING,
        )
        self.assertEqual(response.data["verification_status"], "PENDING")
        organization.official_document.delete(save=False)

    def test_registration_rejects_unsupported_document_type(self):
        response = self.client.post(
            self.registration_url,
            self.registration_data(filename="verification.exe", content=b"test"),
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="organizer@example.com").exists())

    def test_registration_rejects_documents_over_10_megabytes(self):
        response = self.client.post(
            self.registration_url,
            self.registration_data(content=b"x" * (10 * 1024 * 1024 + 1)),
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("10 MB or smaller", str(response.data))
        self.assertFalse(User.objects.filter(email="organizer@example.com").exists())
