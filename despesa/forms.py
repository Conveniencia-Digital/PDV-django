from decimal import Decimal

from django import forms
from despesa.models import Despesa, CategoriaDespesa
from fornecedor.models import Fornecedores

class CategoriaDespesaForms(forms.ModelForm):
    class Meta:
        model = CategoriaDespesa
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CategoriaDespesaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['usuario'].widget = forms.HiddenInput()

    def clean_nome_categoria_despesa(self):
        nome = (self.cleaned_data.get('nome_categoria_despesa') or '').strip()
        if not nome:
            raise forms.ValidationError('Informe o nome da categoria.')

        queryset = CategoriaDespesa.objects.filter(nome_categoria_despesa__iexact=nome)
        if self.user:
            queryset = queryset.filter(usuario=self.user)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError('Esta categoria já está cadastrada.')

        return nome

    def save(self, commit=True):
        categoria = super().save(commit=False)
        if self.user:
            categoria.usuario = self.user
        if commit:
            categoria.save()
        return categoria


class DespesaForms(forms.ModelForm):
    
    class Meta:
        model = Despesa
        exclude = ('lanhouse_card_fee', 'venda_card_fee', 'orcamento_card_fee')
        widgets = {
            'observacao': forms.TextInput(),
            'preco_despesa': forms.NumberInput(attrs={'step': '0.01'}),
            'valor_entrada': forms.NumberInput(attrs={'step': '0.01'}),
        }


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(DespesaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
        self.fields['usuario'].widget = forms.HiddenInput()
        

        self.fields['fornecedor'].queryset = Fornecedores.objects.filter(usuario=user)
        self.fields['categoria_despesa'].queryset = CategoriaDespesa.objects.filter(usuario=user).order_by('nome_categoria_despesa')

    def clean(self):
        cleaned_data = super().clean()
        forma_pagamento = cleaned_data.get('forma_pagamento')
        preco_despesa = cleaned_data.get('preco_despesa')
        valor_entrada = cleaned_data.get('valor_entrada')
        qtd_parcela = cleaned_data.get('qtd_parcela')

        if forma_pagamento != Despesa.FIADO:
            cleaned_data['valor_entrada'] = None
            cleaned_data['qtd_parcela'] = None
            cleaned_data['data_vencimento'] = None
            return cleaned_data

        if valor_entrada is None:
            valor_entrada = Decimal('0.00')
            cleaned_data['valor_entrada'] = valor_entrada
        elif valor_entrada < 0:
            self.add_error('valor_entrada', 'O valor de entrada não pode ser negativo.')

        if preco_despesa is not None and valor_entrada is not None and valor_entrada > preco_despesa:
            self.add_error('valor_entrada', 'O valor de entrada não pode ser maior que a despesa.')

        if qtd_parcela is not None and qtd_parcela <= 0:
            self.add_error('qtd_parcela', 'A quantidade de parcelas deve ser maior que zero.')

        return cleaned_data
