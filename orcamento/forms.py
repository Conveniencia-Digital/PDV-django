from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory, NumberInput

from orcamento.models import ItemsOrcamento, Orcamento, Servico
from peca.models import Pecas
from cliente.models import Cliente
from colaborador.models import Colaborador
from financeiro.form_fields import configure_card_fee_fields


class OrcamentoForms(forms.ModelForm):
    required_css_class = 'required'
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(), empty_label='Selecione o cliente')
   

    class Meta:
        model = Orcamento
        fields = '__all__'

        widgets = {
            'observacao': forms.TextInput()
        }

           
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('usuario')
        super(OrcamentoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user)
        self.fields['tecnico'].queryset = Colaborador.objects.filter(usuario=user)
        self.fields['usuario'].widget = forms.HiddenInput()
        configure_card_fee_fields(self, user)
        


class ServicoForms(forms.ModelForm):
    class Meta:
        model = Servico
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        super(ServicoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():   
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()




class ItemsOrcamentoForms(forms.ModelForm):
    required_css_class = 'required'

    id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    peca = forms.ModelChoiceField(
        queryset=Pecas.objects.all(),
        empty_label='Selecione a peça',
        required=False,
    )
    servico = forms.ModelChoiceField(
        queryset=Servico.objects.all(),
        empty_label='Selecione o serviço',
        required=False,
    )

    class Meta:
        model = ItemsOrcamento
        fields = ('orcamento', 'id', 'peca', 'servico',
                  'quantidade', 'preco_orcamento')

        widgets = {
            'preco_orcamento': NumberInput(attrs={'placeholder': '0,00'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('usuario')
        super(ItemsOrcamentoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['orcamento'].label = ''
        self.fields['orcamento'].widget = forms.HiddenInput()

        self.fields['id'].label = ''
        self.fields['peca'].queryset = Pecas.objects.filter(quantidade__gt=0, usuario=user)
        self.fields['servico'].queryset = Servico.objects.filter(usuario=user)
        self.fields['peca'].widget.attrs['class'] = 'form-select'
        self.fields['servico'].widget.attrs['class'] = 'form-select'

        if not self.instance.pk:
            self.fields['quantidade'].initial = self.fields['quantidade'].initial or 1
            if self.fields['preco_orcamento'].initial in (None, ''):
                self.fields['preco_orcamento'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        peca = cleaned_data.get('peca')
        servico = cleaned_data.get('servico')

        if self.cleaned_data.get('DELETE'):
            return cleaned_data

        if not peca and not servico:
            if self.empty_permitted:
                return cleaned_data
            raise ValidationError('Informe uma peça ou um serviço nesta linha.')
        if peca and servico:
            raise ValidationError('Informe apenas peça ou serviço por linha, não ambos.')

        if peca:
            cleaned_data['servico'] = None
        elif servico:
            cleaned_data['peca'] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.servico_id:
            instance.peca = None
        elif instance.peca_id:
            instance.servico = None
        if commit:
            instance.save()
        return instance


class ItemsOrcamentoFormSet(BaseInlineFormSet):
    def _deve_salvar_form(self, form):
        if not form.cleaned_data or form.cleaned_data.get('DELETE'):
            return False
        return bool(form.cleaned_data.get('peca') or form.cleaned_data.get('servico'))

    def save_new_objects(self, commit=True):
        saved = []
        for form in self.extra_forms:
            if self._deve_salvar_form(form):
                saved.append(form.save(commit=commit))
        self.new_objects = saved
        return saved

    def save_existing_objects(self, commit=True):
        saved = []
        for form in self.initial_forms:
            if form.cleaned_data.get('DELETE'):
                if form.instance.pk:
                    form.instance.delete()
                continue
            if not self._deve_salvar_form(form):
                if form.instance.pk:
                    form.instance.delete()
                continue
            saved.append(form.save(commit=commit))
        self.changed_objects = saved
        return saved
       
       


ItemsOrcamentoFormset = inlineformset_factory(
    Orcamento,
    ItemsOrcamento,
    form=ItemsOrcamentoForms,
    formset=ItemsOrcamentoFormSet,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
