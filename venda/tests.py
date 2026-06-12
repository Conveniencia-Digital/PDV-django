from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cliente.models import Cliente
from colaborador.models import Colaborador
from despesa.models import Despesa
from financeiro.models import CardMachine, CardMachineFee
from produto.models import Produto
from venda.models import ItemsVenda, Vendas
from venda.services import build_vendas_dashboard, resolver_periodo_vendas


class VendasSelectorAndPaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendas-user', password='senha-teste')
        self.client.force_login(self.user)
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nome_cliente='Cliente Venda',
            telefone_contato='(67) 99999-3333',
        )
        self.vendedor = Colaborador.objects.create(
            usuario=self.user,
            nome_colaborador='Vendedor Venda',
            telefone_contato='(67) 98888-3333',
        )
        self.produto = Produto.objects.create(
            usuario=self.user,
            nome_produto='Cabo USB',
            categoria_produtos=Produto.CABOS,
            quantidade=10,
            codigo_de_barras=123456,
            preco_de_custo='5.00',
            preco='10.00',
        )
        self.machine = CardMachine.objects.create(usuario=self.user, name='Cielo')
        CardMachineFee.objects.create(
            card_machine=self.machine,
            payment_type=CardMachineFee.PAYMENT_DEBIT,
            installments=None,
            fee_percentage='2.00',
        )

    def test_formulario_cadastro_usa_seletores_compartilhados(self):
        response = self.client.get(reverse('cadastrar-vendas'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-clientes'))
        self.assertContains(response, 'hx-get="%s?picker=1"' % reverse('cadastrar-cliente'))
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-vendedores'))
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-produtos'))
        self.assertContains(response, 'data-price-target="[data-field=\'preco\']"', html=False)
        self.assertContains(response, 'data-card-payment-section')
        self.assertContains(response, 'selector-section-header')
        self.assertContains(response, 'Adicionar produto')
        self.assertContains(response, 'selector-row-action-spacer')
        self.assertContains(response, 'vendas-payment-summary')

    def test_formulario_edicao_usa_layout_padronizado_de_vendas(self):
        venda = self._criar_venda_com_item()

        response = self.client.get(reverse('editar-vendas', args=[venda.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dados da venda')
        self.assertContains(response, 'selector-section-header')
        self.assertContains(response, 'Adicionar produto')
        self.assertContains(response, 'selector-row-action-spacer')
        self.assertContains(response, 'vendas-payment-summary')
        self.assertContains(response, 'name="main-status"', html=False)

    def test_pagina_vendas_inclui_assets_e_modal_cliente(self):
        response = self.client.get(reverse('vendas'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'css/finance-dashboard.css')
        self.assertContains(response, 'css/client-picker.css')
        self.assertContains(response, 'js/finance-charts.js')
        self.assertContains(response, 'js/venda-dashboard.js')
        self.assertContains(response, 'js/client-picker.js')
        self.assertContains(response, 'js/card-fee-preview.js')
        self.assertContains(response, 'id="clientePickerModal"')
        self.assertContains(response, 'Receita de vendas')
        self.assertContains(response, 'Produtos mais vendidos')
        self.assertContains(response, 'vendasChartsData')

    def test_resolver_periodo_vendas_aceita_aliases(self):
        self.assertEqual(resolver_periodo_vendas({'periodo': 'hoje'}).key, 'hoje')
        self.assertEqual(resolver_periodo_vendas({'periodo': 'today'}).key, 'hoje')
        self.assertEqual(resolver_periodo_vendas({'periodo': 'current_month'}).key, 'este_mes')
        self.assertEqual(
            resolver_periodo_vendas({
                'periodo': 'custom',
                'data_inicio': '2026-06-10',
                'data_fim': '2026-06-01',
            }).start.isoformat(),
            '2026-06-01',
        )

    def _criar_venda_com_item(self, status=Vendas.ENTREGUE, **kwargs):
        venda = Vendas.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            vendedor=self.vendedor,
            forma_pagamento=kwargs.get('forma_pagamento', Vendas.PIX),
            desconto=kwargs.get('desconto', Decimal('0.00')),
            status=status,
            valor_entrada=kwargs.get('valor_entrada'),
            card_payment_type=kwargs.get('card_payment_type'),
            card_fee_amount=kwargs.get('card_fee_amount'),
            card_final_amount=kwargs.get('card_final_amount'),
            pass_card_fee_to_customer=kwargs.get('pass_card_fee_to_customer', False),
        )
        ItemsVenda.objects.create(
            vendas=venda,
            produto=self.produto,
            quantidade=kwargs.get('quantidade', 2),
            preco=kwargs.get('preco', Decimal('10.00')),
        )
        data = kwargs.get('data')
        if data:
            Vendas.objects.filter(pk=venda.pk).update(data_criacao=data)
            venda.refresh_from_db()
        return venda

    def test_dashboard_vendas_calcula_indicadores_pela_regra_de_negocio(self):
        data = timezone.make_aware(datetime(2026, 6, 5, 10, 0, 0))
        self._criar_venda_com_item(
            data=data,
            card_payment_type=CardMachineFee.PAYMENT_DEBIT,
            card_fee_amount=Decimal('1.00'),
            pass_card_fee_to_customer=False,
        )
        self._criar_venda_com_item(status=Vendas.CANCELADA, data=data, preco=Decimal('99.00'))

        dashboard = build_vendas_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(dashboard['total_vendas'], Decimal('20.00'))
        self.assertEqual(dashboard['custo_mercadoria_vendida'], Decimal('10.00'))
        self.assertEqual(dashboard['taxas_maquininha_absorvidas'], Decimal('1.00'))
        self.assertEqual(dashboard['lucro_total'], Decimal('9.00'))
        self.assertEqual(dashboard['qtd_vendas'], 1)
        self.assertEqual(dashboard['qtd_vendas_periodo'], 2)
        self.assertEqual(dashboard['qtd_vendas_canceladas'], 1)
        self.assertEqual(dashboard['quantidade_total_itens_vendidos'], 2)
        self.assertEqual(dashboard['vendas_product_ranking'][0]['product'], 'Cabo USB')
        self.assertEqual(dashboard['vendas_charts']['revenue']['values'][4], 20.0)

    def test_dashboard_vendas_calcula_fiado_a_receber(self):
        data = timezone.make_aware(datetime(2026, 6, 5, 10, 0, 0))
        self._criar_venda_com_item(
            data=data,
            forma_pagamento=Vendas.FIADO,
            valor_entrada=Decimal('5.00'),
        )

        dashboard = build_vendas_dashboard(self.user, {
            'inicio': '2026-06-05',
            'fim': '2026-06-05',
        })

        self.assertEqual(dashboard['total_vendas'], Decimal('20.00'))
        self.assertEqual(dashboard['total_vendas_a_receber'], Decimal('15.00'))

    def test_busca_produtos_filtra_por_usuario_e_termo(self):
        other_user = User.objects.create_user(username='outro-produto', password='senha-teste')
        Produto.objects.create(
            usuario=other_user,
            nome_produto='Cabo USB Outra Loja',
            categoria_produtos=Produto.CABOS,
            quantidade=10,
            codigo_de_barras=999,
            preco_de_custo='1.00',
            preco='99.00',
        )

        response = self.client.get(reverse('buscar-produtos'), {'q': 'cabo'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['id'], self.produto.pk)
        self.assertEqual(payload['results'][0]['price'], '10.00')

    def _submission_token(self):
        response = self.client.get(reverse('cadastrar-vendas'), HTTP_HX_REQUEST='true')
        return response.context['submission_token']

    def _venda_payload(self, token):
        return {
            'submission_token': token,
            'main-usuario': self.user.pk,
            'main-cliente': self.cliente.pk,
            'main-vendedor': self.vendedor.pk,
            'main-desconto': '0.00',
            'main-forma_pagamento': Vendas.CARTAO_DEBITO,
            'main-observacao': '',
            'main-status': Vendas.ENTREGUE,
            'main-data_vencimento': '',
            'main-qtd_parcela': '',
            'main-valor_entrada': '',
            'main-card_machine': self.machine.pk,
            'main-card_installments': '',
            'main-card_payment_type': 'credit',
            'main-card_fee_percentage': '99.99',
            'main-card_fee_amount': '99.99',
            'main-card_base_amount': '99.99',
            'main-card_final_amount': '99.99',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-vendas': '',
            'items-0-id': '',
            'items-0-produto': self.produto.pk,
            'items-0-quantidade': '2',
            'items-0-preco': '10.00',
        }

    def test_venda_cartao_debito_absorvido_cria_despesa_taxa(self):
        token = self._submission_token()

        response = self.client.post(
            reverse('cadastrar-vendas'),
            self._venda_payload(token),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertContains(response, 'vendasChartsData')
        venda = Vendas.objects.get()
        self.assertEqual(venda.card_payment_type, CardMachineFee.PAYMENT_DEBIT)
        self.assertEqual(venda.card_fee_percentage, Decimal('2.00'))
        self.assertEqual(venda.card_fee_amount, Decimal('0.40'))
        self.assertEqual(venda.card_base_amount, Decimal('20.00'))
        self.assertEqual(venda.card_final_amount, Decimal('20.00'))
        self.assertEqual(venda.total(), Decimal('20.00'))

        despesa = Despesa.objects.get(venda_card_fee=venda)
        self.assertEqual(despesa.preco_despesa, Decimal('0.40'))

    def test_token_impede_reenvio_duplicado_da_venda(self):
        token = self._submission_token()
        payload = self._venda_payload(token)

        first = self.client.post(reverse('cadastrar-vendas'), payload, HTTP_HX_REQUEST='true')
        second = self.client.post(reverse('cadastrar-vendas'), payload, HTTP_HX_REQUEST='true')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(Vendas.objects.count(), 1)

    def _venda_edit_payload(self, venda, item, quantidade='8'):
        return {
            'main-usuario': self.user.pk,
            'main-cliente': self.cliente.pk,
            'main-vendedor': self.vendedor.pk,
            'main-desconto': '0.00',
            'main-forma_pagamento': Vendas.PIX,
            'main-observacao': '',
            'main-status': Vendas.ENTREGUE,
            'main-data_vencimento': '',
            'main-qtd_parcela': '',
            'main-valor_entrada': '',
            'main-card_machine': '',
            'main-card_installments': '',
            'main-card_payment_type': '',
            'main-card_fee_percentage': '',
            'main-card_fee_amount': '',
            'main-card_base_amount': '',
            'main-card_final_amount': '',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '1',
            'items-MIN_NUM_FORMS': '1',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-vendas': venda.pk,
            'items-0-id': item.pk,
            'items-0-produto': self.produto.pk,
            'items-0-quantidade': quantidade,
            'items-0-preco': '10.00',
        }

    def test_editar_venda_atualiza_dashboard_sem_duplicar_linha_e_estoque(self):
        venda = Vendas.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            vendedor=self.vendedor,
            forma_pagamento=Vendas.PIX,
            desconto=Decimal('0.00'),
            status=Vendas.ENTREGUE,
        )
        item = ItemsVenda.objects.create(
            vendas=venda,
            produto=self.produto,
            quantidade=10,
            preco=Decimal('10.00'),
        )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 0)

        response = self.client.post(
            reverse('editar-vendas', args=[venda.pk]),
            self._venda_edit_payload(venda, item, quantidade='8'),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertEqual(Vendas.objects.count(), 1)
        item.refresh_from_db()
        self.assertEqual(item.quantidade, 8)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 2)

    def test_pagina_vendas_exibe_acao_de_apagar(self):
        venda = self._criar_venda_com_item()

        response = self.client.get(reverse('vendas'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'hx-post="%s"' % reverse('apagar-vendas', args=[venda.pk]))
        self.assertContains(response, 'Deseja mesmo apagar esta venda?')

    def test_apagar_venda_remove_registro_atualiza_dashboard_e_restaura_estoque(self):
        venda = Vendas.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            vendedor=self.vendedor,
            forma_pagamento=Vendas.PIX,
            desconto=Decimal('0.00'),
            status=Vendas.ENTREGUE,
        )
        ItemsVenda.objects.create(
            vendas=venda,
            produto=self.produto,
            quantidade=3,
            preco=Decimal('10.00'),
        )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 7)

        response = self.client.post(
            reverse('apagar-vendas', args=[venda.pk]),
            {'dashboard_periodo': 'hoje'},
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertEqual(Vendas.objects.count(), 0)
        self.assertEqual(ItemsVenda.objects.count(), 0)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 10)
