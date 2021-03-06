from django import forms
from django.forms import TextInput
from produto.models import Produto


class ProdutoForms(forms.ModelForm):
    class Meta:
        model = Produto
        fields = '__all__'

        widgets = {
            'nome': TextInput(attrs={'placeholder': 'produto'})

        }

    def __init__(self, *args, **kwargs):
        super(ProdutoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
