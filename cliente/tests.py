import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cliente.models import Cliente


class ClientePickerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='operador', password='senha-teste')
        self.other_user = User.objects.create_user(username='outro', password='senha-teste')
        self.client.force_login(self.user)

    def test_busca_clientes_filtra_por_usuario_e_telefone(self):
        cliente = Cliente.objects.create(
            usuario=self.user,
            nome_cliente='Maria Cliente',
            telefone_contato='(67) 99999-1111',
        )
        Cliente.objects.create(
            usuario=self.other_user,
            nome_cliente='Cliente de outra loja',
            telefone_contato='(67) 99999-1111',
        )

        response = self.client.get(reverse('buscar-clientes'), {'q': '99999'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['id'], cliente.pk)
        self.assertEqual(payload['results'][0]['phone'], cliente.telefone_contato)

    def test_cadastro_picker_retorna_evento_para_auto_selecao(self):
        response = self.client.post(
            reverse('cadastrar-cliente') + '?picker=1',
            {
                'client_picker': '1',
                'usuario': self.other_user.pk,
                'nome_cliente': 'Novo Cliente',
                'telefone_contato': '(67) 98888-7777',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        cliente = Cliente.objects.get(nome_cliente='Novo Cliente')
        self.assertEqual(cliente.usuario, self.user)

        trigger = json.loads(response['HX-Trigger'])
        self.assertEqual(trigger['clienteCriado']['id'], cliente.pk)
        self.assertEqual(trigger['clienteCriado']['text'], cliente.nome_cliente)
        self.assertEqual(trigger['clienteCriado']['phone'], cliente.telefone_contato)

    def test_cadastro_picker_invalido_mantem_formulario_no_modal(self):
        response = self.client.post(
            reverse('cadastrar-cliente') + '?picker=1',
            {
                'client_picker': '1',
                'usuario': self.user.pk,
                'telefone_contato': '',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('HX-Trigger', response)
        self.assertContains(response, 'data-client-picker-form="true"')
        self.assertContains(response, 'name="client_picker"')
