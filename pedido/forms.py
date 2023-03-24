from django import forms
from pedido.models import Pedido

class PedidoForms(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = '__all__'

        widgets = {
            'valor_produto': forms.NumberInput()
        }

    def __init__(self, *args, **kwargs):
        super(PedidoForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():   
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()


        