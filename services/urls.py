# urls.py
from django.urls import path
from .views import AccueilView, ServiceCreateView

urlpatterns = [
    path('', AccueilView.as_view(), name='services'),
    path('services/ajout/', ServiceCreateView.as_view(), name='create_services'),
]
