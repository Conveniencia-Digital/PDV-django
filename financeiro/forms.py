from django import forms
from django.utils import timezone

from financeiro.models import CardMachine, CardMachineFee, ContasAReceber, FechamentoCaixa
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
        

class CardMachineFeeTableForm(forms.Form):
    name = forms.CharField(label="Nome da máquina", max_length=90)
    is_active = forms.BooleanField(label="Ativa", required=False, initial=True)
    debit_fee = forms.DecimalField(label="Débito", max_digits=5, decimal_places=2, min_value=0, max_value=100, initial=0)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        for installments in range(1, 13):
            self.fields[f"credit_{installments}_fee"] = forms.DecimalField(
                label=f"Crédito {installments}x",
                max_digits=5,
                decimal_places=2,
                min_value=0,
                max_value=100,
                initial=0,
            )

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["is_active"].widget.attrs["class"] = "form-check-input"

        if self.instance:
            self.fields["name"].initial = self.instance.name
            self.fields["is_active"].initial = self.instance.is_active
            fees = {
                (fee.payment_type, fee.installments): fee
                for fee in self.instance.fees.all()
            }
            debit = fees.get((CardMachineFee.PAYMENT_DEBIT, None))
            self.fields["debit_fee"].initial = debit.fee_percentage if debit else 0
            for installments in range(1, 13):
                fee = fees.get((CardMachineFee.PAYMENT_CREDIT, installments))
                self.fields[f"credit_{installments}_fee"].initial = fee.fee_percentage if fee else 0

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        user = getattr(self, "user", None)
        if user:
            qs = CardMachine.objects.filter(usuario=user, name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Já existe uma máquina com este nome.")
        return name

    def save(self, user):
        machine = self.instance or CardMachine(usuario=user)
        machine.usuario = user
        machine.name = self.cleaned_data["name"]
        machine.is_active = self.cleaned_data["is_active"]
        machine.save()

        self._save_fee(
            machine=machine,
            payment_type=CardMachineFee.PAYMENT_DEBIT,
            installments=None,
            fee_percentage=self.cleaned_data["debit_fee"],
        )
        for installments in range(1, 13):
            self._save_fee(
                machine=machine,
                payment_type=CardMachineFee.PAYMENT_CREDIT,
                installments=installments,
                fee_percentage=self.cleaned_data[f"credit_{installments}_fee"],
            )
        return machine

    def _save_fee(self, machine, payment_type, installments, fee_percentage):
        CardMachineFee.objects.update_or_create(
            card_machine=machine,
            payment_type=payment_type,
            installments=installments,
            defaults={
                "fee_percentage": fee_percentage,
                "is_active": True,
            },
        )

    @property
    def credit_fee_fields(self):
        return [self[f"credit_{installments}_fee"] for installments in range(1, 13)]


class FechamentoCaixaForm(forms.Form):
    data = forms.DateField(
        label="Data do fechamento",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    valor_contado = forms.DecimalField(
        label="Valor contado em caixa",
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )
    observacao = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    allow_duplicate = forms.BooleanField(
        label="Permitir novo fechamento para a mesma data",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["allow_duplicate"].widget.attrs["class"] = "form-check-input"

    def clean(self):
        cleaned_data = super().clean()
        closing_date = cleaned_data.get("data")
        allow_duplicate = cleaned_data.get("allow_duplicate")

        if closing_date and not allow_duplicate:
            exists = FechamentoCaixa.objects.filter(usuario=self.user, data=closing_date).exists()
            if exists:
                self.add_error(
                    "data",
                    "Já existe fechamento para esta data. Marque a opção de permitir novo fechamento para registrar outro.",
                )

        return cleaned_data
