from django.db import models

# Create your models here.

class Categorie(models.Model):
    # "id" n'est pas écrit : Django le crée tout seul
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class StatutEvenement(models.TextChoices):
    # (valeur enregistrée, texte affiché)
    BROUILLON = 'BROUILLON', 'Brouillon'
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    APPROUVEE = 'APPROUVEE', 'Approuvée'
    REJETEE = 'REJETEE', 'Rejetée'


class Evenement(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    image = models.CharField(max_length=255, blank=True)
    dateCreation = models.DateField(auto_now_add=True)
    dateLimite = models.DateField()
    statut = models.CharField(
        max_length=20,
        choices=StatutEvenement.choices,
        default=StatutEvenement.BROUILLON,
    )
    # Numéro de l'organisateur : il vit dans un AUTRE service,
    # donc on garde juste son numéro, pas un lien direct.
    organisateurId = models.PositiveIntegerField()
    # Un événement a UNE catégorie ; une catégorie a plusieurs événements.
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name='evenements',
    )

    def __str__(self):
        return self.titre