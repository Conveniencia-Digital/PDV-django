from datetime import date, datetime
from decimal import Decimal

from django.http import QueryDict
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from cliente.models import Cliente
from colaborador.models import Colaborador
from despesa.models import Despesa
from financeiro.cash_closing import calculate_cash_closing_snapshot, create_cash_closing
from financeiro.forms import CardMachineFeeTableForm
from financeiro.models import (
    CardMachine,
    CardMachineFee,
    CategoriaLancamentoFinanceiro,
    FechamentoCaixa,
    LancamentoFinanceiro,
)
from financeiro.services import (
    FIADO_PAGAR,
    FIADO_RECEBER,
    _cash_impact,
    build_financial_dashboard,
    growth_percent,
    resolve_period,
)
from produto.models import Produto
from venda.models import ItemsVenda, Vendas


class FinancialServiceTests(SimpleTestCase):
    def test_custom_period_accepts_reversed_dates(self):
        period = resolve_period(QueryDict("periodo=custom&data_inicio=2026-06-10&data_fim=2026-06-01"))

        self.assertEqual(period.start.isoformat(), "2026-06-01")
        self.assertEqual(period.end.isoformat(), "2026-06-10")
        self.assertEqual(period.days, 10)

    def test_periods_accept_despesa_style_and_legacy_aliases(self):
        self.assertEqual(resolve_period(QueryDict("periodo=hoje")).key, "hoje")
        self.assertEqual(resolve_period(QueryDict("periodo=ontem")).key, "ontem")
        self.assertEqual(resolve_period(QueryDict("periodo=7dias")).key, "7dias")
        self.assertEqual(resolve_period(QueryDict("periodo=este_mes")).key, "este_mes")
        self.assertEqual(resolve_period(QueryDict("periodo=mes_passado")).key, "mes_passado")
        self.assertEqual(resolve_period(QueryDict("periodo=este_ano")).key, "este_ano")
        self.assertEqual(resolve_period(QueryDict("periodo=todas")).key, "todas")
        self.assertEqual(resolve_period(QueryDict("periodo=today")).key, "hoje")
        self.assertEqual(resolve_period(QueryDict("periodo=current_month")).key, "este_mes")
        self.assertEqual(resolve_period(QueryDict("inicio=2026-06-01&fim=2026-06-10")).key, "personalizado")

    def test_growth_percent_handles_zero_previous_period(self):
        self.assertEqual(growth_percent(Decimal("100.00"), Decimal("0.00")), Decimal("100.00"))
        self.assertEqual(growth_percent(Decimal("0.00"), Decimal("0.00")), Decimal("0.00"))

    def test_cash_impact_counts_only_entry_for_credit_transactions(self):
        self.assertEqual(_cash_impact(Decimal("150.00"), FIADO_RECEBER, Decimal("40.00"), FIADO_RECEBER), Decimal("40.00"))
        self.assertEqual(_cash_impact(Decimal("150.00"), FIADO_PAGAR, Decimal("60.00"), FIADO_PAGAR), Decimal("60.00"))
        self.assertEqual(_cash_impact(Decimal("150.00"), "Pix", None, FIADO_RECEBER), Decimal("150.00"))


class FinancialDashboardFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="financeiro-dashboard-user", password="senha-teste")
        self.client.force_login(self.user)

    def test_dashboard_uses_despesa_filter_visual_pattern(self):
        response = self.client.get(reverse("dashboard-financeiro"), {"periodo": "este_mes"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="inicio"')
        self.assertContains(response, 'name="fim"')
        self.assertContains(response, 'value="hoje"')
        self.assertContains(response, 'value="ontem"')
        self.assertContains(response, 'value="7dias"')
        self.assertContains(response, 'value="este_mes"')
        self.assertContains(response, 'value="mes_passado"')
        self.assertContains(response, 'value="este_ano"')
        self.assertContains(response, 'value="todas"')
        self.assertContains(response, 'Limpar')
        self.assertContains(response, 'btn-periodo-ativo')
        self.assertNotContains(response, '<select class="form-control" id="periodo" name="periodo">')

    def test_dashboard_custom_range_uses_inicio_e_fim(self):
        response = self.client.get(reverse("dashboard-financeiro"), {
            "inicio": "2026-06-01",
            "fim": "2026-06-10",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="2026-06-01"')
        self.assertContains(response, 'value="2026-06-10"')

    def test_dashboard_todas_uses_real_data_range(self):
        first = Despesa.objects.create(
            usuario=self.user,
            nome_despesa="Despesa antiga",
            preco_despesa="50.00",
            forma_pagamento=Despesa.PIX,
        )
        last = Despesa.objects.create(
            usuario=self.user,
            nome_despesa="Despesa nova",
            preco_despesa="70.00",
            forma_pagamento=Despesa.PIX,
        )
        Despesa.objects.filter(pk=first.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 1, 10, 8, 0, 0)))
        Despesa.objects.filter(pk=last.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 6, 10, 8, 0, 0)))

        dashboard = build_financial_dashboard(self.user, {"periodo": "todas"})

        self.assertEqual(dashboard["period"].key, "todas")
        self.assertEqual(dashboard["period"].start.isoformat(), "2026-01-10")
        self.assertEqual(dashboard["period"].end.isoformat(), "2026-06-10")
        self.assertEqual(dashboard["summary"]["selected"]["expenses"], Decimal("120.00"))


