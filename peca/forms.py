from decimal import Decimal

from django import forms
from peca.models import Pecas
from fornecedor.models import Fornecedores
from erp.pricing import (
    calculate_profit_margin,
    calculate_sale_price_from_margin,
    decimals_are_close,
)


class PecasForms(forms.ModelForm):
    pricing_last_edited = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Pecas
        fields = '__all__'

        widgets = {
            'observacao': forms.TextInput(),
            'preco_peca': forms.NumberInput(attrs={'step': '0.01'}),
            'preco_de_custo': forms.NumberInput(attrs={'step': '0.01'}),
            'margem_de_lucro': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '99.99'}),
            'valor_entrada': forms.NumberInput(attrs={'step': '0.01'}),
            
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PecasForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['usuario'].required = False
        self.fields['preco_peca'].required = False
        self.fields['margem_de_lucro'].required = False
        
        self.fields['data_vencimento'].widget = forms.HiddenInput()
        self.fields['qtd_parcela'].widget = forms.HiddenInput()
        self.fields['valor_entrada'].widget = forms.HiddenInput()

        self.fields['fornecedor'].queryset = Fornecedores.objects.filter(usuario=user)

    def clean(self):
        cleaned_data = super().clean()
        usuario = cleaned_data.get('usuario')
        if not usuario and self.initial.get('usuario'):
            cleaned_data['usuario'] = self.initial.get('usuario')

        preco_custo = cleaned_data.get('preco_de_custo')
        preco = cleaned_data.get('preco_peca')
        margem = cleaned_data.get('margem_de_lucro')
        last_edited = cleaned_data.get('pricing_last_edited')

        if preco_custo is not None and preco_custo < 0:
            self.add_error('preco_de_custo', 'O preço de custo não pode ser negativo.')
        if preco is not None and preco < 0:
            self.add_error('preco_peca', 'O preço de venda não pode ser negativo.')
        if margem is not None and margem < 0:
            self.add_error('margem_de_lucro', 'A margem de lucro não pode ser negativa.')
        if margem is not None and margem >= 100:
            self.add_error('margem_de_lucro', 'A margem de lucro deve ser menor que 100%.')

        if self.errors or preco_custo is None:
            return cleaned_data

        self._clean_payment_fields(cleaned_data, preco_custo)

        try:
            if margem is not None and (last_edited in ('margin', 'cost') or not preco):
                cleaned_data['preco_peca'] = calculate_sale_price_from_margin(preco_custo, margem)
            elif preco is not None:
                cleaned_data['margem_de_lucro'] = calculate_profit_margin(preco_custo, preco)
            elif margem is not None:
                cleaned_data['preco_peca'] = calculate_sale_price_from_margin(preco_custo, margem)
            else:
                self.add_error('preco_peca', 'Informe o preço de venda ou a margem de lucro.')
        except ValueError as error:
            self.add_error('margem_de_lucro', str(error))

        if (
            not last_edited
            and cleaned_data.get('preco_peca') is not None
            and cleaned_data.get('margem_de_lucro') is not None
        ):
            expected_price = calculate_sale_price_from_margin(
                preco_custo,
                cleaned_data['margem_de_lucro'],
            )
            if not decimals_are_close(cleaned_data['preco_peca'], expected_price):
                self.add_error('preco_peca', 'Preço de venda e margem de lucro não conferem.')

        return cleaned_data

    def _clean_payment_fields(self, cleaned_data, preco_custo):
        if cleaned_data.get('forma_pagamento') != Pecas.FIADO:
            cleaned_data['valor_entrada'] = None
            cleaned_data['qtd_parcela'] = None
            cleaned_data['data_vencimento'] = None
            return

        quantidade = cleaned_data.get('quantidade')
        if quantidade is None:
            return

        custo_total = preco_custo * quantidade
        entrada = cleaned_data.get('valor_entrada') or Decimal('0.00')
        cleaned_data['valor_entrada'] = entrada

        if entrada < 0:
            self.add_error('valor_entrada', 'O valor de entrada não pode ser negativo.')
        elif entrada > custo_total:
            self.add_error('valor_entrada', 'O valor de entrada não pode ser maior que o custo total do estoque.')
