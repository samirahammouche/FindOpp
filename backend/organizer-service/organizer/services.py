"""Business rules of the organizer space.

They are used both by the REST views and by the RabbitMQ consumer,
so the same rule applies whatever the way the information arrives.
"""
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.utils import timezone

from .messaging import publication_payload, publish_event
from .models import DailyStat, Organization, Publication


def register_organization(data):
    """Create (or update) the profile from the "Create account" information."""
    organization, created = Organization.objects.update_or_create(
        user_id=data["user_id"],
        defaults={k: v for k, v in data.items() if k != "user_id"},
    )
    return organization, created


def submit_publication(publication):
    """Draft / rejected -> pending (sent to the admins for review)."""
    publication.status = Publication.Status.PENDING
    publication.rejection_reason = ""
    publication.submitted_at = timezone.now()
    publication.save()
    publish_event("publication.submitted", publication_payload(publication))
    return publication


def after_update(publication, was_status):
    """An approved publication that is edited goes back to review."""
    if was_status == Publication.Status.APPROVED:
        submit_publication(publication)
        publish_event("publication.updated", publication_payload(publication))


def duplicate_publication(original):
    copy = Publication.objects.get(pk=original.pk)
    copy.pk = None
    copy.title = f"{original.title} (copy)"
    copy.status = Publication.Status.DRAFT
    copy.rejection_reason = ""
    copy.submitted_at = copy.published_at = None
    copy.views_count = copy.saves_count = 0
    copy.save()
    return copy


def delete_publication(publication):
    payload = publication_payload(publication)
    publication.delete()
    publish_event("publication.deleted", payload)


def status_counts(organization):
    rows = organization.publications.values("status").annotate(n=Count("id"))
    result = {s: 0 for s in Publication.Status.values}
    result.update({row["status"]: row["n"] for row in rows})
    result["all"] = sum(result.values())
    return result


PUBLICATION_ORDERINGS = {
    "newest": "-created_at", "oldest": "created_at",
    "deadline": "application_deadline", "-deadline": "-application_deadline",
    "views": "-views_count", "title": "title",
}


def filter_publications(queryset, status="", category="", search="", ordering=""):
    """Filters of "My publications" (used by the API and by the page)."""
    if status:
        queryset = queryset.filter(status=status)
    if category:
        queryset = queryset.filter(category=category)
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(short_description__icontains=search))
    return queryset.order_by(PUBLICATION_ORDERINGS.get(ordering, "-created_at"))


def apply_moderation_decision(publication, status, reason=""):
    """Approve or reject a pending publication (decision of the Admin service)."""
    publication.status = status
    if status == Publication.Status.APPROVED:
        publication.rejection_reason = ""
        publication.published_at = publication.published_at or timezone.now()
    else:
        publication.rejection_reason = reason
    publication.save()
    notify_status_change(publication)
    return publication


def notify_status_change(publication):
    organization = publication.organization
    if not organization.notify_status_changes:
        return
    subject = f"FindOpp – your publication is now {publication.get_status_display().lower()}"
    lines = [
        f"Hello {organization.name},",
        "",
        f'The status of "{publication.title}" is now: {publication.get_status_display()}.',
    ]
    if publication.rejection_reason:
        lines += ["", f"Reason: {publication.rejection_reason}"]
    lines += ["", "The FindOpp team"]
    send_mail(subject, "\n".join(lines), None, [organization.contact_email], fail_silently=True)


@transaction.atomic
def track_event(publication, event):
    """+1 view or +1 save (total and daily stats)."""
    stat, _ = DailyStat.objects.get_or_create(publication=publication, date=timezone.localdate())
    if event == "view":
        Publication.objects.filter(pk=publication.pk).update(views_count=F("views_count") + 1)
        DailyStat.objects.filter(pk=stat.pk).update(views=F("views") + 1)
    else:
        Publication.objects.filter(pk=publication.pk).update(saves_count=F("saves_count") + 1)
        DailyStat.objects.filter(pk=stat.pk).update(saves=F("saves") + 1)


def expire_publications():
    """Approved publications whose deadline is passed become "expired"."""
    return Publication.objects.filter(
        status=Publication.Status.APPROVED,
        application_deadline__lt=timezone.localdate(),
    ).update(status=Publication.Status.EXPIRED)


def _percent_change(current, previous):
    if not previous:
        return None
    return round((current - previous) * 100 / previous, 1)


def dashboard_data(organization, days=30):
    """Everything shown in the "Overview" section."""
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    previous_start = start - timedelta(days=days)
    month_start = today.replace(day=1)
    publications = organization.publications.all()
    stats = DailyStat.objects.filter(publication__organization=organization)

    live = publications.filter(status=Publication.Status.APPROVED).exclude(application_deadline__lt=today)
    new_live_this_month = live.filter(published_at__date__gte=month_start).count()

    totals = publications.aggregate(views=Sum("views_count"), saves=Sum("saves_count"))
    views_period = stats.filter(date__gte=start).aggregate(v=Sum("views"))["v"] or 0
    views_previous = stats.filter(date__gte=previous_start, date__lt=start).aggregate(v=Sum("views"))["v"] or 0
    saves_this_month = stats.filter(date__gte=month_start).aggregate(s=Sum("saves"))["s"] or 0

    per_day = {
        row["date"]: row["total"]
        for row in stats.filter(date__gte=start).values("date").annotate(total=Sum("views"))
    }
    chart = [
        {"date": start + timedelta(days=i), "views": per_day.get(start + timedelta(days=i), 0)}
        for i in range(days)
    ]

    return {
        "organization": {
            "name": organization.name,
            "org_type": organization.org_type,
            "is_verified": organization.is_verified,
        },
        "kpis": {
            "live_publications": live.count(),
            "new_live_this_month": new_live_this_month,
            "total_views": totals["views"] or 0,
            "views_change_percent": _percent_change(views_period, views_previous),
            "saves": totals["saves"] or 0,
            "saves_this_month": saves_this_month,
            "pending_publications": publications.filter(status=Publication.Status.PENDING).count(),
        },
        "views_chart": {"from": start, "to": today, "points": chart},
    }
