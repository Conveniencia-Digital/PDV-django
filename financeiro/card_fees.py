from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.core.exceptions import ValidationError

from despesa.models import CategoriaDespesa, Despesa
from financeiro.models import CardMachine, CardMachineFee


ZERO = Decimal("0.00")
MONEY_QUANT = Decimal("0.01")
CARD_FEE_CATEGORY = "Taxas de Maquininha"


@dataclass(frozen=True)
class CardFeeCalculation:
    payment_type: Optional[str]
    installments: Optional[int]
    fee_percentage: Decimal
    fee_amount: Decimal
    base_amount: Decimal
    final_amount: Decimal


def money(value):
    return Decimal(value or ZERO).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def is_card_payment_method(payment_method):
    return payment_method in ("Cartāo de credito", "Cartāo de debito")


def payment_type_for_method(payment_method):
    if payment_method == "Cartāo de debito":
        return CardMachineFee.PAYMENT_DEBIT
    if payment_method == "Cartāo de credito":
        return CardMachineFee.PAYMENT_CREDIT
    return None


def calculate_card_fee(user, payment_method, card_machine, installments, base_amount, pass_fee_to_customer):
    base_amount = max(money(base_amount), ZERO)
    payment_type = payment_type_for_method(payment_method)

    if not payment_type:
        return CardFeeCalculation(
            payment_type=None,
            installments=None,
            fee_percentage=ZERO,
            fee_amount=ZERO,
            base_amount=base_amount,
            final_amount=base_amount,
        )

    if not card_machine:
        raise ValidationError("Selecione a máquina de cartão.")

    if isinstance(card_machine, CardMachine):
        machine = card_machine
    else:
        machine = CardMachine.objects.filter(pk=card_machine).first()

    if not machine or machine.usuario_id != user.id:
        raise ValidationError("Máquina de cartão inválida.")

    if payment_type == CardMachineFee.PAYMENT_CREDIT:
        try:
            installments = int(installments or 1)
        except (TypeError, ValueError):
            raise ValidationError("Informe uma quantidade de parcelas válida.")
        if installments < 1 or installments > 12:
            raise ValidationError("A quantidade de parcelas deve estar entre 1 e 12.")
    else:
        installments = None

    fee_query = CardMachineFee.objects.filter(
        card_machine=machine,
        payment_type=payment_type,
        is_active=True,
    )
    if payment_type == CardMachineFee.PAYMENT_CREDIT:
        fee_query = fee_query.filter(installments=installments)
    else:
        fee_query = fee_query.filter(installments__isnull=True)

    fee = fee_query.first()
    if not fee:
        label = "débito" if payment_type == CardMachineFee.PAYMENT_DEBIT else f"crédito {installments}x"
        raise ValidationError(f"Cadastre a taxa de {label} para esta máquina.")

    fee_percentage = money(fee.fee_percentage)
    fee_amount = money(base_amount * fee_percentage / Decimal("100"))
    final_amount = money(base_amount + fee_amount) if pass_fee_to_customer else base_amount

    return CardFeeCalculation(
        payment_type=payment_type,
        installments=installments,
        fee_percentage=fee_percentage,
        fee_amount=fee_amount,
        base_amount=base_amount,
        final_amount=final_amount,
    )


