from django.urls import path
from .views import ClientView, EntrepriseCreateView, EntrepriseUpdateView, EntrepriseDeleteView

urlpatterns = [
    path('', ClientView.as_view(), name="listes-clients"),
    path("client/create/", EntrepriseCreateView.as_view(), name="entreprise_create"),
    path(
        "client/<int:entreprise_id>/update/",
        EntrepriseUpdateView.as_view(),
        name="entreprise_update"
    ),
    path("client/<int:entreprise_id>/delete/", EntrepriseDeleteView.as_view(), name="entreprise_delete"),
]
