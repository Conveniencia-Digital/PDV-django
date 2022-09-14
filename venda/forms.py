from django import forms
from django.forms import inlineformset_factory, TextInput

from venda.models import Vendas, ItemsVenda


class VendasForm(forms.ModelForm):
    nf = forms.IntegerField()

    class Meta:
        model = Vendas
        fields = ('nf', )


class ItemsVendaForm(forms.ModelForm):
    required_css_class = 'required'
    id = forms.IntegerField()

    class Meta:
        model = ItemsVenda
        fields = ('vendas', 'id', 'produto', 'quantidade', 'preco')

        widgets = {
            'quantidade': TextInput(attrs={'placeholder': 'Quantidade'}),
            'preco': TextInput(attrs={'placeholder': 'Preco do produto'})
        }

    def __init__(self, *args, **kwargs):
        super(ItemsVendaForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['id'].label = ''
        self.fields['id'].widget = forms.HiddenInput()

        self.fields['vendas'].label = ''
        self.fields['vendas'].widget = forms.HiddenInput()

        self.fields['preco'].widget.attrs['step'] = 0.01


VendasItemsFormset = inlineformset_factory(Vendas,
                                           ItemsVenda,
                                           form=ItemsVendaForm,
                                           extra=0,
                                           can_delete=False,
                                           min_num=1,
                                           validate_min=True)
