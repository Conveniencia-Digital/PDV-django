from django import forms
from django.forms import TextInput, NumberInput
from produto.models import Produto


class ProdutoForms(forms.ModelForm):
    
    class Meta:
        model = Produto
        fields = '__all__'

        widgets = {
            'nome_produto': TextInput(attrs={'placeholder': 'Digite o nome do produto'}),
            'quantidade': NumberInput(attrs={'placeholder': 'Quantidade'})
            
        }

    def __init__(self, *args, **kwargs):
        super(ProdutoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
