from django.contrib import admin
from .models import Entreprise
# Register your models here.

class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('raison_sociale', 'email', 'telephone', 'commune')
    search_fields = ('raison_sociale', 'email', 'telephone')
admin.site.register(Entreprise, EntrepriseAdmin)
