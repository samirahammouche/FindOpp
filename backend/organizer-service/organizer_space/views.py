"""Pages of the organizer space (Django templates).

The pages and the REST API live in the same microservice: the views below use
the same models, serializers (validation) and business rules (organizer/services.py)
as the API, without any HTTP call between them.
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from accounts.auth_client import AuthServiceError, change_password
from organizer import services
from organizer.models import Publication
from organizer.serializers import (
    OrganizationSerializer,
    PublicationListSerializer,
    PublicationSerializer,
    SettingsSerializer,
    check_ready_to_submit,
)

from .charts import build_views_chart
from .decorators import organizer_required, remember_organization
from .forms import ContactForm, PasswordForm, ProfileForm, PublicationFilterForm, PublicationForm

PAGE_SIZE = 6
TABS = [("", "All"), ("approved", "Approved"), ("pending", "Pending"), ("draft", "Drafts"),
        ("expired", "Expired"), ("rejected", "Rejected")]


def add_errors(form, errors):
    """Shows serializer / business errors on the right fields of a Django form."""
    for field, error in errors.items():
        text = " ".join(str(e) for e in error) if isinstance(error, (list, tuple)) else str(error)
        form.add_error(field if field in form.fields else None, text)


# ------------------------------------------------------------------ Overview (class view)

@method_decorator(organizer_required, name="dispatch")
class DashboardView(View):
    """Overview: greeting, 4 KPI cards, 30-day views chart and the latest publications."""

    template_name = "organizer_space/overview.html"

    def get(self, request):
        organization = request.organization
        data = services.dashboard_data(organization)
        latest = organization.publications.order_by("-created_at")[:PAGE_SIZE]
        return render(request, self.template_name, {
            "dashboard": data,
            "kpis": data["kpis"],
            "chart": build_views_chart(data["views_chart"]),
            "publications": PublicationListSerializer(latest, many=True).data,
            "publications_count": organization.publications.count(),
        })


# ------------------------------------------------------------------ My publications

@organizer_required
def publication_list(request):
    form = PublicationFilterForm(request.GET or None)
    filters = form.cleaned_data if form.is_valid() else {}
    queryset = services.filter_publications(request.organization.publications.all(), **filters)
    page = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))
    counts = services.status_counts(request.organization)
    current = filters.get("status", "")
    return render(request, "organizer_space/publications/list.html", {
        "form": form,
        "publications": PublicationListSerializer(page.object_list, many=True).data,
        "count": page.paginator.count,
        "tabs": [{"value": v, "label": label, "count": counts.get(v or "all", 0), "active": v == current}
                 for v, label in TABS],
        "pages": {"number": page.number, "last": page.paginator.num_pages, "range": page.paginator.page_range,
                  "has_previous": page.has_previous(), "has_next": page.has_next(),
                  "previous": page.number - 1, "next": page.number + 1},
    })


def _save_publication(request, form, publication=None):
    """Save draft or Submit.

    Returns (publication, ok): `publication` is None if nothing was saved,
    `ok` is False when the form must be shown again with its errors.
    """
    data = form.to_api()
    if request.FILES.get("cover_image"):
        data["cover_image"] = request.FILES["cover_image"]
    serializer = PublicationSerializer(publication, data=data, partial=publication is not None)
    if not serializer.is_valid():
        add_errors(form, serializer.errors)
        return publication, False

    was_status = publication.status if publication else None
    if publication:
        publication = serializer.save()
    else:
        publication = serializer.save(organization=request.organization, status=Publication.Status.DRAFT)

    if request.POST.get("action") == "submit" and publication.status in (
            Publication.Status.DRAFT, Publication.Status.REJECTED):
        errors = check_ready_to_submit(publication)
        if errors:
            add_errors(form, errors)
            messages.warning(request, "Saved as a draft. Complete the highlighted fields to submit it.")
            return publication, False
        services.submit_publication(publication)
        messages.success(request, f"“{publication.title}” was submitted for review.")
    else:
        services.after_update(publication, was_status)
        messages.success(request, f"“{publication.title}” was saved.")
    return publication, True


@organizer_required
def publication_create(request):
    publication = None
    if request.method == "POST":
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication, ok = _save_publication(request, form)
            if ok:
                return redirect("organizer_space:publications")
            if publication:  # saved as a draft but not complete: continue on its edit page
                return render(request, "organizer_space/publications/form.html", {
                    "form": form, "publication": PublicationSerializer(publication).data,
                    "action_url": reverse("organizer_space:publication_edit", args=[publication.pk]),
                })
    else:
        form = PublicationForm(initial={"category": request.GET.get("category", "hackathon"), "currency": "DZD"})
    return render(request, "organizer_space/publications/form.html", {"form": form, "publication": None})


@organizer_required
def publication_edit(request, pk):
    publication = get_object_or_404(Publication, pk=pk, organization=request.organization)
    if publication.status == Publication.Status.EXPIRED:
        messages.error(request, "An expired publication can no longer be edited.")
        return redirect("organizer_space:publications")
    if request.method == "POST":
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication, ok = _save_publication(request, form, publication)
            if ok:
                return redirect("organizer_space:publications")
    else:
        form = PublicationForm(initial=PublicationForm.initial_from_api(PublicationSerializer(publication).data))
    return render(request, "organizer_space/publications/form.html",
                  {"form": form, "publication": PublicationSerializer(publication).data})


@require_POST
@organizer_required
def publication_action(request, pk, action):
    """Buttons of the ⋯ menu: submit, duplicate, delete."""
    publication = get_object_or_404(Publication, pk=pk, organization=request.organization)
    if action == "submit":
        if publication.status not in (Publication.Status.DRAFT, Publication.Status.REJECTED):
            messages.error(request, "Only a draft or a rejected publication can be submitted.")
        elif check_ready_to_submit(publication):
            messages.error(request, "This publication is incomplete. Fill in the missing fields.")
            return redirect("organizer_space:publication_edit", pk=pk)
        else:
            services.submit_publication(publication)
            messages.success(request, "Publication submitted for review.")
    elif action == "duplicate":
        copy = services.duplicate_publication(publication)
        messages.success(request, f"Draft “{copy.title}” created.")
    elif action == "delete":
        services.delete_publication(publication)
        messages.success(request, "Publication deleted.")
    next_url = request.POST.get("next", "")
    return redirect(next_url if next_url.startswith("/organizer/") else "organizer_space:publications")


# ------------------------------------------------------------------ Organization profile + Space settings
# One page, like the Figma design: the public profile, then the space settings below it.

@organizer_required
def profile_view(request):
    organization = request.organization
    remember_organization(request, organization)
    contact_form = ContactForm(initial={"contact_email": organization.contact_email, "phone": organization.phone})
    password_form = PasswordForm()
    section = request.POST.get("section", "")
    back = reverse("organizer_space:profile") + "#settings"

    if request.method == "POST":
        if section == "notifications":
            organization.notify_status_changes = not organization.notify_status_changes
            organization.save(update_fields=["notify_status_changes", "updated_at"])
            messages.success(request, "Notification preference saved.")
            return redirect(back)

        if section == "contact":
            contact_form = ContactForm(request.POST)
            if contact_form.is_valid():
                serializer = SettingsSerializer(organization, data=contact_form.cleaned_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    messages.success(request, "Contact details saved.")
                    return redirect(back)
                add_errors(contact_form, serializer.errors)

        if section == "password":
            password_form = PasswordForm(request.POST)
            if password_form.is_valid():
                try:  # the password belongs to the Auth service
                    change_password(request.session["token"], password_form.cleaned_data["old_password"],
                                    password_form.cleaned_data["new_password"])
                    messages.success(request, "Password changed.")
                    return redirect(back)
                except AuthServiceError as error:
                    add_errors(password_form, error.errors)

    return render(request, "organizer_space/profile.html", {
        "profile": OrganizationSerializer(organization).data,
        "settings": SettingsSerializer(organization).data,
        "contact_form": contact_form, "password_form": password_form, "open_section": section,
    })


@organizer_required
def profile_edit(request):
    organization = request.organization
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            data = {k: v for k, v in form.cleaned_data.items() if k not in ("logo", "cover_image")}
            for name in ("logo", "cover_image"):
                if request.FILES.get(name):
                    data[name] = request.FILES[name]
            serializer = OrganizationSerializer(organization, data=data, partial=True)
            if serializer.is_valid():
                remember_organization(request, serializer.save())
                messages.success(request, "Profile updated.")
                return redirect("organizer_space:profile")
            add_errors(form, serializer.errors)
    else:
        form = ProfileForm(initial=OrganizationSerializer(organization).data)
    return render(request, "organizer_space/profile_form.html",
                  {"form": form, "profile": OrganizationSerializer(organization).data})


def settings_redirect(request):
    """/organizer/settings/ -> the settings section of the profile page."""
    return redirect(reverse("organizer_space:profile") + "#settings")
