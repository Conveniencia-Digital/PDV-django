import json
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from cliente.models import Cliente
from colaborador.models import Colaborador
from despesa.models import Despesa
from financeiro.models import CardMachine, CardMachineFee
from lanhouse.models import ItemsLanhouse, LanhouseModel, LanhouseServico
from lanhouse.periodo import build_lanhouse_dashboard_charts, metricas_lanhouse


class LanhouseClientPickerTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='lanhouse-user', password='senha-teste')
        self.client.force_login(self.user)
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nome_cliente='Cliente Lanhouse',
            telefone_contato='(67) 99999-0000',
        )
        self.vendedor = Colaborador.objects.create(
            usuario=self.user,
            nome_colaborador='Vendedor',
            telefone_contato='(67) 98888-0000',
        )
        self.servico = LanhouseServico.objects.create(
            usuario=self.user,
            servico='Impressao colorida',
            preco_custo='1.00',
            preco='5.50',
        )
        self.machine = CardMachine.objects.create(usuario=self.user, name='Stone')
        CardMachineFee.objects.create(
            card_machine=self.machine,
            payment_type=CardMachineFee.PAYMENT_DEBIT,
            installments=None,
            fee_percentage='1.00',
        )
        CardMachineFee.objects.create(
            card_machine=self.machine,
            payment_type=CardMachineFee.PAYMENT_CREDIT,
            installments=12,
            fee_percentage='12.00',
        )

    def test_formulario_cadastro_usa_seletor_cliente_compartilhado(self):
        response = self.client.get(reverse('cadastrar-lanhouse'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-client-picker')
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-clientes'))
        self.assertContains(response, 'hx-get="%s?picker=1"' % reverse('cadastrar-cliente'))
        self.assertContains(response, 'data-client-picker-native="true"')
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-vendedores'))
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-servicos-lanhouse'))
        self.assertContains(response, 'Create New Service')
        self.assertContains(response, 'data-price-target="[data-field=\'preco\']"', html=False)
        self.assertContains(response, 'data-card-payment-section')
        self.assertContains(response, 'Máquina de cartão')
        self.assertContains(response, 'class="row g-3 lanhouse-fiado-row" hidden')

    def test_pagina_lanhouse_inclui_assets_e_modal_cliente(self):
        response = self.client.get(reverse('lanhouse'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'css/finance-dashboard.css')
        self.assertContains(response, 'css/client-picker.css')
        self.assertContains(response, 'js/client-picker.js')
        self.assertContains(response, 'js/pricing-margin.js')
        self.assertContains(response, 'js/finance-charts.js')
        self.assertContains(response, 'js/lanhouse-dashboard.js')
        self.assertContains(response, 'id="clientePickerModal"')
        self.assertContains(response, 'id="lanhouseServicoPickerModal"')
        self.assertContains(response, 'Receita líquida')
        self.assertContains(response, 'Custo de serviços')
        self.assertContains(response, 'Lucro líquido')
        self.assertContains(response, 'Ticket médio por atendimento')
        self.assertContains(response, 'Quantidade total de serviços')
        self.assertContains(response, 'Clientes atendidos')
        self.assertContains(response, 'Receita Lan House')
        self.assertContains(response, 'Serviços mais realizados')
        self.assertContains(response, 'Nenhuma receita de Lan House no período.')
        self.assertContains(response, 'Nenhum serviço realizado no período.')
        self.assertContains(response, 'href="%s"' % reverse('lanhouse'))
        self.assertContains(response, 'hx-get="%s"' % reverse('lanhouse'))
        self.assertContains(response, 'hx-target="#bloco-dados"')
        self.assertContains(response, 'hx-swap="outerHTML"')
        self.assertNotContains(response, 'hx-get="%s"' % reverse('relatorio-lanhouse'))

    def test_modal_sucesso_lanhouse_fecha_atualizando_bloco_principal(self):
        self._criar_venda_lanhouse(quantidade=2, preco='5.00')

        response = self.client.get(reverse('lanhouse'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="bloco-dados"')
        self.assertContains(response, 'id="cards-relatorio"')
        self.assertContains(response, 'id="lanhouse-Tbody"')
        self.assertContains(response, 'Receita Lan House')
        self.assertNotContains(response, '<html')

    def test_formulario_servico_exibe_margem_e_calculadora_compartilhada(self):
        response = self.client.get(reverse('cadastrar-servico-lanhouse'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Margem de lucro (%)')
        self.assertContains(response, 'data-profit-margin-calculator')
        self.assertContains(response, 'data-pricing-field="cost"')
        self.assertContains(response, 'data-pricing-field="margin"')
        self.assertContains(response, 'data-pricing-field="price"')
        self.assertContains(response, 'name="pricing_last_edited"')

    def test_busca_servicos_lanhouse_filtra_por_usuario_e_termo(self):
        other_user = User.objects.create_user(username='outro-lanhouse', password='senha-teste')
        LanhouseServico.objects.create(
            usuario=other_user,
            servico='Impressao de outra loja',
            preco_custo='1.00',
            preco='99.00',
        )

        response = self.client.get(reverse('buscar-servicos-lanhouse'), {'q': 'impressao'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['id'], self.servico.pk)
        self.assertEqual(payload['results'][0]['price'], '5.50')

    def test_busca_vendedores_filtra_por_usuario_e_termo(self):
        other_user = User.objects.create_user(username='outro-vendedor', password='senha-teste')
        Colaborador.objects.create(
            usuario=other_user,
            nome_colaborador='Vendedor Outra Loja',
            telefone_contato='(67) 90000-0000',
        )

        response = self.client.get(reverse('buscar-vendedores'), {'q': 'vendedor'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['name'], 'Vendedor')
        self.assertEqual(payload['results'][0]['phone'], '(67) 98888-0000')

    def test_cadastro_servico_picker_retorna_evento_para_auto_selecao(self):
        response = self.client.post(
            reverse('cadastrar-servico-lanhouse') + '?picker=1',
            {
                'service_picker': '1',
                'usuario': self.user.pk,
                'servico': 'Scanner rapido',
                'preco_custo': '2.00',
                'preco': '8.00',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        servico = LanhouseServico.objects.get(servico='Scanner rapido')
        trigger = json.loads(response['HX-Trigger'])
        self.assertEqual(trigger['lanhouseServicoCriado']['id'], servico.pk)
        self.assertEqual(trigger['lanhouseServicoCriado']['text'], servico.servico)
        self.assertEqual(trigger['lanhouseServicoCriado']['price'], '8.00')

    def test_cadastro_servico_picker_invalido_mantem_formulario_no_modal(self):
        response = self.client.post(
            reverse('cadastrar-servico-lanhouse') + '?picker=1',
            {
                'service_picker': '1',
                'usuario': self.user.pk,
                'servico': '',
                'preco_custo': '',
                'preco': '',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('HX-Trigger', response)
        self.assertContains(response, 'data-service-picker-form="true"')
        self.assertContains(response, 'name="service_picker"')

    def test_cadastro_servico_calcula_preco_por_custo_e_margem(self):
        response = self.client.post(
            reverse('cadastrar-servico-lanhouse') + '?picker=1',
            {
                'service_picker': '1',
                'usuario': self.user.pk,
                'servico': 'Encadernacao',
                'preco_custo': '10.00',
                'margem_de_lucro': '50.00',
                'preco': '',
                'pricing_last_edited': 'margin',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        servico = LanhouseServico.objects.get(servico='Encadernacao')
        self.assertEqual(servico.preco, Decimal('20.00'))
        self.assertEqual(servico.margem_de_lucro, Decimal('50.00'))

    def test_cadastro_servico_calcula_margem_por_custo_e_preco(self):
        response = self.client.post(
            reverse('cadastrar-servico-lanhouse') + '?picker=1',
            {
                'service_picker': '1',
                'usuario': self.user.pk,
                'servico': 'Impressao A3',
                'preco_custo': '10.00',
                'margem_de_lucro': '',
                'preco': '15.00',
                'pricing_last_edited': 'price',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        servico = LanhouseServico.objects.get(servico='Impressao A3')
        self.assertEqual(servico.preco, Decimal('15.00'))
        self.assertEqual(servico.margem_de_lucro, Decimal('33.33'))

    def test_cadastro_servico_rejeita_margem_maior_ou_igual_a_100(self):
        response = self.client.post(
            reverse('cadastrar-servico-lanhouse'),
            {
                'usuario': self.user.pk,
                'servico': 'Servico invalido',
                'preco_custo': '10.00',
                'margem_de_lucro': '100.00',
                'preco': '',
                'pricing_last_edited': 'margin',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(LanhouseServico.objects.filter(servico='Servico invalido').exists())
        self.assertContains(response, 'A margem de lucro deve ser menor que 100%.')

    def _criar_venda_lanhouse(
        self,
        servico=None,
        quantidade=1,
        preco='5.00',
        desconto='0.00',
        created_at=None,
        cliente=None,
        card_final_amount=None,
        pass_card_fee=False,
        card_fee_amount=None,
    ):
        venda = LanhouseModel.objects.create(
            usuario=self.user,
            cliente=cliente or self.cliente,
            vendedor=self.vendedor,
            desconto=desconto,
            forma_pagamento=LanhouseModel.PIX,
            card_machine=self.machine if card_final_amount is not None else None,
            card_payment_type=CardMachineFee.PAYMENT_CREDIT if card_final_amount is not None else None,
            card_fee_amount=card_fee_amount,
            card_base_amount=None,
            card_final_amount=card_final_amount,
            pass_card_fee_to_customer=pass_card_fee,
        )
        ItemsLanhouse.objects.create(
            lanhouse=venda,
            servico=servico or self.servico,
            quantidade=quantidade,
            preco=preco,
        )
        if created_at:
            LanhouseModel.objects.filter(pk=venda.pk).update(data_criacao=created_at)
            venda.refresh_from_db()
        return venda

    def test_metricas_lanhouse_sem_registros_zeram_kpis_novos(self):
        metricas = metricas_lanhouse(LanhouseModel.objects.none())

        self.assertEqual(metricas['ticket_medio_atendimento'], Decimal('0.00'))
        self.assertEqual(metricas['quantidade_total_servicos'], 0)
        self.assertEqual(metricas['quantidade_total_clientes_atendidos'], 0)

    def test_metricas_lanhouse_calculam_ticket_servicos_e_clientes_distintos(self):
        outro_cliente = Cliente.objects.create(
            usuario=self.user,
            nome_cliente='Outro Cliente',
            telefone_contato='(67) 97777-0000',
        )
        self._criar_venda_lanhouse(quantidade=2, preco='10.00')
        self._criar_venda_lanhouse(quantidade=3, preco='5.00')
        self._criar_venda_lanhouse(quantidade=1, preco='15.00', cliente=outro_cliente)

        metricas = metricas_lanhouse(LanhouseModel.objects.filter(usuario=self.user))

        self.assertEqual(metricas['total_lanhouse'], Decimal('50.00'))
        self.assertEqual(metricas['qtd_lanhouse'], 3)
        self.assertEqual(metricas['ticket_medio_atendimento'], Decimal('16.67'))
        self.assertEqual(metricas['quantidade_total_servicos'], 6)
        self.assertEqual(metricas['quantidade_total_clientes_atendidos'], 2)

    def test_tabela_lanhouse_mostra_valor_total_no_lugar_de_status(self):
        self._criar_venda_lanhouse(quantidade=2, preco='5.50', desconto='1.00')

        response = self.client.get(reverse('lanhouse'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Valor Total')
        self.assertNotContains(response, '<th>Status</th>', html=True)
        self.assertContains(response, 'R$ 10,00')

    def test_tabela_lanhouse_valor_total_usa_taxa_repassada_ao_cliente(self):
        self._criar_venda_lanhouse(
            quantidade=2,
            preco='5.50',
            card_final_amount=Decimal('12.32'),
            pass_card_fee=True,
            card_fee_amount=Decimal('1.32'),
        )

        response = self.client.get(reverse('lanhouse'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'R$ 12,32')

    def test_tabela_lanhouse_valor_total_usa_total_sem_taxa_absorvida(self):
        self._criar_venda_lanhouse(
            quantidade=2,
            preco='5.50',
            card_final_amount=Decimal('11.00'),
            pass_card_fee=False,
            card_fee_amount=Decimal('0.11'),
        )

        response = self.client.get(reverse('lanhouse'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'R$ 11,00')

    def test_tabela_lanhouse_renderiza_cabecalho_unico_e_linhas_collapse_pareadas(self):
        self._criar_venda_lanhouse(quantidade=1, preco='5.00')
        self._criar_venda_lanhouse(quantidade=1, preco='7.00')

        response = self.client.get(reverse('lanhouse'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="lanhouse-header"', count=1)
        self.assertContains(response, 'class="collapse lanhouse-details-row"', count=2)
        self.assertContains(response, 'data-bs-target="#detalhes-', count=2)

    def test_cadastro_lanhouse_sucesso_atualiza_dashboard_completo(self):
        token = self._submission_token()
        payload = self._lanhouse_payload(token, LanhouseModel.PIX)
        payload['dashboard_periodo'] = '7dias'

        response = self.client.post(reverse('cadastrar-lanhouse'), payload, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertEqual(response['HX-Trigger'], 'lanhouseVendaSalva')
        self.assertContains(response, 'id="bloco-dados"')
        self.assertContains(response, 'id="lanhouse-Tbody"')
        self.assertContains(response, 'id="lanhouseChartsData"')
        self.assertContains(response, 'class="lanhouse-header"', count=1)

    def test_excluir_lanhouse_atualiza_dashboard_sem_linha_orfa_de_collapse(self):
        venda = self._criar_venda_lanhouse(quantidade=1, preco='5.00')

        response = self.client.get(
            reverse('apagar-lanhouse', args=[venda.pk]),
            {'dashboard_periodo': 'hoje'},
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertFalse(LanhouseModel.objects.filter(pk=venda.pk).exists())
        self.assertNotContains(response, 'id="detalhes-%s"' % venda.pk)
        self.assertContains(response, 'Nenhum serviço lanhouse encontrado.')

    def test_dashboard_lanhouse_receita_diaria_agrupa_por_hora(self):
        hoje = timezone.localdate()
        horario = timezone.make_aware(datetime.combine(hoje, time(hour=14, minute=35)))
        self._criar_venda_lanhouse(quantidade=2, preco='5.50', desconto='1.00', created_at=horario)

        dashboard = build_lanhouse_dashboard_charts(self.user, {'periodo': 'hoje'})

        revenue = dashboard['lanhouse_charts']['revenue']
        self.assertEqual(revenue['grouping'], 'hour')
        self.assertEqual(len(revenue['labels']), 24)
        self.assertEqual(revenue['values'][revenue['labels'].index('14:00')], 10.0)
        self.assertTrue(dashboard['lanhouse_revenue_has_data'])

    def test_dashboard_lanhouse_respeita_filtro_ontem(self):
        hoje = timezone.localdate()
        ontem = hoje - timedelta(days=1)
        self._criar_venda_lanhouse(
            quantidade=1,
            preco='7.00',
            created_at=timezone.make_aware(datetime.combine(ontem, time(hour=10))),
        )
        self._criar_venda_lanhouse(
            quantidade=1,
            preco='99.00',
            created_at=timezone.make_aware(datetime.combine(hoje, time(hour=10))),
        )

        dashboard = build_lanhouse_dashboard_charts(self.user, {'periodo': 'ontem'})
        revenue = dashboard['lanhouse_charts']['revenue']

        self.assertEqual(revenue['values'][revenue['labels'].index('10:00')], 7.0)

    def test_dashboard_lanhouse_custom_sem_dados_mantem_empty_state(self):
        dashboard = build_lanhouse_dashboard_charts(self.user, {
            'inicio': '2020-01-01',
            'fim': '2020-01-02',
        })

        revenue = dashboard['lanhouse_charts']['revenue']
        self.assertEqual(revenue['grouping'], 'day')
        self.assertEqual(revenue['labels'], ['01/01', '02/01'])
        self.assertEqual(revenue['values'], [0.0, 0.0])
        self.assertFalse(dashboard['lanhouse_revenue_has_data'])
        self.assertFalse(dashboard['lanhouse_service_has_data'])

    def test_dashboard_lanhouse_ranking_servicos_ordena_quantidade_e_receita(self):
        servico_extra = LanhouseServico.objects.create(
            usuario=self.user,
            servico='Plastificacao',
            preco_custo='2.00',
            preco='12.00',
        )
        hoje = timezone.localdate()
        self._criar_venda_lanhouse(
            servico=self.servico,
            quantidade=3,
            preco='4.00',
            created_at=timezone.make_aware(datetime.combine(hoje, time(hour=9))),
        )
        self._criar_venda_lanhouse(
            servico=servico_extra,
            quantidade=1,
            preco='30.00',
            created_at=timezone.make_aware(datetime.combine(hoje, time(hour=11))),
        )

        dashboard = build_lanhouse_dashboard_charts(self.user, {'periodo': 'este_mes'})
        ranking = dashboard['lanhouse_service_ranking']

        self.assertEqual(ranking[0]['service'], 'Impressao colorida')
        self.assertEqual(ranking[0]['quantity'], 3)
        self.assertEqual(ranking[0]['revenue'], Decimal('12.00'))
        self.assertEqual(ranking[1]['service'], 'Plastificacao')
        self.assertEqual(dashboard['lanhouse_charts']['services']['quantities'], [3, 1])

    def test_dashboard_lanhouse_periodo_longo_agrupa_receita_por_mes(self):
        hoje = timezone.localdate()
        antigo = hoje - timedelta(days=180)
        self._criar_venda_lanhouse(
            quantidade=1,
            preco='10.00',
            created_at=timezone.make_aware(datetime.combine(antigo, time(hour=9))),
        )
        self._criar_venda_lanhouse(
            quantidade=1,
            preco='15.00',
            created_at=timezone.make_aware(datetime.combine(hoje, time(hour=9))),
        )

        dashboard = build_lanhouse_dashboard_charts(self.user, {'periodo': 'todas'})
        revenue = dashboard['lanhouse_charts']['revenue']

        self.assertEqual(revenue['grouping'], 'month')
        self.assertIn(antigo.strftime('%m/%Y'), revenue['labels'])
        self.assertIn(hoje.strftime('%m/%Y'), revenue['labels'])

    def _lanhouse_payload(self, token, forma_pagamento, card_installments='', pass_fee=False):
        payload = {
            'submission_token': token,
            'main-usuario': self.user.pk,
            'main-cliente': self.cliente.pk,
            'main-vendedor': self.vendedor.pk,
            'main-desconto': '0.00',
            'main-forma_pagamento': forma_pagamento,
            'main-observacao': '',
            'main-data_vencimento': '',
            'main-qtd_parcela': '',
            'main-valor_entrada': '',
            'main-card_machine': self.machine.pk,
            'main-card_installments': card_installments,
            'main-card_payment_type': 'credit',
            'main-card_fee_percentage': '99.99',
            'main-card_fee_amount': '99.99',
            'main-card_base_amount': '99.99',
            'main-card_final_amount': '99.99',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-lanhouse': '',
            'items-0-id': '',
            'items-0-servico': self.servico.pk,
            'items-0-quantidade': '2',
            'items-0-preco': '5.50',
        }
        if pass_fee:
            payload['main-pass_card_fee_to_customer'] = 'on'
        return payload

    def _submission_token(self):
        response = self.client.get(reverse('cadastrar-lanhouse'), HTTP_HX_REQUEST='true')
        return response.context['submission_token']

    def test_lanhouse_cartao_debito_absorvido_cria_despesa_taxa(self):
        token = self._submission_token()

        response = self.client.post(
            reverse('cadastrar-lanhouse'),
            self._lanhouse_payload(token, LanhouseModel.CARTAO_DEBITO),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        lanhouse = LanhouseModel.objects.get()
        self.assertEqual(lanhouse.card_payment_type, CardMachineFee.PAYMENT_DEBIT)
        self.assertEqual(lanhouse.card_fee_percentage, Decimal('1.00'))
        self.assertEqual(lanhouse.card_fee_amount, Decimal('0.11'))
        self.assertEqual(lanhouse.card_base_amount, Decimal('11.00'))
        self.assertEqual(lanhouse.card_final_amount, Decimal('11.00'))
        self.assertFalse(lanhouse.pass_card_fee_to_customer)

        despesa = Despesa.objects.get(lanhouse_card_fee=lanhouse)
        self.assertEqual(despesa.preco_despesa, Decimal('0.11'))
        self.assertEqual(despesa.categoria_despesa.nome_categoria_despesa, 'Taxas de Maquininha')

    def test_lanhouse_cartao_credito_repassado_atualiza_total_sem_despesa(self):
        token = self._submission_token()

        response = self.client.post(
            reverse('cadastrar-lanhouse'),
            self._lanhouse_payload(token, LanhouseModel.CARTAO_CREDITO, card_installments='12', pass_fee=True),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        lanhouse = LanhouseModel.objects.get()
        self.assertEqual(lanhouse.card_payment_type, CardMachineFee.PAYMENT_CREDIT)
        self.assertEqual(lanhouse.card_installments, 12)
        self.assertEqual(lanhouse.card_fee_amount, Decimal('1.32'))
        self.assertEqual(lanhouse.card_final_amount, Decimal('12.32'))
        self.assertEqual(lanhouse.total(), Decimal('12.32'))
        self.assertTrue(lanhouse.pass_card_fee_to_customer)
        self.assertFalse(Despesa.objects.filter(lanhouse_card_fee=lanhouse).exists())

    def test_preview_taxa_cartao_lanhouse_retorna_calculo_backend(self):
        response = self.client.get(
            reverse('preview-taxa-cartao-lanhouse'),
            {
                'forma_pagamento': LanhouseModel.CARTAO_CREDITO,
                'card_machine': self.machine.pk,
                'installments': '12',
                'base_amount': '100.00',
                'pass_fee': '1',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['payment_type'], CardMachineFee.PAYMENT_CREDIT)
        self.assertEqual(payload['fee_percentage'], '12.00')
        self.assertEqual(payload['fee_amount'], '12.00')
        self.assertEqual(payload['final_amount'], '112.00')
