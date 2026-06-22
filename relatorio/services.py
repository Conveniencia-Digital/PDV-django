from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Max, Min
from django.utils import timezone

from despesa.models import Despesa
from despesa.services import fixed_occurrence_count, is_expense_paid
from financeiro.models import LancamentoFinanceiro
from lanhouse.models import LanhouseModel
from orcamento.models import Orcamento
from peca.models import Pecas
from produto.models import Produto
from venda.models import Vendas


ZERO = Decimal("0.00")
FINALIZED_ORCAMENTO_STATUSES = [
    Orcamento.FINALIZADO,
    Orcamento.FINALIZADO_ENTREGUE,
    Orcamento.GARANTIA_ENCERRADA,
]
REPORT_PERIODS = [
    ("hoje", "Hoje"),
    ("ontem", "Ontem"),
    ("7dias", "7 dias"),
    ("este_mes", "Este mes"),
    ("mes_passado", "Mes passado"),
    ("este_ano", "Este ano"),
    ("todas", "Todas"),
]


@dataclass(frozen=True)
class ReportPeriod:
    key: str
    label: str
    start: date
    end: date

    @property
    def days(self):
        return max((self.end - self.start).days + 1, 1)


def money(value):
    return Decimal(value or ZERO).quantize(Decimal("0.01"))


def decimal_to_float(value):
    return float(money(value))


def available_report_periods():
    return REPORT_PERIODS


def resolve_report_period(params):
    today = timezone.localdate()
    key = _period_alias(params.get("periodo"))
    start_param = params.get("inicio") or params.get("data_inicio")
    end_param = params.get("fim") or params.get("data_fim")

    if not key and not start_param and not end_param:
        key = "este_mes"

    if key == "personalizado" or (not key and (start_param or end_param)):
        start = _parse_date(start_param) or _parse_date(end_param) or today
        end = _parse_date(end_param) or start
        if start > end:
            start, end = end, start
        return ReportPeriod("personalizado", "Periodo personalizado", start, end)

    if key == "hoje":
        return ReportPeriod("hoje", "Hoje", today, today)
    if key == "ontem":
        yesterday = today - timedelta(days=1)
        return ReportPeriod("ontem", "Ontem", yesterday, yesterday)
    if key == "7dias":
        return ReportPeriod("7dias", "Ultimos 7 dias", today - timedelta(days=6), today)
    if key == "mes_passado":
        first_day_current = today.replace(day=1)
        last_day_previous = first_day_current - timedelta(days=1)
        return ReportPeriod(
            "mes_passado",
            "Mes passado",
            last_day_previous.replace(day=1),
            last_day_previous,
        )
    if key == "este_ano":
        return ReportPeriod("este_ano", "Este ano", today.replace(month=1, day=1), today)
    if key == "todas":
        return ReportPeriod("todas", "Todo periodo", today, today)

    return ReportPeriod("este_mes", "Mes atual", today.replace(day=1), today)


