from django.db import models
from cliente.models import Cliente


class ContasAReceber(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nome_contas_a_receber = models.CharField(max_length=90)
    preco_contas_a_receber = models.DecimalField(max_digits=9, decimal_places=2)
