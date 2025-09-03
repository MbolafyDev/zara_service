from django.db import models
from django.utils import timezone

# Create your models here.
class ActifsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(est_actif=True)

class Entreprise(models.Model):
    raison_sociale = models.CharField(max_length=255)
    date_debut = models.DateField(default=timezone.now, null=True, blank=True)
    page_facebook = models.CharField(max_length=255, blank=True, null=True)
    lien_page = models.URLField(blank=True, null=True)
    activite_produits = models.CharField(max_length=255, blank=True, null=True)
    personne_de_contact = models.CharField(max_length=255, blank=True, null=True)
    lien_profil = models.URLField(blank=True, null=True)
    nif = models.CharField(max_length=50, blank=True, null=True)
    stat = models.CharField(max_length=50, blank=True, null=True)
    rcs = models.CharField(max_length=50, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fokontany = models.CharField(max_length=255, blank=True, null=True)
    commune = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    cin_numero = models.CharField(max_length=50, blank=True, null=True)
    date_cin = models.DateField(blank=True, null=True)
    lieu_cin = models.CharField(max_length=255, blank=True, null=True)
    remarque = models.TextField(blank=True, null=True)

    objects = models.Manager()   # manager par défaut
    actifs = ActifsManager()

    def __str__(self):
        return self.raison_sociale
    