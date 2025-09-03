from django.urls import path
from .views import FacturationCommandesServicesView, FacturationCommandesServicesPartialView, VoirFacturesServicesView, ImprimerFacturesServicesView, TelechargerFactureServicePDFView

urlpatterns = [
    path('', FacturationCommandesServicesView.as_view(), name="facturation"),
    path(
        "facturation/partial/",
        FacturationCommandesServicesPartialView.as_view(),
        name="facturation_commandes_services_partial"
    ),
    path(
        'facturation/voir_factures_services/',
        VoirFacturesServicesView.as_view(),
        name="voir_factures_services"
    ),
    path(
        'facturation/imprimer_factures_services/',
        ImprimerFacturesServicesView.as_view(),
        name='imprimer_factures_services'
    ),
    path(
        "imprimer/telecharger_facture_service_pdf/",
        TelechargerFactureServicePDFView.as_view(),
        name="telecharger_facture_service_pdf"
    ),
]
