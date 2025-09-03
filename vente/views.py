from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.utils.timezone import now
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views import View
from django.core.paginator import Paginator
from services.models import Service
from datetime import date
from .models import Commande, LigneCommande
from common.models import Pages
from clients.models import Entreprise
from urllib.parse import urlencode
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.

class VenteView(LoginRequiredMixin, ListView):
    template_name= "vente/vente.html"
    context_object_name = "commandes"
    paginate_by = 10

    def get_queryset(self):
        qs = (Commande.objects
            .select_related("client", "page")
            .prefetch_related("lignes_commandes__service")
            .order_by("-date_commande"))

        # ---- Lire & nettoyer les filtres ----
        filtre_date_commande = (self.request.GET.get("date_commande") or "").strip()
        filtre_service_id_raw = (self.request.GET.get("service_id") or "").strip()
        filtre_client_id_raw = (self.request.GET.get("client_id") or "").strip()
        filtre_statut = (self.request.GET.get("statut") or "").strip()
        page_id = (self.request.GET.get("page_id") or "").strip()

        # caster au besoin
        def parse_int(s):
            try:
                return int(s)
            except (TypeError, ValueError):
                return None

        filtre_service_id = parse_int(filtre_service_id_raw)
        filtre_client_id = parse_int(filtre_client_id_raw)

        # ---- Appliquer les filtres ----
        if filtre_statut:
            qs = qs.filter(statut_vente=filtre_statut)
        if page_id:
            qs = qs.filter(page_id=page_id)
        if filtre_date_commande:
            qs = qs.filter(date_commande=filtre_date_commande)
        if filtre_client_id:
            qs = qs.filter(client_id=filtre_client_id)
        if filtre_service_id:
            qs = qs.filter(lignes_commandes__service_id=filtre_service_id).distinct()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # récupérer queryset filtré pour calcul du montant total
        commandes_valides = self.get_queryset().exclude(statut_vente__in=["Annulée", "Supprimée"])
        total_montant = sum(c.montant_commande for c in commandes_valides)

        # récupérer filtres
        filtre_date_commande = (self.request.GET.get("date_commande") or "").strip()
        filtre_service_id_raw = (self.request.GET.get("service_id") or "").strip()
        filtre_client_id_raw = (self.request.GET.get("client_id") or "").strip()
        filtre_statut = (self.request.GET.get("statut") or "").strip()
        page_id = (self.request.GET.get("page_id") or "").strip()

        extra_querystring = urlencode({
            "date_commande": filtre_date_commande,
            "service_id": filtre_service_id_raw,
            "client_id": filtre_client_id_raw,
            "statut": filtre_statut,
            "page_id": page_id,
        })

        # ajouter au context
        context.update({
            "filtre_date_commande": filtre_date_commande,
            "filtre_service_id": filtre_service_id_raw,
            "filtre_client_id": filtre_client_id_raw,
            "filtre_statut": filtre_statut,
            "filtre_page": page_id,

            "pages": Pages.actifs.filter(type="SERVICE"),
            "services": Service.objects.all(),
            "clients": Entreprise.objects.all().order_by("raison_sociale"),

            "total_montant": total_montant,
            "extra_querystring": extra_querystring,
        })

        return context

