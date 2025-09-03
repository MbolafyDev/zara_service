from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from django.http import QueryDict
from django.utils.dateparse import parse_date
from vente.models import Commande, Caisse
from encaissement.views import EncaissementServiceUnitaireView
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from common.pdf import render_html_to_pdf

# Create your views here.
class FacturationCommandesServicesView(LoginRequiredMixin, View):
    STATUTS_VENTE = ["En attente", "Payée", "Supprimée"]

    def get(self, request, *args, **kwargs):
        params = request.GET.copy()
        selected_date = params.get("date_commande")
        selected_statut = params.get("statut_vente")
        type_facture = params.get("type_facture")  # peut être None; l'UI mettra la valeur par défaut

        # Premier chargement : afficher tous les statuts
        if not request.GET:
            selected_statut = ""

        commandes = Commande.objects.all().order_by('-date_commande', '-numero_proforma')

        # Filtres
        if selected_date:
            parsed_date = parse_date(selected_date)
            if parsed_date:
                commandes = commandes.filter(date_commande=parsed_date)

        if selected_statut and selected_statut in self.STATUTS_VENTE:
            commandes = commandes.filter(statut_vente=selected_statut)

        # Pagination
        paginator = Paginator(commandes, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Conserver les filtres dans la pagination (hors 'page')
        clean_params = QueryDict(mutable=True)
        for key, values in params.lists():
            if key != 'page':
                clean_values = [v for v in values if v.strip() or v == '']
                clean_params.setlist(key, clean_values)
        extra_querystring = '&' + clean_params.urlencode() if clean_params else ''

        context = {
            "commandes": page_obj.object_list,
            "page_obj": page_obj,
            "selected_date": selected_date or "",
            "selected_statut": selected_statut or "",
            "extra_querystring": extra_querystring,
            "statuts_vente": self.STATUTS_VENTE,
            "type_facture": type_facture,
        }
        return render(request, "facturation/facturation.html", context)


def ma_vue(request):
    # exemple : instancier la classe et appeler post
    view = EncaissementServiceUnitaireView()
    return view.post(request)


def _default_type_for_commande(commande):
    return "FACTURE" if commande.statut_vente == "Payée" else "FACTURE PROFORMA"


class FacturationCommandesServicesPartialView(LoginRequiredMixin, View):
    """
    Partial pour recharger uniquement le tableau (HTMX/Ajax)
    """
    def get(self, request, *args, **kwargs):
        from .views import facturation_commandes_services  # si nécessaire d'appeler la fonction originale
        response = facturation_commandes_services(request)
        response.template_name = 'facturation/includes/facturation_services_table.html'
        return response
    

@method_decorator([require_http_methods(["POST"])], name="dispatch")
class VoirFacturesServicesView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        commande_id = request.POST.get("commande_id")
        if not commande_id:
            messages.error(request, "Veuillez sélectionner une commande.")
            return redirect('facturation_commandes_services')

        commande = get_object_or_404(Commande, id=commande_id)
        requested_type = request.POST.get("type_facture")
        effective_type = requested_type or _default_type_for_commande(commande)

        # FACTURE interdit si non Payée
        if effective_type == "FACTURE" and commande.statut_vente != "Payée":
            messages.error(request, "Type FACTURE non autorisé : la commande sélectionnée n'est pas Payée.")
            return redirect('facturation_commandes_services')

        caisses = Caisse.objects.all()

        return render(request, "facturation/facture.html", {
            "commandes": Commande.objects.filter(id=commande.id),
            "impression": False,
            "type_facture": effective_type,
            "caisses": caisses,
        })
    

class ImprimerFacturesServicesView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        commande_id = request.POST.get('commande_id')
        if not commande_id:
            messages.error(request, "Veuillez sélectionner une commande.")
            return redirect('facturation')

        commande = get_object_or_404(Commande, id=commande_id)
        requested_type = request.POST.get("type_facture")
        effective_type = requested_type or _default_type_for_commande(commande)

        if effective_type == "FACTURE" and commande.statut_vente != "Payée":
            messages.error(request, "Type FACTURE non autorisé : la commande sélectionnée n'est pas Payée.")
            return redirect('facturation')

        caisses = Caisse.objects.all()

        return render(request, 'facturation/facture.html', {
            'commandes': Commande.objects.filter(id=commande.id),
            'impression': True,
            'type_facture': effective_type,
            'caisses': caisses,  
        })

    def get(self, request, *args, **kwargs):
        # Empêche l'accès via GET
        return redirect('facturation')
    

class TelechargerFactureServicePDFView(LoginRequiredMixin, View):
    """
    Génère un PDF de la facture/proforma pour la commande sélectionnée.
    """

    def post(self, request, *args, **kwargs):
        commande_id = request.POST.get("commande_id")
        if not commande_id:
            messages.error(request, "Veuillez sélectionner une commande.")
            return redirect('facturation_commandes_services')

        commande = get_object_or_404(Commande, id=commande_id)

        # Type demandé ou défaut (FACTURE si Payée sinon PROFORMA)
        requested_type = request.POST.get("type_facture")
        effective_type = requested_type or ("FACTURE" if commande.statut_vente == "Payée" else "FACTURE PROFORMA")

        # FACTURE interdit si non Payée
        if effective_type == "FACTURE" and commande.statut_vente != "Payée":
            messages.error(request, "Type FACTURE non autorisé : la commande sélectionnée n'est pas Payée.")
            return redirect('facturation_commandes_services')

        caisses = Caisse.objects.all()

        context = {
            "commandes": Commande.objects.filter(id=commande.id),
            "impression": False,  # inutile ici, on rend en PDF
            "type_facture": effective_type,
            "caisses": caisses,
        }

        filename = f"{effective_type}_{commande.numero_proforma or commande.id}.pdf"
        return render_html_to_pdf("facturation/facture.html", context, request, filename)