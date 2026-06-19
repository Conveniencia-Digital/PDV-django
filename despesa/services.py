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
EXPENSE_CATEGORY_PANEL_HEIGHT = 360
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
EXPENSE_TYPE_FILTERS = (
    ("todos", "Todos"),
    ("empresa", "Empresa"),
    ("prolabore", "Pró-labore"),
    ("divida", "Dívida"),
)
EXPENSE_TYPE_ALIASES = {
    "todos": "todos",
    "all": "todos",
    "empresa": "empresa",
    "despesa_empresa": "empresa",
    "business": "empresa",
    "prolabore": "prolabore",
    "pró-labore": "prolabore",
    "divida": "divida",
    "dívida": "divida",
    "debt": "divida",
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


def available_expense_type_filters():
    return EXPENSE_TYPE_FILTERS


def resolve_expense_type_filter(params):
    return EXPENSE_TYPE_ALIASES.get(params.get("tipo"), params.get("tipo")) or "todos"


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


def _month_start(value):
    return value.replace(day=1)


def _next_month(value):
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1, day=1)
    return value.replace(month=value.month + 1, day=1)


def _created_date(expense):
    if not expense.data_cadastro:
        return timezone.localdate()
    return timezone.localtime(expense.data_cadastro).date()


def _period_bounds_for_fixed_expense(expense, period):
    created_month = _month_start(_created_date(expense))
    if getattr(period, "all_data", False):
        return created_month, timezone.localdate()

    start = max(period.start, created_month)
    return start, period.end


def fixed_occurrence_count(expense, period):
    if not expense.despesa_fixa or not expense.dia_vencimento_fixo:
        return 0

    start, end = _period_bounds_for_fixed_expense(expense, period)
    if start > end:
        return 0

    occurrences = 0
    current = _month_start(start)
    end_month = _month_start(end)
    while current <= end_month:
        due_date = expense.data_vencimento_fixo_no_mes(current.year, current.month)
        if due_date and start <= due_date <= end:
            occurrences += 1
        current = _next_month(current)

    return occurrences


def filter_expenses_for_period_or_fixed_due(queryset, period):
    non_fixed = filter_expenses_by_period(queryset.filter(despesa_fixa=False), period)
    fixed_ids = [
        expense.pk
        for expense in queryset.filter(despesa_fixa=True)
        if fixed_occurrence_count(expense, period) > 0
    ]
    return (non_fixed | queryset.filter(pk__in=fixed_ids)).distinct()


def filter_expenses_by_type(queryset, type_filter):
    if type_filter == "empresa":
        return queryset.filter(tipo=Despesa.TIPO_EMPRESA)
    if type_filter == "prolabore":
        return queryset.filter(tipo=Despesa.TIPO_PROLABORE)
    if type_filter == "divida":
        return queryset.filter(tipo=Despesa.TIPO_DIVIDA)
    return queryset


def filter_paid_expenses(queryset):
    return (
        queryset
        .exclude(forma_pagamento=Despesa.FIADO, fiado_pago=False)
        .exclude(tipo=Despesa.TIPO_DIVIDA, fiado_pago=False)
    )


def is_expense_paid(expense):
    if expense.tipo == Despesa.TIPO_DIVIDA and not expense.fiado_pago:
        return False
    if expense.forma_pagamento == Despesa.FIADO and not expense.fiado_pago:
        return False
    return True


def expense_paid_cash_amount(expense, occurrences=1):
    total = money(expense.preco_despesa)
    multiplier = max(occurrences or 0, 0)

    if expense.tipo == Despesa.TIPO_DIVIDA and not expense.fiado_pago:
        return ZERO
    if expense.forma_pagamento == Despesa.FIADO and not expense.fiado_pago:
        return min(money(expense.valor_entrada), total) * multiplier
    return total * multiplier


def filter_created_by_period(queryset, period, field_name="data_criacao"):
    if getattr(period, "all_data", False):
        return queryset
    return queryset.filter(**{f"{field_name}__date__range": (period.start, period.end)})


