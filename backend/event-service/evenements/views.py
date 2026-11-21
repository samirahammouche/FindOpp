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


class MesEvenementsView(generics.ListCreateAPIView):
    # GET: mes evenements. POST: creer (toujours en BROUILLON)
    permission_classes = [IsOrganizer]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EvenementWriteSerializer
        return EvenementSerializer

    def get_queryset(self):
        queryset = (Evenement.objects
                    .filter(organisateurId=int(self.request.user.id))
                    .select_related('categorie')
                    .order_by('-dateCreation', '-id'))
        statut = self.request.query_params.get('statut')
        if statut in StatutEvenement.values:
            queryset = queryset.filter(statut=statut)
        return queryset

    def perform_create(self, serializer):
        # Le SERVEUR impose le statut et l'organisateur
        serializer.save(organisateurId=int(self.request.user.id),
                        statut=StatutEvenement.BROUILLON)


class MonEvenementDetailView(generics.RetrieveUpdateDestroyAPIView):
    # Voir, modifier, supprimer SON evenement (403 si ce n'est pas le sien)
    permission_classes = [IsOrganizer, IsOwner]
    queryset = Evenement.objects.select_related('categorie')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EvenementSerializer
        return EvenementWriteSerializer

    def update(self, request, *args, **kwargs):
        evenement = self.get_object()
        if evenement.statut not in STATUTS_MODIFIABLES:
            return reponse_conflit(
                'Modification impossible: en attente ou deja approuve.')
        return super().update(request, *args, **kwargs)


class SoumettreView(APIView):
    # BROUILLON ou REJETEE -> EN_ATTENTE
    permission_classes = [IsOrganizer, IsOwner]

    def post(self, request, pk):
        evenement = get_object_or_404(Evenement, pk=pk)
        self.check_object_permissions(request, evenement)

        if evenement.statut not in STATUTS_MODIFIABLES:
            return reponse_conflit('Cet evenement a deja ete soumis.')
        if evenement.dateLimite < timezone.localdate():
            return Response({'detail': 'La date limite est depassee.'},
                            status=status.HTTP_400_BAD_REQUEST)

        evenement.statut = StatutEvenement.EN_ATTENTE
        evenement.save(update_fields=['statut'])
        return Response(EvenementSerializer(evenement).data)


class ModerationListView(generics.ListAPIView):
    """L'admin liste les événements. Par défaut : ceux en attente."""
    serializer_class = EvenementSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [OrderingFilter]
    ordering = ['dateCreation']

    def get_queryset(self):
        statut = self.request.query_params.get('statut', StatutEvenement.EN_ATTENTE)
        return Evenement.objects.select_related('categorie').filter(statut=statut)


class ModerationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """L'admin voit, modifie ou supprime n'importe quel événement."""
    queryset = Evenement.objects.select_related('categorie')
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EvenementSerializer
        return EvenementWriteSerializer


class _ChangerStatutView(APIView):
    """Base commune à approuver et rejeter. Le "_" au début dit : usage interne."""
    permission_classes = [IsAdminRole]
    nouveau_statut = None  # défini par les classes filles

    def post(self, request, pk):
        evenement = get_object_or_404(Evenement, pk=pk)
        if evenement.statut != StatutEvenement.EN_ATTENTE:
            return reponse_conflit(
                f"Seul un événement EN_ATTENTE peut être traité "
                f"(statut actuel : {evenement.statut})."
            )
        evenement.statut = self.nouveau_statut
        evenement.save(update_fields=['statut'])
        return Response(EvenementSerializer(evenement).data)


class ApprouverView(_ChangerStatutView):
    nouveau_statut = StatutEvenement.APPROUVEE


class RejeterView(_ChangerStatutView):
    nouveau_statut = StatutEvenement.REJETEE    