class CardMachineFeeTableFormTests(TestCase):
    def test_save_creates_machine_with_debit_and_credit_installment_fees(self):
        user = User.objects.create_user(username="financeiro-user", password="senha-teste")
        data = {
            "name": "InfinitePay",
            "is_active": "on",
            "debit_fee": "1.00",
        }
        for installment in range(1, 13):
            data[f"credit_{installment}_fee"] = str(installment)

        form = CardMachineFeeTableForm(data=data, user=user)

        self.assertTrue(form.is_valid(), form.errors)
        machine = form.save(user)
        self.assertEqual(machine.name, "InfinitePay")
        self.assertEqual(CardMachine.objects.count(), 1)
        self.assertEqual(CardMachineFee.objects.filter(card_machine=machine).count(), 13)
        self.assertEqual(
            CardMachineFee.objects.get(card_machine=machine, payment_type=CardMachineFee.PAYMENT_DEBIT).fee_percentage,
            Decimal("1.00"),
        )
        self.assertEqual(
            CardMachineFee.objects.get(
                card_machine=machine,
                payment_type=CardMachineFee.PAYMENT_CREDIT,
                installments=12,
            ).fee_percentage,
            Decimal("12.00"),
        )


class CashClosingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="caixa-user", password="senha-teste")
        self.client.force_login(self.user)
        self.client_model = Cliente.objects.create(
            usuario=self.user,
            nome_cliente="Cliente caixa",
            telefone_contato="67999990000",
        )
        self.seller = Colaborador.objects.create(
            usuario=self.user,
            nome_colaborador="Vendedor caixa",
            telefone_contato="67999990001",
        )
        self.product = Produto.objects.create(
            usuario=self.user,
            nome_produto="Produto caixa",
            quantidade=10,
            preco_de_custo=Decimal("20.00"),
            margem_de_lucro=Decimal("50.00"),
            preco=Decimal("100.00"),
            forma_pagamento="Pix",
        )
        Produto.objects.filter(pk=self.product.pk).update(
            data_criacao=timezone.make_aware(datetime(2026, 6, 1, 9, 0, 0))
        )
        self.closing_date = date(2026, 6, 11)

    def _sale_for_closing_date(self, amount=Decimal("100.00")):
        venda = Vendas.objects.create(
            usuario=self.user,
            cliente=self.client_model,
            vendedor=self.seller,
            desconto=Decimal("0.00"),
            forma_pagamento=Vendas.PIX,
            status=Vendas.ENTREGUE,
        )
        ItemsVenda.objects.create(vendas=venda, produto=self.product, quantidade=1, preco=amount)
        Vendas.objects.filter(pk=venda.pk).update(
            data_criacao=timezone.make_aware(datetime(2026, 6, 11, 10, 0, 0))
        )
        return venda

    def _expense_for_closing_date(self, amount=Decimal("30.00")):
        despesa = Despesa.objects.create(
            usuario=self.user,
            nome_despesa="Despesa caixa",
            preco_despesa=amount,
            forma_pagamento=Despesa.PIX,
        )
        Despesa.objects.filter(pk=despesa.pk).update(
            data_cadastro=timezone.make_aware(datetime(2026, 6, 11, 12, 0, 0))
        )
        return despesa

    def test_snapshot_usa_venda_despesa_e_saldo_de_abertura(self):
        FechamentoCaixa.objects.create(
            usuario=self.user,
            data=date(2026, 6, 10),
            saldo_abertura=Decimal("0.00"),
            total_receitas=Decimal("0.00"),
            total_despesas=Decimal("0.00"),
            saldo_esperado=Decimal("50.00"),
            valor_contado=Decimal("50.00"),
            diferenca=Decimal("0.00"),
            status=FechamentoCaixa.BALANCEADO,
        )
        self._sale_for_closing_date()
        self._expense_for_closing_date()

        snapshot = calculate_cash_closing_snapshot(self.user, self.closing_date)

        self.assertEqual(snapshot.opening_balance, Decimal("50.00"))
        self.assertEqual(snapshot.revenue, Decimal("100.00"))
        self.assertEqual(snapshot.expenses, Decimal("30.00"))
        self.assertEqual(snapshot.expected_balance, Decimal("120.00"))

    def test_fechamento_balanceado_nao_cria_ajuste(self):
        self._sale_for_closing_date()
        self._expense_for_closing_date()

        closing = create_cash_closing(self.user, self.closing_date, Decimal("70.00"))

        self.assertEqual(closing.status, FechamentoCaixa.BALANCEADO)
        self.assertEqual(closing.diferenca, Decimal("0.00"))
        self.assertEqual(LancamentoFinanceiro.objects.count(), 0)
        self.assertFalse(Despesa.objects.filter(nome_despesa__icontains="Falta de Caixa").exists())

    def test_sobra_de_caixa_cria_lancamento_financeiro_de_receita(self):
        self._sale_for_closing_date()
        self._expense_for_closing_date()

        closing = create_cash_closing(self.user, self.closing_date, Decimal("90.00"))

        self.assertEqual(closing.status, FechamentoCaixa.SOBRA)
        self.assertEqual(closing.diferenca, Decimal("20.00"))
        entry = LancamentoFinanceiro.objects.get()
        self.assertEqual(entry.tipo, LancamentoFinanceiro.RECEITA)
        self.assertEqual(entry.categoria.nome, "Sobra de Caixa")
        self.assertEqual(entry.valor, Decimal("20.00"))

        dashboard = build_financial_dashboard(self.user, {
            "periodo": "custom",
            "data_inicio": "2026-06-11",
            "data_fim": "2026-06-11",
        })
        self.assertEqual(dashboard["summary"]["selected"]["revenue"], Decimal("120.00"))

    def test_falta_de_caixa_cria_despesa_automatica(self):
        self._sale_for_closing_date()
        self._expense_for_closing_date()

        closing = create_cash_closing(self.user, self.closing_date, Decimal("55.00"))

        self.assertEqual(closing.status, FechamentoCaixa.FALTA)
        self.assertEqual(closing.diferenca, Decimal("-15.00"))
        shortage = Despesa.objects.get(nome_despesa__startswith="Falta de Caixa")
        self.assertEqual(shortage.preco_despesa, Decimal("15.00"))
        self.assertEqual(shortage.categoria_despesa.nome_categoria_despesa, "Falta de Caixa")

        dashboard = build_financial_dashboard(self.user, {
            "periodo": "custom",
            "data_inicio": "2026-06-11",
            "data_fim": "2026-06-11",
        })
        self.assertEqual(dashboard["summary"]["selected"]["expenses"], Decimal("45.00"))

    def test_bloqueia_fechamento_duplicado_exceto_quando_permitido(self):
        self._sale_for_closing_date()
        create_cash_closing(self.user, self.closing_date, Decimal("100.00"))

        with self.assertRaises(ValueError):
            create_cash_closing(self.user, self.closing_date, Decimal("100.00"))

        create_cash_closing(self.user, self.closing_date, Decimal("100.00"), allow_duplicate=True)

        self.assertEqual(FechamentoCaixa.objects.filter(usuario=self.user, data=self.closing_date).count(), 2)

    def test_pagina_exibe_cards_formulario_e_historico_filtrado(self):
        create_cash_closing(self.user, self.closing_date, Decimal("0.00"), allow_duplicate=True)
        response = self.client.get(reverse("fechamento-caixa"), {
            "periodo": "custom",
            "data_inicio": "2026-06-11",
            "data_fim": "2026-06-11",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saldo esperado hoje")
        self.assertContains(response, "Valor contado")
        self.assertContains(response, "Histórico de fechamentos")
        self.assertContains(response, "11/06/2026")
