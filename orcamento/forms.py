from django import forms
from django.forms import inlineformset_factory

from orcamento.models import ItemsOrcamento, Orcamento


class OrcamentoForms(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Orcamento
        fields = ('cliente',)


class ItemsOrcamentoForms(forms.ModelForm):
    required_css_class = 'required'

    id = forms.IntegerField()

    class Meta:
        model = ItemsOrcamento
        fields = ('orcamento', 'id', 'peca', 'quantidade', 'preco_orcamento')

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
