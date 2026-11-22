from django.contrib import admin

from .models import DailyStat, Organization, Publication


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "org_type", "city", "contact_email", "verification_status", "created_at")
    list_filter = ("org_type", "verification_status")
    search_fields = ("name", "city", "contact_email")


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "category", "status", "application_deadline", "views_count")
    list_filter = ("category", "status")
    search_fields = ("title", "organization__name")


@admin.register(DailyStat)
class DailyStatAdmin(admin.ModelAdmin):
    list_display = ("publication", "date", "views", "saves")
    list_filter = ("date",)
