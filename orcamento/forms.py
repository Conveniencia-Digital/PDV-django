from django import forms
from django.forms import inlineformset_factory, NumberInput

from orcamento.models import ItemsOrcamento, Orcamento
from peca.models import Pecas
from cliente.models import Cliente


class OrcamentoForms(forms.ModelForm):
    required_css_class = 'required'
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), empty_label='Selecione o cliente')

    class Meta:
        model = Orcamento
        fields = ('cliente', 'celular')


class ItemsOrcamentoForms(forms.ModelForm):
    required_css_class = 'required'

    id = forms.IntegerField()
    peca = forms.ModelChoiceField(queryset=Pecas.objects.all(), empty_label='Selecione a peca')

    class Meta:
        model = ItemsOrcamento
        fields = ('orcamento', 'id', 'peca', 'quantidade', 'preco_orcamento')

        widgets = {
            'preco_orcamento': NumberInput(attrs={'placeholder': '0,00'})
        }

    def __init__(self, *args, **kwargs):
        super(ItemsOrcamentoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['orcamento'].label = ''
        self.fields['orcamento'].widget = forms.HiddenInput()

        self.fields['id'].label = ''
        self.fields['id'].widget = forms.HiddenInput()


ItemsOrcamentoFormset = inlineformset_factory(
    Orcamento,
    ItemsOrcamento,
    form=ItemsOrcamentoForms,
    extra=0,
    can_delete=False,
    min_num=1,
    validate_min=True
)
