from django.urls import path
from .views import EncaissementServicesView, EncaissementServiceUnitaireView, EncaissementValideView

urlpatterns = [
    path("", EncaissementValideView.as_view(), name="encaissement"),
    path('non-valides', EncaissementServicesView.as_view(), name="encaissement_non_valides"),
    path("encaissement/unitaire/", EncaissementServiceUnitaireView.as_view(), name="encaissement_service_unitaire"),
     path("encaissements/valides/partial/", EncaissementValideView.as_view(), name="encaissement_valides_partial"),
]
