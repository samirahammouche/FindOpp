from pathlib import Path

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Organization

User = get_user_model()

admin.site.register(User)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization_type",
        "city",
        "organizer_email",
        "verification_status",
        "document_link",
    )
    list_filter = ("verification_status", "organization_type", "city")
    search_fields = ("name", "city", "organizer__email")
    readonly_fields = ("organizer", "document_download")
    fields = (
        "organizer",
        "name",
        "organization_type",
        "city",
        "website",
        "document_download",
        "verification_status",
    )
    actions = ("approve_organizers", "reject_organizers")

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/document/",
                self.admin_site.admin_view(self.download_document),
                name="accounts_organization_download_document",
            ),
        ]
        return custom_urls + super().get_urls()

    @admin.display(ordering="organizer__email", description="Organizer email")
    def organizer_email(self, organization):
        return organization.organizer.email

    def download_document(self, request, object_id):
        organization = get_object_or_404(Organization, pk=object_id)
        if not self.has_view_or_change_permission(request, organization):
            raise PermissionDenied
        if not organization.official_document:
            raise Http404("No supporting document is available.")

        extension = Path(organization.official_document.name).suffix
        return FileResponse(
            organization.official_document.open("rb"),
            as_attachment=True,
            filename=f"supporting-document{extension}",
        )

    @admin.display(description="Supporting document")
    def document_link(self, organization):
        if not organization.official_document:
            return "—"
        url = reverse(
            "admin:accounts_organization_download_document",
            args=[organization.pk],
        )
        return format_html('<a href="{}">Download</a>', url)

    @admin.display(description="Supporting document")
    def document_download(self, organization):
        return self.document_link(organization)

    @admin.action(description="Approve selected organizer accounts")
    def approve_organizers(self, request, queryset):
        for organization in queryset.select_related("organizer"):
            organization.verification_status = (
                Organization.VerificationStatus.APPROVED
            )
            organization.save(update_fields=["verification_status"])
            organization.organizer.is_active = True
            organization.organizer.save(update_fields=["is_active"])
        self.message_user(
            request,
            "Selected organizer accounts were approved.",
            messages.SUCCESS,
        )

    @admin.action(description="Reject selected organizer accounts")
    def reject_organizers(self, request, queryset):
        for organization in queryset.select_related("organizer"):
            organization.verification_status = (
                Organization.VerificationStatus.REJECTED
            )
            organization.save(update_fields=["verification_status"])
            organization.organizer.is_active = False
            organization.organizer.save(update_fields=["is_active"])
        self.message_user(
            request,
            "Selected organizer accounts were rejected.",
            messages.SUCCESS,
        )
