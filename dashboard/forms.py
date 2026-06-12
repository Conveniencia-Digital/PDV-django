from django import forms
from dashboard.models import Tarefas


class TarefaForms(forms.ModelForm):
    class Meta:
        model = Tarefas
        fields = '__all__'
        widgets = {
            'custo': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super(TarefaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
           field.widget.attrs['class'] = 'form-control'

        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['custo'].initial = self.fields['custo'].initial or '0.00'

    def clean_custo(self):
        custo = self.cleaned_data.get('custo')
        if custo is not None and custo < 0:
            raise forms.ValidationError('O custo não pode ser negativo.')
        return custo
