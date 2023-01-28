from django import forms
from financeiro.models import ContasAReceber


class ContasAReceberForms(forms.ModelForm):
    class Meta:
        model = ContasAReceber
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ContasAReceberForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()
