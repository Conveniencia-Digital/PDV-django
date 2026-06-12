from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Max, Min, Sum
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from django.utils import timezone
from django.utils.dateparse import parse_date

from financeiro.services import decimal_to_float, money
from lanhouse.models import ItemsLanhouse, LanhouseModel


ZERO = Decimal("0.00")


@dataclass(frozen=True)
class PeriodoLanhouse:
    key: str
    label: str
    start: date = None
    end: date = None
    all_data: bool = False

    @property
    def days(self):
        if self.all_data or not self.start or not self.end:
            return 0
        return max((self.end - self.start).days + 1, 1)


def inicio_fim_dia(data):
    inicio = timezone.make_aware(datetime.combine(data, datetime.min.time()))
    fim = timezone.make_aware(datetime.combine(data, datetime.max.time()))
    return inicio, fim


def _mes_passado(hoje):
    primeiro_deste_mes = hoje.replace(day=1)
    ultimo_mes_passado = primeiro_deste_mes - timedelta(days=1)
    return ultimo_mes_passado.replace(day=1), ultimo_mes_passado


def resolver_periodo_lanhouse(params):
    inicio = params.get('inicio') or params.get('data_inicio')
    fim = params.get('fim') or params.get('data_fim')
    periodo = params.get('periodo')
    hoje = timezone.localdate()

    aliases = {
        'today': 'hoje',
        'yesterday': 'ontem',
        'last_7_days': '7dias',
        'current_month': 'este_mes',
        'previous_month': 'mes_passado',
        'current_year': 'este_ano',
    }
    periodo = aliases.get(periodo, periodo)

    if not inicio and not fim and not periodo:
        periodo = 'hoje'

    if periodo == 'hoje':
        return PeriodoLanhouse('hoje', 'Hoje', hoje, hoje)
    if periodo == 'ontem':
        data = hoje - timedelta(days=1)
        return PeriodoLanhouse('ontem', 'Ontem', data, data)
    if periodo == '7dias':
        return PeriodoLanhouse('7dias', 'Últimos 7 dias', hoje - timedelta(days=6), hoje)
    if periodo == 'este_mes':
        return PeriodoLanhouse('este_mes', 'Este mês', hoje.replace(day=1), hoje)
    if periodo == 'mes_passado':
        start, end = _mes_passado(hoje)
        return PeriodoLanhouse('mes_passado', 'Mês passado', start, end)
    if periodo == 'este_ano':
        return PeriodoLanhouse('este_ano', 'Este ano', hoje.replace(month=1, day=1), hoje)
    if periodo == 'todas':
        return PeriodoLanhouse('todas', 'Todo período', all_data=True)

    inicio_date = parse_date(inicio) if inicio else None
    fim_date = parse_date(fim) if fim else None

    if inicio_date and not fim_date:
        fim_date = inicio_date
    elif fim_date and not inicio_date:
        inicio_date = fim_date
    elif not inicio_date and not fim_date:
        inicio_date = fim_date = hoje

    if inicio_date > fim_date:
        inicio_date, fim_date = fim_date, inicio_date

    return PeriodoLanhouse('personalizado', 'Período personalizado', inicio_date, fim_date)


def aplicar_filtro_periodo(queryset, request):
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    periodo = request.GET.get('periodo')

    if not inicio and not fim and not periodo:
        periodo = 'hoje'

    periodo_resolvido = resolver_periodo_lanhouse(request.GET)
    if not periodo_resolvido.all_data:
        ini = timezone.make_aware(datetime.combine(periodo_resolvido.start, datetime.min.time()))
        fim_dt = timezone.make_aware(datetime.combine(periodo_resolvido.end, datetime.max.time()))
        queryset = queryset.filter(data_criacao__range=(ini, fim_dt))

    return queryset, inicio, fim, periodo


