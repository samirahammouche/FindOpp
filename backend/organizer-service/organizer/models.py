from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

IMAGE_VALIDATOR = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])


class Organization(models.Model):
    """Public profile of an organizer.

    It is created from the information given in the "Create account" form
    (handled by the Auth service). `user_id` is the id of the account in the
    Auth service: it links the JWT token to this profile.
    """

    class Type(models.TextChoices):
        UNIVERSITY = "university", "University"
        COMPANY = "company", "Company"
        NGO = "ngo", "NGO"
        CLUB = "club", "Student club"

    class Verification(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    user_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=150)
    org_type = models.CharField(max_length=20, choices=Type.choices)
    city = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    logo = models.FileField(upload_to="logos/", blank=True, validators=[IMAGE_VALIDATOR])
    cover_image = models.FileField(upload_to="covers/", blank=True, validators=[IMAGE_VALIDATOR])
    verification_status = models.CharField(
        max_length=20, choices=Verification.choices, default=Verification.PENDING
    )
    # "Space settings" > Publication notifications
    notify_status_changes = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()}, {self.city})"

    @property
    def is_verified(self):
        return self.verification_status == self.Verification.VERIFIED


class Publication(models.Model):
    """An opportunity published by an organizer (hackathon, scholarship, event, club)."""

    class Category(models.TextChoices):
        HACKATHON = "hackathon", "Hackathon"
        SCHOLARSHIP = "scholarship", "Scholarship"
        EVENT = "event", "Event"
        CLUB = "club", "Club"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    class Funding(models.TextChoices):
        FULLY_FUNDED = "fully_funded", "Fully funded"
        STIPEND = "stipend", "Stipend"
        PRIZE = "prize", "Prize"
        FREE = "free", "Free"

    STUDY_LEVELS = ["bachelor", "master", "phd"]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="publications"
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Opportunity details
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=300, blank=True)
    full_description = models.TextField(blank=True)
    cover_image = models.FileField(upload_to="publications/", blank=True, validators=[IMAGE_VALIDATOR])
    location = models.CharField(max_length=150, blank=True)
    is_remote = models.BooleanField(default=False)
    application_link = models.URLField(blank=True)

    # Eligibility
    study_levels = models.JSONField(default=list, blank=True)     # ["bachelor", "master"]
    fields_of_study = models.JSONField(default=list, blank=True)  # ["Computer science", "Robotics"]
    eligible_region = models.CharField(max_length=100, blank=True)
    open_to_all_nationalities = models.BooleanField(default=False)

    # Funding and dates
    funding_type = models.CharField(max_length=20, choices=Funding.choices, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="DZD")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)

    # Moderation (decided by the Admin service)
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Statistics (filled by the public site)
    views_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"

    @property
    def is_live(self):
        return self.status == self.Status.APPROVED and (
            self.application_deadline is None
            or self.application_deadline >= timezone.localdate()
        )


class DailyStat(models.Model):
    """Views and saves of a publication for one day (used for the 30-day chart)."""

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="daily_stats")
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("publication", "date")
        ordering = ["date"]

    def __str__(self):
        return f"{self.publication.title} - {self.date}: {self.views} views, {self.saves} saves"