def build_profitability_report(user, params):
    period = _normalize_all_data_period(user, resolve_report_period(params))
    source_rows = _source_rows(user, period)
    revenue = sum((row["revenue"] for row in source_rows), ZERO)
    variable_costs = sum((row["variable_cost"] for row in source_rows), ZERO)
    contribution_margin = money(revenue - variable_costs)
    contribution_margin_percent = _percent(contribution_margin, revenue)
    contribution_margin_rate = contribution_margin / revenue if revenue > ZERO else ZERO

    fixed_expenses = _fixed_expenses_total(user, period)
    operating_result = money(contribution_margin - fixed_expenses["total"])
    profit_margin_percent = _percent(operating_result, revenue)
    break_even_revenue = _break_even_revenue(fixed_expenses["total"], contribution_margin_rate)
    gap_to_break_even = max(break_even_revenue - revenue, ZERO)
    transaction_count = sum(row["count"] for row in source_rows)
    average_ticket = money(revenue / transaction_count) if transaction_count else ZERO
    projection_rows = _projection_rows(revenue, period)
    accounts = _accounts_summary(user, period)

    return {
        "period": period,
        "periods": available_report_periods(),
        "filters": {
            "periodo": period.key,
            "inicio": params.get("inicio") or params.get("data_inicio") or "",
            "fim": params.get("fim") or params.get("data_fim") or "",
            "data_inicio": params.get("inicio") or params.get("data_inicio") or "",
            "data_fim": params.get("fim") or params.get("data_fim") or "",
        },
        "summary": {
            "revenue": money(revenue),
            "variable_costs": money(variable_costs),
            "contribution_margin": contribution_margin,
            "contribution_margin_percent": contribution_margin_percent,
            "fixed_expenses": fixed_expenses["total"],
            "fixed_expense_occurrences": fixed_expenses["occurrences"],
            "operating_result": operating_result,
            "profit_margin_percent": profit_margin_percent,
            "break_even_revenue": break_even_revenue,
            "gap_to_break_even": money(gap_to_break_even),
            "break_even_reached": revenue >= break_even_revenue if break_even_revenue > ZERO else revenue > ZERO,
            "average_ticket": average_ticket,
            "transaction_count": transaction_count,
            "average_daily_revenue": money(revenue / period.days),
        },
        "source_rows": source_rows,
        "projection_rows": projection_rows,
        "accounts": accounts,
        "charts": {
            "projection": {
                "labels": [row["label"] for row in projection_rows],
                "values": [decimal_to_float(row["amount"]) for row in projection_rows],
            },
            "sources": {
                "labels": [row["source"] for row in source_rows],
                "values": [decimal_to_float(row["revenue"]) for row in source_rows],
            },
            "accounts_payable": {
                "labels": [row["category"] for row in accounts["payable_rows"]],
                "values": [decimal_to_float(row["amount"]) for row in accounts["payable_rows"]],
            },
            "accounts_receivable": {
                "labels": [row["category"] for row in accounts["receivable_rows"]],
                "values": [decimal_to_float(row["amount"]) for row in accounts["receivable_rows"]],
            },
        },
    }


def _source_rows(user, period):
    rows = []
    rows.append(_source_summary("Vendas", _sales_queryset(user, period)))
    rows.append(_source_summary("Orcamentos", _orcamento_queryset(user, period)))
    rows.append(_source_summary("Lan House", _lanhouse_queryset(user, period)))
    rows.extend(_manual_revenue_rows(user, period))

    return [
        row
        for row in rows
        if row["revenue"] > ZERO or row["variable_cost"] > ZERO
    ]


def _source_summary(source, queryset):
    revenue = ZERO
    variable_cost = ZERO
    count = 0

    for item in queryset:
        revenue += money(item.total())
        variable_cost += money(item.custo_total())
        variable_cost += money(getattr(item, "card_fee_amount", None))
        count += 1

    contribution = money(revenue - variable_cost)
    return {
        "source": source,
        "revenue": money(revenue),
        "variable_cost": money(variable_cost),
        "contribution": contribution,
        "contribution_percent": _percent(contribution, revenue),
        "count": count,
    }


def _manual_revenue_rows(user, period):
    queryset = (
        LancamentoFinanceiro.objects
        .filter(
            usuario=user,
            tipo=LancamentoFinanceiro.RECEITA,
            data_lancamento__range=(period.start, period.end),
        )
        .select_related("categoria")
    )
    rows_by_category = {}
    for entry in queryset:
        source = entry.categoria.nome if entry.categoria_id else "Receitas manuais"
        if source not in rows_by_category:
            rows_by_category[source] = {
                "source": source,
                "revenue": ZERO,
                "variable_cost": ZERO,
                "contribution": ZERO,
                "contribution_percent": ZERO,
                "count": 0,
            }
        rows_by_category[source]["revenue"] += money(entry.valor)
        rows_by_category[source]["count"] += 1

    rows = []
    for row in rows_by_category.values():
        row["revenue"] = money(row["revenue"])
        row["contribution"] = row["revenue"]
        row["contribution_percent"] = _percent(row["contribution"], row["revenue"])
        rows.append(row)
    return rows


def _sales_queryset(user, period):
    return (
        Vendas.objects
        .filter(
            usuario=user,
            status=Vendas.ENTREGUE,
            data_criacao__date__range=(period.start, period.end),
        )
        .prefetch_related("vendas_items__produto")
    )


