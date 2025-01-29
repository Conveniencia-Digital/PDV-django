from django import forms

from comunidade.models import Comunidade


class ComunidadeForms(forms.ModelForm):
    class Meta:
        model = Comunidade
        fields = '__all__'

        widgets = {
            'mensagem': forms.TextInput(attrs={'placeholder': 'Mensagem...'})
        }

    def __init__(self, *args, **kwargs):
        super(ComunidadeForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['usuario'].widget = forms.HiddenInput()
