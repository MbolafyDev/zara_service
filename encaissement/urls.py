from django.urls import path
from .views import EncaissementServicesView, EncaissementServiceUnitaireView

urlpatterns = [
    path('', EncaissementServicesView.as_view(), name="encaissement"),
    path("encaissement/unitaire/", EncaissementServiceUnitaireView.as_view(), name="encaissement_service_unitaire"),
]
