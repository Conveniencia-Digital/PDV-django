import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from fornecedor.models import Fornecedores


class FornecedorPickerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='fornecedor-user', password='senha-teste')
        self.other_user = User.objects.create_user(username='outro-fornecedor', password='senha-teste')
        self.client.force_login(self.user)

    def test_busca_fornecedores_filtra_usuario_e_termo(self):
        fornecedor = Fornecedores.objects.create(
            usuario=self.user,
            nome_fornecedor='Distribuidora Centro',
            cnpj='12.345.678/0001-90',
            telefone_contato='(67) 99999-0000',
        )
        Fornecedores.objects.create(
            usuario=self.other_user,
            nome_fornecedor='Distribuidora Centro Outra Loja',
            telefone_contato='(67) 98888-0000',
        )

        response = self.client.get(reverse('buscar-fornecedores'), {'q': 'centro'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['id'], fornecedor.pk)
        self.assertEqual(payload['results'][0]['text'], fornecedor.nome_fornecedor)
        self.assertEqual(payload['results'][0]['meta'], fornecedor.cnpj)

    def test_cadastro_fornecedor_picker_retorna_evento_para_auto_selecao(self):
        response = self.client.post(
            reverse('cadastrar-fornecedor') + '?picker=1',
            {
                'usuario': self.user.pk,
                'nome_fornecedor': 'Fornecedor Novo',
                'cnpj': '',
                'telefone_contato': '(67) 97777-0000',
                'telefone_contato_2': '',
                'rua': '',
                'bairro': '',
                'observacao': '',
                'supplier_picker': '1',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        fornecedor = Fornecedores.objects.get(nome_fornecedor='Fornecedor Novo')
        trigger = json.loads(response['HX-Trigger'])
        self.assertEqual(trigger['fornecedorCriado']['id'], fornecedor.pk)
        self.assertEqual(trigger['fornecedorCriado']['text'], fornecedor.nome_fornecedor)
        self.assertEqual(trigger['fornecedorCriado']['phone'], fornecedor.telefone_contato)

    def test_formulario_fornecedor_picker_usa_modal_filho(self):
        response = self.client.get(
            reverse('cadastrar-fornecedor') + '?picker=1',
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-supplier-picker-form="true"')
        self.assertContains(response, 'name="supplier_picker"')
        self.assertContains(response, '#fornecedorPickerModalConteudo')
