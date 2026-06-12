from django import forms
from django.forms import inlineformset_factory, NumberInput
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal

from venda.models import Vendas, ItemsVenda
from produto.models import Produto
from cliente.models import Cliente
from colaborador.models import Colaborador
from financeiro.form_fields import configure_card_fee_fields



class VendasForm(forms.ModelForm):
    required_css_class = 'required'
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), empty_label='Selecione o cliente')
    vendedor = forms.ModelChoiceField(queryset=Colaborador.objects.all(), empty_label='Selecione o vendedor')

    class Meta:
        model = Vendas
        fields = '__all__'
        widgets = {
            'observacao': forms.TextInput()

         }
    def clean(self):
        cleaned_data = super().clean()
        desconto = cleaned_data.get('desconto') or Decimal('0.00')

        total_bruto = Decimal('0.00')

        # percorre os dados POST do formset
        i = 0
        while True:
            preco_key = f'items-{i}-preco'
            qtd_key = f'items-{i}-quantidade'

            if preco_key not in self.data:
                break

            preco = Decimal(self.data.get(preco_key) or '0')
            qtd = int(self.data.get(qtd_key) or 0)

            total_bruto += preco * qtd
            i += 1

        if desconto > total_bruto:
            raise ValidationError({
                'desconto': 'O desconto não pode ser maior que o total bruto da venda.'
            })

        return cleaned_data

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(VendasForm, self).__init__(*args, **kwargs)      
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['data_vencimento'].widget = forms.HiddenInput()
        self.fields['qtd_parcela'].widget = forms.HiddenInput()
        self.fields['valor_entrada'].widget = forms.HiddenInput()
        self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user)
        self.fields['vendedor'].queryset = Colaborador.objects.filter(usuario=user)
        configure_card_fee_fields(self, user)


class ItemsVendaForm(forms.ModelForm):
    required_css_class = 'required'
    id = forms.IntegerField(required=False)
    #produto = forms.ModelChoiceField(queryset=Produto.objects.all(), empty_label='Selecione o produto')

    class Meta:
        model = ItemsVenda
        fields = ('vendas', 'id', 'produto', 'quantidade', 'preco')

        widgets = {
            'quantidade': NumberInput(attrs={'placeholder': 'Quantidade'}),
            'preco': NumberInput(attrs={'placeholder': 'Preco do produto', "readonly": "readonly"})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ItemsVendaForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['id'].label = ''
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['vendas'].label = ''
        self.fields['vendas'].widget = forms.HiddenInput()
        self.fields['preco'].widget.attrs['step'] = 0.01

        produtos = Produto.objects.filter(usuario=user)
        if self.instance and self.instance.pk and self.instance.produto_id:
            produtos = produtos.filter(Q(quantidade__gt=0) | Q(pk=self.instance.produto_id))
        else:
            produtos = produtos.filter(quantidade__gt=0)
        self.fields['produto'].queryset = produtos


VendasItemsFormset = inlineformset_factory(
    Vendas,
    ItemsVenda,
    form=ItemsVendaForm,
    extra=0,
    can_delete=False,
    min_num=1,
    validate_min=True
)
                                           
                                           
                                           
