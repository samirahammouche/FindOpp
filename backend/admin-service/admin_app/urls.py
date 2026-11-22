from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminViewSet, JournalActiviteViewSet,
    ApproveEventView, RejectEventView, 
    ValidateOrganizerView, SuspendOrganizerView, ReactivateOrganizerView, VerifyAdminView
)

router = DefaultRouter()
router.register(r'admins', AdminViewSet, basename='admin')
router.register(r'journal', JournalActiviteViewSet, basename='journal')

urlpatterns = [
    # Standard CRUD routes
    path('', include(router.urls)),
    
    # Moderation custom routes
    path('moderation/events/<int:event_id>/approve/', ApproveEventView.as_view(), name='approve-event'),
    path('moderation/events/<int:event_id>/reject/', RejectEventView.as_view(), name='reject-event'),
    path('moderation/organizers/<int:organizer_id>/validate/', ValidateOrganizerView.as_view(), name='validate-organizer'),
    path('moderation/organizers/<int:organizer_id>/suspend/', SuspendOrganizerView.as_view(), name='suspend-organizer'),
    path('moderation/organizers/<int:organizer_id>/reactivate/', ReactivateOrganizerView.as_view(), name='reactivate-organizer'),
    path('internal/verify-admin/', VerifyAdminView.as_view(), name='verify-admin'),
]