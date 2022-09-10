from django.db import models


class Pecas(models.Model):
    nome_peca = models.CharField(max_length=99)
    preco_peca = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return self.nome_peca
