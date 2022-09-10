from django.db import models


class Servico(models.Model):
    nome_servico = models.CharField(max_length=100)
    preco_servico = models.DecimalField(max_digits=9, decimal_places=2)

