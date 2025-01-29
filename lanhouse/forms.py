from django import forms
from django.forms import inlineformset_factory

from cliente.models import Cliente
from colaborador.models import Colaborador
from lanhouse.models import ItemsLanhouse, LanhouseModel, LanhouseServico


class LanhouseServicoForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = LanhouseServico
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(LanhouseServicoForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['usuario'].widget = forms.HiddenInput()


class LanhouseForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = LanhouseModel
        fields = '__all__'

        widgets = {'observacao': forms.TextInput()}

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


class ItemsLanhouseForm(forms.ModelForm):
    required_css_class = 'required'
    id = forms.IntegerField()

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
    LanhouseModel, ItemsLanhouse, form=ItemsLanhouseForm, extra=0, can_delete=False, min_num=1, validate_min=True
)
