from django import forms
from django.forms import inlineformset_factory, NumberInput

from erp.pricing import (
    calculate_profit_margin,
    calculate_sale_price_from_margin,
    decimals_are_close,
)
from lanhouse.models import LanhouseModel, LanhouseServico, ItemsLanhouse
from cliente.models import Cliente
from colaborador.models import Colaborador
from financeiro.form_fields import configure_card_fee_fields




class LanhouseServicoForm(forms.ModelForm):
    required_css_class = 'required'
    pricing_last_edited = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = LanhouseServico
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(LanhouseServicoForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['usuario'].required = False
        self.fields['preco'].required = False
        self.fields['margem_de_lucro'].required = False
        self.fields['preco_custo'].widget.attrs['step'] = '0.01'
        self.fields['preco'].widget.attrs['step'] = '0.01'
        self.fields['margem_de_lucro'].widget.attrs['step'] = '0.01'
        self.fields['margem_de_lucro'].widget.attrs['min'] = '0'
        self.fields['margem_de_lucro'].widget.attrs['max'] = '99.99'

    def clean(self):
        cleaned_data = super().clean()
        usuario = cleaned_data.get('usuario')
        if not usuario and self.user:
            cleaned_data['usuario'] = self.user

        preco_custo = cleaned_data.get('preco_custo')
        preco = cleaned_data.get('preco')
        margem = cleaned_data.get('margem_de_lucro')
        last_edited = cleaned_data.get('pricing_last_edited')

        if preco_custo is not None and preco_custo < 0:
            self.add_error('preco_custo', 'O preço de custo não pode ser negativo.')
        if preco is not None and preco < 0:
            self.add_error('preco', 'O preço de venda não pode ser negativo.')
        if margem is not None and margem < 0:
            self.add_error('margem_de_lucro', 'A margem de lucro não pode ser negativa.')
        if margem is not None and margem >= 100:
            self.add_error('margem_de_lucro', 'A margem de lucro deve ser menor que 100%.')

        if self.errors or preco_custo is None:
            return cleaned_data

        try:
            if margem is not None and (last_edited in ('margin', 'cost') or not preco):
                cleaned_data['preco'] = calculate_sale_price_from_margin(preco_custo, margem)
            elif preco is not None:
                cleaned_data['margem_de_lucro'] = calculate_profit_margin(preco_custo, preco)
            elif margem is not None:
                cleaned_data['preco'] = calculate_sale_price_from_margin(preco_custo, margem)
            else:
                self.add_error('preco', 'Informe o preço de venda ou a margem de lucro.')
        except ValueError as error:
            self.add_error('margem_de_lucro', str(error))

        if (
            not last_edited
            and cleaned_data.get('preco') is not None
            and cleaned_data.get('margem_de_lucro') is not None
        ):
            expected_price = calculate_sale_price_from_margin(
                preco_custo,
                cleaned_data['margem_de_lucro'],
            )
            if not decimals_are_close(cleaned_data['preco'], expected_price):
                self.add_error('preco', 'Preço de venda e margem de lucro não conferem.')

        return cleaned_data

    def clean_servico(self):
        servico = self.cleaned_data['servico'].strip()
        usuario = self.cleaned_data.get('usuario') or self.user
        if usuario:
            qs = LanhouseServico.objects.filter(usuario=usuario, servico__iexact=servico)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Este serviço já está cadastrado.')
        return servico





class LanhouseForm(forms.ModelForm):
    required_css_class = 'required'
    
    class Meta:
        model = LanhouseModel
        fields = "__all__"

        widgets = {
            'observacao': forms.TextInput()
        }

    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(LanhouseForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['data_vencimento'].widget = forms.HiddenInput()
        self.fields['valor_entrada'].widget = forms.HiddenInput()
        self.fields['qtd_parcela'].widget = forms.HiddenInput()
        self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user)
        self.fields['vendedor'].queryset = Colaborador.objects.filter(usuario=user)
        configure_card_fee_fields(self, user)


        
        


class ItemsLanhouseForm(forms.ModelForm):
    required_css_class = 'required'
    id = forms.IntegerField(required=False)

    class Meta:
        model = ItemsLanhouse
        fields = ('lanhouse', 'id', 'servico', 'quantidade', 'preco')
       

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ItemsLanhouseForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['id'].label = ''
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['lanhouse'].label = ''
        self.fields['lanhouse'].widget = forms.HiddenInput()
        self.fields['preco'].widget.attrs['step'] = 0.01

        self.fields['servico'].queryset = LanhouseServico.objects.filter(usuario=user)



LanhouseFormset = inlineformset_factory(
    LanhouseModel,
    ItemsLanhouse,
    form=ItemsLanhouseForm,
    extra=0,
    can_delete=False,
    min_num=1,
    validate_min=True
)
