from django import forms

from cliente.models import Cliente
from pedido.models import Pedido


class PedidoForms(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = '__all__'

        widgets = {
            'valor_produto': forms.NumberInput(),
            'observacao': forms.TextInput()
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PedidoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user)
