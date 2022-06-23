from django.forms import ModelForm, TextInput
from produto.models import Produto


class ProdutoForms(ModelForm):
    class Meta:
        model = Produto
        fields = '__all__'

        widgets = {
            'nome': TextInput(attrs={'placeholder': 'produto'})

        }


