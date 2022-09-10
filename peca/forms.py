from django import forms
from peca.models import Pecas


class PecasForms(forms.ModelForm):
    class Meta:
        model = Pecas
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PecasForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

