# services/urls.py
from django.urls import path
from .views import (
    AccueilView,
    ServiceCreateView,
    ServiceUpdateView,
    ServiceDeleteView,
    ServiceDetailModalView,
)

urlpatterns = [
    path('', AccueilView.as_view(), name='services'),

    path('services/<int:pk>/detail-modal/', ServiceDetailModalView.as_view(), name='service_detail_modal'),
    path('services/ajout/', ServiceCreateView.as_view(), name='create_services'),
    path('services/<int:pk>/edit/', ServiceUpdateView.as_view(), name='service_edit'),     # ← slash final
    path('services/<int:pk>/delete/', ServiceDeleteView.as_view(), name='service_delete'), # ← slash final
]