def metricas_lanhouse(queryset):
    from decimal import Decimal

    total_lanhouse = sum(
        (Decimal(l.total() or 0) for l in queryset),
        Decimal('0.00'),
    )

    total_descontos = sum(
        (
            Decimal(l.desconto) if l.desconto else Decimal('0.00')
            for l in queryset
        ),
        Decimal('0.00'),
    )

    custo_mercadoria = sum(
        (
            Decimal(item.servico.preco_custo or 0) * item.quantidade
            for l in queryset
            for item in l.lanhouse_items.all()
        ),
        Decimal('0.00'),
    )

    taxas_maquininha_absorvidas = sum(
        (
            Decimal(l.card_fee_amount or 0)
            for l in queryset
            if l.card_payment_type and not l.pass_card_fee_to_customer
        ),
        Decimal('0.00'),
    )

    lucro_total = sum(
        (
            Decimal(l.total() or 0)
            - Decimal(l.custo_total() or 0)
            - (
                Decimal(l.card_fee_amount or 0)
                if l.card_payment_type and not l.pass_card_fee_to_customer
                else Decimal('0.00')
            )
        )
        for l in queryset
    )

    qtd_lanhouse = queryset.count() if hasattr(queryset, 'count') else len(queryset)
    quantidade_total_servicos = sum(
        (
            item.quantidade
            for l in queryset
            for item in l.lanhouse_items.all()
        ),
        0,
    )
    clientes_atendidos = (
        queryset.values('cliente_id').distinct().count()
        if hasattr(queryset, 'values')
        else len({l.cliente_id for l in queryset})
    )
    ticket_medio_atendimento = (
        total_lanhouse / qtd_lanhouse
        if qtd_lanhouse > 0
        else Decimal('0.00')
    )

    base_margem = total_lanhouse
    margem = (
        (lucro_total / base_margem) * 100
        if base_margem > 0
        else Decimal('0.00')
    )

    return {
        'total_lanhouse': total_lanhouse,
        'lucro_total': lucro_total,
        'qtd_lanhouse': qtd_lanhouse,
        'total_descontos': total_descontos.quantize(Decimal('0.01')),
        'custo_mercadoria': custo_mercadoria.quantize(Decimal('0.01')),
        'taxas_maquininha_absorvidas': taxas_maquininha_absorvidas.quantize(Decimal('0.01')),
        'margem_lucro_lanhouse': margem.quantize(Decimal('0.01')),
        'ticket_medio_atendimento': ticket_medio_atendimento.quantize(Decimal('0.01')),
        'quantidade_total_servicos': quantidade_total_servicos,
        'quantidade_total_clientes_atendidos': clientes_atendidos,
    }


def build_lanhouse_dashboard_charts(user, params):
    periodo = resolver_periodo_lanhouse(params)
    revenue_chart = receita_lanhouse_por_periodo(user, periodo)
    service_ranking = ranking_servicos_lanhouse(user, periodo)
    chart_height = max(320, min(720, 42 * max(len(service_ranking), 1)))

    return {
        'lanhouse_chart_period': periodo,
        'lanhouse_revenue_has_data': any(value > 0 for value in revenue_chart['values']),
        'lanhouse_service_has_data': bool(service_ranking),
        'lanhouse_service_ranking': service_ranking,
        'lanhouse_service_chart_height': chart_height,
        'lanhouse_charts': {
            'revenue': revenue_chart,
            'services': {
                'labels': [item['service'] for item in service_ranking],
                'revenues': [decimal_to_float(item['revenue']) for item in service_ranking],
                'quantities': [item['quantity'] for item in service_ranking],
            },
        },
    }


