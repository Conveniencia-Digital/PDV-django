from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cliente.models import Cliente
from colaborador.models import Colaborador
from despesa.models import Despesa
from lanhouse.models import ItemsLanhouse, LanhouseModel, LanhouseServico
from orcamento.models import ItemsOrcamento, Orcamento, Servico
from peca.models import Pecas
from produto.models import Produto
from relatorio.services import build_profitability_report, resolve_report_period
from venda.models import ItemsVenda, Vendas


class RelatorioRentabilidadeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='relatorio-user', password='senha-teste')
        self.client.force_login(self.user)
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nome_cliente='Cliente teste',
            telefone_contato='67999999999',
        )
        self.vendedor = Colaborador.objects.create(
            usuario=self.user,
            nome_colaborador='Vendedor teste',
            telefone_contato='67988888888',
        )

    def _create_sale(self):
        produto = Produto.objects.create(
            usuario=self.user,
            nome_produto='Produto margem',
            quantidade=10,
            preco_de_custo=Decimal('600.00'),
            preco=Decimal('1000.00'),
            forma_pagamento=Produto.PIX,
        )
        venda = Vendas.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            vendedor=self.vendedor,
            desconto=Decimal('0.00'),
            forma_pagamento=Vendas.PIX,
            status=Vendas.ENTREGUE,
        )
        ItemsVenda.objects.create(
            vendas=venda,
            produto=produto,
            quantidade=1,
            preco=Decimal('1000.00'),
        )
        Vendas.objects.filter(pk=venda.pk).update(
            data_criacao=timezone.make_aware(datetime(2026, 6, 5, 10, 0, 0))
        )
        return venda

    def _create_fixed_expense(self):
        despesa = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Aluguel fixo',
            preco_despesa=Decimal('200.00'),
            forma_pagamento=Despesa.PIX,
            despesa_fixa=True,
            dia_vencimento_fixo=5,
        )
        Despesa.objects.filter(pk=despesa.pk).update(
            data_cadastro=timezone.make_aware(datetime(2026, 6, 1, 8, 0, 0))
        )
        return despesa

    def _set_created_at(self, model, pk, field_name='data_criacao'):
        model.objects.filter(pk=pk).update(
            **{field_name: timezone.make_aware(datetime(2026, 6, 5, 10, 0, 0))}
        )

    def test_calcula_margem_ponto_de_equilibrio_e_projecoes(self):
        self._create_sale()
        self._create_fixed_expense()

        report = build_profitability_report(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-05',
            'data_fim': '2026-06-05',
        })

        summary = report['summary']
        self.assertEqual(summary['revenue'], Decimal('1000.00'))
        self.assertEqual(summary['variable_costs'], Decimal('600.00'))
        self.assertEqual(summary['contribution_margin'], Decimal('400.00'))
        self.assertEqual(summary['contribution_margin_percent'], Decimal('40.00'))
        self.assertEqual(summary['fixed_expenses'], Decimal('200.00'))
        self.assertEqual(summary['operating_result'], Decimal('200.00'))
        self.assertEqual(summary['profit_margin_percent'], Decimal('20.00'))
        self.assertEqual(summary['break_even_revenue'], Decimal('500.00'))
        self.assertTrue(summary['break_even_reached'])
        self.assertEqual(report['projection_rows'][1]['amount'], Decimal('7000.00'))
        self.assertEqual(report['source_rows'][0]['source'], 'Vendas')

    def test_pagina_renderiza_indicadores_e_moeda_brasileira(self):
        self._create_sale()
        self._create_fixed_expense()

        response = self.client.get(reverse('relatorio'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-05',
            'data_fim': '2026-06-05',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ponto de equilíbrio')
        self.assertContains(response, 'Margem de contribuição')
        self.assertContains(response, 'Projeção de faturamento')
        self.assertContains(response, 'R$ 1.000,00')
        self.assertContains(response, 'R$ 500,00')
        self.assertContains(response, '40,00%')

    def test_periodo_customizado_inverte_datas_quando_necessario(self):
        period = resolve_report_period({
            'periodo': 'custom',
            'data_inicio': '2026-06-10',
            'data_fim': '2026-06-05',
        })

        self.assertEqual(period.key, 'personalizado')
        self.assertEqual(period.start.isoformat(), '2026-06-05')
        self.assertEqual(period.end.isoformat(), '2026-06-10')

    def test_calcula_contas_a_pagar_receber_e_diferenca_por_categoria(self):
        peca = Pecas.objects.create(
            usuario=self.user,
            nome_peca='Tela fiada',
            quantidade=3,
            preco_de_custo=Decimal('20.00'),
            preco_peca=Decimal('80.00'),
            forma_pagamento=Pecas.FIADO,
            valor_entrada=Decimal('10.00'),
        )
        self._set_created_at(Pecas, peca.pk)
        produto_pagar = Produto.objects.create(
            usuario=self.user,
            nome_produto='Produto fiado',
            quantidade=2,
            preco_de_custo=Decimal('30.00'),
            preco=Decimal('90.00'),
            forma_pagamento=Produto.FIADO,
            valor_entrada=Decimal('15.00'),
        )
        self._set_created_at(Produto, produto_pagar.pk)
        despesa = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Despesa fiada',
            preco_despesa=Decimal('120.00'),
            forma_pagamento=Despesa.FIADO,
            valor_entrada=Decimal('20.00'),
        )
        self._set_created_at(Despesa, despesa.pk, 'data_cadastro')

        produto_venda = Produto.objects.create(
            usuario=self.user,
            nome_produto='Produto vendido',
            quantidade=5,
            preco_de_custo=Decimal('80.00'),
            preco=Decimal('200.00'),
            forma_pagamento=Produto.PIX,
        )
        venda = Vendas.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            vendedor=self.vendedor,
            desconto=Decimal('0.00'),
            forma_pagamento=Vendas.FIADO,
            valor_entrada=Decimal('50.00'),
            status=Vendas.ENTREGUE,
        )
        ItemsVenda.objects.create(
            vendas=venda,
            produto=produto_venda,
            quantidade=1,
            preco=Decimal('200.00'),
        )
        self._set_created_at(Vendas, venda.pk)

        servico = Servico.objects.create(usuario=self.user, servico='Reparo')
        orcamento = Orcamento.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            tecnico=self.vendedor,
            celular='Aparelho teste',
            status=Orcamento.FINALIZADO,
            desconto=Decimal('0.00'),
            forma_pagamento=Orcamento.FIADO,
            valor_entrada=Decimal('100.00'),
        )
        ItemsOrcamento.objects.create(
            orcamento=orcamento,
            servico=servico,
            quantidade=1,
            preco_orcamento=Decimal('300.00'),
        )
        self._set_created_at(Orcamento, orcamento.pk)

        lanhouse_servico = LanhouseServico.objects.create(
            usuario=self.user,
            servico='Impressão',
            preco_custo=Decimal('10.00'),
            preco=Decimal('80.00'),
        )
        lanhouse = LanhouseModel.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            vendedor=self.vendedor,
            desconto=Decimal('10.00'),
            forma_pagamento=LanhouseModel.FIADO,
            valor_entrada=Decimal('60.00'),
        )
        ItemsLanhouse.objects.create(
            lanhouse=lanhouse,
            servico=lanhouse_servico,
            quantidade=2,
            preco=Decimal('80.00'),
        )
        self._set_created_at(LanhouseModel, lanhouse.pk)

        report = build_profitability_report(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-05',
            'data_fim': '2026-06-05',
        })

        accounts = report['accounts']
        self.assertEqual(accounts['payable_total'], Decimal('195.00'))
        self.assertEqual(accounts['receivable_total'], Decimal('440.00'))
        self.assertEqual(accounts['difference'], Decimal('245.00'))
        self.assertEqual(accounts['payable_count'], 3)
        self.assertEqual(accounts['receivable_count'], 3)
        self.assertEqual(
            {row['category']: row['amount'] for row in accounts['payable_rows']},
            {
                'Peças': Decimal('50.00'),
                'Produtos': Decimal('45.00'),
                'Despesas': Decimal('100.00'),
            },
        )
        self.assertEqual(
            {row['category']: row['amount'] for row in accounts['receivable_rows']},
            {
                'Assistência técnica': Decimal('200.00'),
                'Vendas': Decimal('150.00'),
                'Lanhouse': Decimal('90.00'),
            },
        )

        response = self.client.get(reverse('relatorio'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-05',
            'data_fim': '2026-06-05',
        })

        self.assertContains(response, 'Contas a pagar e receber')
        self.assertContains(response, 'Contas a pagar por categoria')
        self.assertContains(response, 'Contas a receber por categoria')
        self.assertContains(response, 'R$ 195,00')
        self.assertContains(response, 'R$ 440,00')
        self.assertContains(response, 'R$ 245,00')
