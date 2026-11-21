
from django.utils import timezone
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

class EvenementWriteSerializer(serializers.ModelSerializer):
    # ECRITURE: on envoie seulement l'id de la categorie

    class Meta:
        model = Evenement
        fields = ['id', 'titre', 'description', 'image', 'dateCreation',
                  'dateLimite', 'statut', 'organisateurId', 'categorie']
        # Le client NE PEUT PAS choisir ces champs
        read_only_fields = ['id', 'dateCreation', 'statut', 'organisateurId']

    def validate_dateLimite(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError(
                'La date limite ne peut pas etre dans le passe.')
        return value

    def to_representation(self, instance):
        # Apres creation ou modification, on repond au format lecture
        return EvenementSerializer(instance, context=self.context).data        