def preview_card_fee(user, payment_method, machine_pk, installments, base_amount, pass_fee_to_customer):
    base_amount = money(base_amount)

    if not is_card_payment_method(payment_method):
        return {
            "payload": {
                "is_card": False,
                "payment_type": None,
                "installments": None,
                "fee_percentage": "0.00",
                "fee_amount": "0.00",
                "base_amount": str(base_amount),
                "final_amount": str(base_amount),
                "message": "",
            },
            "status": 200,
        }

    if not machine_pk:
        return {
            "payload": {
                "is_card": True,
                "payment_type": None,
                "installments": installments,
                "fee_percentage": "0.00",
                "fee_amount": "0.00",
                "base_amount": str(base_amount),
                "final_amount": str(base_amount),
                "message": "Selecione a máquina de cartão.",
            },
            "status": 200,
        }

    machine = CardMachine.objects.filter(pk=machine_pk, usuario=user).first()
    if not machine:
        return {
            "payload": {
                "is_card": True,
                "payment_type": None,
                "installments": installments,
                "fee_percentage": "0.00",
                "fee_amount": "0.00",
                "base_amount": str(base_amount),
                "final_amount": str(base_amount),
                "message": "Máquina de cartão inválida.",
            },
            "status": 422,
        }

    try:
        calculation = calculate_card_fee(
            user=user,
            payment_method=payment_method,
            card_machine=machine,
            installments=installments,
            base_amount=base_amount,
            pass_fee_to_customer=pass_fee_to_customer,
        )
    except ValidationError as error:
        messages = getattr(error, "messages", None) or [str(error)]
        return {
            "payload": {
                "is_card": True,
                "payment_type": None,
                "installments": installments,
                "fee_percentage": "0.00",
                "fee_amount": "0.00",
                "base_amount": str(base_amount),
                "final_amount": str(base_amount),
                "message": messages[0],
            },
            "status": 422,
        }

    return {
        "payload": {
            "is_card": True,
            "payment_type": calculation.payment_type,
            "installments": calculation.installments,
            "fee_percentage": str(calculation.fee_percentage),
            "fee_amount": str(calculation.fee_amount),
            "base_amount": str(calculation.base_amount),
            "final_amount": str(calculation.final_amount),
            "message": "",
        },
        "status": 200,
    }


def apply_card_fee_to_transaction(transaction, calculation):
    transaction.card_payment_type = calculation.payment_type
    transaction.card_installments = calculation.installments
    transaction.card_fee_percentage = calculation.fee_percentage
    transaction.card_fee_amount = calculation.fee_amount
    transaction.card_base_amount = calculation.base_amount
    transaction.card_final_amount = calculation.final_amount
    if not calculation.payment_type:
        transaction.card_machine = None
        transaction.pass_card_fee_to_customer = False


def apply_card_fee_to_lanhouse(lanhouse, calculation):
    apply_card_fee_to_transaction(lanhouse, calculation)


def sync_card_fee_expense(transaction, relation_field, document_label, should_create=True):
    should_create = (
        should_create
        and transaction.card_payment_type
        and not transaction.pass_card_fee_to_customer
        and money(transaction.card_fee_amount) > ZERO
    )

    if not should_create:
        Despesa.objects.filter(**{relation_field: transaction}).delete()
        return None

    category = (
        CategoriaDespesa.objects
        .filter(usuario=transaction.usuario, nome_categoria_despesa=CARD_FEE_CATEGORY)
        .first()
    )
    if not category:
        category = CategoriaDespesa.objects.create(
            usuario=transaction.usuario,
            nome_categoria_despesa=CARD_FEE_CATEGORY,
        )

    machine_name = transaction.card_machine.name if transaction.card_machine else "maquininha"
    defaults = {
        "usuario": transaction.usuario,
        "categoria_despesa": category,
        "nome_despesa": f"Taxa de maquininha - {document_label} #{transaction.pk}",
        "preco_despesa": money(transaction.card_fee_amount),
        "forma_pagamento": Despesa.PIX,
        "observacao": (
            f"Taxa absorvida da {machine_name}. "
            f"Percentual: {money(transaction.card_fee_percentage)}%. "
            f"Valor base: R$ {money(transaction.card_base_amount)}."
        ),
        "fornecedor": None,
        "data_vencimento": None,
        "qtd_parcela": None,
        "valor_entrada": None,
    }
    expense, _created = Despesa.objects.update_or_create(
        **{relation_field: transaction},
        defaults=defaults,
    )
    return expense


def sync_lanhouse_card_fee_expense(lanhouse):
    return sync_card_fee_expense(lanhouse, "lanhouse_card_fee", "Lan House")
