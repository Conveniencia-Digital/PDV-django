from django import forms

from dashboard.models import Tarefas


class TarefaForms(forms.ModelForm):
    class Meta:
        model = Tarefas
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(TarefaForms, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['usuario'].widget = forms.HiddenInput()
