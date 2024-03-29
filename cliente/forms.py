from django import forms
from cliente.models import Cliente



class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'data_nascimento' :forms.NumberInput(attrs={'type': 'date'}),
            'observacao': forms.TextInput()
        }

    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['usuario'].widget = forms.HiddenInput()
    