def expense_category_ranking(user, period, type_filter="todos"):
    if type_filter not in ("todos", "empresa"):
        return []

    queryset = Despesa.objects.filter(usuario=user, despesa_fixa=False, tipo=Despesa.TIPO_EMPRESA).select_related("categoria_despesa")
    queryset = filter_expenses_by_period(queryset, period)

    totals_by_category = {}
    for expense in queryset:
        amount = expense_paid_cash_amount(expense)
        if amount <= ZERO:
            continue
        category = expense.categoria_despesa.nome_categoria_despesa if expense.categoria_despesa else UNCATEGORIZED
        totals_by_category[category] = totals_by_category.get(category, ZERO) + amount

    fixed_queryset = (
        Despesa.objects.filter(
            usuario=user,
            despesa_fixa=True,
            tipo=Despesa.TIPO_EMPRESA,
        )
        .select_related("categoria_despesa")
    )
    for expense in fixed_queryset:
        occurrences = fixed_occurrence_count(expense, period)
        if not occurrences:
            continue
        amount = expense_paid_cash_amount(expense, occurrences)
        if amount <= ZERO:
            continue
        category = expense.categoria_despesa.nome_categoria_despesa if expense.categoria_despesa else UNCATEGORIZED
        totals_by_category[category] = totals_by_category.get(category, ZERO) + amount

    total_amount = sum(totals_by_category.values(), ZERO)
    ranking = []
    for category, amount in sorted(totals_by_category.items(), key=lambda item: (-item[1], item[0])):
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


def expense_total_amount(user, period, type_filter="todos"):
    queryset = filter_expenses_by_period(
        Despesa.objects.filter(usuario=user, despesa_fixa=False),
        period,
    )
    queryset = filter_expenses_by_type(queryset, type_filter).only(
        "preco_despesa",
        "forma_pagamento",
        "valor_entrada",
        "tipo",
        "fiado_pago",
    )
    total = sum((expense_paid_cash_amount(despesa) for despesa in queryset), ZERO)

    fixed_queryset = filter_expenses_by_type(
        Despesa.objects.filter(usuario=user, despesa_fixa=True),
        type_filter,
    ).only(
        "preco_despesa",
        "forma_pagamento",
        "valor_entrada",
        "tipo",
        "fiado_pago",
        "despesa_fixa",
        "dia_vencimento_fixo",
        "data_cadastro",
    )
    for despesa in fixed_queryset:
        occurrences = fixed_occurrence_count(despesa, period)
        if occurrences:
            total += expense_paid_cash_amount(despesa, occurrences)

    return money(total)


def _pending_payable_queryset(user, period, type_filter, *, debts):
    queryset = Despesa.objects.filter(usuario=user, despesa_fixa=False)
    if debts:
        queryset = queryset.filter(tipo=Despesa.TIPO_DIVIDA, fiado_pago=False)
    else:
        queryset = queryset.filter(tipo=Despesa.TIPO_EMPRESA, forma_pagamento=Despesa.FIADO, fiado_pago=False)
    queryset = filter_expenses_by_period(queryset, period)
    return filter_expenses_by_type(queryset, type_filter)


def _fixed_pending_payable_queryset(user, type_filter, *, debts):
    queryset = Despesa.objects.filter(usuario=user, despesa_fixa=True)
    if debts:
        queryset = queryset.filter(tipo=Despesa.TIPO_DIVIDA, fiado_pago=False)
    else:
        queryset = queryset.filter(tipo=Despesa.TIPO_EMPRESA, forma_pagamento=Despesa.FIADO, fiado_pago=False)
    return filter_expenses_by_type(queryset, type_filter)


def _sum_pending_expenses(user, period, type_filter="todos", *, debts=False):
    total = ZERO
    count = 0

    despesas = _pending_payable_queryset(user, period, type_filter, debts=debts).only(
        "preco_despesa",
        "valor_entrada",
        "fiado_pago",
    )
    for despesa in despesas:
        total += _positive_balance(despesa.preco_despesa, despesa.valor_entrada)
        count += 1

    fixed_despesas = _fixed_pending_payable_queryset(user, type_filter, debts=debts).only(
        "preco_despesa",
        "valor_entrada",
        "despesa_fixa",
        "dia_vencimento_fixo",
        "data_cadastro",
    )
    for despesa in fixed_despesas:
        occurrences = fixed_occurrence_count(despesa, period)
        if occurrences:
            total += _positive_balance(despesa.preco_despesa, despesa.valor_entrada) * occurrences
            count += occurrences

    return money(total), count


