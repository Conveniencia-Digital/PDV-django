from django import forms
from suporte.models import Suporte


class SuporteForms(forms.ModelForm):
   
    class Meta:
        model = Suporte
        fields = '__all__'

        widgets = {
            'mensagem': forms.TextInput(attrs={'placeholder': 'Mensagem'})
        }
    
    def __init__(self, *args, **kwargs):
        super(SuporteForms, self).__init__(*args, **kwargs)

        for field_name, fields in self.fields.items():
            fields.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()


