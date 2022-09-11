from django.db import models


class Despesa(models.Model):
    nome_despesa = models.CharField(max_length=90)
    preco_despesa = models.DecimalField(max_digits=9, decimal_places=2)