def expense_payable_total(user, period, type_filter="todos"):
    total, _count = _sum_pending_expenses(user, period, type_filter, debts=False)

    if type_filter not in ("prolabore", "divida"):
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


def debt_payable_summary(user, period, type_filter="todos"):
    if type_filter in ("empresa", "prolabore"):
        return {"total": ZERO, "count": 0}
    total, count = _sum_pending_expenses(user, period, type_filter, debts=True)
    return {"total": money(total), "count": count}


def build_debt_summary(user, period, type_filter="todos"):
    if type_filter in ("empresa", "prolabore"):
        return {
            "total": ZERO,
            "pending_total": ZERO,
            "paid_total": ZERO,
            "count": 0,
            "category_cards": [],
        }

    totals_by_category = {}
    count = 0

    queryset = filter_expenses_by_period(
        Despesa.objects.filter(usuario=user, tipo=Despesa.TIPO_DIVIDA, despesa_fixa=False).select_related("categoria_despesa"),
        period,
    )
    for despesa in queryset:
        _add_debt_to_category(totals_by_category, despesa)
        count += 1

    fixed_queryset = Despesa.objects.filter(
        usuario=user,
        tipo=Despesa.TIPO_DIVIDA,
        despesa_fixa=True,
    ).select_related("categoria_despesa")
    for despesa in fixed_queryset:
        occurrences = fixed_occurrence_count(despesa, period)
        if not occurrences:
            continue
        _add_debt_to_category(totals_by_category, despesa, occurrences)
        count += occurrences

    total = sum((item["total"] for item in totals_by_category.values()), ZERO)
    pending_total = sum((item["pending"] for item in totals_by_category.values()), ZERO)
    paid_total = sum((item["paid"] for item in totals_by_category.values()), ZERO)
    category_cards = []
    for category, values in sorted(totals_by_category.items(), key=lambda item: (-item[1]["total"], item[0])):
        percentage = ZERO if total == ZERO else (values["total"] / total * Decimal("100")).quantize(Decimal("0.01"))
        category_cards.append({
            "category": category,
            "total": money(values["total"]),
            "pending": money(values["pending"]),
            "paid": money(values["paid"]),
            "percentage": percentage,
        })

    return {
        "total": money(total),
        "pending_total": money(pending_total),
        "paid_total": money(paid_total),
        "count": count,
        "category_cards": category_cards,
    }


def _add_debt_to_category(totals_by_category, despesa, multiplier=1):
    category = despesa.categoria_despesa.nome_categoria_despesa if despesa.categoria_despesa else UNCATEGORIZED
    values = totals_by_category.setdefault(category, {
        "total": ZERO,
        "pending": ZERO,
        "paid": ZERO,
    })
    if despesa.fiado_pago:
        amount = money(despesa.preco_despesa) * multiplier
        values["paid"] += amount
        values["total"] += amount
        return

    amount = _positive_balance(despesa.preco_despesa, despesa.valor_entrada) * multiplier
    values["pending"] += amount
    values["total"] += amount


def _expense_total(queryset):
    return money(queryset.aggregate(total=Sum("preco_despesa"))["total"])


def _month_count(start, end):
    if not start or not end:
        return 1
    return max((end.year - start.year) * 12 + end.month - start.month + 1, 1)


def prolabore_category_ranking(user, period):
    queryset = filter_expenses_by_period(
        Despesa.objects.filter(usuario=user, tipo=Despesa.TIPO_PROLABORE),
        period,
    )
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


