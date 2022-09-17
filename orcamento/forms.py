from django import forms
from django.forms import TextInput, inlineformset_factory

from orcamento.models import ItemsOrcamento, Orcamento


class OrcamentoForms(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = ('cliente',)


class ItemsOrcamentoForms(forms.ModelForm):
    class Meta:
        model = ItemsOrcamento
        fields = ('nome_orcamento', 'preco_orcamento', 'quantidade')
        exclude = ['orcamento']

        widgets = {
            'preco_orcamento': TextInput(attrs={'data-field': 'preco_orcamento'})
        }

    def __init__(self, *args, **kwargs):
        super(ItemsOrcamentoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


ItemsOrcamentoFormset = inlineformset_factory(Orcamento,
                                              ItemsOrcamento,
                                              form=ItemsOrcamentoForms,
                                              extra=0,
                                              can_delete=False,
                                              min_num=1,
                                              validate_min=True)
