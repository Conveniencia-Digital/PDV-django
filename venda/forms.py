from django import forms
from django.forms import inlineformset_factory, NumberInput

from venda.models import Vendas, ItemsVenda
from produto.models import Produto
from cliente.models import Cliente
from colaborador.models import Colaborador



class VendasForm(forms.ModelForm):
    required_css_class = 'required'
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), empty_label='Selecione o cliente')
    vendedor = forms.ModelChoiceField(queryset=Colaborador.objects.all(), empty_label='Selecione o vendedor')

    class Meta:
        model = Vendas
        fields = ('cliente', 'vendedor', 'desconto', 'observacao', 'status', 'forma_pagamento')

    def __init__(self, *args, **kwargs):
        super(VendasForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['status'].label = ''
        self.fields['status'].widget = forms.HiddenInput()


class ItemsVendaForm(forms.ModelForm):
    required_css_class = 'required'
    id = forms.IntegerField()
    produto = forms.ModelChoiceField(queryset=Produto.objects.all(), empty_label='Selecione o produto')

    class Meta:
        model = ItemsVenda
        fields = ('vendas', 'id', 'produto', 'quantidade', 'preco')

        widgets = {
            'quantidade': NumberInput(attrs={'placeholder': 'Quantidade'}),
            'preco': NumberInput(attrs={'placeholder': 'Preco do produto'})
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


VendasItemsFormset = inlineformset_factory(
    Vendas,
    ItemsVenda,
    form=ItemsVendaForm,
    extra=0,
    can_delete=False,
    min_num=1,
    validate_min=True
)
                                           
                                           
                                           
