import json
from datetime import datetime
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
        self.assertContains(response, 'Ações')
        self.assertContains(response, 'Internet')
        self.assertContains(response, 'Sem categoria')
        self.assertContains(response, '02/06/2026')
        self.assertContains(response, '14:35')

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
        self.assertGreater(dashboard['expense_chart_height'], 320)

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

    def test_cadastro_fiado_salva_campos_e_atualiza_total_a_pagar(self):
        response = self.client.post(
            reverse('cadastrar-despesa'),
            {
                'usuario': self.user.pk,
                'nome_despesa': 'Fornecedor fiado',
                'preco_despesa': '120.00',
                'forma_pagamento': Despesa.FIADO,
                'valor_entrada': '20.00',
                'qtd_parcela': '3',
                'data_vencimento': '2026-06-20',
                'dashboard_periodo': 'today',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        despesa = Despesa.objects.get(nome_despesa='Fornecedor fiado')
        self.assertEqual(despesa.valor_entrada, Decimal('20.00'))
        self.assertEqual(despesa.qtd_parcela, 3)
        self.assertEqual(despesa.data_vencimento.isoformat(), '2026-06-20')
        self.assertContains(response, 'Total de despesas a pagar')
        self.assertContains(response, '100')

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
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        despesa = form.save()
        self.assertIsNone(despesa.valor_entrada)
        self.assertIsNone(despesa.qtd_parcela)
        self.assertIsNone(despesa.data_vencimento)

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
            },
            initial={'usuario': self.user},
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('valor_entrada', form.errors)

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
