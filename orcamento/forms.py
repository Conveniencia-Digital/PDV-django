from django import forms
from orcamento.models import Orcamento


class OrcamentoForms(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(OrcamentoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
