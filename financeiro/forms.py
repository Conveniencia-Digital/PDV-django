from django import forms
from financeiro.models import ContasAReceber
from cliente.models import Cliente


class ContasAReceberForms(forms.ModelForm):
    class Meta:
        model = ContasAReceber
        fields = '__all__'
        widgets = {
            'observacao': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ContasAReceberForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['cliente'].queryset = Cliente.objects.filter(usuario=user)
        
