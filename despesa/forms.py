from decimal import Decimal

from django import forms
from django.utils import timezone
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
    FIADO_STATUS_CHOICES = (
        ('False', 'Não pago'),
        ('True', 'Pago'),
    )
    fiado_pago = forms.TypedChoiceField(
        choices=FIADO_STATUS_CHOICES,
        coerce=lambda value: str(value).lower() in ('true', '1'),
        empty_value=False,
        initial='False',
        required=False,
        label='Status do fiado',
    )
    data_lancamento = forms.DateField(
        required=False,
        label='Data',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control selector-standard-control'}),
    )
    DECIMAL_FIELDS = ('preco_despesa', 'valor_entrada')
    PROLABORE_DEFAULT_DESCRIPTION = 'Pró-labore'
    FIXED_EXPENSE_TOGGLE_SCRIPT = (
        "var s=this.closest('[data-despesa-fixa-section]');"
        "var r=s&&s.querySelector('[data-despesa-fixa-row]');"
        "var d=s&&s.querySelector('[name=dia_vencimento_fixo]');"
        "if(r){r.hidden=!this.checked;r.setAttribute('aria-hidden',this.checked?'false':'true');}"
        "if(d){d.type=this.checked?'number':'hidden';d.required=this.checked;if(!this.checked){d.value='';}}"
    )
    
    class Meta:
        model = Despesa
        exclude = ('lanhouse_card_fee', 'venda_card_fee', 'orcamento_card_fee')
        widgets = {
            'observacao': forms.TextInput(),
            'preco_despesa': forms.NumberInput(attrs={'step': '0.01'}),
            'valor_entrada': forms.NumberInput(attrs={'step': '0.01'}),
            'dia_vencimento_fixo': forms.NumberInput(attrs={'min': '1', 'max': '31', 'step': '1'}),
            'dia_vencimento_parcela': forms.NumberInput(attrs={'min': '1', 'max': '31', 'step': '1'}),
        }


    @staticmethod
    def _normalize_decimal_data(data):
        if not data:
            return data

        normalized = data.copy()
        for field_name in DespesaForms.DECIMAL_FIELDS:
            value = normalized.get(field_name)
            if not isinstance(value, str):
                continue

            value = value.strip()
            if ',' in value and ('.' not in value or value.rfind(',') > value.rfind('.')):
                normalized[field_name] = value.replace('.', '').replace(',', '.')

        return normalized


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        self.tipo_forcado = kwargs.pop('tipo_forcado', None)
        if args:
            args = list(args)
            args[0] = self._normalize_decimal_data(args[0])
            args = tuple(args)
        elif kwargs.get('data') is not None:
            kwargs['data'] = self._normalize_decimal_data(kwargs['data'])

        super(DespesaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['tipo'].widget = forms.HiddenInput()
        self.fields['tipo'].required = False
        self.fields['fiado_pago'].widget.attrs.update({
            'class': 'form-select selector-standard-control',
        })
        self.fields['despesa_fixa'].widget.attrs.update({
            'class': 'form-check-input',
            'data-despesa-fixa-toggle': 'true',
            'onchange': self.FIXED_EXPENSE_TOGGLE_SCRIPT,
        })

        if self.tipo_forcado:
            self.fields['tipo'].initial = self.tipo_forcado

        if self.tipo_forcado == Despesa.TIPO_PROLABORE:
            if not self.is_bound:
                initial_date = timezone.localdate()
                if self.instance and self.instance.pk and self.instance.data_cadastro:
                    initial_date = timezone.localtime(self.instance.data_cadastro).date()
                self.fields['data_lancamento'].initial = initial_date
            self.fields['nome_despesa'].label = 'Descricao'
            self.fields['fornecedor'].widget = forms.HiddenInput()
            self.fields['despesa_fixa'].widget = forms.HiddenInput()
            self.fields['dia_vencimento_fixo'].widget = forms.HiddenInput()
            self.fields['forma_pagamento'].choices = [
                choice for choice in self.fields['forma_pagamento'].choices
                if choice[0] != Despesa.FIADO
            ]

        if self.tipo_forcado == Despesa.TIPO_DIVIDA:
            self.fields['nome_despesa'].label = 'Descricao da dívida'
            self.fields['fiado_pago'].label = 'Status da dívida'
        

        self.fields['fornecedor'].queryset = Fornecedores.objects.filter(usuario=user)
        self.fields['categoria_despesa'].queryset = CategoriaDespesa.objects.filter(usuario=user).order_by('nome_categoria_despesa')

    def clean(self):
        cleaned_data = super().clean()
        forma_pagamento = cleaned_data.get('forma_pagamento')
        preco_despesa = cleaned_data.get('preco_despesa')
        valor_entrada = cleaned_data.get('valor_entrada')
        qtd_parcela = cleaned_data.get('qtd_parcela')
        dia_vencimento_parcela = cleaned_data.get('dia_vencimento_parcela')
        despesa_fixa = cleaned_data.get('despesa_fixa')
        dia_vencimento_fixo = cleaned_data.get('dia_vencimento_fixo')
        nome_despesa = (cleaned_data.get('nome_despesa') or '').strip()
        tipo = self.tipo_forcado or cleaned_data.get('tipo') or Despesa.TIPO_EMPRESA
        cleaned_data['tipo'] = tipo
        cleaned_data['nome_despesa'] = nome_despesa

        if tipo == Despesa.TIPO_PROLABORE:
            if not cleaned_data.get('data_lancamento'):
                cleaned_data['data_lancamento'] = timezone.localdate()
            cleaned_data['fornecedor'] = None
            cleaned_data['despesa_fixa'] = False
            cleaned_data['dia_vencimento_fixo'] = None
            cleaned_data['fiado_pago'] = False
            despesa_fixa = False

            if not cleaned_data.get('categoria_despesa'):
                self.add_error('categoria_despesa', 'Informe a categoria do Pró-labore.')
            if forma_pagamento == Despesa.FIADO:
                self.add_error('forma_pagamento', 'Pró-labore deve reduzir o caixa no momento da retirada.')

        if tipo == Despesa.TIPO_DIVIDA:
            despesa_fixa = bool(despesa_fixa)

        if despesa_fixa:
            if dia_vencimento_fixo is None:
                self.add_error('dia_vencimento_fixo', 'Informe o dia de vencimento da despesa fixa.')
            elif not 1 <= dia_vencimento_fixo <= 31:
                self.add_error('dia_vencimento_fixo', 'O dia de vencimento deve estar entre 1 e 31.')
        else:
            cleaned_data['dia_vencimento_fixo'] = None

        if forma_pagamento != Despesa.FIADO:
            cleaned_data['valor_entrada'] = None
            cleaned_data['qtd_parcela'] = None
            cleaned_data['data_vencimento'] = None
            cleaned_data['dia_vencimento_parcela'] = None
            if tipo != Despesa.TIPO_DIVIDA:
                cleaned_data['fiado_pago'] = False
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

        if qtd_parcela and qtd_parcela > 1:
            cleaned_data['data_vencimento'] = None
            if dia_vencimento_parcela is None:
                self.add_error('dia_vencimento_parcela', 'Informe o dia de vencimento de cada mês.')
            elif not 1 <= dia_vencimento_parcela <= 31:
                self.add_error('dia_vencimento_parcela', 'O dia de vencimento deve estar entre 1 e 31.')
        else:
            cleaned_data['dia_vencimento_parcela'] = None

        return cleaned_data
