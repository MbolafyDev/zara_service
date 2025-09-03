from django.shortcuts import render
from django.views.generic import CreateView, ListView
from .models import Service
from django.http import QueryDict
from .forms import ServiceForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class AccueilView(LoginRequiredMixin, ListView):
    model = Service
    template_name= "services/services.html"
    context_object_name = "services"
    paginate_by = 30

    def get_queryset(self):
        # applique les filtres à la liste des services
        queryset = Service.objects.all()
        query = self.request.GET.get('q', '')
        tarif_min = self.request.GET.get('tarif_min')
        tarif_max = self.request.GET.get('tarif_max')

        if query:
            queryset = queryset.filter(nom__icontains=query)
        
        if tarif_min:
            try:
                querysert = queryset.filter(tarif__get=int(tarif_min))
            except ValueError:
                pass
        
        if tarif_max:
            try:
                queryset = queryset.filter(tarif__lte=int(tarif_max))
            except ValueError:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        # Ajoute les paramètre supplémentaires au contexte

        context =  super().get_context_data(**kwargs)

        #copie et nettoie les paramètres GET (utile pour pagination + filtres)
        params = self.request.GET.copy()
        clean_params = QueryDict(mutable=True)
        for key, values in params.lists():
            clean_values = [v for v in values if v.strip()]
            if clean_values and key != 'page':
                clean_params.setlist(key, clean_values)

        extra_querystring = '&' + clean_params.urlencode() if clean_params else ''

        # Ajouter dans le contexte
        context['query'] = self.request.GET.get('q', '')
        context['tarif_min'] = self.request.GET.get('tarif_min')
        context['tarif_max'] = self.request.GET.get('tarif_max')
        context['extra_querystring'] = extra_querystring

        return context
    
# Ajouter un services
class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "vente/vente.html"
    success_url = reverse_lazy("services")