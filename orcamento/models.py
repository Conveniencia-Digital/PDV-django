from django.db import models

from peca.models import Pecas


class Orcamento(models.Model):
    nf = models.CharField('nota fiscal', max_length=7, unique=True)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.nf


class ItemsOrcamento(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.SET_NULL, blank=True, null=True)
    nome_orcamento = models.ForeignKey(Pecas, on_delete=models.CASCADE)
    preco_orcamento = models.DecimalField(max_digits=9, decimal_places=2)
    quantidade = models.IntegerField()

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return f'{self.pk} - {self.orcamento.pk} - {self.nome_orcamento}'
