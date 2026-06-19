import json
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cliente.models import Cliente
from colaborador.models import Colaborador
from produto.forms import ProdutoForms
from produto.models import CategoriaProduto, Produto
from venda.models import ItemsVenda, Vendas


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
        self.assertContains(response, 'produto-filter-form')
        self.assertContains(response, 'input changed delay:400ms')
        self.assertContains(response, 'hx-trigger="change"')
        self.assertContains(response, 'fornecedorPickerModal')
        self.assertNotContains(response, 'success_tic_delete')

    def test_formulario_produto_usa_seletor_moderno_de_categoria(self):
        response = self.client.get(reverse('criar-produtos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-client-picker')
        self.assertContains(response, 'Criar nova categoria')
        self.assertContains(response, reverse('buscar-categorias-produto'))
        self.assertContains(response, 'Cadastrar fornecedor')
        self.assertContains(response, reverse('buscar-fornecedores'))

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

    def test_dashboard_despesa_paga_e_a_pagar_usam_preco_de_custo(self):
        categoria = CategoriaProduto.objects.create(usuario=self.user, nome='Estoque')
        Produto.objects.create(
            usuario=self.user,
            categoria=categoria,
            categoria_produtos='Estoque',
            nome_produto='Produto pago',
            quantidade=2,
            preco_de_custo=Decimal('10.00'),
            margem_de_lucro=Decimal('90.00'),
            preco=Decimal('100.00'),
            forma_pagamento=Produto.DINHEIRO,
        )
        Produto.objects.create(
            usuario=self.user,
            categoria=categoria,
            categoria_produtos='Estoque',
            nome_produto='Produto fiado',
            quantidade=3,
            preco_de_custo=Decimal('30.00'),
            margem_de_lucro=Decimal('85.00'),
            preco=Decimal('200.00'),
            forma_pagamento=Produto.FIADO,
            valor_entrada=Decimal('20.00'),
        )

        response = self.client.get(reverse('produtos'))

        self.assertEqual(response.context['produto_despesa_paga_total'], Decimal('40.00'))
        self.assertEqual(response.context['produto_despesa_a_pagar_total'], Decimal('70.00'))
        self.assertContains(response, 'Despesa paga')
        self.assertContains(response, 'Despesa a pagar')

    def test_formulario_fiado_valida_entrada_pelo_custo_total_do_produto(self):
        form = ProdutoForms(
            {
                'usuario': self.user.pk,
                'nome_produto': 'Produto fiado',
                'categoria': '',
                'quantidade': '2',
                'codigo_de_barras': '',
                'preco_de_custo': '10.00',
                'margem_de_lucro': '90.00',
                'preco': '100.00',
                'forma_pagamento': Produto.FIADO,
                'fornecedor': '',
                'observacao': '',
                'data_vencimento': '',
                'qtd_parcela': '1',
                'valor_entrada': '50.00',
            },
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('valor_entrada', form.errors)

    def test_lista_produtos_filtra_por_nome_e_categoria(self):
        categoria_fones = CategoriaProduto.objects.create(usuario=self.user, nome='Fones Premium')
        categoria_cabos = CategoriaProduto.objects.create(usuario=self.user, nome='Cabos USB')
        produto_fone = Produto.objects.create(
            usuario=self.user,
            categoria=categoria_fones,
            categoria_produtos='Fones Premium',
            nome_produto='Fone Bluetooth Pro',
            quantidade=4,
            preco_de_custo=Decimal('30.00'),
            margem_de_lucro=Decimal('50.00'),
            preco=Decimal('60.00'),
            forma_pagamento='Pix',
        )
        Produto.objects.create(
            usuario=self.user,
            categoria=categoria_cabos,
            categoria_produtos='Cabos USB',
            nome_produto='Cabo USB-C',
            quantidade=7,
            preco_de_custo=Decimal('10.00'),
            margem_de_lucro=Decimal('50.00'),
            preco=Decimal('20.00'),
            forma_pagamento='Pix',
        )

        response = self.client.get(reverse('produtos'), {
            'q': 'fone',
            'categoria': str(categoria_fones.pk),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['object_list']), [produto_fone])
        self.assertEqual(response.context['produto_resultado_total'], 1)
        self.assertTrue(response.context['produto_filtros_ativos'])

    def test_apagar_produto_htmx_remove_linha_e_acesso_direto_redireciona(self):
        categoria = CategoriaProduto.objects.create(usuario=self.user, nome='Fones')
        produto = Produto.objects.create(
            usuario=self.user,
            categoria=categoria,
            categoria_produtos='Fones',
            nome_produto='Fone para excluir',
            quantidade=1,
            preco_de_custo=Decimal('10.00'),
            margem_de_lucro=Decimal('50.00'),
            preco=Decimal('20.00'),
            forma_pagamento='Pix',
        )

        response = self.client.get(
            reverse('apagar-produtos', args=[produto.pk]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        trigger = json.loads(response['HX-Trigger'])
        self.assertIn('produtoExcluido', trigger)
        self.assertFalse(Produto.objects.filter(pk=produto.pk).exists())

        produto = Produto.objects.create(
            usuario=self.user,
            categoria=categoria,
            categoria_produtos='Fones',
            nome_produto='Fone redirect',
            quantidade=1,
            preco_de_custo=Decimal('10.00'),
            margem_de_lucro=Decimal('50.00'),
            preco=Decimal('20.00'),
            forma_pagamento='Pix',
        )

        response = self.client.get(reverse('apagar-produtos', args=[produto.pk]))

        self.assertRedirects(response, reverse('produtos'))
        self.assertFalse(Produto.objects.filter(pk=produto.pk).exists())

    def test_apagar_multiplos_produtos_em_sequencia_retorna_partial_vazio(self):
        categoria = CategoriaProduto.objects.create(usuario=self.user, nome='Cabos')
        produtos = [
            Produto.objects.create(
                usuario=self.user,
                categoria=categoria,
                categoria_produtos='Cabos',
                nome_produto=f'Cabo teste {indice}',
                quantidade=1,
                preco_de_custo=Decimal('10.00'),
                margem_de_lucro=Decimal('50.00'),
                preco=Decimal('20.00'),
                forma_pagamento='Pix',
            )
            for indice in range(2)
        ]

        for produto in produtos:
            response = self.client.get(
                reverse('apagar-produtos', args=[produto.pk]),
                HTTP_HX_REQUEST='true',
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'')
            self.assertIn('produtoExcluido', json.loads(response['HX-Trigger']))

        self.assertFalse(Produto.objects.filter(pk__in=[produto.pk for produto in produtos]).exists())

    def test_apagar_produto_com_venda_vinculada_bloqueia_exclusao(self):
        categoria = CategoriaProduto.objects.create(usuario=self.user, nome='Fones')
        produto = Produto.objects.create(
            usuario=self.user,
            categoria=categoria,
            categoria_produtos='Fones',
            nome_produto='Fone com historico',
            quantidade=2,
            preco_de_custo=Decimal('10.00'),
            margem_de_lucro=Decimal('50.00'),
            preco=Decimal('20.00'),
            forma_pagamento='Pix',
        )
        cliente = Cliente.objects.create(
            usuario=self.user,
            nome_cliente='Cliente teste',
            telefone_contato='67999999999',
        )
        vendedor = Colaborador.objects.create(
            usuario=self.user,
            nome_colaborador='Vendedor teste',
            telefone_contato='67988888888',
        )
        venda = Vendas.objects.create(
            usuario=self.user,
            cliente=cliente,
            vendedor=vendedor,
            forma_pagamento='Pix',
            desconto=Decimal('0.00'),
        )
        item = ItemsVenda.objects.create(
            vendas=venda,
            produto=produto,
            quantidade=1,
            preco=Decimal('20.00'),
        )

        response = self.client.get(
            reverse('apagar-produtos', args=[produto.pk]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        trigger = json.loads(response['HX-Trigger'])
        self.assertIn('produtoExclusaoBloqueada', trigger)
        self.assertTrue(Produto.objects.filter(pk=produto.pk).exists())
        self.assertTrue(ItemsVenda.objects.filter(pk=item.pk, produto=produto, vendas=venda).exists())

    def test_detalhe_produto_exibe_tempo_em_estoque(self):
        categoria = CategoriaProduto.objects.create(usuario=self.user, nome='Fones')
        produto = Produto.objects.create(
            usuario=self.user,
            categoria=categoria,
            categoria_produtos='Fones',
            nome_produto='Fone antigo',
            quantidade=2,
            preco_de_custo=Decimal('25.00'),
            margem_de_lucro=Decimal('50.00'),
            preco=Decimal('50.00'),
            forma_pagamento='Pix',
        )
        data_cadastro = timezone.make_aware(
            datetime.combine(timezone.localdate() - timedelta(days=4), time(hour=12))
        )
        Produto.objects.filter(pk=produto.pk).update(data_criacao=data_cadastro)

        response = self.client.get(reverse('detalhe-produto', args=[produto.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tempo em estoque')
        self.assertContains(response, '4 dias')
