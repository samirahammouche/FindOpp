from rest_framework import serializers
from .models import Categorie, Evenement


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom']


class EvenementSerializer(serializers.ModelSerializer):
    # Affiche la catégorie complète (id + nom) et pas seulement son numéro
    categorie = CategorieSerializer(read_only=True)

    class Meta:
        model = Evenement
        fields = ['id', 'titre', 'description', 'image', 'dateCreation',
                  'dateLimite', 'statut', 'organisateurId', 'categorie']