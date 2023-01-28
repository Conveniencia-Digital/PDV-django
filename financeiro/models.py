from django.db import models
from cliente.models import Cliente
from django.contrib.auth.models import User


class ContasAReceber(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nome_contas_a_receber = models.CharField(max_length=90)
    preco_contas_a_receber = models.DecimalField(max_digits=9, decimal_places=2)
    observacao = models.TextField(null=True, blank=True)

