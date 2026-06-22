import json
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from cliente.models import Cliente
from colaborador.models import Colaborador
from despesa.models import Despesa
from financeiro.models import CardMachine, CardMachineFee
from orcamento.models import ItemsOrcamento, Orcamento, Servico
from orcamento.periodo import build_orcamento_dashboard_charts
from peca.models import Pecas


class OrcamentoClientPickerTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='orcamento-user', password='senha-teste')
        self.client.force_login(self.user)
        self.cliente = Cliente.objects.create(
            usuario=self.user,
            nome_cliente='Cliente Orcamento',
            telefone_contato='(67) 99999-2222',
        )
        self.tecnico = Colaborador.objects.create(
            usuario=self.user,
            nome_colaborador='Tecnico',
            telefone_contato='(67) 98888-2222',
        )
        self.servico = Servico.objects.create(usuario=self.user, servico='Troca de tela')
        self.peca = Pecas.objects.create(
            usuario=self.user,
            nome_peca='Tela Moto G',
            preco_peca='120.00',
            preco_de_custo='80.00',
            quantidade=5,
            forma_pagamento=Pecas.DINHEIRO,
        )
        self.machine = CardMachine.objects.create(usuario=self.user, name='Rede')
        CardMachineFee.objects.create(
            card_machine=self.machine,
            payment_type=CardMachineFee.PAYMENT_DEBIT,
            installments=None,
            fee_percentage='2.00',
        )

    def test_formulario_cadastro_usa_seletor_cliente_compartilhado(self):
        response = self.client.get(reverse('cadastrar-orcamento'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-client-picker')
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-clientes'))
        self.assertContains(response, 'hx-get="%s?picker=1"' % reverse('cadastrar-cliente'))
        self.assertContains(response, 'data-client-picker-native="true"')
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-vendedores'))
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-servicos-orcamento'))
        self.assertContains(response, 'data-search-url="%s"' % reverse('buscar-pecas'))
        self.assertContains(response, 'Create New Service')
        self.assertContains(response, 'Criar nova peça')
        self.assertContains(response, 'data-bs-target="#orcamentoPecaPickerModal"')
        self.assertContains(response, 'data-card-payment-section')
        self.assertContains(response, 'orcamento-modal-body')
        self.assertContains(response, 'orcamento-form-section')
        self.assertContains(response, 'orcamento-section-header')
        self.assertContains(response, 'orcamento-add-button')
        self.assertContains(response, 'Adicionar peça')
        self.assertContains(response, 'Adicionar serviço')
        self.assertContains(response, 'orcamento-item-row')

    def test_formulario_edicao_usa_layout_orcamento_compartilhado(self):
        orcamento = self._criar_orcamento()

        response = self.client.get(reverse('editar-orcamento', args=[orcamento.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'orcamento-modal-body')
        self.assertContains(response, 'orcamento-form-section')
        self.assertContains(response, 'orcamento-section-header')
        self.assertContains(response, 'orcamento-add-button')
        self.assertContains(response, 'Adicionar peça')
        self.assertContains(response, 'Adicionar serviço')
        self.assertContains(response, 'orcamento-item-row')

    def test_edicao_mostra_peca_sem_estoque_e_permite_trocar_fiado_para_pix(self):
        orcamento, item = self._criar_orcamento_com_peca_sem_estoque()

        response = self.client.get(reverse('editar-orcamento', args=[orcamento.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.peca.nome_peca)
        self.assertContains(response, 'data-field="peca"')

        payload = {
            'dashboard_periodo': 'hoje',
            'dashboard_inicio': '',
            'dashboard_fim': '',
            'main-usuario': self.user.pk,
            'main-cliente': self.cliente.pk,
            'main-celular': 'Moto G editado',
            'main-data_entrega': '',
            'main-status': Orcamento.FINALIZADO_ENTREGUE,
            'main-observacao': '',
            'main-tecnico': self.tecnico.pk,
            'main-desconto': '0.00',
            'main-forma_pagamento': Orcamento.PIX,
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
            'items-0-orcamento': orcamento.pk,
            'items-0-id': item.pk,
            'items-0-peca': self.peca.pk,
            'items-0-servico': '',
            'items-0-quantidade': '1',
            'items-0-preco_orcamento': '120.00',
        }

        response = self.client.post(reverse('editar-orcamento', args=[orcamento.pk]), payload, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Trigger-After-Swap'], 'orcamentoSalvo')
        orcamento.refresh_from_db()
        item.refresh_from_db()
        self.peca.refresh_from_db()
        self.assertEqual(orcamento.forma_pagamento, Orcamento.PIX)
        self.assertEqual(item.peca, self.peca)
        self.assertEqual(self.peca.quantidade, 0)

    def test_pagina_orcamento_inclui_assets_e_modal_cliente(self):
        response = self.client.get(reverse('orcamento'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'css/finance-dashboard.css')
        self.assertContains(response, 'css/client-picker.css')
        self.assertContains(response, 'js/finance-charts.js')
        self.assertContains(response, 'js/orcamento-dashboard.js')
        self.assertContains(response, 'js/client-picker.js')
        self.assertContains(response, 'js/card-fee-preview.js')
        self.assertContains(response, 'id="clientePickerModal"')
        self.assertContains(response, 'id="orcamentoServicoPickerModal"')
        self.assertContains(response, 'id="orcamentoPecaPickerModal"')
        self.assertContains(response, 'js/pricing-margin.js')
        self.assertContains(response, 'id="orcamentoChartsData"')
        self.assertContains(response, 'id="orcamentoRevenueChart"')
        self.assertContains(response, 'id="orcamentoItemsChart"')
        self.assertNotContains(response, 'success_tic')
        self.assertNotContains(response, 'relatorioorcaamento')

    def test_busca_servicos_orcamento_filtra_por_usuario_e_termo(self):
        other_user = User.objects.create_user(username='outro-orcamento', password='senha-teste')
        Servico.objects.create(usuario=other_user, servico='Troca de tela outra loja')

        response = self.client.get(reverse('buscar-servicos-orcamento'), {'q': 'tela'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['id'], self.servico.pk)

    def test_cadastro_servico_picker_retorna_evento_para_auto_selecao(self):
        response = self.client.post(
            reverse('cadastrar-servico') + '?picker=1',
            {
                'service_picker': '1',
                'usuario': self.user.pk,
                'servico': 'Limpeza interna',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        servico = Servico.objects.get(servico='Limpeza interna')
        trigger = json.loads(response['HX-Trigger'])
        self.assertEqual(trigger['orcamentoServicoCriado']['id'], servico.pk)
        self.assertEqual(trigger['orcamentoServicoCriado']['text'], servico.servico)

    def _submission_token(self):
        response = self.client.get(reverse('cadastrar-orcamento'), HTTP_HX_REQUEST='true')
        return response.context['submission_token']

    def _orcamento_payload(self, token):
        return {
            'submission_token': token,
            'main-usuario': self.user.pk,
            'main-cliente': self.cliente.pk,
            'main-celular': 'Moto G',
            'main-data_entrega': '',
            'main-status': Orcamento.FINALIZADO_ENTREGUE,
            'main-observacao': '',
            'main-tecnico': self.tecnico.pk,
            'main-desconto': '0.00',
            'main-forma_pagamento': Orcamento.CARTAO_DEBITO,
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
            'items-0-orcamento': '',
            'items-0-id': '',
            'items-0-peca': '',
            'items-0-servico': self.servico.pk,
            'items-0-quantidade': '2',
            'items-0-preco_orcamento': '50.00',
        }

    def _criar_orcamento(self, status=Orcamento.FINALIZADO_ENTREGUE):
        orcamento = Orcamento.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            celular='Moto G',
            status=status,
            tecnico=self.tecnico,
            desconto=Decimal('0.00'),
            forma_pagamento=Orcamento.PIX,
        )
        ItemsOrcamento.objects.create(
            orcamento=orcamento,
            servico=self.servico,
            quantidade=1,
            preco_orcamento=Decimal('50.00'),
        )
        return orcamento

    def _criar_orcamento_com_peca_sem_estoque(self):
        self.peca.quantidade = 1
        self.peca.save(update_fields=['quantidade'])
        orcamento = Orcamento.objects.create(
            usuario=self.user,
            cliente=self.cliente,
            celular='Moto G',
            status=Orcamento.FINALIZADO_ENTREGUE,
            tecnico=self.tecnico,
            desconto=Decimal('0.00'),
            forma_pagamento=Orcamento.FIADO,
            qtd_parcela=2,
            valor_entrada=Decimal('20.00'),
            data_vencimento=date(2026, 6, 30),
        )
        item = ItemsOrcamento.objects.create(
            orcamento=orcamento,
            peca=self.peca,
            quantidade=1,
            preco_orcamento=Decimal('120.00'),
        )
        self.peca.refresh_from_db()
        self.assertEqual(self.peca.quantidade, 0)
        return orcamento, item

    def _orcamento_edit_payload(self, orcamento):
        item = orcamento.orcamento_items.first()
        return {
            'dashboard_periodo': 'hoje',
            'dashboard_inicio': '',
            'dashboard_fim': '',
            'main-usuario': self.user.pk,
            'main-cliente': self.cliente.pk,
            'main-celular': 'Moto G editado',
            'main-data_entrega': '',
            'main-status': Orcamento.FINALIZADO_ENTREGUE,
            'main-observacao': '',
            'main-tecnico': self.tecnico.pk,
            'main-desconto': '5.00',
            'main-forma_pagamento': Orcamento.PIX,
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
            'items-0-orcamento': orcamento.pk,
            'items-0-id': item.pk,
            'items-0-peca': '',
            'items-0-servico': self.servico.pk,
            'items-0-quantidade': '3',
            'items-0-preco_orcamento': '40.00',
        }

    def test_tabela_orcamento_renderiza_cabecalho_unico_e_linhas_collapse_pareadas(self):
        self._criar_orcamento()
        self._criar_orcamento(status=Orcamento.ANALISE)

        response = self.client.get(reverse('orcamento'))

        self.assertContains(response, 'class="orcamento-header"', count=1)
        self.assertContains(response, 'class="collapse orcamento-details-row"', count=2)
        self.assertContains(response, 'data-bs-target="#detalhes-orcamento-', count=2)
        self.assertContains(response, 'hx-get="%s"' % reverse('apagar-orcamento', args=[Orcamento.objects.first().pk]))
        self.assertContains(response, 'hx-get="%s"' % reverse('detalhe-orcamento', args=[Orcamento.objects.first().pk]))
        self.assertContains(response, 'hx-get="%s"' % reverse('relatorio-lucro-orcamento', args=[Orcamento.objects.first().pk]))
        self.assertContains(response, 'title="Custos e lucros"')
        self.assertNotContains(response, 'hx-get="%s"' % reverse('relatorio-orcamento-individual', args=[Orcamento.objects.first().pk]))

    def test_detalhe_orcamento_inline_renderiza_recibo_igual_vendas(self):
        orcamento = self._criar_orcamento()
        orcamento.desconto = Decimal('10.00')
        orcamento.forma_pagamento = Orcamento.FIADO
        orcamento.valor_entrada = Decimal('20.00')
        orcamento.qtd_parcela = 2
        orcamento.data_vencimento = date(2026, 6, 30)
        orcamento.observacao = 'Cliente aprovou o reparo.'
        orcamento.save()
        ItemsOrcamento.objects.create(
            orcamento=orcamento,
            peca=self.peca,
            quantidade=1,
            preco_orcamento=Decimal('120.00'),
        )

        response = self.client.get(reverse('detalhe-orcamento', args=[orcamento.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recibo de orçamento')
        self.assertContains(response, 'contentPrint')
        self.assertContains(response, 'Ordem de serviço:</strong> #%s' % orcamento.pk)
        self.assertContains(response, self.cliente.nome_cliente)
        self.assertContains(response, self.tecnico.nome_colaborador)
        self.assertContains(response, self.servico.servico)
        self.assertContains(response, self.peca.nome_peca)
        self.assertContains(response, 'Serviço')
        self.assertContains(response, 'Peça')
        self.assertContains(response, Orcamento.FIADO)
        self.assertContains(response, '30/06/2026')
        self.assertContains(response, 'Cliente aprovou o reparo.')
        self.assertContains(response, "onclick=\"imprimir('.contentPrint')\"")

    def test_relatorio_individual_orcamento_renderiza_dados_completos(self):
        orcamento = self._criar_orcamento()
        orcamento.desconto = Decimal('10.00')
        orcamento.forma_pagamento = Orcamento.FIADO
        orcamento.valor_entrada = Decimal('20.00')
        orcamento.qtd_parcela = 2
        orcamento.data_vencimento = date(2026, 6, 30)
        orcamento.observacao = 'Cliente aprovou o reparo.'
        orcamento.save()
        ItemsOrcamento.objects.create(
            orcamento=orcamento,
            peca=self.peca,
            quantidade=1,
            preco_orcamento=Decimal('120.00'),
        )

        response = self.client.get(reverse('relatorio-orcamento-individual', args=[orcamento.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Relatório de orçamento')
        self.assertContains(response, f'Orçamento:</strong> #{orcamento.pk}')
        self.assertContains(response, self.cliente.nome_cliente)
        self.assertContains(response, self.cliente.telefone_contato)
        self.assertContains(response, self.tecnico.nome_colaborador)
        self.assertContains(response, self.servico.servico)
        self.assertContains(response, self.peca.nome_peca)
        self.assertContains(response, 'Serviço')
        self.assertContains(response, 'Peça')
        self.assertContains(response, 'R$ 10,00')
        self.assertContains(response, Orcamento.FIADO)
        self.assertContains(response, '2')
        self.assertContains(response, '30/06/2026')
        self.assertContains(response, 'Cliente aprovou o reparo.')
        self.assertContains(response, 'imprimirOrcamento')

    def test_relatorio_individual_orcamento_respeita_usuario(self):
        orcamento = self._criar_orcamento()
        other_user = User.objects.create_user(username='outro-relatorio-orcamento', password='senha-teste')
        self.client.force_login(other_user)

        response = self.client.get(reverse('relatorio-orcamento-individual', args=[orcamento.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 404)

    def test_relatorio_lucro_orcamento_renderiza_indicadores_principais(self):
        orcamento = self._criar_orcamento()
        orcamento.desconto = Decimal('10.00')
        orcamento.forma_pagamento = Orcamento.CARTAO_DEBITO
        orcamento.card_machine = self.machine
        orcamento.card_payment_type = CardMachineFee.PAYMENT_DEBIT
        orcamento.card_fee_percentage = Decimal('2.00')
        orcamento.card_fee_amount = Decimal('2.00')
        orcamento.card_base_amount = Decimal('160.00')
        orcamento.card_final_amount = Decimal('160.00')
        orcamento.pass_card_fee_to_customer = False
        orcamento.save()
        ItemsOrcamento.objects.create(
            orcamento=orcamento,
            peca=self.peca,
            quantidade=1,
            preco_orcamento=Decimal('120.00'),
        )

        response = self.client.get(reverse('relatorio-lucro-orcamento', args=[orcamento.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Custos e lucros do orçamento')
        self.assertContains(response, 'Receita líquida')
        self.assertContains(response, 'Custo total')
        self.assertContains(response, 'Lucro líquido')
        self.assertContains(response, 'Margem de lucro')
        self.assertContains(response, 'Markup sobre custo')
        self.assertContains(response, self.servico.servico)
        self.assertContains(response, self.peca.nome_peca)
        self.assertContains(response, 'R$ 160,00')
        self.assertContains(response, 'R$ 80,00')
        self.assertContains(response, 'R$ 78,00')
        self.assertContains(response, '48,75%')
        self.assertContains(response, 'Taxa de maquininha absorvida')
        self.assertContains(response, "onclick=\"imprimirLucroOrcamento('.contentPrint')\"")

    def test_relatorio_lucro_orcamento_respeita_usuario(self):
        orcamento = self._criar_orcamento()
        other_user = User.objects.create_user(username='outro-lucro-orcamento', password='senha-teste')
        self.client.force_login(other_user)

        response = self.client.get(reverse('relatorio-lucro-orcamento', args=[orcamento.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 404)

    def test_cadastro_orcamento_sucesso_atualiza_dashboard_completo(self):
        token = self._submission_token()
        payload = self._orcamento_payload(token)
        payload['dashboard_periodo'] = '7dias'

        response = self.client.post(reverse('cadastrar-orcamento'), payload, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertEqual(response['HX-Trigger-After-Swap'], 'orcamentoSalvo')
        self.assertContains(response, 'id="bloco-dados"')
        self.assertContains(response, 'id="orcamento-Tbody"')
        self.assertContains(response, 'id="orcamentoChartsData"')
        self.assertContains(response, 'class="orcamento-header"', count=1)

    def test_editar_orcamento_sucesso_nao_duplica_e_atualiza_dashboard(self):
        orcamento = self._criar_orcamento()
        payload = self._orcamento_edit_payload(orcamento)

        response = self.client.post(reverse('editar-orcamento', args=[orcamento.pk]), payload, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertEqual(response['HX-Trigger-After-Swap'], 'orcamentoSalvo')
        self.assertEqual(Orcamento.objects.count(), 1)
        orcamento.refresh_from_db()
        self.assertEqual(orcamento.celular, 'Moto G editado')
        self.assertEqual(orcamento.orcamento_items.count(), 1)
        item = orcamento.orcamento_items.first()
        self.assertEqual(item.quantidade, 3)
        self.assertEqual(item.preco_orcamento, Decimal('40.00'))

    def test_excluir_orcamento_atualiza_dashboard_sem_linha_orfa_de_collapse(self):
        orcamento = self._criar_orcamento()

        response = self.client.get(
            reverse('apagar-orcamento', args=[orcamento.pk]),
            {'dashboard_periodo': 'hoje'},
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response['HX-Reswap'], 'outerHTML')
        self.assertEqual(response['HX-Trigger-After-Swap'], 'orcamentoExcluido')
        self.assertFalse(Orcamento.objects.filter(pk=orcamento.pk).exists())
        self.assertNotContains(response, f'id="detalhes-orcamento-{orcamento.pk}"')
        self.assertContains(response, 'Nenhum orçamento encontrado.')

    def test_charts_orcamento_preservam_regra_de_status(self):
        self._criar_orcamento(status=Orcamento.FINALIZADO_ENTREGUE)
        self._criar_orcamento(status=Orcamento.ANALISE)
        self._criar_orcamento(status=Orcamento.CANCELADO)

        charts = build_orcamento_dashboard_charts(self.user, {'periodo': 'hoje'})

        self.assertEqual(sum(charts['orcamento_charts']['revenue']['values']), 50.0)
        self.assertEqual(sum(charts['orcamento_charts']['items']['quantities']), 2)

    def test_orcamento_finalizado_cartao_debito_absorvido_cria_despesa_taxa(self):
        token = self._submission_token()

        response = self.client.post(
            reverse('cadastrar-orcamento'),
            self._orcamento_payload(token),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        orcamento = Orcamento.objects.get()
        self.assertEqual(orcamento.card_payment_type, CardMachineFee.PAYMENT_DEBIT)
        self.assertEqual(orcamento.card_fee_percentage, Decimal('2.00'))
        self.assertEqual(orcamento.card_fee_amount, Decimal('2.00'))
        self.assertEqual(orcamento.card_base_amount, Decimal('100.00'))
        self.assertEqual(orcamento.card_final_amount, Decimal('100.00'))

        despesa = Despesa.objects.get(orcamento_card_fee=orcamento)
        self.assertEqual(despesa.preco_despesa, Decimal('2.00'))

    def test_token_impede_reenvio_duplicado_do_orcamento(self):
        token = self._submission_token()
        payload = self._orcamento_payload(token)

        first = self.client.post(reverse('cadastrar-orcamento'), payload, HTTP_HX_REQUEST='true')
        second = self.client.post(reverse('cadastrar-orcamento'), payload, HTTP_HX_REQUEST='true')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(Orcamento.objects.count(), 1)
