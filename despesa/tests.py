import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from despesa.forms import DespesaForms
from despesa.models import CategoriaDespesa, Despesa
from despesa.services import build_expense_dashboard, resolve_expense_period
from peca.models import Pecas
from produto.models import Produto


class DespesaTabelaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='despesa-user', password='senha-teste')
        self.client.force_login(self.user)

    def test_tabela_exibe_data_hora_cadastro_na_primeira_coluna(self):
        despesa = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Internet',
            preco_despesa='120.00',
            forma_pagamento=Despesa.PIX,
        )
        data_cadastro = timezone.make_aware(datetime(2026, 6, 2, 14, 35, 22))
        Despesa.objects.filter(pk=despesa.pk).update(data_cadastro=data_cadastro)

        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-02',
            'data_fim': '2026-06-02',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data/Hora')
        self.assertContains(response, 'Despesa')
        self.assertContains(response, 'Categoria')
        self.assertContains(response, 'Valor')
        self.assertContains(response, 'Forma de pagamento')
        self.assertContains(response, 'Tipo')
        self.assertContains(response, 'Ações')
        self.assertContains(response, 'Internet')
        self.assertContains(response, 'Sem categoria')
        self.assertContains(response, '02/06/2026')
        self.assertContains(response, '14:35')

    def test_dashboard_formata_moeda_em_real_com_separador_de_milhar(self):
        data_cadastro = timezone.make_aware(datetime(2026, 6, 2, 14, 35, 22))
        despesa = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Aluguel loja',
            preco_despesa=Decimal('1234.56'),
            forma_pagamento=Despesa.PIX,
        )
        Despesa.objects.filter(pk=despesa.pk).update(data_cadastro=data_cadastro)

        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-02',
            'data_fim': '2026-06-02',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'R$ 1.234,56')

    def test_dashboard_separa_blocos_de_despesas_fixas_prolabore_e_dividas(self):
        data_cadastro = timezone.make_aware(datetime(2026, 6, 5, 10, 0, 0))
        fixa = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Internet fixa',
            preco_despesa=Decimal('250.00'),
            forma_pagamento=Despesa.PIX,
            despesa_fixa=True,
            dia_vencimento_fixo=5,
        )
        prolabore = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Retirada pessoal',
            preco_despesa=Decimal('300.00'),
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_PROLABORE,
        )
        divida = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Cartão pessoal',
            preco_despesa=Decimal('400.00'),
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_DIVIDA,
            fiado_pago=False,
        )
        Despesa.objects.filter(pk__in=[fixa.pk, prolabore.pk, divida.pk]).update(data_cadastro=data_cadastro)

        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-05',
            'data_fim': '2026-06-05',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="fixed-expense-section"')
        self.assertContains(response, 'id="prolabore-section"')
        self.assertContains(response, 'id="debt-section"')
        self.assertContains(response, 'id="expenseSectionCollapse"')
        self.assertContains(response, 'id="prolaboreSectionCollapse"')
        self.assertContains(response, 'id="debtSectionCollapse"')
        self.assertContains(response, 'fixed-table-scroll')
        self.assertContains(response, 'id="prolaboreCategoryChart"')
        self.assertContains(response, 'Participação por categoria do Pró-labore')
        self.assertIn(fixa, list(response.context['fixed_expense_list']))
        self.assertIn(prolabore, list(response.context['prolabore_expense_list']))
        self.assertIn(divida, list(response.context['debt_list']))

    def test_ranking_agrupa_por_categoria_ordena_e_calcula_percentual(self):
        categoria_alta = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Aluguel')
        categoria_baixa = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Internet')
        data_cadastro = timezone.make_aware(datetime(2026, 6, 3, 10, 0, 0))

        despesas = [
            Despesa.objects.create(usuario=self.user, categoria_despesa=categoria_baixa, nome_despesa='Internet', preco_despesa='100.00'),
            Despesa.objects.create(usuario=self.user, categoria_despesa=categoria_alta, nome_despesa='Aluguel', preco_despesa='300.00'),
            Despesa.objects.create(usuario=self.user, categoria_despesa=None, nome_despesa='Sem categoria', preco_despesa='50.00'),
        ]
        Despesa.objects.filter(pk__in=[item.pk for item in despesas]).update(data_cadastro=data_cadastro)

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        ranking = dashboard['expense_category_ranking']
        self.assertEqual([item['category'] for item in ranking], ['Aluguel', 'Internet', 'Sem categoria'])
        self.assertEqual(ranking[0]['amount'], 300)
        self.assertEqual(ranking[0]['percentage'], Decimal('66.67'))
        self.assertEqual(dashboard['expense_charts']['category_ranking']['labels'][0], 'Aluguel')

    def test_despesa_fixa_fiada_considera_entrada_como_pago_e_saldo_a_pagar(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Aluguel')
        despesa = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Aluguel loja',
            preco_despesa=Decimal('600.00'),
            forma_pagamento=Despesa.FIADO,
            valor_entrada=Decimal('250.00'),
            fiado_pago=False,
            despesa_fixa=True,
            dia_vencimento_fixo=5,
        )
        Despesa.objects.filter(pk=despesa.pk).update(
            data_cadastro=timezone.make_aware(datetime(2026, 6, 1, 9, 0, 0))
        )

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-05',
            'data_fim': '2026-06-05',
        })

        self.assertEqual(dashboard['expense_total'], Decimal('250.00'))
        self.assertEqual(dashboard['expense_payable_total'], Decimal('350.00'))
        self.assertEqual(dashboard['fixed_expense_total'], Decimal('250.00'))
        self.assertEqual(dashboard['expense_category_ranking'][0]['category'], 'Aluguel')
        self.assertEqual(dashboard['expense_category_ranking'][0]['amount'], Decimal('250.00'))
        self.assertEqual(dashboard['expense_charts']['category_ranking']['values'], [250.0])

    def test_filtro_customizado_limita_tabela_e_grafico(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Operacional')
        dentro = Despesa.objects.create(usuario=self.user, categoria_despesa=categoria, nome_despesa='Dentro', preco_despesa='80.00')
        fora = Despesa.objects.create(usuario=self.user, categoria_despesa=categoria, nome_despesa='Fora', preco_despesa='200.00')
        Despesa.objects.filter(pk=dentro.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 6, 4, 9, 0, 0)))
        Despesa.objects.filter(pk=fora.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 5, 20, 9, 0, 0)))

        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '80')
        self.assertNotContains(response, '200')
        self.assertContains(response, 'Operacional')

    def test_periodo_vazio_mostra_estado_amigavel_sem_canvas(self):
        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-01-01',
            'data_fim': '2026-01-02',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sem despesas no periodo selecionado.')
        self.assertContains(response, 'Nenhum resultado encontrado.')
        self.assertNotContains(response, 'id="expenseCategoryChart"')

    def test_muitas_categorias_retorna_dados_para_grafico_responsivo(self):
        data_cadastro = timezone.make_aware(datetime(2026, 6, 5, 12, 0, 0))
        for index in range(15):
            categoria = CategoriaDespesa.objects.create(
                usuario=self.user,
                nome_categoria_despesa=f'Categoria {index:02d}',
            )
            despesa = Despesa.objects.create(
                usuario=self.user,
                categoria_despesa=categoria,
                nome_despesa=f'Despesa {index:02d}',
                preco_despesa=str(10 + index),
            )
            Despesa.objects.filter(pk=despesa.pk).update(data_cadastro=data_cadastro)

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(len(dashboard['expense_category_ranking']), 15)
        self.assertEqual(dashboard['expense_category_ranking'][0]['category'], 'Categoria 14')
        self.assertEqual(dashboard['expense_chart_height'], 360)

    def test_resolve_periodo_aceita_filtros_solicitados(self):
        self.assertEqual(resolve_expense_period({'periodo': 'hoje'}).key, 'hoje')
        self.assertEqual(resolve_expense_period({'periodo': 'ontem'}).key, 'ontem')
        self.assertEqual(resolve_expense_period({'periodo': '7dias'}).key, '7dias')
        self.assertEqual(resolve_expense_period({'periodo': 'este_mes'}).key, 'este_mes')
        self.assertEqual(resolve_expense_period({'periodo': 'mes_passado'}).key, 'mes_passado')
        self.assertEqual(resolve_expense_period({'periodo': 'este_ano'}).key, 'este_ano')
        self.assertTrue(resolve_expense_period({'periodo': 'todas'}).all_data)
        self.assertEqual(resolve_expense_period({'periodo': 'today'}).key, 'hoje')
        self.assertEqual(resolve_expense_period({'periodo': 'current_month'}).key, 'este_mes')
        self.assertEqual(resolve_expense_period({'periodo': 'custom', 'data_inicio': '2026-06-10', 'data_fim': '2026-06-01'}).start.isoformat(), '2026-06-01')

    def test_filtros_usam_mesmo_padrao_visual_dos_dashboards(self):
        response = self.client.get(reverse('despesa'), {'periodo': 'este_mes'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="inicio"')
        self.assertContains(response, 'name="fim"')
        self.assertContains(response, 'Hoje')
        self.assertContains(response, '7 dias')
        self.assertContains(response, 'Este mês')
        self.assertContains(response, 'Mês passado')
        self.assertContains(response, 'Este ano')
        self.assertContains(response, 'Todas')
        self.assertContains(response, 'Limpar')
        self.assertContains(response, 'btn-periodo-ativo')
        self.assertContains(response, 'name="tipo"')
        self.assertContains(response, 'Pró-labore')

    def test_filtro_por_intervalo_usa_inicio_e_fim(self):
        dentro = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Dentro do intervalo',
            preco_despesa='80.00',
            forma_pagamento=Despesa.PIX,
        )
        fora = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Fora do intervalo',
            preco_despesa='200.00',
            forma_pagamento=Despesa.PIX,
        )
        Despesa.objects.filter(pk=dentro.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 6, 4, 9, 0, 0)))
        Despesa.objects.filter(pk=fora.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 5, 20, 9, 0, 0)))

        response = self.client.get(reverse('despesa'), {
            'inicio': '2026-06-01',
            'fim': '2026-06-10',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dentro do intervalo')
        self.assertNotContains(response, 'Fora do intervalo')
        self.assertContains(response, 'value="2026-06-01"')
        self.assertContains(response, 'value="2026-06-10"')

    def test_cadastro_htmx_retorna_bloco_completo_para_evitar_injecao_invalida(self):
        payload = {
            'usuario': self.user.pk,
            'nome_despesa': 'Energia',
            'preco_despesa': '150.00',
            'forma_pagamento': Despesa.PIX,
            'dashboard_periodo': 'today',
        }

        response = self.client.post(
            reverse('cadastrar-despesa'),
            payload,
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Retarget'], '#bloco-dados')
        self.assertEqual(response.headers['HX-Reswap'], 'outerHTML')
        self.assertEqual(response.headers['HX-Trigger'], 'despesaSalva')
        self.assertContains(response, 'id="bloco-dados"')
        self.assertContains(response, 'id="despesa-Tbody"')
        self.assertContains(response, 'despesaChartsData')

    def test_cadastros_htmx_em_sequencia_preservam_mesmo_alvo(self):
        for index in range(2):
            response = self.client.post(
                reverse('cadastrar-despesa'),
                {
                    'usuario': self.user.pk,
                    'nome_despesa': f'Despesa sequencial {index}',
                    'preco_despesa': '25.00',
                    'forma_pagamento': Despesa.PIX,
                    'dashboard_periodo': 'today',
                },
                HTTP_HX_REQUEST='true',
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['HX-Retarget'], '#bloco-dados')
            self.assertContains(response, 'id="bloco-dados"', count=1)
            self.assertContains(response, 'id="despesa-Tbody"', count=1)
            self.assertNotContains(response, 'success_tic')

    def test_cadastro_htmx_invalido_retorna_formulario_para_modal(self):
        response = self.client.post(
            reverse('cadastrar-despesa'),
            {
                'usuario': self.user.pk,
                'nome_despesa': '',
                'preco_despesa': '',
                'forma_pagamento': Despesa.PIX,
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Retarget'], '#adicionar-conteudo')
        self.assertEqual(response.headers['HX-Reswap'], 'innerHTML')
        self.assertContains(response, 'data-despesa-modal-form="true"')
        self.assertContains(response, 'Verifique os campos destacados')

    def test_formulario_cadastro_tem_campos_fiado_condicionais(self):
        response = self.client.get(
            reverse('cadastrar-despesa'),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-despesa-fiado-row')
        self.assertContains(response, 'Valor de entrada')
        self.assertContains(response, 'Quantidade de parcelas')
        self.assertContains(response, 'Data de vencimento')
        self.assertContains(response, 'Dia do vencimento mensal')
        self.assertContains(response, 'Status')
        self.assertContains(response, 'Não pago')
        self.assertContains(response, 'Pago')

    def test_formulario_cadastro_tem_campos_despesa_fixa_condicionais(self):
        response = self.client.get(
            reverse('cadastrar-despesa'),
            HTTP_HX_REQUEST='true',
        )
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-despesa-fixa-section')
        self.assertContains(response, 'data-despesa-fixa-row')
        self.assertContains(response, 'onchange=')
        self.assertContains(response, 'Despesa fixa')
        self.assertContains(response, 'Dia de vencimento')
        self.assertRegex(html, r'name="dia_vencimento_fixo"[^>]*type="number"|type="number"[^>]*name="dia_vencimento_fixo"')

    def test_formulario_prolabore_reusa_modal_com_campos_pessoais(self):
        response = self.client.get(
            reverse('cadastrar-prolabore'),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cadastrar Pró-labore')
        self.assertContains(response, 'Use Pró-labore para registrar retiradas pessoais')
        self.assertContains(response, 'name="data_lancamento"')
        self.assertContains(response, 'Descricao do Pró-labore')
        self.assertContains(response, 'Categoria pessoal')
        self.assertNotContains(response, 'Fornecedor (opcional)')
        self.assertNotContains(response, 'Despesa fixa')

    def test_formulario_divida_reusa_modal_com_status(self):
        response = self.client.get(
            reverse('cadastrar-divida'),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cadastrar Dívida')
        self.assertContains(response, 'Use Dívida')
        self.assertContains(response, 'Descricao da dívida')
        self.assertContains(response, 'data-despesa-divida-status')
        self.assertContains(response, 'Status da dívida')
        self.assertContains(response, 'Dívidas não pagas ficam em a pagar')
        self.assertContains(response, 'Fornecedor (opcional)')

    def test_formulario_cadastro_usa_layout_padronizado(self):
        response = self.client.get(
            reverse('cadastrar-despesa'),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'erp-modal-form')
        self.assertContains(response, 'erp-modal-body')
        self.assertContains(response, 'selector-standard-control')
        self.assertNotContains(response, 'form-floating')

    def test_formulario_cadastro_usa_seletor_moderno_de_categoria(self):
        CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Operacional')

        response = self.client.get(
            reverse('cadastrar-despesa'),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-client-picker')
        self.assertContains(response, 'Criar nova categoria')
        self.assertContains(response, reverse('buscar-categorias-despesa'))
        self.assertContains(response, 'Cadastrar fornecedor')
        self.assertContains(response, reverse('buscar-fornecedores'))
        self.assertContains(response, 'Operacional')

    def test_busca_categoria_despesa_retorna_json_para_selector(self):
        CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Aluguel')
        CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Internet')

        response = self.client.get(reverse('buscar-categorias-despesa'), {'q': 'alu'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['text'], 'Aluguel')

    def test_categoria_criada_pelo_picker_retorna_evento_para_auto_selecionar(self):
        response = self.client.post(
            reverse('categoria-despesa') + '?picker=1',
            {
                'usuario': self.user.pk,
                'nome_categoria_despesa': 'Manutencao',
                'category_picker': '1',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        trigger = json.loads(response.headers['HX-Trigger'])
        categoria = CategoriaDespesa.objects.get(usuario=self.user, nome_categoria_despesa='Manutencao')
        self.assertEqual(trigger['despesaCategoriaCriada']['id'], categoria.pk)
        self.assertEqual(trigger['despesaCategoriaCriada']['text'], 'Manutencao')

    def test_categoria_criada_no_modal_retorna_lista_atualizada(self):
        response = self.client.post(
            reverse('categoria-despesa'),
            {
                'usuario': self.user.pk,
                'nome_categoria_despesa': 'Aluguel',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'despesaCategoriaSalva')
        self.assertContains(response, 'Categoria despesa')
        self.assertContains(response, 'Aluguel')

    def test_editar_categoria_atualiza_linha(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Casa')

        response = self.client.post(
            reverse('editar-categoria-despesa', args=[categoria.pk]),
            {
                'usuario': self.user.pk,
                'nome_categoria_despesa': 'Casa e mercado',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'despesaCategoriaEditada')
        categoria.refresh_from_db()
        self.assertEqual(categoria.nome_categoria_despesa, 'Casa e mercado')
        self.assertContains(response, 'Casa e mercado')

    def test_apagar_categoria_preserva_despesas_como_sem_categoria(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Antiga')
        despesa = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Conta antiga',
            preco_despesa='35.00',
            forma_pagamento=Despesa.PIX,
        )

        response = self.client.get(
            reverse('apagar-categoria-despesa', args=[categoria.pk]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'despesaCategoriaExcluida')
        self.assertFalse(CategoriaDespesa.objects.filter(pk=categoria.pk).exists())
        despesa.refresh_from_db()
        self.assertIsNone(despesa.categoria_despesa)

    def test_cadastro_fiado_salva_campos_e_atualiza_total_a_pagar(self):
        data_vencimento = timezone.localdate() + timedelta(days=7)
        response = self.client.post(
            reverse('cadastrar-despesa'),
            {
                'usuario': self.user.pk,
                'nome_despesa': 'Fornecedor fiado',
                'preco_despesa': '120.00',
                'forma_pagamento': Despesa.FIADO,
                'valor_entrada': '20.00',
                'qtd_parcela': '3',
                'dia_vencimento_parcela': str(data_vencimento.day),
                'fiado_pago': 'False',
                'dashboard_periodo': 'today',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        despesa = Despesa.objects.get(nome_despesa='Fornecedor fiado')
        self.assertEqual(despesa.valor_entrada, Decimal('20.00'))
        self.assertEqual(despesa.qtd_parcela, 3)
        self.assertIsNone(despesa.data_vencimento)
        self.assertEqual(despesa.dia_vencimento_parcela, data_vencimento.day)
        self.assertFalse(despesa.fiado_pago)
        self.assertContains(response, 'Despesas a pagar')
        self.assertContains(response, '100')
        self.assertContains(response, 'Não pago')
        self.assertContains(response, f'Fiado parcelado - vence todo dia {data_vencimento.day}')
        self.assertContains(response, 'Faltam 7 dias para pagar')

    def test_cadastro_despesa_fixa_salva_dia_e_atualiza_card(self):
        dia_vencimento = timezone.localdate().day
        response = self.client.post(
            reverse('cadastrar-despesa'),
            {
                'usuario': self.user.pk,
                'nome_despesa': 'Aluguel',
                'preco_despesa': '1200.00',
                'forma_pagamento': Despesa.PIX,
                'despesa_fixa': 'on',
                'dia_vencimento_fixo': str(dia_vencimento),
                'dashboard_periodo': 'today',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        despesa = Despesa.objects.get(nome_despesa='Aluguel')
        self.assertTrue(despesa.despesa_fixa)
        self.assertEqual(despesa.dia_vencimento_fixo, dia_vencimento)
        self.assertContains(response, 'Despesas fixas')
        self.assertContains(response, f'Despesa fixa - vence dia {dia_vencimento}')
        self.assertContains(response, '1200')

    def test_cadastro_despesa_fixa_aceita_valor_com_virgula(self):
        response = self.client.post(
            reverse('cadastrar-despesa'),
            {
                'usuario': self.user.pk,
                'nome_despesa': 'Aluguel loja',
                'preco_despesa': '600,00',
                'forma_pagamento': Despesa.PIX,
                'despesa_fixa': 'on',
                'dia_vencimento_fixo': '10',
                'dashboard_periodo': 'today',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'despesaSalva')
        despesa = Despesa.objects.get(nome_despesa='Aluguel loja')
        self.assertEqual(despesa.preco_despesa, Decimal('600.00'))
        self.assertTrue(despesa.despesa_fixa)
        self.assertEqual(despesa.dia_vencimento_fixo, 10)

    def test_cadastro_prolabore_salva_com_categoria_e_atualiza_dashboard(self):
        categoria = CategoriaDespesa.objects.create(
            usuario=self.user,
            nome_categoria_despesa='Alimentação',
        )

        response = self.client.post(
            reverse('cadastrar-prolabore'),
            {
                'usuario': self.user.pk,
                'tipo': Despesa.TIPO_PROLABORE,
                'nome_despesa': 'Alimentação pessoal',
                'data_lancamento': '2026-06-09',
                'categoria_despesa': categoria.pk,
                'preco_despesa': '50,00',
                'forma_pagamento': Despesa.PIX,
                'observacao': 'Retirada pessoal',
                'dashboard_periodo': 'custom',
                'dashboard_inicio': '2026-06-09',
                'dashboard_fim': '2026-06-09',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'prolaboreSalvo')
        despesa = Despesa.objects.get(tipo=Despesa.TIPO_PROLABORE)
        self.assertEqual(despesa.nome_despesa, 'Alimentação pessoal')
        self.assertEqual(despesa.categoria_despesa, categoria)
        self.assertEqual(despesa.preco_despesa, Decimal('50.00'))
        self.assertEqual(timezone.localtime(despesa.data_cadastro).date().isoformat(), '2026-06-09')
        self.assertContains(response, 'Pró-labore')
        self.assertContains(response, 'Alimentação pessoal')
        self.assertContains(response, 'Alimentação')
        self.assertContains(response, 'Controle pessoal')
        self.assertContains(response, '09/06/2026')

    def test_cadastro_divida_nao_paga_nao_contabiliza_como_despesa(self):
        categoria = CategoriaDespesa.objects.create(
            usuario=self.user,
            nome_categoria_despesa='Cartão pessoal',
        )

        response = self.client.post(
            reverse('cadastrar-divida'),
            {
                'usuario': self.user.pk,
                'tipo': Despesa.TIPO_DIVIDA,
                'nome_despesa': 'Fatura pessoal',
                'categoria_despesa': categoria.pk,
                'preco_despesa': '140,00',
                'forma_pagamento': Despesa.PIX,
                'fiado_pago': 'False',
                'dashboard_periodo': 'todas',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'dividaSalva')
        divida = Despesa.objects.get(tipo=Despesa.TIPO_DIVIDA)
        self.assertEqual(divida.nome_despesa, 'Fatura pessoal')
        self.assertEqual(divida.categoria_despesa, categoria)
        self.assertFalse(divida.fiado_pago)
        dashboard = build_expense_dashboard(self.user, {'periodo': 'todas'})
        self.assertEqual(dashboard['expense_total'], Decimal('0.00'))
        self.assertEqual(dashboard['expense_payable_total'], Decimal('0.00'))
        self.assertEqual(dashboard['debt_payable_total'], Decimal('140.00'))
        self.assertEqual(dashboard['debt_payable_count'], 1)
        self.assertEqual(dashboard['expense_category_ranking'], [])
        self.assertContains(response, 'Dívida')
        self.assertContains(response, 'Não pago')

    def test_divida_paga_contabiliza_total_sem_misturar_rankings(self):
        categoria_empresa = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Operacional')
        categoria_prolabore = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Casa')
        categoria_divida = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Cartão pessoal')
        data_cadastro = timezone.make_aware(datetime(2026, 6, 9, 10, 0, 0))

        empresa = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria_empresa,
            nome_despesa='Conta empresa',
            preco_despesa='200.00',
            forma_pagamento=Despesa.PIX,
        )
        prolabore = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria_prolabore,
            nome_despesa='Retirada pessoal',
            preco_despesa='50.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_PROLABORE,
        )
        divida = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria_divida,
            nome_despesa='Fatura paga',
            preco_despesa='70.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_DIVIDA,
            fiado_pago=True,
        )
        Despesa.objects.filter(pk__in=[empresa.pk, prolabore.pk, divida.pk]).update(data_cadastro=data_cadastro)

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-09',
            'data_fim': '2026-06-09',
        })

        self.assertEqual(dashboard['expense_total'], Decimal('320.00'))
        self.assertEqual([item['category'] for item in dashboard['expense_category_ranking']], ['Operacional'])
        self.assertEqual(dashboard['expense_category_ranking'][0]['amount'], Decimal('200.00'))
        self.assertEqual(dashboard['prolabore_summary']['category_ranking'][0]['category'], 'Casa')
        self.assertEqual(dashboard['prolabore_summary']['category_ranking'][0]['amount'], Decimal('50.00'))

    def test_dividas_aparecem_em_tabela_separada_com_cards_por_categoria(self):
        categoria_empresa = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Operacional')
        categoria_divida = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Cartão pessoal')
        data_cadastro = timezone.make_aware(datetime(2026, 6, 9, 10, 0, 0))

        despesa = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria_empresa,
            nome_despesa='Conta empresa',
            preco_despesa='200.00',
            forma_pagamento=Despesa.PIX,
        )
        divida_pendente = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria_divida,
            nome_despesa='Fatura pessoal',
            preco_despesa='120.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_DIVIDA,
            fiado_pago=False,
        )
        divida_paga = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria_divida,
            nome_despesa='Parcela quitada',
            preco_despesa='30.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_DIVIDA,
            fiado_pago=True,
        )
        Despesa.objects.filter(pk__in=[despesa.pk, divida_pendente.pk, divida_paga.pk]).update(data_cadastro=data_cadastro)

        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-09',
            'data_fim': '2026-06-09',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(despesa, list(response.context['object_list']))
        self.assertNotIn(divida_pendente, list(response.context['object_list']))
        self.assertIn(divida_pendente, list(response.context['debt_list']))
        self.assertIn(divida_paga, list(response.context['debt_list']))
        self.assertContains(response, 'id="divida-Tbody"')
        self.assertContains(response, 'Dívidas por categoria')
        self.assertContains(response, 'Cartão pessoal')
        self.assertContains(response, 'Pendente: R$ 120,00')
        self.assertContains(response, 'Pago: R$ 30,00')

    def test_filtro_tipo_divida_mostra_apenas_tabela_de_dividas(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Cartão pessoal')
        data_cadastro = timezone.make_aware(datetime(2026, 6, 9, 10, 0, 0))
        divida = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Fatura pessoal',
            preco_despesa='120.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_DIVIDA,
            fiado_pago=False,
        )
        Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Conta empresa',
            preco_despesa='200.00',
            forma_pagamento=Despesa.PIX,
        )
        Despesa.objects.update(data_cadastro=data_cadastro)

        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-09',
            'data_fim': '2026-06-09',
            'tipo': 'divida',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['object_list']), [])
        self.assertEqual(list(response.context['debt_list']), [divida])
        self.assertContains(response, 'Fatura pessoal')
        self.assertContains(response, 'Nenhum resultado encontrado.')

    def test_formulario_prolabore_exige_categoria_pessoal(self):
        response = self.client.post(
            reverse('cadastrar-prolabore'),
            {
                'usuario': self.user.pk,
                'tipo': Despesa.TIPO_PROLABORE,
                'preco_despesa': '50.00',
                'forma_pagamento': Despesa.PIX,
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Retarget'], '#adicionar-conteudo')
        self.assertContains(response, 'Informe a categoria do Pró-labore.')

    def test_filtro_tipo_prolabore_limita_tabela(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Casa')
        prolabore = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Retirada transporte',
            preco_despesa='80.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_PROLABORE,
        )
        despesa = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Despesa empresa',
            preco_despesa='120.00',
            forma_pagamento=Despesa.PIX,
        )
        data_cadastro = timezone.make_aware(datetime(2026, 6, 6, 10, 0, 0))
        Despesa.objects.filter(pk__in=[prolabore.pk, despesa.pk]).update(data_cadastro=data_cadastro)

        response = self.client.get(reverse('despesa'), {
            'periodo': 'custom',
            'data_inicio': '2026-06-06',
            'data_fim': '2026-06-06',
            'tipo': 'prolabore',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pró-labore')
        self.assertContains(response, 'Retirada transporte')
        self.assertContains(response, 'Casa')
        self.assertNotContains(response, 'Despesa empresa')
        self.assertContains(response, 'selected>Pró-labore')

    def test_editar_e_excluir_prolabore_preserva_fluxo_htmx(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Transporte')
        nova_categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Saúde')
        prolabore = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Retirada antiga',
            preco_despesa='70.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_PROLABORE,
        )

        response = self.client.post(
            reverse('editar-despesa', args=[prolabore.pk]),
            {
                'usuario': self.user.pk,
                'tipo': Despesa.TIPO_PROLABORE,
                'nome_despesa': 'Outro nome',
                'data_lancamento': '2026-06-08',
                'categoria_despesa': nova_categoria.pk,
                'preco_despesa': '90.00',
                'forma_pagamento': Despesa.DINHEIRO,
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'prolaboreEditado')
        prolabore.refresh_from_db()
        self.assertEqual(prolabore.nome_despesa, 'Outro nome')
        self.assertEqual(prolabore.categoria_despesa, nova_categoria)
        self.assertEqual(prolabore.preco_despesa, Decimal('90.00'))
        self.assertEqual(timezone.localtime(prolabore.data_cadastro).date().isoformat(), '2026-06-08')

        response = self.client.get(
            reverse('apagar-despesa', args=[prolabore.pk]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Trigger'], 'prolaboreExcluido')
        self.assertFalse(Despesa.objects.filter(pk=prolabore.pk).exists())

    def test_cadastro_despesa_fixa_sem_dia_retorna_campo_visivel_no_modal(self):
        response = self.client.post(
            reverse('cadastrar-despesa'),
            {
                'usuario': self.user.pk,
                'nome_despesa': 'Aluguel sem dia',
                'preco_despesa': '600.00',
                'forma_pagamento': Despesa.PIX,
                'despesa_fixa': 'on',
            },
            HTTP_HX_REQUEST='true',
        )

        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Retarget'], '#adicionar-conteudo')
        self.assertEqual(response.headers['HX-Reswap'], 'innerHTML')
        self.assertContains(response, 'Verifique os campos destacados')
        self.assertContains(response, 'Informe o dia de vencimento da despesa fixa.')
        self.assertContains(response, 'aria-hidden="false"')
        self.assertRegex(html, r'name="dia_vencimento_fixo"[^>]*type="number"|type="number"[^>]*name="dia_vencimento_fixo"')

    def test_formulario_nao_fiado_limpa_campos_de_parcelamento(self):
        form = DespesaForms(
            data={
                'usuario': self.user.pk,
                'nome_despesa': 'Despesa pix',
                'preco_despesa': '60.00',
                'forma_pagamento': Despesa.PIX,
                'valor_entrada': '10.00',
                'qtd_parcela': '2',
                'data_vencimento': '2026-06-30',
                'fiado_pago': 'True',
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        despesa = form.save()
        self.assertIsNone(despesa.valor_entrada)
        self.assertIsNone(despesa.qtd_parcela)
        self.assertIsNone(despesa.data_vencimento)
        self.assertFalse(despesa.fiado_pago)

    def test_formulario_divida_nao_fiada_preserva_status_pago(self):
        form = DespesaForms(
            data={
                'usuario': self.user.pk,
                'tipo': Despesa.TIPO_DIVIDA,
                'nome_despesa': 'Dívida paga',
                'preco_despesa': '60.00',
                'forma_pagamento': Despesa.PIX,
                'fiado_pago': 'True',
            },
            initial={'usuario': self.user, 'tipo': Despesa.TIPO_DIVIDA},
            user=self.user,
            tipo_forcado=Despesa.TIPO_DIVIDA,
        )

        self.assertTrue(form.is_valid(), form.errors)
        divida = form.save()
        self.assertEqual(divida.tipo, Despesa.TIPO_DIVIDA)
        self.assertTrue(divida.fiado_pago)
        self.assertIsNone(divida.valor_entrada)
        self.assertIsNone(divida.qtd_parcela)
        self.assertIsNone(divida.data_vencimento)

    def test_formulario_despesa_nao_fixa_limpa_dia_vencimento_fixo(self):
        form = DespesaForms(
            data={
                'usuario': self.user.pk,
                'nome_despesa': 'Despesa eventual',
                'preco_despesa': '60.00',
                'forma_pagamento': Despesa.PIX,
                'dia_vencimento_fixo': '15',
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        despesa = form.save()
        self.assertFalse(despesa.despesa_fixa)
        self.assertIsNone(despesa.dia_vencimento_fixo)

    def test_formulario_despesa_fixa_exige_dia_vencimento(self):
        form = DespesaForms(
            data={
                'usuario': self.user.pk,
                'nome_despesa': 'Despesa fixa sem dia',
                'preco_despesa': '60.00',
                'forma_pagamento': Despesa.PIX,
                'despesa_fixa': 'on',
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('dia_vencimento_fixo', form.errors)

    def test_formulario_fiado_valida_entrada_maior_que_total(self):
        form = DespesaForms(
            data={
                'usuario': self.user.pk,
                'nome_despesa': 'Despesa invalida',
                'preco_despesa': '60.00',
                'forma_pagamento': Despesa.FIADO,
                'valor_entrada': '70.00',
                'qtd_parcela': '1',
                'data_vencimento': '2026-06-30',
                'fiado_pago': 'False',
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('valor_entrada', form.errors)

    def test_formulario_fiado_parcelado_substitui_data_por_dia_mensal(self):
        form = DespesaForms(
            data={
                'usuario': self.user.pk,
                'nome_despesa': 'Despesa parcelada',
                'preco_despesa': '180.00',
                'forma_pagamento': Despesa.FIADO,
                'valor_entrada': '0.00',
                'qtd_parcela': '3',
                'data_vencimento': '2026-06-30',
                'dia_vencimento_parcela': '12',
                'fiado_pago': 'False',
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        despesa = form.save()
        self.assertEqual(despesa.qtd_parcela, 3)
        self.assertEqual(despesa.dia_vencimento_parcela, 12)
        self.assertIsNone(despesa.data_vencimento)

    def test_formulario_fiado_parcelado_exige_dia_vencimento_mensal(self):
        form = DespesaForms(
            data={
                'usuario': self.user.pk,
                'nome_despesa': 'Despesa parcelada sem dia',
                'preco_despesa': '180.00',
                'forma_pagamento': Despesa.FIADO,
                'valor_entrada': '0.00',
                'qtd_parcela': '3',
                'fiado_pago': 'False',
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('dia_vencimento_parcela', form.errors)

    def test_total_despesas_a_pagar_respeita_filtro_e_inclui_estoque_fiado(self):
        dentro = timezone.make_aware(datetime(2026, 6, 5, 9, 0, 0))
        fora = timezone.make_aware(datetime(2026, 5, 20, 9, 0, 0))

        despesa = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Conta fiada',
            preco_despesa='100.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='20.00',
        )
        despesa_pix = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Conta pix',
            preco_despesa='500.00',
            forma_pagamento=Despesa.PIX,
        )
        despesa_fora = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Conta antiga',
            preco_despesa='900.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='0.00',
        )
        Despesa.objects.filter(pk__in=[despesa.pk, despesa_pix.pk]).update(data_cadastro=dentro)
        Despesa.objects.filter(pk=despesa_fora.pk).update(data_cadastro=fora)

        peca = Pecas.objects.create(
            usuario=self.user,
            nome_peca='Tela',
            preco_peca='80.00',
            preco_de_custo='30.00',
            quantidade=2,
            forma_pagamento=Pecas.FIADO,
            valor_entrada='10.00',
        )
        produto = Produto.objects.create(
            usuario=self.user,
            nome_produto='Cabo',
            preco_de_custo='20.00',
            preco='35.00',
            quantidade=3,
            forma_pagamento=Produto.FIADO,
            valor_entrada='15.00',
        )
        produto_fora = Produto.objects.create(
            usuario=self.user,
            nome_produto='Produto antigo',
            preco_de_custo='100.00',
            preco='150.00',
            quantidade=1,
            forma_pagamento=Produto.FIADO,
            valor_entrada='0.00',
        )
        Pecas.objects.filter(pk=peca.pk).update(data_criacao=dentro)
        Produto.objects.filter(pk=produto.pk).update(data_criacao=dentro)
        Produto.objects.filter(pk=produto_fora.pk).update(data_criacao=fora)

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(dashboard['expense_payable_total'], Decimal('175.00'))

    def test_total_a_pagar_separa_despesas_e_dividas(self):
        dentro = timezone.make_aware(datetime(2026, 6, 5, 9, 0, 0))

        despesa_fiada = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Conta fiada',
            preco_despesa='120.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='20.00',
            fiado_pago=False,
        )
        divida = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Dívida pendente',
            preco_despesa='90.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_DIVIDA,
            fiado_pago=False,
        )
        Despesa.objects.filter(pk__in=[despesa_fiada.pk, divida.pk]).update(data_cadastro=dentro)

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(dashboard['expense_payable_total'], Decimal('100.00'))
        self.assertEqual(dashboard['debt_payable_total'], Decimal('90.00'))
        self.assertEqual(dashboard['debt_payable_count'], 1)

    def test_total_despesas_contabiliza_apenas_fiado_pago(self):
        dentro = timezone.make_aware(datetime(2026, 6, 5, 9, 0, 0))
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Operacional')

        fiado_nao_pago = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Conta pendente',
            preco_despesa='100.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='0.00',
            fiado_pago=False,
        )
        fiado_pago = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Conta paga',
            preco_despesa='80.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='0.00',
            fiado_pago=True,
        )
        pix = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Conta pix',
            preco_despesa='20.00',
            forma_pagamento=Despesa.PIX,
        )
        Despesa.objects.filter(pk__in=[fiado_nao_pago.pk, fiado_pago.pk, pix.pk]).update(data_cadastro=dentro)

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(dashboard['expense_total'], Decimal('100.00'))
        self.assertEqual(dashboard['expense_payable_total'], Decimal('100.00'))
        self.assertEqual(dashboard['expense_category_ranking'][0]['amount'], Decimal('100.00'))

    def test_tabela_informa_dias_para_pagar_e_atraso(self):
        hoje = timezone.localdate()
        Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Conta a vencer',
            preco_despesa='60.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='0.00',
            data_vencimento=hoje + timedelta(days=3),
            fiado_pago=False,
        )
        Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Conta atrasada',
            preco_despesa='40.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='0.00',
            data_vencimento=hoje - timedelta(days=2),
            fiado_pago=False,
        )

        response = self.client.get(reverse('despesa'), {'periodo': 'today'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Faltam 3 dias para pagar')
        self.assertContains(response, '2 dias em atraso')

    def test_indicador_despesa_fixa_respeita_filtro(self):
        dentro = timezone.make_aware(datetime(2026, 6, 5, 9, 0, 0))
        fora = timezone.make_aware(datetime(2026, 5, 20, 9, 0, 0))

        fixa_dentro = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Internet fixa',
            preco_despesa='100.00',
            forma_pagamento=Despesa.PIX,
            despesa_fixa=True,
            dia_vencimento_fixo=5,
        )
        Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Compra eventual',
            preco_despesa='80.00',
            forma_pagamento=Despesa.PIX,
        )
        fixa_fora = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Aluguel antigo',
            preco_despesa='900.00',
            forma_pagamento=Despesa.PIX,
            despesa_fixa=True,
            dia_vencimento_fixo=20,
        )
        fixa_fiada = Despesa.objects.create(
            usuario=self.user,
            nome_despesa='Internet fiada',
            preco_despesa='300.00',
            forma_pagamento=Despesa.FIADO,
            valor_entrada='0.00',
            despesa_fixa=True,
            dia_vencimento_fixo=6,
            fiado_pago=False,
        )
        Despesa.objects.filter(pk__in=[fixa_dentro.pk, fixa_fiada.pk]).update(data_cadastro=dentro)
        Despesa.objects.filter(pk=fixa_fora.pk).update(data_cadastro=fora)

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(dashboard['fixed_expense_count'], 2)
        self.assertEqual(dashboard['fixed_expense_total'], Decimal('100.00'))

    def test_despesa_fixa_contabiliza_vencimento_mensal_no_periodo(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Recorrentes')
        fixa = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Assinatura mensal',
            preco_despesa='75.00',
            forma_pagamento=Despesa.PIX,
            despesa_fixa=True,
            dia_vencimento_fixo=10,
        )
        Despesa.objects.filter(pk=fixa.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 5, 20, 9, 0, 0)))

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-10',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(dashboard['expense_total'], Decimal('75.00'))
        self.assertEqual(dashboard['fixed_expense_count'], 1)
        self.assertEqual(dashboard['expense_category_ranking'][0]['category'], 'Recorrentes')

        dashboard_fora = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-11',
            'data_fim': '2026-06-11',
        })

        self.assertEqual(dashboard_fora['expense_total'], Decimal('0.00'))
        self.assertEqual(dashboard_fora['fixed_expense_count'], 0)

    def test_indicadores_prolabore_respeitam_periodo_e_categoria(self):
        categoria = CategoriaDespesa.objects.create(usuario=self.user, nome_categoria_despesa='Lazer')
        prolabore = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Pró-labore',
            preco_despesa='120.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_PROLABORE,
        )
        fora = Despesa.objects.create(
            usuario=self.user,
            categoria_despesa=categoria,
            nome_despesa='Pró-labore',
            preco_despesa='500.00',
            forma_pagamento=Despesa.PIX,
            tipo=Despesa.TIPO_PROLABORE,
        )
        Despesa.objects.filter(pk=prolabore.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 6, 7, 10, 0, 0)))
        Despesa.objects.filter(pk=fora.pk).update(data_cadastro=timezone.make_aware(datetime(2026, 5, 20, 10, 0, 0)))

        dashboard = build_expense_dashboard(self.user, {
            'periodo': 'custom',
            'data_inicio': '2026-06-01',
            'data_fim': '2026-06-10',
        })

        self.assertEqual(dashboard['prolabore_summary']['selected_total'], Decimal('120.00'))
        self.assertEqual(dashboard['prolabore_summary']['count'], 1)
        self.assertEqual(dashboard['prolabore_summary']['category_ranking'][0]['category'], 'Lazer')
        self.assertEqual(dashboard['prolabore_summary']['category_ranking'][0]['amount'], Decimal('120.00'))
        self.assertEqual(dashboard['expense_charts']['prolabore_category_ranking']['labels'], ['Lazer'])
        self.assertEqual(dashboard['expense_charts']['prolabore_category_ranking']['values'], [120.0])
