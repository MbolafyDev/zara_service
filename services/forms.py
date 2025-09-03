from django import forms
from .models import Service

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['nom', 'reference', 'tarif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'tarif': forms.NumberInput(attrs={'class': 'form-control'}),
        }