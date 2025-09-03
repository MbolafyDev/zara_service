from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.http import QueryDict
from django.core.paginator import Paginator
from vente.models import Commande, Vente
from common.models import Pages, Caisse
from django.db.models import F, Q, Sum
from clients.models import Entreprise

class EncaissementValideView(LoginRequiredMixin, ListView):
    login_url = 'login'
    template_name = "encaissement/encaissement_valides.html"
    context_object_name = "ventes"
    paginate_by = 10

    # --- Utilitaires ---
    def _display_mode(self):
        mode = self.request.GET.get("display", "").strip().lower()
        return mode if mode in ("table", "cards") else "table"

    def _extra_querystring(self):
        # Conserver les filtres dans la pagination (sauf 'page')
        params = self.request.GET.copy()
        params.pop("page", None)
        return params.urlencode()

    # --- Queryset filtré ---
    def get_queryset(self):
        qs = (
            Vente.objects.select_related("commande__client", "paiement")
            .filter(commande__statut_vente="Payée")
            .order_by("-date_encaissement", "-id")
        )

        # Filtres
        date_encaissement = (self.request.GET.get("date_encaissement") or "").strip()
        client_id = (self.request.GET.get("client_id") or "").strip()
        paiement_id = (self.request.GET.get("paiement_id") or "").strip()

        if date_encaissement:
            qs = qs.filter(date_encaissement=date_encaissement)

        if client_id:
            qs = qs.filter(commande__client_id=client_id)

        if paiement_id:
            qs = qs.filter(paiement_id=paiement_id)

        return qs

    # --- Contexte + pagination ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["ventes"] = page_obj.object_list

        total = queryset.aggregate(total=Sum("montant"))["total"] or 0
        context["total_encaisse"] = total

        # Sélecteurs
        context["clients"] = Entreprise.objects.order_by("raison_sociale")
        context["paiements"] = Caisse.objects.order_by("nom")

        # Valeurs sélectionnées
        context["date_encaissement"] = self.request.GET.get("date_encaissement", "")
        context["client_id"] = self.request.GET.get("client_id", "")
        context["paiement_id"] = self.request.GET.get("paiement_id", "")

        # Affichage & pagination
        context["display_mode"] = self._display_mode()
        context["extra_querystring"] = self._extra_querystring()

        # Date du jour
        context["today"] = now().date()
        return context

    # --- Rendu partiel si HTMX ---
    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request") == "true":
            # Renvoyer uniquement le wrapper quand HTMX demande un rafraîchissement
            return render(self.request, "encaissement/includes/encaissements_list_wrapper.html", context)
        return super().render_to_response(context, **response_kwargs)


class EncaissementServicesView(LoginRequiredMixin, ListView):
    login_url = 'login'  # redirection si non connecté
    model = Commande
    template_name = "encaissement/encaissement_services.html"
    context_object_name = "commandes"
    paginate_by = 10

    def get_queryset(self):
        queryset = (Commande.objects
                    .select_related("client", "page")
                    .prefetch_related("lignes_commandes__service")
                    .order_by("date_commande"))

        selected_date = self.request.GET.get("date_commande")
        selected_statut_vente = self.request.GET.get("statut_vente") or "En attente"

        # Par défaut : uniquement en attente
        if not self.request.GET:
            queryset = queryset.filter(statut_vente="En attente")
        else:
            if selected_statut_vente:
                queryset = queryset.filter(statut_vente=selected_statut_vente)
            if selected_date:
                queryset = queryset.filter(date_commande=selected_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # total montant
        context["total_montant"] = sum(c.montant_commande for c in queryset)

        # pagination
        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj
        context["commandes"] = page_obj.object_list

        # filtres
        context["selected_date"] = self.request.GET.get("date_commande") or ""
        context["selected_statut_vente"] = self.request.GET.get("statut_vente") or "En attente"

        # querystring supplémentaire
        params = self.request.GET.copy()
        clean_params = QueryDict(mutable=True)
        for key, values in params.lists():
            clean_values = [v for v in values if v.strip()]
            if clean_values and key != "page":
                clean_params.setlist(key, clean_values)
        context["extra_querystring"] = "&" + clean_params.urlencode() if clean_params else ""

        # autres contextes
        context["caisses"] = Caisse.objects.all()
        context["today"] = now().date()
        context["is_admin"] = self.request.user.is_staff

        return context


class EncaissementServiceUnitaireView(LoginRequiredMixin, View):
    login_url = 'login'
    STATUTS_VENTE = ["En attente", "Payée", "Supprimée"]

    def post(self, request, *args, **kwargs):
        commande_id = request.POST.get("commande_id")
        paiement_id = request.POST.get("paiement")
        date_encaissement = parse_date(request.POST.get("date_encaissement")) or now().date()
        reference = (request.POST.get("reference") or "").strip()

        if not commande_id:
            messages.warning(request, "Commande manquante.")
            return redirect("encaissement_services")

        if not paiement_id:
            messages.warning(request, "Veuillez choisir un mode de paiement.")
            return redirect("encaissement_services")

        try:
            with transaction.atomic():
                commande = (Commande.objects
                            .select_for_update()
                            .annotate(a_deja_vente=Exists(
                                Vente.objects.filter(commande_id=OuterRef("pk"))
                            ))
                            .get(pk=commande_id))

                paiement = Caisse.actifs.select_for_update().get(pk=paiement_id)

                if commande.statut_vente not in self.STATUTS_VENTE or commande.statut_vente in ("Payée", "Supprimée"):
                    messages.warning(
                        request,
                        f"La commande {commande.numero_proforma} n'est pas encaisseable (statut : {commande.statut_vente})."
                    )
                    raise transaction.Rollback

                if commande.a_deja_vente:
                    messages.warning(
                        request,
                        f"La commande {commande.numero_proforma} est déjà encaissée."
                    )
                    raise transaction.Rollback

                vente = Vente.objects.create(
                    commande=commande,
                    paiement=paiement,
                    montant=commande.montant_commande,
                    date_encaissement=date_encaissement,
                    reference=reference or None,
                )

                commande.statut_vente = "Payée"
                commande.save(update_fields=["statut_vente"])

        except Commande.DoesNotExist:
            messages.error(request, "Commande introuvable.")
        except Caisse.DoesNotExist:
            messages.error(request, "Caisse invalide ou inactive.")
        except transaction.Rollback:
            pass
        except Exception as e:
            messages.error(request, f"Erreur lors de l'encaissement : {e}")
        else:
            messages.success(
                request,
                f"Commande {commande.numero_proforma} encaissée avec succès. Facture générée : {vente.numero_facture}."
            )

        return redirect("encaissement")

    def get(self, request, *args, **kwargs):
        messages.warning(request, "Méthode non autorisée.")
        return redirect("encaissement")
