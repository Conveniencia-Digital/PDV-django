from django import forms
from django.forms import inlineformset_factory, TextInput

from orcamento.models import Orcamento, ItemsOrcamento


class OrcamentoForms(forms.ModelForm):
    required_css_class = 'required'

    nf = forms.IntegerField(label="Nota Fiscal")

    class Meta:
        model = Orcamento
        fields = ('nf',)


class OrcamentoItemsForms(forms.ModelForm):
    required_css_class = 'required'
    id = forms.IntegerField()

    class Meta:
        model = ItemsOrcamento
        fields = ('orcamento', 'id', 'nome_orcamento', 'preco_orcamento', 'quantidade')

        widgets = {
            'preco_orcamento': TextInput(attrs={'data-field': 'preco_orcamento'})
        }

    def __init__(self, *args, **kwargs):
        super(OrcamentoItemsForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

            self.fields['orcamento'].label = ''
            self.fields['orcamento'].widget = forms.HiddenInput()

            self.fields['id'].label = ''
            self.fields['id'].widget = forms.HiddenInput()


ItemsOrcamentoFormset = inlineformset_factory(Orcamento,
                                              ItemsOrcamento,
                                              form=OrcamentoItemsForms,
                                              extra=0,
                                              can_delete=False,
                                              min_num=1,
                                              validate_min=True)
