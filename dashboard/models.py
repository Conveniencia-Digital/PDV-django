from decimal import Decimal

from django.db import models
from colaborador.models import Colaborador
from django.contrib.auth.models import User


class Tarefas(models.Model):
    FINALIZADO = 'Finalizado'
    A_FAZER = 'A fazer'
    STATUS = [
        (FINALIZADO, 'Finalizado'),
        (A_FAZER, 'A fazer')
    ]
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    tarefa = models.CharField(max_length=200)
    custo = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal('0.00'))
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=10, default=A_FAZER)
