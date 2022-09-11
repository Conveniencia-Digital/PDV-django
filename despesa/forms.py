from django import forms
from despesa.models import Despesa


class DespesaForms(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(DespesaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
