from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date

from despesa.models import Despesa
from financeiro.services import decimal_to_float, money
from peca.models import Pecas
from produto.models import Produto


ZERO = Decimal("0.00")
UNCATEGORIZED = "Sem categoria"
EXPENSE_PERIODS = (
    ("hoje", "Hoje"),
    ("ontem", "Ontem"),
    ("7dias", "7 dias"),
    ("este_mes", "Este mes"),
    ("mes_passado", "Mes passado"),
    ("este_ano", "Este ano"),
    ("todas", "Todas"),
)
EXPENSE_PERIOD_KEYS = {key for key, _label in EXPENSE_PERIODS}
EXPENSE_PERIOD_ALIASES = {
    "today": "hoje",
    "yesterday": "ontem",
    "last_7_days": "7dias",
    "current_month": "este_mes",
    "previous_month": "mes_passado",
    "current_year": "este_ano",
    "custom": "personalizado",
}


@dataclass(frozen=True)
class ExpensePeriod:
    key: str
    label: str
    start: object = None
    end: object = None
    all_data: bool = False

    @property
    def days(self):
        if self.all_data or not self.start or not self.end:
            return 0
        return max((self.end - self.start).days + 1, 1)


def available_expense_periods():
    return EXPENSE_PERIODS


def resolve_expense_period(params):
    today = timezone.localdate()
    inicio = params.get("inicio") or params.get("data_inicio")
    fim = params.get("fim") or params.get("data_fim")
    key = EXPENSE_PERIOD_ALIASES.get(params.get("periodo"), params.get("periodo"))

    if not inicio and not fim and not key:
        key = "hoje"

    if key == "hoje":
        return ExpensePeriod("hoje", "Hoje", today, today)
    if key == "ontem":
        date = today - timedelta(days=1)
        return ExpensePeriod("ontem", "Ontem", date, date)
    if key == "7dias":
        return ExpensePeriod("7dias", "Ultimos 7 dias", today - timedelta(days=6), today)
    if key == "este_mes":
        return ExpensePeriod("este_mes", "Este mes", today.replace(day=1), today)
    if key == "mes_passado":
        first_day_this_month = today.replace(day=1)
        last_day_previous_month = first_day_this_month - timedelta(days=1)
        return ExpensePeriod(
            "mes_passado",
            "Mes passado",
            last_day_previous_month.replace(day=1),
            last_day_previous_month,
        )
    if key == "este_ano":
        return ExpensePeriod("este_ano", "Este ano", today.replace(month=1, day=1), today)
    if key == "todas":
        return ExpensePeriod("todas", "Todo periodo", all_data=True)

    start = parse_date(inicio) if inicio else None
    end = parse_date(fim) if fim else None
    if start and not end:
        end = start
    elif end and not start:
        start = end
    elif not start and not end:
        start = end = today

    if start > end:
        start, end = end, start

    return ExpensePeriod("personalizado", "Periodo personalizado", start, end)


def filter_expenses_by_period(queryset, period):
    if getattr(period, "all_data", False):
        return queryset
    return queryset.filter(data_cadastro__date__range=(period.start, period.end))


def filter_created_by_period(queryset, period, field_name="data_criacao"):
    if getattr(period, "all_data", False):
        return queryset
    return queryset.filter(**{f"{field_name}__date__range": (period.start, period.end)})


def expense_category_ranking(user, period):
    queryset = Despesa.objects.filter(usuario=user)
    queryset = filter_expenses_by_period(queryset, period)
    rows = (
        queryset
        .values("categoria_despesa_id", "categoria_despesa__nome_categoria_despesa")
        .annotate(amount=Sum("preco_despesa"))
        .order_by("-amount", "categoria_despesa__nome_categoria_despesa")
    )

    total_amount = sum((money(row["amount"]) for row in rows), ZERO)
    ranking = []
    for row in rows:
        amount = money(row["amount"])
        category = row["categoria_despesa__nome_categoria_despesa"] or UNCATEGORIZED
        percentage = ZERO if total_amount == ZERO else (amount / total_amount * Decimal("100")).quantize(Decimal("0.01"))
        ranking.append({
            "category": category,
            "amount": amount,
            "percentage": percentage,
        })
    return ranking


def _positive_balance(total, entry_value):
    balance = money(total) - money(entry_value)
    if balance < ZERO:
        return ZERO
    return balance


def expense_payable_total(user, period):
    total = ZERO

    despesas = (
        filter_expenses_by_period(
            Despesa.objects.filter(usuario=user, forma_pagamento=Despesa.FIADO),
            period,
        )
        .only("preco_despesa", "valor_entrada")
    )
    for despesa in despesas:
        total += _positive_balance(despesa.preco_despesa, despesa.valor_entrada)

    pecas = (
        filter_created_by_period(
            Pecas.objects.filter(usuario=user, forma_pagamento=Pecas.FIADO),
            period,
        )
        .only("preco_de_custo", "quantidade", "valor_entrada")
    )
    for peca in pecas:
        total += _positive_balance(peca.preco_de_custo * peca.quantidade, peca.valor_entrada)

    produtos = (
        filter_created_by_period(
            Produto.objects.filter(usuario=user, forma_pagamento=Produto.FIADO),
            period,
        )
        .only("preco_de_custo", "quantidade", "valor_entrada")
    )
    for produto in produtos:
        total += _positive_balance(produto.preco_de_custo * produto.quantidade, produto.valor_entrada)

    return money(total)


def build_expense_dashboard(user, params):
    period = resolve_expense_period(params)
    category_ranking = expense_category_ranking(user, period)
    total_amount = sum((item["amount"] for item in category_ranking), ZERO)
    payable_total = expense_payable_total(user, period)
    chart_height = max(320, min(720, 44 * max(len(category_ranking), 1)))
    inicio = params.get("inicio") or params.get("data_inicio") or ""
    fim = params.get("fim") or params.get("data_fim") or ""

    return {
        "period": period,
        "expense_periods": available_expense_periods(),
        "expense_filters": {
            "periodo": period.key,
            "inicio": inicio,
            "fim": fim,
            "data_inicio": inicio,
            "data_fim": fim,
        },
        "periodo": period.key,
        "inicio": inicio,
        "fim": fim,
        "expense_category_ranking": category_ranking,
        "expense_total": money(total_amount),
        "expense_payable_total": payable_total,
        "expense_count": filter_expenses_by_period(
            Despesa.objects.filter(usuario=user),
            period,
        ).count(),
        "expense_chart_height": chart_height,
        "expense_charts": {
            "category_ranking": {
                "labels": [item["category"] for item in category_ranking],
                "values": [decimal_to_float(item["amount"]) for item in category_ranking],
                "percentages": [decimal_to_float(item["percentage"]) for item in category_ranking],
            },
        },
    }
