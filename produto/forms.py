from django import forms
from django.forms import TextInput, NumberInput
from produto.models import Produto
from fornecedor.models import Fornecedores


class ProdutoForms(forms.ModelForm):

    class Meta:
        model = Produto
        fields = '__all__'

        widgets = {
            'observacao': forms.TextInput(),
            
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProdutoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        
        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['valor_entrada'].widget = forms.HiddenInput()
        self.fields['data_vencimento'].widget = forms.HiddenInput()
        self.fields['qtd_parcela'].widget = forms.HiddenInput()
        self.fields['fornecedor'].queryset = Fornecedores.objects.filter(usuario=user)

