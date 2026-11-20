from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Evenement, StatutEvenement
from .serializers import EvenementSerializer


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
    """Le flux : triés par date limite."""
    serializer_class = EvenementSerializer

    def get_queryset(self):
        return evenements_visibles()


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