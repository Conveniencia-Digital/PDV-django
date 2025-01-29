from django.contrib.auth.models import User
from django.db import models

from colaborador.models import Colaborador


class Tarefas(models.Model):
    FINALIZADO = 'Finalizado'
    A_FAZER = 'A fazer'
    STATUS = [(FINALIZADO, 'Finalizado'), (A_FAZER, 'A fazer')]
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    tarefa = models.CharField(max_length=200)
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=10, default=A_FAZER)
