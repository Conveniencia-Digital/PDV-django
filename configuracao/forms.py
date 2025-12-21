# forms.py
from django import forms
from .models import TaxaPagamento

class TaxaPagamentoForm(forms.ModelForm):
    class Meta:
        model = TaxaPagamento
        exclude = ("user",)
        widgets = {
            field: forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }) for field in model._meta.fields
            if field.name not in ["id", "user"]
        }