def _orcamento_queryset(user, period):
    return (
        Orcamento.objects
        .filter(
            usuario=user,
            status__in=FINALIZED_ORCAMENTO_STATUSES,
            data_criacao__date__range=(period.start, period.end),
        )
        .prefetch_related("orcamento_items__peca")
    )


def _lanhouse_queryset(user, period):
    return (
        LanhouseModel.objects
        .filter(
            usuario=user,
            data_criacao__date__range=(period.start, period.end),
        )
        .prefetch_related("lanhouse_items__servico")
    )


def _accounts_summary(user, period):
    payable_rows = [
        _account_row("Peças", *_payable_stock_summary(
            Pecas.objects.filter(usuario=user, forma_pagamento=Pecas.FIADO),
            period,
        )),
        _account_row("Produtos", *_payable_stock_summary(
            Produto.objects.filter(usuario=user, forma_pagamento=Produto.FIADO),
            period,
        )),
        _account_row("Despesas", *_payable_expense_summary(user, period)),
    ]
    receivable_rows = [
        _account_row("Assistência técnica", *_receivable_summary(
            Orcamento.objects.filter(
                usuario=user,
                status__in=FINALIZED_ORCAMENTO_STATUSES,
                forma_pagamento=Orcamento.FIADO,
            ),
            period,
        )),
        _account_row("Vendas", *_receivable_summary(
            Vendas.objects.filter(
                usuario=user,
                status=Vendas.ENTREGUE,
                forma_pagamento=Vendas.FIADO,
            ),
            period,
        )),
        _account_row("Lanhouse", *_receivable_summary(
            LanhouseModel.objects.filter(
                usuario=user,
                forma_pagamento=LanhouseModel.FIADO,
            ),
            period,
        )),
    ]

    payable_total = money(sum((row["amount"] for row in payable_rows), ZERO))
    receivable_total = money(sum((row["amount"] for row in receivable_rows), ZERO))
    difference = money(receivable_total - payable_total)

    _with_percentages(payable_rows, payable_total)
    _with_percentages(receivable_rows, receivable_total)

    if difference > ZERO:
        difference_label = "A receber acima do a pagar"
        difference_tone = "success"
    elif difference < ZERO:
        difference_label = "A pagar acima do a receber"
        difference_tone = "danger"
    else:
        difference_label = "A pagar e a receber equilibrados"
        difference_tone = "info"

    return {
        "payable_total": payable_total,
        "receivable_total": receivable_total,
        "difference": difference,
        "difference_abs": money(abs(difference)),
        "difference_label": difference_label,
        "difference_tone": difference_tone,
        "payable_count": sum(row["count"] for row in payable_rows),
        "receivable_count": sum(row["count"] for row in receivable_rows),
        "payable_rows": payable_rows,
        "receivable_rows": receivable_rows,
    }


def _payable_stock_summary(queryset, period):
    total = ZERO
    count = 0

    for item in _created_in_period(queryset, period).only(
        "preco_de_custo",
        "quantidade",
        "valor_entrada",
    ):
        balance = _positive_balance(
            money(item.preco_de_custo) * (item.quantidade or 0),
            item.valor_entrada,
        )
        if balance > ZERO:
            total += balance
            count += 1

    return money(total), count


def _payable_expense_summary(user, period):
    total = ZERO
    count = 0

    expenses = (
        Despesa.objects
        .filter(
            usuario=user,
            tipo=Despesa.TIPO_EMPRESA,
            despesa_fixa=False,
            forma_pagamento=Despesa.FIADO,
            fiado_pago=False,
            data_cadastro__date__range=(period.start, period.end),
        )
        .only("preco_despesa", "valor_entrada")
    )
    for expense in expenses:
        balance = _positive_balance(expense.preco_despesa, expense.valor_entrada)
        if balance > ZERO:
            total += balance
            count += 1

    fixed_expenses = (
        Despesa.objects
        .filter(
            usuario=user,
            tipo=Despesa.TIPO_EMPRESA,
            despesa_fixa=True,
            forma_pagamento=Despesa.FIADO,
            fiado_pago=False,
        )
        .only(
            "preco_despesa",
            "valor_entrada",
            "despesa_fixa",
            "dia_vencimento_fixo",
            "data_cadastro",
        )
    )
    for expense in fixed_expenses:
        occurrences = fixed_occurrence_count(expense, period)
        if not occurrences:
            continue
        balance = _positive_balance(expense.preco_despesa, expense.valor_entrada)
        if balance > ZERO:
            total += balance * occurrences
            count += occurrences

    return money(total), count


