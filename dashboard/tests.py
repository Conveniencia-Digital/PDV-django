from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from dashboard.forms import TarefaForms
from dashboard.models import Tarefas


class TarefaCustoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='painel-user', password='senha-teste')
        self.client.force_login(self.user)

    def test_formulario_cadastro_exibe_campo_monetario_custo(self):
        response = self.client.get(reverse('cadastrar-tarefa'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="custo"')
        self.assertContains(response, 'Custo')
        self.assertContains(response, 'step="0.01"')
        self.assertContains(response, 'min="0"')

    def test_cadastro_tarefa_salva_custo(self):
        response = self.client.post(
            reverse('cadastrar-tarefa'),
            {
                'usuario': self.user.pk,
                'tarefa': 'Comprar material',
                'custo': '12.50',
                'status': Tarefas.A_FAZER,
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        tarefa = Tarefas.objects.get(tarefa='Comprar material')
        self.assertEqual(tarefa.custo, Decimal('12.50'))
        self.assertContains(response, 'R$ 12,50')

    def test_formulario_rejeita_custo_negativo(self):
        form = TarefaForms(data={
            'usuario': self.user.pk,
            'tarefa': 'Tarefa invalida',
            'custo': '-1.00',
            'status': Tarefas.A_FAZER,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('custo', form.errors)

    def test_painel_exibe_coluna_custo(self):
        Tarefas.objects.create(usuario=self.user, tarefa='Servico externo', custo='35.90')

        response = self.client.get(reverse('inicio'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Custo')
        self.assertContains(response, 'R$ 35,90')
