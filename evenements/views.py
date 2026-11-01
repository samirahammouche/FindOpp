from django.shortcuts import render
from rest_framework import generics
from .models import Evenement, StatutEvenement
from .serializers import EvenementSerializer

# Create your views here.


class EvenementListView(generics.ListAPIView):
    """Liste publique : seulement les événements approuvés."""
    serializer_class = EvenementSerializer

    def get_queryset(self):
        return (
            Evenement.objects
            .filter(statut=StatutEvenement.APPROUVEE)
            .select_related('categorie')
            .order_by('-dateCreation')
        )


class EvenementDetailView(generics.RetrieveAPIView):
    """Détail d'un événement approuvé."""
    serializer_class = EvenementSerializer

    def get_queryset(self):
        return (
            Evenement.objects
            .filter(statut=StatutEvenement.APPROUVEE)
            .select_related('categorie')
        )