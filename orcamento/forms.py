from django import forms
from django.forms import inlineformset_factory, NumberInput

from orcamento.models import ItemsOrcamento, Orcamento
from peca.models import Pecas
from cliente.models import Cliente
from servico.models import Servico
from servico.forms import ServicoForms
from colaborador.models import Colaborador


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
        
    


class ItemsOrcamentoForms(forms.ModelForm):
    required_css_class = 'required'

    id = forms.IntegerField()
    peca = forms.ModelChoiceField(
        queryset=Pecas.objects.all(), empty_label='Selecione a peca')

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
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['peca'].queryset = Pecas.objects.filter(quantidade__gt=0, usuario=user)
        self.fields['servico'].queryset = Servico.objects.filter(usuario=user)
       
       


ItemsOrcamentoFormset = inlineformset_factory(
    Orcamento,
    ItemsOrcamento,
    form=ItemsOrcamentoForms,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)
