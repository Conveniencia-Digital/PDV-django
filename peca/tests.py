import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from peca.forms import PecasForms
from peca.models import Pecas


class PecasPricingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pecas-user', password='senha-teste')
        self.client.force_login(self.user)

    def _form_data(self, **overrides):
        data = {
            'usuario': self.user.pk,
            'nome_peca': 'Tela Moto G',
            'preco_peca': '',
            'categoria_peca': Pecas.TELAS,
            'quantidade': '2',
            'codigo_de_barras': '',
            'preco_de_custo': '10.00',
            'margem_de_lucro': '',
            'forma_pagamento': Pecas.DINHEIRO,
            'data_vencimento': '',
            'qtd_parcela': '',
            'valor_entrada': '',
            'fornecedor': '',
            'observacao': '',
            'pricing_last_edited': '',
        }
        data.update(overrides)
        return data

    def test_custo_e_margem_calculam_preco_de_venda(self):
        form = PecasForms(
            self._form_data(margem_de_lucro='50.00', pricing_last_edited='margin'),
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        peca = form.save()
        self.assertEqual(peca.preco_peca, Decimal('20.00'))
        self.assertEqual(peca.margem_de_lucro, Decimal('50.00'))

    def test_custo_e_preco_calculam_margem(self):
        form = PecasForms(
            self._form_data(preco_peca='15.00', pricing_last_edited='price'),
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        peca = form.save()
        self.assertEqual(peca.preco_peca, Decimal('15.00'))
        self.assertEqual(peca.margem_de_lucro, Decimal('33.33'))

    def test_margem_invalida_exibe_erro(self):
        form = PecasForms(
            self._form_data(margem_de_lucro='100.00', pricing_last_edited='margin'),
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('margem_de_lucro', form.errors)

    def test_formulario_fiado_valida_entrada_pelo_custo_total_da_peca(self):
        form = PecasForms(
            self._form_data(
                quantidade='2',
                preco_de_custo='10.00',
                preco_peca='100.00',
                forma_pagamento=Pecas.FIADO,
                valor_entrada='50.00',
                qtd_parcela='1',
                pricing_last_edited='price',
            ),
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('valor_entrada', form.errors)

    def test_pagina_pecas_indicadores_usam_preco_de_custo(self):
        Pecas.objects.create(
            usuario=self.user,
            nome_peca='Tela paga',
            preco_peca=Decimal('100.00'),
            preco_de_custo=Decimal('15.00'),
            margem_de_lucro=Decimal('85.00'),
            quantidade=2,
            forma_pagamento=Pecas.DINHEIRO,
        )
        Pecas.objects.create(
            usuario=self.user,
            nome_peca='Bateria fiada',
            preco_peca=Decimal('100.00'),
            preco_de_custo=Decimal('20.00'),
            margem_de_lucro=Decimal('80.00'),
            quantidade=4,
            forma_pagamento=Pecas.FIADO,
            valor_entrada=Decimal('30.00'),
        )

        response = self.client.get(reverse('pecas'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['preco_custo'], Decimal('110.00'))
        self.assertEqual(response.context['preco_venda'], Decimal('600.00'))
        self.assertEqual(response.context['despesa_paga_total'], Decimal('60.00'))
        self.assertEqual(response.context['despesa_a_pagar_total'], Decimal('50.00'))
        self.assertContains(response, 'Despesa paga')
        self.assertContains(response, 'Despesa a pagar')
        self.assertContains(response, 'css/client-picker.css')
        self.assertContains(response, 'js/client-picker.js')
        self.assertContains(response, 'fornecedorPickerModal')

    def test_formulario_de_peca_usa_calculadora_de_margem(self):
        response = self.client.get(reverse('cadastrar-peca'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-client-picker')
        self.assertContains(response, 'Cadastrar fornecedor')
        self.assertContains(response, reverse('buscar-fornecedores'))
        self.assertContains(response, 'data-profit-margin-calculator')
        self.assertContains(response, 'data-pricing-field="cost"')
        self.assertContains(response, 'data-pricing-field="margin"')
        self.assertContains(response, 'data-pricing-field="price"')
        self.assertContains(response, 'data-pricing-last-edited="true"')

    def test_busca_pecas_filtra_usuario_e_termo(self):
        other_user = User.objects.create_user(username='outro-pecas', password='senha-teste')
        peca = Pecas.objects.create(
            usuario=self.user,
            nome_peca='Tela Samsung A31',
            preco_peca='120.00',
            preco_de_custo='80.00',
            margem_de_lucro='33.33',
            quantidade=3,
            forma_pagamento=Pecas.DINHEIRO,
        )
        Pecas.objects.create(
            usuario=other_user,
            nome_peca='Tela Samsung Outra Loja',
            preco_peca='99.00',
            preco_de_custo='50.00',
            quantidade=3,
            forma_pagamento=Pecas.DINHEIRO,
        )

        response = self.client.get(reverse('buscar-pecas'), {'q': 'samsung'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['id'], peca.pk)
        self.assertEqual(payload['results'][0]['price'], '120.00')

    def test_cadastro_peca_picker_retorna_evento_para_auto_selecao(self):
        response = self.client.post(
            reverse('cadastrar-peca') + '?picker=1',
            self._form_data(
                piece_picker='1',
                nome_peca='Conector USB-C',
                preco_de_custo='10.00',
                preco_peca='15.00',
                pricing_last_edited='price',
            ),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        peca = Pecas.objects.get(nome_peca='Conector USB-C')
        trigger = json.loads(response['HX-Trigger'])
        self.assertEqual(trigger['orcamentoPecaCriada']['id'], peca.pk)
        self.assertEqual(trigger['orcamentoPecaCriada']['text'], peca.nome_peca)
        self.assertEqual(trigger['orcamentoPecaCriada']['price'], '15.00')
