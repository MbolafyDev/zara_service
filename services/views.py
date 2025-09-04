# services/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, ListView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import QueryDict, JsonResponse
from django.template.loader import render_to_string

from common.utils import is_admin
from .models import Service
from .forms import ServiceForm


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Action réservée à l’administrateur.")
        return redirect("services")


class AccueilView(LoginRequiredMixin, ListView):
    model = Service
    template_name = "services/services.html"
    context_object_name = "services"
    paginate_by = 30

    def _display_mode(self):
        mode = (self.request.GET.get("display") or "auto").strip().lower()
        return mode if mode in ("auto", "table", "cards") else "auto"

    def get_queryset(self):
        qs = Service.objects.all().order_by("id")
        q = (self.request.GET.get('q') or '').strip()
        tmin = (self.request.GET.get('tarif_min') or '').strip()
        tmax = (self.request.GET.get('tarif_max') or '').strip()
        if q:
            qs = qs.filter(nom__icontains=q)
        if tmin:
            try:
                qs = qs.filter(tarif__gte=int(tmin))
            except ValueError:
                pass
        if tmax:
            try:
                qs = qs.filter(tarif__lte=int(tmax))
            except ValueError:
                pass
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
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
        ctx.update({
            "query": self.request.GET.get("q", ""),
            "tarif_min": self.request.GET.get("tarif_min"),
            "tarif_max": self.request.GET.get("tarif_max"),
            "display_mode": display_mode,
            "extra_querystring": f"&{clean.urlencode()}" if clean else "",
            "is_admin": is_admin(self.request.user),
        })
        return ctx


class ServiceDetailModalView(LoginRequiredMixin, View):
    template_name = "services/includes/service_detail_modal.html"

    def get(self, request, pk, *args, **kwargs):
        service = get_object_or_404(Service, pk=pk)
        html = render_to_string(self.template_name, {"service": service}, request=request)
        return JsonResponse({"html": html})


class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "services/services.html"
    success_url = reverse_lazy("services")

    def form_valid(self, form):
        messages.success(self.request, "Service créé avec succès.")
        return super().form_valid(form)


# --- ÉDITION DEPUIS MODAL: gérer POST explicitement (fiable) ---
class ServiceUpdateView(LoginRequiredMixin, AdminRequiredMixin, View):

    def post(self, request, pk, *args, **kwargs):
        service = get_object_or_404(Service, pk=pk)
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service modifié avec succès.")
        else:
            # On peut afficher les erreurs dans un message condensé
            err_txt = "; ".join(
                f"{field}: {', '.join(map(str, errs))}"
                for field, errs in form.errors.items()
            )
            messages.error(request, f"Échec de la modification: {err_txt}")
        return redirect("services")

    # Optionnel: si quelqu’un ouvre l’URL en GET, on affiche un fallback
    def get(self, request, pk, *args, **kwargs):
        service = get_object_or_404(Service, pk=pk)
        form = ServiceForm(instance=service)
        return render(request, "services/includes/edit_modal.html", {"form": form, "service": service})


# --- SUPPRESSION DEPUIS MODAL: POST explicite ---
class ServiceDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):

    def post(self, request, pk, *args, **kwargs):
        service = get_object_or_404(Service, pk=pk)
        service.delete()
        messages.success(request, "Service supprimé avec succès.")
        return redirect("services")