class CreerCommandeServiceView(LoginRequiredMixin, View):
    template_name = "vente/includes/commande.html"

    def get(self, request, *args, **kwargs):
        pages = Pages.actifs.filter(type="SERVICE")
        services = Service.objects.all()  # ⚠️ utilise .objects si tu n’as pas de manager actifs

        services_json = json.dumps(
            list(services.values("id", "nom", "reference", "tarif")),
            cls=DjangoJSONEncoder
        )

        context = {
            "pages": pages,
            "services": services,
            "clients": Entreprise.objects.all().order_by("raison_sociale"),
            "date_du_jour": now().date(),
            "services_json": services_json,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        client_id = request.POST.get("client_id")
        client = get_object_or_404(Entreprise, id=client_id)

        page_id = request.POST.get("page")
        page = get_object_or_404(Pages, id=page_id)

        commande = Commande.objects.create(
            client=client,
            page=page,
            remarque=request.POST.get("remarque"),
            date_commande=request.POST.get("date_commande") or now(),
        )

        service_ids = request.POST.getlist("service")
        tarifs = request.POST.getlist("tarif")
        quantites = request.POST.getlist("quantite")

        for i in range(len(service_ids)):
            service = get_object_or_404(Service, pk=service_ids[i])
            tarif = int(tarifs[i])
            quantite = int(quantites[i])
            LigneCommande.objects.create(
                commande=commande,
                service=service,
                tarif=tarif,
                quantite=quantite,
            )

        return render(request, "vente/vente.html", {"commandes": Commande.objects.all()})

class DetailCommandeServiceView(LoginRequiredMixin, View):
    template_name = "vente/detail_commande_service.html"

    def get(self, request, commande_id):
        # Récupère la commande avec ses relations
        commande = get_object_or_404(
            Commande.objects.select_related("client", "page"),
            id=commande_id
        )
        lignes = commande.lignes_commandes.select_related("service").all()

        context = {
            "commande": commande,
            "lignes": lignes,
            "montant_commande": commande.montant_commande,
        }
        return render(request, self.template_name, context)

    
class DetailCommandeServiceModalView(LoginRequiredMixin, View):
    template_name = "vente/includes/service_detail_modal.html"

    def get(self, request, commande_id, *args, **kwargs):
        commande = get_object_or_404(
            Commande.objects.select_related("client", "page"),
            id=commande_id
        )
        lignes = commande.lignes_commandes.select_related("service").all()

        html = render_to_string(
            self.template_name,
            {
                "commande": commande,
                "lignes": lignes,
                "montant_commande": commande.montant_commande,
            },
            request=request
        )
        return JsonResponse({"html": html})
    
class ModifierCommandeServiceView(LoginRequiredMixin, View):
    template_name = "vente/modifier_commande.html"

    def get(self, request, commande_id, *args, **kwargs):
        commande = get_object_or_404(Commande, id=commande_id)

        if commande.actions_desactivees():
            messages.warning(request, "Modification interdite pour cette commande.")
            return redirect("detail_commande_service", commande_id=commande.id)

        pages = Pages.actifs.filter(type="SERVICE")
        services = Service.objects.all()
        lignes = commande.lignes_commandes.all()

        return render(request, self.template_name, {
            "commande": commande,
            "pages": pages,
            "services": services,
            "lignes": lignes,
        })

    def post(self, request, commande_id, *args, **kwargs):
        commande = get_object_or_404(Commande, id=commande_id)

        if commande.actions_desactivees():
            messages.warning(request, "Modification interdite pour cette commande.")
            return redirect("detail_commande_service", commande_id=commande.id)

        commande.page = get_object_or_404(Pages, id=request.POST.get("page"))
        commande.remarque = request.POST.get("remarque")
        commande.date_commande = request.POST.get("date_commande") or now()
        commande.save()

        # Supprimer les anciennes lignes
        LigneCommande.objects.filter(commande=commande).delete()

        # Recréer les lignes
        service_ids = request.POST.getlist("service")
        tarifs = request.POST.getlist("tarif")
        quantites = request.POST.getlist("quantite")

        for i in range(len(service_ids)):
            service = get_object_or_404(Service, pk=service_ids[i])
            tarif = int(tarifs[i])
            quantite = int(quantites[i])
            LigneCommande.objects.create(
                commande=commande,
                service=service,
                tarif=tarif,
                quantite=quantite
            )

        return redirect("accueil")
    

class SupprimerCommandeServiceView(LoginRequiredMixin, View):
    def post(self, request, commande_id, *args, **kwargs):
        commande = get_object_or_404(Commande, id=commande_id)

        if commande.actions_desactivees():
            messages.warning(request, "Impossible de supprimer cette commande.")
            return redirect('accueil')

        commande.statut_vente = "Supprimée"
        commande.save(update_fields=["statut_vente"])

        # Si ton modèle a bien la méthode soft_delete
        commande.soft_delete(user=request.user)

        messages.success(request, "Commande supprimée avec succès.")
        return redirect('accueil')

    def get(self, request, commande_id, *args, **kwargs):
        # On évite les suppressions via GET → redirection
        return redirect('accueil')