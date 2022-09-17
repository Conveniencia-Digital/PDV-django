from django.db import models
from peca.models import Pecas


class Orcamento(models.Model):
    cliente = models.CharField(max_length=20)


class ItemsOrcamento(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.SET_NULL, related_name='orcamento_items', null=True, blank=True)
    nome_orcamento = models.ForeignKey(Pecas, on_delete=models.CASCADE)
    preco_orcamento = models.DecimalField(max_digits=9, decimal_places=2)
    quantidade = models.IntegerField()

