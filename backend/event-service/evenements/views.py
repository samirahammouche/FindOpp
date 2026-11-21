from django.utils import timezone
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categorie, Evenement, StatutEvenement
from .permissions import IsAdminRole, IsOrganizer, IsOwner
from .serializers import (CategorieSerializer, EvenementSerializer,
                          EvenementWriteSerializer)

# Statuts dans lesquels l'organisateur peut modifier son evenement
STATUTS_MODIFIABLES = (StatutEvenement.BROUILLON, StatutEvenement.REJETEE)


def reponse_conflit(message):
    return Response({'detail': message}, status=status.HTTP_409_CONFLICT)


def evenements_visibles():
    """Événements visibles par un visiteur : approuvés ET non expirés,
    triés par date limite (la plus proche d'abord)."""
    today = timezone.localdate()
    return (
        Evenement.objects
        .filter(statut=StatutEvenement.APPROUVEE, dateLimite__gte=today)
        .select_related('categorie')
        .order_by('dateLimite', '-dateCreation')
    )


class EvenementListView(generics.ListAPIView):
    # /api/events/?search=salon&categorie=1&ordering=-dateCreation
    serializer_class = EvenementSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['titre', 'description', 'categorie__nom']
    ordering_fields = ['dateLimite', 'dateCreation', 'titre']
    ordering = ['dateLimite', '-dateCreation']

    def get_queryset(self):
        queryset = evenements_visibles()
        categorie = self.request.query_params.get('categorie')
        if categorie and categorie.isdigit():
            queryset = queryset.filter(categorie_id=int(categorie))
        return queryset


class EvenementDetailView(generics.RetrieveAPIView):
    """Détail d'un événement approuvé."""
    serializer_class = EvenementSerializer

    def get_queryset(self):
        return (
            Evenement.objects
            .filter(statut=StatutEvenement.APPROUVEE)
            .select_related('categorie')
        )


class SuggestionListView(APIView):
    """Les 6 événements dont la date limite est la plus proche."""

    def get(self, request):
        serializer = EvenementSerializer(evenements_visibles()[:6], many=True)
        return Response(serializer.data)


class CategorieListCreateView(generics.ListCreateAPIView):
    # GET: tout le monde. POST: administrateur seulement.
    queryset = Categorie.objects.order_by('nom')
    serializer_class = CategorieSerializer
    pagination_class = None

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminRole()]
        return [AllowAny()]