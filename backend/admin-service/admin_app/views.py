from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .models import Admin, JournalActivite
from .serializers import AdminSerializer, JournalActiviteSerializer

class AdminViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    """
    API endpoint that allows admins to be viewed.
    Read-only: No create, update, or delete via API.
    """
    queryset = Admin.objects.all().order_by('id')
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated] # Only logged-in users can see this

class JournalActiviteViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """
    API endpoint that allows the activity journal to be viewed.
    Read-only: Audit logs cannot be altered.
    """
    queryset = JournalActivite.objects.all().order_by('-date_action')
    serializer_class = JournalActiviteSerializer
    permission_classes = [IsAuthenticated]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.moderation_service import ModerationService

class ApproveEventView(APIView):
    def post(self, request, event_id):
        # 1. Initialize the service with the logged-in admin
        service = ModerationService(admin_user=request.user)
        
        # 2. Call the business logic
        success, message = service.approve_event(event_id)
        
        # 3. Return the appropriate HTTP response
        if success:
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class RejectEventView(APIView):
    def post(self, request, event_id):
        service = ModerationService(admin_user=request.user)
        success, message = service.reject_event(event_id)
        
        if success:
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ValidateOrganizerView(APIView):
    def post(self, request, organizer_id):
        service = ModerationService(admin_user=request.user)
        success, message = service.validate_organizer(organizer_id)
        
        if success:
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class SuspendOrganizerView(APIView):
    def post(self, request, organizer_id):
        service = ModerationService(admin_user=request.user)
        success, message = service.suspend_organizer(organizer_id)
        
        if success:
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ReactivateOrganizerView(APIView):
    def post(self, request, organizer_id):
        service = ModerationService(admin_user=request.user)
        success, message = service.reactivate_organizer(organizer_id)
        
        if success:
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate

class VerifyAdminView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)

        if user is not None:
            return Response({
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)