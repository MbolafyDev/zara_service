# views.py
from django.shortcuts import render
from django.views.generic import CreateView, ListView
from .models import Service
from django.http import QueryDict
from .forms import ServiceForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict

class AccueilView(LoginRequiredMixin, ListView):
    model = Service
    template_name = "services/services.html"
    context_object_name = "services"
    paginate_by = 30

    def _display_mode(self):
        mode = (self.request.GET.get("display") or "auto").strip().lower()
        return mode if mode in ("auto", "table", "cards") else "auto"

    def get_queryset(self):
        qs = Service.objects.all()
        query = (self.request.GET.get('q') or '').strip()
        tarif_min = (self.request.GET.get('tarif_min') or '').strip()
        tarif_max = (self.request.GET.get('tarif_max') or '').strip()

        if query:
            qs = qs.filter(nom__icontains=query)

        if tarif_min:
            try:
                qs = qs.filter(tarif__gte=int(tarif_min))   # <- corrige tarif__get -> tarif__gte
            except ValueError:
                pass

        if tarif_max:
            try:
                qs = qs.filter(tarif__lte=int(tarif_max))
            except ValueError:
                pass
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Nettoyer les GET et préserver display pour la pagination
        params = self.request.GET.copy()
        clean = QueryDict(mutable=True)
        for k, vals in params.lists():
            vals = [v for v in vals if (v or '').strip()]
            if vals and k != "page":
                clean.setlist(k, vals)

        display_mode = self._display_mode()
        if clean.get('display') != display_mode:
            clean = clean.copy()
            clean['display'] = display_mode

        extra_querystring = f"&{clean.urlencode()}" if clean else ""

        ctx.update({
            "query": self.request.GET.get("q", ""),
            "tarif_min": self.request.GET.get("tarif_min"),
            "tarif_max": self.request.GET.get("tarif_max"),
            "display_mode": display_mode,               # <- clé pour ton template
            "extra_querystring": extra_querystring,     # <- pour la pagination
        })
        return ctx


class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    # Si tu crées via le modal sur la même page, on peut laisser un petit template partiel,
    # mais on peut aussi ne pas rendre du tout (on redirige via success_url).
    template_name = "services/services.html"
    success_url = reverse_lazy("services")
