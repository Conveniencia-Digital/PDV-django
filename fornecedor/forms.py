from django import forms
from fornecedor.models import Fornecedores


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedores
        fields = '__all__'

       

    def __init__(self, *args, **kwargs):
        super(FornecedorForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()

