from django.urls import path
from .views import VenteView,CreerCommandeServiceView, DetailCommandeServiceModalView, SupprimerCommandeServiceView, ModifierCommandeServiceView, DetailCommandeServiceView

urlpatterns = [
    path('', VenteView.as_view(), name="accueil"),
    path('commande/creer/services/',CreerCommandeServiceView.as_view(),name="creer_commande_service"),
    path(
        "commande/<int:commande_id>/",
        DetailCommandeServiceView.as_view(),
        name="detail_commande_service"
    ),
    path(
        "commandes/<int:commande_id>/detail-modal/",
        DetailCommandeServiceModalView.as_view(),
        name="detail_commande_service_modal"
    ),
    path(
        "commandes/<int:commande_id>/modifier/",
        ModifierCommandeServiceView.as_view(),
        name="modifier_commande_service"
    ),
    path(
        "commandes/<int:commande_id>/supprimer/",
        SupprimerCommandeServiceView.as_view(),
        name="supprimer_commande_service"
    ),
]
