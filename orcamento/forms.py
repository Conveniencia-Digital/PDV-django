from django import forms
from django.forms import inlineformset_factory

from orcamento.models import Orcamento, ItemsOrcamento


class OrcamentoForms(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = '__all__'


class OrcamentoItemsForms(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = ItemsOrcamento
        fields = ('nome_orcamento', 'preco_orcamento', 'quantidade')

    def __init__(self, *args, **kwargs):
        super(OrcamentoItemsForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


ItemsOrcamentoFormset = inlineformset_factory(Orcamento,
                                              ItemsOrcamento,
                                              form=OrcamentoItemsForms,
                                              extra=0,
                                              can_delete=False,
                                              min_num=1,
                                              validate_min=True)
