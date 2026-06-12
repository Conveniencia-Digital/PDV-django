import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from produto.models import CategoriaProduto, Produto


class ProdutoCategoriaPickerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ana', password='senha123')
        self.client.login(username='ana', password='senha123')

    def test_lista_produtos_cria_categorias_padrao_no_banco(self):
        response = self.client.get(reverse('produtos'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(CategoriaProduto.objects.filter(usuario=self.user, nome='Fones').exists())
        self.assertContains(response, 'Valor de venda em estoque')
        self.assertContains(response, 'produtoChartsData')

    def test_formulario_produto_usa_seletor_moderno_de_categoria(self):
        response = self.client.get(reverse('criar-produtos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-client-picker')
        self.assertContains(response, 'Criar nova categoria')
        self.assertContains(response, reverse('buscar-categorias-produto'))

    def test_categoria_criada_pelo_picker_retorna_evento_para_auto_selecionar(self):
        response = self.client.post(
            reverse('criar-categoria-produto') + '?picker=1',
            {
                'usuario': self.user.pk,
                'nome': 'Games',
                'category_picker': '1',
            },
        )

        self.assertEqual(response.status_code, 200)
        trigger = json.loads(response['HX-Trigger'])
        categoria = CategoriaProduto.objects.get(usuario=self.user, nome='Games')
        self.assertEqual(trigger['produtoCategoriaCriada']['id'], categoria.pk)
        self.assertEqual(trigger['produtoCategoriaCriada']['text'], 'Games')

    def test_produto_salva_categoria_fk_e_texto_legado(self):
        categoria = CategoriaProduto.objects.create(usuario=self.user, nome='Games')
        response = self.client.post(
            reverse('criar-produtos'),
            {
                'usuario': self.user.pk,
                'nome_produto': 'Controle sem fio',
                'categoria': categoria.pk,
                'quantidade': 2,
                'codigo_de_barras': '',
                'preco_de_custo': '50.00',
                'margem_de_lucro': '50.00',
                'preco': '100.00',
                'forma_pagamento': 'Pix',
                'fornecedor': '',
                'observacao': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#produto-Tbody')
        produto = Produto.objects.get(nome_produto='Controle sem fio')
        self.assertEqual(produto.categoria, categoria)
        self.assertEqual(produto.categoria_produtos, 'Games')

    def test_dashboard_calcula_principais_indicadores(self):
        categoria = CategoriaProduto.objects.create(usuario=self.user, nome='Fones')
        Produto.objects.create(
            usuario=self.user,
            categoria=categoria,
            categoria_produtos='Fones',
            nome_produto='Fone Bluetooth',
            quantidade=3,
            preco_de_custo=Decimal('20.00'),
            margem_de_lucro=Decimal('60.00'),
            preco=Decimal('50.00'),
            forma_pagamento='Pix',
        )

        response = self.client.get(reverse('produtos'))

        self.assertEqual(response.context['produto_quantidade_total'], 3)
        self.assertEqual(response.context['produto_valor_venda_total'], Decimal('150.00'))
        self.assertEqual(response.context['produto_custo_total'], Decimal('60.00'))
        self.assertEqual(response.context['produto_lucro_potencial'], Decimal('90.00'))
        self.assertTrue(response.context['produto_margin_has_data'])
