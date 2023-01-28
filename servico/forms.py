from django import forms
from servico.models import Servico


class ServicoForms(forms.ModelForm):

    class Meta:
        model = Servico
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ServicoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
        self.fields['usuario'].widget = forms.HiddenInput()