def build_prolabore_summary(user, period):
    today_period = resolve_expense_period({"periodo": "hoje"})
    month_period = resolve_expense_period({"periodo": "este_mes"})
    previous_month_period = resolve_expense_period({"periodo": "mes_passado"})

    selected_queryset = filter_expenses_by_period(
        Despesa.objects.filter(usuario=user, tipo=Despesa.TIPO_PROLABORE),
        period,
    )
    selected_total = _expense_total(selected_queryset)
    count = selected_queryset.count()

    return {
        "today_total": _expense_total(filter_expenses_by_period(
            Despesa.objects.filter(usuario=user, tipo=Despesa.TIPO_PROLABORE),
            today_period,
        )),
        "month_total": _expense_total(filter_expenses_by_period(
            Despesa.objects.filter(usuario=user, tipo=Despesa.TIPO_PROLABORE),
            month_period,
        )),
        "previous_month_total": _expense_total(filter_expenses_by_period(
            Despesa.objects.filter(usuario=user, tipo=Despesa.TIPO_PROLABORE),
            previous_month_period,
        )),
        "selected_total": selected_total,
        "count": count,
        "average_per_day": money(selected_total / period.days) if period.days else ZERO,
        "average_per_month": money(selected_total / _month_count(period.start, period.end)),
        "category_ranking": prolabore_category_ranking(user, period),
    }


def build_expense_dashboard(user, params):
    period = resolve_expense_period(params)
    type_filter = resolve_expense_type_filter(params)
    category_ranking = expense_category_ranking(user, period, type_filter)
    total_amount = expense_total_amount(user, period, type_filter)
    payable_total = expense_payable_total(user, period, type_filter)
    debt_payable = debt_payable_summary(user, period, type_filter)
    debt_summary = build_debt_summary(user, period, type_filter)
    period_expenses = filter_expenses_by_period(Despesa.objects.filter(usuario=user), period)
    period_expenses = filter_expenses_by_type(period_expenses, type_filter)
    non_fixed_expense_count = period_expenses.filter(despesa_fixa=False).count()
    if type_filter in ("todos", "empresa"):
        fixed_expenses = Despesa.objects.filter(
            usuario=user,
            despesa_fixa=True,
            tipo=Despesa.TIPO_EMPRESA,
        )
    else:
        fixed_expenses = Despesa.objects.none()
    fixed_occurrences = 0
    fixed_expense_total = ZERO
    for expense in fixed_expenses:
        occurrences = fixed_occurrence_count(expense, period)
        fixed_occurrences += occurrences
        if occurrences:
            fixed_expense_total += expense_paid_cash_amount(expense, occurrences)
    chart_height = EXPENSE_CATEGORY_PANEL_HEIGHT
    inicio = params.get("inicio") or params.get("data_inicio") or ""
    fim = params.get("fim") or params.get("data_fim") or ""
    prolabore_summary = build_prolabore_summary(user, period)

    return {
        "period": period,
        "expense_periods": available_expense_periods(),
        "expense_type_filters": available_expense_type_filters(),
        "expense_filters": {
            "periodo": period.key,
            "tipo": type_filter,
            "inicio": inicio,
            "fim": fim,
            "data_inicio": inicio,
            "data_fim": fim,
        },
        "periodo": period.key,
        "inicio": inicio,
        "fim": fim,
        "tipo": type_filter,
        "expense_category_ranking": category_ranking,
        "expense_total": total_amount,
        "expense_payable_total": payable_total,
        "debt_payable_total": debt_payable["total"],
        "debt_payable_count": debt_payable["count"],
        "debt_summary": debt_summary,
        "expense_count": non_fixed_expense_count + fixed_occurrences,
        "fixed_expense_count": fixed_occurrences,
        "fixed_expense_total": money(fixed_expense_total),
        "prolabore_summary": prolabore_summary,
        "expense_chart_height": chart_height,
        "expense_charts": {
            "category_ranking": {
                "labels": [item["category"] for item in category_ranking],
                "values": [decimal_to_float(item["amount"]) for item in category_ranking],
                "percentages": [decimal_to_float(item["percentage"]) for item in category_ranking],
            },
            "prolabore_category_ranking": {
                "labels": [item["category"] for item in prolabore_summary["category_ranking"]],
                "values": [decimal_to_float(item["amount"]) for item in prolabore_summary["category_ranking"]],
                "percentages": [decimal_to_float(item["percentage"]) for item in prolabore_summary["category_ranking"]],
            },
        },
    }
