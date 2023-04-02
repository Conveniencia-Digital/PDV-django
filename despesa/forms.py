from django import forms
from despesa.models import Despesa, CategoriaDespesa
from fornecedor.models import Fornecedores

class CategoriaDespesaForms(forms.ModelForm):
    class Meta:
        model = CategoriaDespesa
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CategoriaDespesaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['usuario'].widget = forms.HiddenInput()


class DespesaForms(forms.ModelForm):
    
    class Meta:
        model = Despesa
        fields = '__all__'
        widgets = {
            'observacao': forms.TextInput(),
        }


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(DespesaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
        self.fields['usuario'].widget = forms.HiddenInput()
        

        self.fields['fornecedor'].queryset = Fornecedores.objects.filter(usuario=user)
        self.fields['categoria_despesa'].queryset = CategoriaDespesa.objects.filter(usuario=user)


