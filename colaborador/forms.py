from django import forms
from colaborador.models import Colaborador


class ColaboradorForms(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = '__all__'

        widgets = {
            'data_nascimento' :forms.NumberInput(attrs={'type': 'date'}),
            'data_pagamento': forms.NumberInput(attrs={'type': 'date'}),
            
        }

    def __init__(self, *args, **kwargs):
        super(ColaboradorForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()
