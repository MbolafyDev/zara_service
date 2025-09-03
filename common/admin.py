from django.contrib import admin
from .models import Pages, Caisse

# Register your models here.


class PageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact')
    search_fields = ('nom', 'contact')

admin.site.register(Pages, PageAdmin)
admin.site.register(Caisse)
