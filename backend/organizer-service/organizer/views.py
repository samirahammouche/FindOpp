from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import services
from .models import Organization, Publication
from .permissions import IsInternalService, IsOrganizer
from .serializers import (
    OrganizationRegistrationSerializer,
    OrganizationSerializer,
    PublicationListSerializer,
    PublicationSerializer,
    SettingsSerializer,
    StatusUpdateSerializer,
    TrackSerializer,
    check_ready_to_submit,
)


def get_organization(request):
    """Profile of the organizer who owns the token."""
    try:
        return Organization.objects.get(user_id=request.user.id)
    except Organization.DoesNotExist:
        raise NotFound("No organizer profile for this account. Create the account first.")


# ---------------------------------------------------------------- Overview

@api_view(["GET"])
@permission_classes([IsOrganizer])
def dashboard(request):
    """GET /api/organizer/dashboard/?days=30  -> Overview (KPIs + views chart)."""
    try:
        days = min(max(int(request.query_params.get("days", 30)), 7), 365)
    except ValueError:
        days = 30
    return Response(services.dashboard_data(get_organization(request), days))


# ---------------------------------------------------------------- Profile & settings

class ProfileView(generics.RetrieveUpdateAPIView):
    """GET / PATCH /api/organizer/profile/  -> Organization profile."""

    serializer_class = OrganizationSerializer
    permission_classes = [IsOrganizer]

    def get_object(self):
        return get_organization(self.request)


class SettingsView(generics.RetrieveUpdateAPIView):
    """GET / PATCH /api/organizer/settings/  -> Space settings."""

    serializer_class = SettingsSerializer
    permission_classes = [IsOrganizer]

    def get_object(self):
        return get_organization(self.request)


# ---------------------------------------------------------------- My publications

class PublicationViewSet(viewsets.ModelViewSet):
    """CRUD of the organizer's own publications.

    GET    /api/organizer/publications/?status=&category=&search=&ordering=
    POST   /api/organizer/publications/                 (Save draft)
    GET    /api/organizer/publications/{id}/
    PATCH  /api/organizer/publications/{id}/            (Edit)
    DELETE /api/organizer/publications/{id}/
    POST   /api/organizer/publications/{id}/submit/     (Submit for review)
    POST   /api/organizer/publications/{id}/duplicate/
    GET    /api/organizer/publications/counts/          (All · Approved · Pending ... tabs)
    """

    permission_classes = [IsOrganizer]
    def get_serializer_class(self):
        return PublicationListSerializer if self.action == "list" else PublicationSerializer

    def get_queryset(self):
        queryset = Publication.objects.filter(
            organization__user_id=self.request.user.id
        ).select_related("organization")
        params = self.request.query_params
        return services.filter_publications(
            queryset, params.get("status", ""), params.get("category", ""),
            params.get("search", ""), params.get("ordering", ""),
        )

    def perform_create(self, serializer):
        serializer.save(organization=get_organization(self.request), status=Publication.Status.DRAFT)

    def update(self, request, *args, **kwargs):
        publication = self.get_object()
        if publication.status == Publication.Status.EXPIRED:
            return Response({"detail": "An expired publication can no longer be edited."},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        was_status = serializer.instance.status
        services.after_update(serializer.save(), was_status)

    def perform_destroy(self, instance):
        services.delete_publication(instance)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        publication = self.get_object()
        if publication.status not in (Publication.Status.DRAFT, Publication.Status.REJECTED):
            return Response({"detail": f"A {publication.status} publication cannot be submitted."},
                            status=status.HTTP_400_BAD_REQUEST)
        errors = check_ready_to_submit(publication)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        services.submit_publication(publication)
        return Response(PublicationSerializer(publication, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        copy = services.duplicate_publication(self.get_object())
        return Response(PublicationSerializer(copy, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def counts(self, request):
        return Response(services.status_counts(get_organization(request)))


# ---------------------------------------------------------------- Public site

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def track(request, pk):
    """POST /api/publications/{id}/track/  {"event": "view" | "save"}

    Called by the public site when a student opens or saves an opportunity.
    Only approved publications are counted.
    """
    publication = get_object_or_404(Publication, pk=pk, status=Publication.Status.APPROVED)
    serializer = TrackSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    services.track_event(publication, serializer.validated_data["event"])
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- Internal (other services)

class InternalOrganizationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """POST /api/internal/organizers/  (header X-Internal-Key)

    Same as the RabbitMQ event "organizer.registered": the Auth service sends
    the "Create account" information and the profile is created.
    """

    permission_classes = [IsInternalService]
    authentication_classes = []
    serializer_class = OrganizationRegistrationSerializer
    queryset = Organization.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # update_or_create: the user_id may already exist if the event was received twice
        serializer.fields["user_id"].validators = []
        serializer.is_valid(raise_exception=True)
        organization, created = services.register_organization(serializer.validated_data)
        return Response(OrganizationSerializer(organization).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([IsInternalService])
def internal_publication_status(request, pk):
    """POST /api/internal/publications/{id}/status/  {"status": "approved"|"rejected", "reason": ""}

    Same as the RabbitMQ event "publication.status_changed" (decision of the Admin service).
    """
    publication = get_object_or_404(Publication, pk=pk)
    if publication.status != Publication.Status.PENDING:
        return Response({"detail": "Only a pending publication can be approved or rejected."},
                        status=status.HTTP_400_BAD_REQUEST)
    serializer = StatusUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    services.apply_moderation_decision(publication, serializer.validated_data["status"],
                                       serializer.validated_data.get("reason", ""))
    return Response(PublicationSerializer(publication).data)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    """Health check used by Consul and Traefik."""
    return Response({"status": "ok", "service": "organizer-service"})

