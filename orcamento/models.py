from django.db import models


class Orcamento(models.Model):
    nome_orcamento = models.CharField(max_length=90)
    preco_orcamento = models.DecimalField(max_digits=9, decimal_places=2)
