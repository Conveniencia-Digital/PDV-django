from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from despesa.models import CategoriaDespesa, Despesa
from financeiro.models import (
    CategoriaLancamentoFinanceiro,
    FechamentoCaixa,
    LancamentoFinanceiro,
)
from financeiro.services import (
    CASH_OVER_CATEGORY,
    CASH_SHORTAGE_CATEGORY,
    Period,
    get_financial_period_metrics,
    money,
    resolve_period,
)


ZERO = Decimal("0.00")


@dataclass(frozen=True)
class CashClosingSnapshot:
    date: object
    opening_balance: Decimal
    revenue: Decimal
    expenses: Decimal
    expected_balance: Decimal


def ensure_cash_closing_categories(user):
    income_category, _created = CategoriaLancamentoFinanceiro.objects.get_or_create(
        usuario=user,
        nome=CASH_OVER_CATEGORY,
        tipo=CategoriaLancamentoFinanceiro.RECEITA,
    )
    expense_category, _created = CategoriaDespesa.objects.get_or_create(
        usuario=user,
        nome_categoria_despesa=CASH_SHORTAGE_CATEGORY,
    )
    return income_category, expense_category


def calculate_cash_closing_snapshot(user, closing_date):
    previous_closing = (
        FechamentoCaixa.objects
        .filter(usuario=user, data__lt=closing_date)
        .order_by("-data", "-created_at")
        .first()
    )
    opening_balance = money(previous_closing.valor_contado if previous_closing else ZERO)
    period = Period("fechamento", "Fechamento de Caixa", closing_date, closing_date)
    metrics = get_financial_period_metrics(user, period, include_cash_adjustments=False)
    revenue = money(metrics["revenue"])
    expenses = money(metrics["expenses"])
    expected_balance = money(opening_balance + revenue - expenses)

    return CashClosingSnapshot(
        date=closing_date,
        opening_balance=opening_balance,
        revenue=revenue,
        expenses=expenses,
        expected_balance=expected_balance,
    )


def classify_difference(difference):
    difference = money(difference)
    if difference > ZERO:
        return FechamentoCaixa.SOBRA
    if difference < ZERO:
        return FechamentoCaixa.FALTA
    return FechamentoCaixa.BALANCEADO


def create_cash_closing(user, closing_date, counted_balance, notes="", allow_duplicate=False):
    counted_balance = money(counted_balance)

    with transaction.atomic():
        if not allow_duplicate and FechamentoCaixa.objects.filter(usuario=user, data=closing_date).exists():
            raise ValueError("Já existe fechamento para esta data.")

        income_category, expense_category = ensure_cash_closing_categories(user)
        snapshot = calculate_cash_closing_snapshot(user, closing_date)
        difference = money(counted_balance - snapshot.expected_balance)
        status = classify_difference(difference)

        closing = FechamentoCaixa.objects.create(
            usuario=user,
            data=closing_date,
            saldo_abertura=snapshot.opening_balance,
            total_receitas=snapshot.revenue,
            total_despesas=snapshot.expenses,
            saldo_esperado=snapshot.expected_balance,
            valor_contado=counted_balance,
            diferenca=difference,
            status=status,
            observacao=notes,
        )

        if difference > ZERO:
            entry = LancamentoFinanceiro.objects.create(
                usuario=user,
                categoria=income_category,
                tipo=LancamentoFinanceiro.RECEITA,
                descricao=f"{CASH_OVER_CATEGORY} - Fechamento {closing_date:%d/%m/%Y}",
                valor=difference,
                data_lancamento=closing_date,
                observacao=notes,
            )
            closing.lancamento_sobra = entry
            closing.save(update_fields=["lancamento_sobra"])
        elif difference < ZERO:
            expense = Despesa.objects.create(
                usuario=user,
                categoria_despesa=expense_category,
                nome_despesa=f"{CASH_SHORTAGE_CATEGORY} - Fechamento {closing_date:%d/%m/%Y}",
                preco_despesa=abs(difference),
                forma_pagamento=Despesa.DINHEIRO,
                observacao=notes,
            )
            created_at = timezone.make_aware(datetime.combine(closing_date, time(hour=23, minute=59, second=59)))
            Despesa.objects.filter(pk=expense.pk).update(data_cadastro=created_at)
            closing.despesa_falta = expense
            closing.save(update_fields=["despesa_falta"])

        return closing


def build_cash_closing_dashboard(user, params):
    period = resolve_period(params)
    today = timezone.localdate()
    today_snapshot = calculate_cash_closing_snapshot(user, today)
    today_closing = (
        FechamentoCaixa.objects
        .filter(usuario=user, data=today)
        .order_by("-created_at")
        .first()
    )
    closings = (
        FechamentoCaixa.objects
        .filter(usuario=user, data__range=(period.start, period.end))
        .select_related("usuario", "lancamento_sobra", "despesa_falta")
        .order_by("-data", "-created_at")
    )

    cash_over_total = sum((closing.diferenca for closing in closings if closing.diferenca > ZERO), ZERO)
    cash_shortage_total = sum((abs(closing.diferenca) for closing in closings if closing.diferenca < ZERO), ZERO)

    return {
        "period": period,
        "filters": {
            "periodo": period.key,
            "inicio": params.get("inicio") or params.get("data_inicio") or "",
            "fim": params.get("fim") or params.get("data_fim") or "",
            "data_inicio": params.get("inicio") or params.get("data_inicio") or "",
            "data_fim": params.get("fim") or params.get("data_fim") or "",
        },
        "today_snapshot": today_snapshot,
        "today_closing": today_closing,
        "today_counted_balance": today_closing.valor_contado if today_closing else ZERO,
        "today_difference": today_closing.diferenca if today_closing else ZERO,
        "cash_over_total": money(cash_over_total),
        "cash_shortage_total": money(cash_shortage_total),
        "closing_count": closings.count(),
        "closings": closings,
    }
