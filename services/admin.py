from django.contrib import admin
from .models import Service
# Register your models here.
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'reference', 'tarif')
    search_fields = ('nom', 'tarif')
admin.site.register(Service, ServiceAdmin)