def receita_lanhouse_por_periodo(user, periodo):
    periodo = _normalizar_periodo_total(user, periodo)
    if periodo.all_data and not periodo.start:
        return {'labels': [], 'values': [], 'grouping': 'empty'}

    if periodo.days == 1:
        rows = _receita_lanhouse_agrupada(user, periodo, TruncHour)
        totals = {hour: ZERO for hour in range(24)}
        for row in rows:
            bucket = row['period']
            hour = timezone.localtime(bucket).hour if isinstance(bucket, datetime) else bucket.hour
            totals[hour] = totals.get(hour, ZERO) + money(row['amount'])
        return {
            'labels': [f'{hour:02d}:00' for hour in range(24)],
            'values': [decimal_to_float(totals.get(hour, ZERO)) for hour in range(24)],
            'grouping': 'hour',
        }

    if periodo.days > 120:
        rows = _receita_lanhouse_agrupada(user, periodo, TruncMonth)
        buckets = _month_buckets(periodo.start, periodo.end)
        totals = {bucket: ZERO for bucket in buckets}
        for row in rows:
            bucket = _as_date(row['period']).replace(day=1)
            totals[bucket] = totals.get(bucket, ZERO) + money(row['amount'])
        return {
            'labels': [bucket.strftime('%m/%Y') for bucket in buckets],
            'values': [decimal_to_float(totals.get(bucket, ZERO)) for bucket in buckets],
            'grouping': 'month',
        }

    rows = _receita_lanhouse_agrupada(user, periodo, TruncDate)
    buckets = _day_buckets(periodo.start, periodo.end)
    totals = {bucket: ZERO for bucket in buckets}
    for row in rows:
        bucket = _as_date(row['period'])
        totals[bucket] = totals.get(bucket, ZERO) + money(row['amount'])
    return {
        'labels': [bucket.strftime('%d/%m') for bucket in buckets],
        'values': [decimal_to_float(totals.get(bucket, ZERO)) for bucket in buckets],
        'grouping': 'day',
    }


def ranking_servicos_lanhouse(user, periodo, limit=12):
    gross_expression = _item_total_expression()
    rows = (
        _items_lanhouse_periodo(user, periodo)
        .values('servico_id', 'servico__servico')
        .annotate(
            quantity=Sum('quantidade'),
            revenue=Sum(gross_expression),
            transactions=Count('lanhouse_id', distinct=True),
        )
        .order_by('-quantity', '-revenue', 'servico__servico')[:limit]
    )

    return [
        {
            'service': row['servico__servico'] or 'Serviço sem nome',
            'quantity': row['quantity'] or 0,
            'revenue': money(row['revenue']),
            'transactions': row['transactions'],
        }
        for row in rows
    ]


def _receita_lanhouse_agrupada(user, periodo, trunc_function):
    gross_expression = _item_total_expression()
    rows = (
        _items_lanhouse_periodo(user, periodo)
        .annotate(period=trunc_function('lanhouse__data_criacao'))
        .values('period', 'lanhouse_id', 'lanhouse__desconto', 'lanhouse__card_final_amount')
        .annotate(gross=Sum(gross_expression))
        .order_by('period')
    )

    return [
        {
            'period': row['period'],
            'amount': _valor_lanhouse(row['gross'], row['lanhouse__desconto'], row['lanhouse__card_final_amount']),
        }
        for row in rows
    ]


def _valor_lanhouse(gross, desconto, card_final_amount):
    if card_final_amount is not None:
        return money(card_final_amount)
    return max(money(gross) - money(desconto), ZERO)


def _items_lanhouse_periodo(user, periodo):
    queryset = ItemsLanhouse.objects.filter(lanhouse__usuario=user)
    if periodo.all_data:
        return queryset
    return queryset.filter(lanhouse__data_criacao__date__range=(periodo.start, periodo.end))


def _normalizar_periodo_total(user, periodo):
    if not periodo.all_data:
        return periodo

    bounds = LanhouseModel.objects.filter(usuario=user).aggregate(
        start=Min('data_criacao'),
        end=Max('data_criacao'),
    )
    if not bounds['start'] or not bounds['end']:
        return PeriodoLanhouse('todas', 'Todo período', all_data=True)
    return PeriodoLanhouse(
        'todas',
        'Todo período',
        timezone.localtime(bounds['start']).date(),
        timezone.localtime(bounds['end']).date(),
    )


def _item_total_expression():
    return ExpressionWrapper(
        F('preco') * F('quantidade'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _day_buckets(start, end):
    buckets = []
    current = start
    while current <= end:
        buckets.append(current)
        current += timedelta(days=1)
    return buckets


def _month_buckets(start, end):
    buckets = []
    current = start.replace(day=1)
    end_month = end.replace(day=1)
    while current <= end_month:
        buckets.append(current)
        current = _next_month(current)
    return buckets


def _next_month(day):
    if day.month == 12:
        return day.replace(year=day.year + 1, month=1)
    return day.replace(month=day.month + 1)


def _as_date(value):
    if isinstance(value, datetime):
        return timezone.localtime(value).date()
    return value
