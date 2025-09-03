from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
class ActifsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(est_actif=True)

class Service(models.Model):
    nom = models.CharField("Nom de l'article", max_length=100)
    reference = models.CharField("Référence", max_length=50, unique=True)
    tarif = models.PositiveIntegerField("Tarif (Ar)")

    objects = models.Manager()   # manager par défaut
    actifs = ActifsManager()

    def __str__(self):
        return self.nom