from django import forms

from financeiro.models import CardMachine


CARD_CALCULATED_FIELDS = (
    "card_payment_type",
    "card_fee_percentage",
    "card_fee_amount",
    "card_base_amount",
    "card_final_amount",
)


def configure_card_fee_fields(form, user):
    for name in CARD_CALCULATED_FIELDS:
        if name in form.fields:
            form.fields[name].widget = forms.HiddenInput()
            form.fields[name].required = False

    if "card_machine" in form.fields:
        current_machine = getattr(form.instance, "card_machine_id", None)
        machines = CardMachine.objects.filter(usuario=user, is_active=True)
        if current_machine:
            machines = CardMachine.objects.filter(usuario=user).filter(
                pk__in=list(machines.values_list("pk", flat=True)) + [current_machine]
            )
        form.fields["card_machine"].queryset = machines.order_by("name")
        form.fields["card_machine"].required = False
        form.fields["card_machine"].label = "Máquina de cartão"
        form.fields["card_machine"].empty_label = "Selecione a maquininha"

    if "card_installments" in form.fields:
        form.fields["card_installments"].required = False
        form.fields["card_installments"].label = "Parcelas"
        form.fields["card_installments"].widget = forms.Select(
            choices=[("", "Selecione")] + [(i, f"{i}x") for i in range(1, 13)]
        )

    if "pass_card_fee_to_customer" in form.fields:
        form.fields["pass_card_fee_to_customer"].required = False
        form.fields["pass_card_fee_to_customer"].label = "Repassar taxa ao cliente"
