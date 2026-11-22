from django.utils import timezone
from rest_framework import serializers

from .models import Organization, Publication


def file_url(file):
    """Relative URL of an uploaded file ("" when empty), e.g. /organizer-media/logos/x.png"""
    return file.url if file else ""


class OrganizationSerializer(serializers.ModelSerializer):
    """"Organization profile" section. Verification is decided by the admins."""

    org_type_label = serializers.CharField(source="get_org_type_display", read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id", "name", "org_type", "org_type_label", "city", "description",
            "contact_email", "phone", "website", "linkedin", "instagram",
            "logo", "cover_image", "logo_url", "cover_image_url",
            "verification_status", "is_verified", "created_at", "updated_at",
        ]
        read_only_fields = ["verification_status", "created_at", "updated_at"]
        extra_kwargs = {"logo": {"write_only": True}, "cover_image": {"write_only": True}}

    def get_logo_url(self, obj):
        return file_url(obj.logo)

    def get_cover_image_url(self, obj):
        return file_url(obj.cover_image)


class OrganizationRegistrationSerializer(serializers.ModelSerializer):
    """Data sent by the Auth service when an organizer creates an account."""

    class Meta:
        model = Organization
        fields = [
            "user_id", "name", "org_type", "city", "contact_email",
            "phone", "website", "description",
        ]


class SettingsSerializer(serializers.ModelSerializer):
    """"Space settings" section (the password is changed in the Auth service)."""

    class Meta:
        model = Organization
        fields = ["notify_status_changes", "contact_email", "phone"]


class PublicationListSerializer(serializers.ModelSerializer):
    """One row of the "My publications" table."""

    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Publication
        fields = [
            "id", "title", "category", "category_label", "status", "status_label",
            "application_deadline", "views_count", "saves_count", "updated_at",
        ]


class PublicationSerializer(serializers.ModelSerializer):
    """"Create a publication" form (and edit)."""

    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    organization_verified = serializers.BooleanField(source="organization.is_verified", read_only=True)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            "id", "organization_name", "organization_verified",
            "category", "category_label", "status", "status_label",
            "title", "short_description", "full_description", "cover_image", "cover_image_url",
            "location", "is_remote", "application_link",
            "study_levels", "fields_of_study", "eligible_region", "open_to_all_nationalities",
            "funding_type", "amount", "currency",
            "start_date", "end_date", "application_deadline",
            "rejection_reason", "submitted_at", "published_at",
            "views_count", "saves_count", "created_at", "updated_at",
        ]
        extra_kwargs = {"cover_image": {"write_only": True}}
        read_only_fields = [
            "status", "rejection_reason", "submitted_at", "published_at",
            "views_count", "saves_count", "created_at", "updated_at",
        ]

    def get_cover_image_url(self, obj):
        return file_url(obj.cover_image)

    def validate_study_levels(self, value):
        wrong = [v for v in value if v not in Publication.STUDY_LEVELS]
        if wrong:
            raise serializers.ValidationError(
                f"Unknown level(s): {wrong}. Allowed: {Publication.STUDY_LEVELS}"
            )
        return value

    def validate_fields_of_study(self, value):
        if not all(isinstance(v, str) and v.strip() for v in value):
            raise serializers.ValidationError("Each field of study must be a non-empty text.")
        return [v.strip() for v in value]

    def validate(self, data):
        start = data.get("start_date", getattr(self.instance, "start_date", None))
        end = data.get("end_date", getattr(self.instance, "end_date", None))
        deadline = data.get("application_deadline", getattr(self.instance, "application_deadline", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "The end date must be after the start date."})
        if deadline and start and deadline > start:
            raise serializers.ValidationError(
                {"application_deadline": "The application deadline must be before the start date."}
            )
        return data


# Fields that must be filled before a draft can be submitted for review.
REQUIRED_TO_SUBMIT = {
    "title": "Publication title",
    "short_description": "Short description",
    "full_description": "Full description",
    "application_link": "External application link",
    "application_deadline": "Application deadline",
    "funding_type": "Funding",
}


def check_ready_to_submit(publication):
    """Return a dict of errors ({} when the publication can be submitted)."""
    errors = {}
    for field, label in REQUIRED_TO_SUBMIT.items():
        if not getattr(publication, field):
            errors[field] = f"{label} is required before submitting."
    if not publication.location and not publication.is_remote:
        errors["location"] = "Give a location or mark the opportunity as remote."
    if not publication.study_levels:
        errors["study_levels"] = "Choose at least one study level."
    if publication.application_deadline and publication.application_deadline < timezone.localdate():
        errors["application_deadline"] = "The application deadline is already passed."
    return errors


class StatusUpdateSerializer(serializers.Serializer):
    """Moderation decision sent by the Admin service."""

    status = serializers.ChoiceField(choices=[Publication.Status.APPROVED, Publication.Status.REJECTED])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["status"] == Publication.Status.REJECTED and not data.get("reason"):
            raise serializers.ValidationError({"reason": "A reason is required to reject a publication."})
        return data


class TrackSerializer(serializers.Serializer):
    """Event sent by the public site when a student views or saves a publication."""

    event = serializers.ChoiceField(choices=["view", "save"])
