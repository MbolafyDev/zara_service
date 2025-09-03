from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.views import View
from django.utils.dateparse import parse_date
from django.core.validators import URLValidator, validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction, IntegrityError
from .models import Entreprise

# Liste des clients - accessible uniquement si connecté
class ClientView(LoginRequiredMixin, ListView):  # Nom de l’URL de login
    model = Entreprise
    template_name = "clients/clients_list.html"
    context_object_name = 'clients'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['display_mode'] = self.request.GET.get('display', 'table')
        context['extra_querystring'] = self.request.GET.urlencode()
        return context

# Création d’entreprise
class EntrepriseCreateView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        data = {k: request.POST.get(k) or None for k in [
            "raison_sociale", "date_debut", "page_facebook", "lien_page",
            "activite_produits", "personne_de_contact", "lien_profil",
            "nif", "stat", "rcs", "adresse", "telephone", "email",
            "fokontany", "commune", "region", "cin_numero", "date_cin",
            "lieu_cin", "remarque"
        ]}
        data["date_debut"] = parse_date(data["date_debut"]) if data["date_debut"] else None
        data["date_cin"]   = parse_date(data["date_cin"])   if data["date_cin"]   else None

        errors = []
        if not data["raison_sociale"]:
            errors.append("La raison sociale est obligatoire.")

        url_validator = URLValidator()
        for field in ["lien_page", "lien_profil"]:
            if data[field]:
                try:
                    url_validator(data[field])
                except ValidationError:
                    errors.append(f"L’URL fournie pour « {field.replace('_', ' ')} » est invalide.")

        if data["email"]:
            try:
                validate_email(data["email"])
            except ValidationError:
                errors.append("L’email fourni est invalide.")

        if errors:
            for e in errors:
                messages.warning(request, e)
            return redirect(f"{request.META.get('HTTP_REFERER','/')}?open=addEntrepriseModal")

        try:
            with transaction.atomic():
                Entreprise.objects.create(**data)
                messages.success(request, "Entreprise ajoutée avec succès.")
        except IntegrityError as e:
            messages.warning(request, f"Erreur lors de l’enregistrement : {e}")

        return redirect("listes-clients")


# Mise à jour d’entreprise
class EntrepriseUpdateView(LoginRequiredMixin, View):

    def post(self, request, entreprise_id, *args, **kwargs):
        entreprise = get_object_or_404(Entreprise, id=entreprise_id)
        data = {k: request.POST.get(k) or None for k in [
            "raison_sociale", "date_debut", "page_facebook", "lien_page",
            "activite_produits", "personne_de_contact", "lien_profil",
            "nif", "stat", "rcs", "adresse", "telephone", "email",
            "fokontany", "commune", "region", "cin_numero", "date_cin",
            "lieu_cin", "remarque"
        ]}
        data["date_debut"] = parse_date(data["date_debut"]) if data["date_debut"] else None
        data["date_cin"]   = parse_date(data["date_cin"])   if data["date_cin"]   else None

        errors = []
        if not data["raison_sociale"]:
            errors.append("La raison sociale est obligatoire.")

        url_validator = URLValidator()
        for field in ["lien_page", "lien_profil"]:
            if data[field]:
                try:
                    url_validator(data[field])
                except ValidationError:
                    errors.append(f"L’URL fournie pour « {field.replace('_', ' ')} » est invalide.")

        if data["email"]:
            try:
                validate_email(data["email"])
            except ValidationError:
                errors.append("L’email fourni est invalide.")

        if errors:
            for e in errors:
                messages.warning(request, e)
            return redirect(f"{request.META.get('HTTP_REFERER','/')}?open=editModal{entreprise.id}")

        for field, val in data.items():
            setattr(entreprise, field, val)

        try:
            with transaction.atomic():
                entreprise.save()
                messages.success(request, "Entreprise mise à jour avec succès.")
        except IntegrityError as e:
            messages.warning(request, f"Erreur lors de la mise à jour : {e}")

        return redirect("listes-clients")


# Suppression d’entreprise
class EntrepriseDeleteView(LoginRequiredMixin, View):
    def post(self, request, entreprise_id, *args, **kwargs):
        entreprise = get_object_or_404(Entreprise, id=entreprise_id)

        if hasattr(entreprise, "soft_delete"):
            entreprise.soft_delete(user=request.user)
        else:
            entreprise.delete()

        return redirect("listes-clients")