def _receivable_summary(queryset, period):
    total = ZERO
    count = 0

    for item in _created_in_period(queryset, period):
        balance = _positive_balance(item.total(), item.valor_entrada)
        if balance > ZERO:
            total += balance
            count += 1

    return money(total), count


def _created_in_period(queryset, period):
    return queryset.filter(data_criacao__date__range=(period.start, period.end))


def _positive_balance(total, entry_value):
    balance = money(total) - money(entry_value)
    if balance < ZERO:
        return ZERO
    return money(balance)


def _account_row(category, amount, count):
    return {
        "category": category,
        "amount": money(amount),
        "count": count,
        "percentage": ZERO,
    }


def _with_percentages(rows, total):
    for row in rows:
        row["percentage"] = _percent(row["amount"], total)
    return rows


def _fixed_expenses_total(user, period):
    total = ZERO
    occurrences_total = 0
    queryset = Despesa.objects.filter(
        usuario=user,
        tipo=Despesa.TIPO_EMPRESA,
        despesa_fixa=True,
    )

    for expense in queryset:
        occurrences = fixed_occurrence_count(expense, period)
        occurrences_total += occurrences
        if occurrences and is_expense_paid(expense):
            total += money(expense.preco_despesa) * occurrences

    return {
        "total": money(total),
        "occurrences": occurrences_total,
    }


def _break_even_revenue(fixed_expenses, contribution_margin_rate):
    fixed_expenses = money(fixed_expenses)
    if fixed_expenses <= ZERO or contribution_margin_rate <= ZERO:
        return ZERO
    return money(fixed_expenses / contribution_margin_rate)


def _projection_rows(revenue, period):
    average_daily_revenue = money(revenue / period.days)
    month_days = monthrange(period.end.year, period.end.month)[1]
    rows = [
        ("Diária", 1),
        ("7 dias", 7),
        ("30 dias", 30),
        (f"Mes de {period.end:%m/%Y}", month_days),
        ("12 meses", 365),
    ]
    return [
        {
            "label": label,
            "days": days,
            "amount": money(average_daily_revenue * days),
        }
        for label, days in rows
    ]


def _percent(value, total):
    total = money(total)
    if total <= ZERO:
        return ZERO
    return (money(value) / total * Decimal("100")).quantize(Decimal("0.01"))


def _normalize_all_data_period(user, period):
    if period.key != "todas":
        return period

    dates = []
    for start, end in (
        _date_bounds(Vendas.objects.filter(usuario=user, status=Vendas.ENTREGUE), "data_criacao"),
        _date_bounds(Orcamento.objects.filter(usuario=user, status__in=FINALIZED_ORCAMENTO_STATUSES), "data_criacao"),
        _date_bounds(LanhouseModel.objects.filter(usuario=user), "data_criacao"),
        _date_bounds(Despesa.objects.filter(usuario=user), "data_cadastro"),
        _date_bounds(LancamentoFinanceiro.objects.filter(usuario=user), "data_lancamento"),
        _date_bounds(Pecas.objects.filter(usuario=user), "data_criacao"),
        _date_bounds(Produto.objects.filter(usuario=user), "data_criacao"),
    ):
        if start:
            dates.append(_as_date(start))
        if end:
            dates.append(_as_date(end))

    today = timezone.localdate()
    if not dates:
        return ReportPeriod("todas", "Todo periodo", today, today)
    return ReportPeriod("todas", "Todo periodo", min(dates), max(dates))


def _date_bounds(queryset, field_name):
    bounds = queryset.aggregate(start=Min(field_name), end=Max(field_name))
    return bounds["start"], bounds["end"]


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return value.date()


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _period_alias(key):
    aliases = {
        "today": "hoje",
        "yesterday": "ontem",
        "last_7_days": "7dias",
        "current_month": "este_mes",
        "previous_month": "mes_passado",
        "current_year": "este_ano",
        "custom": "personalizado",
    }
    return aliases.get(key, key)
