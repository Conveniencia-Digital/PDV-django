from django.db import models
from peca.models import Pecas


class Orcamento(models.Model):
    nf = models.CharField(max_length=20)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.nf


class ItemsOrcamento(models.Model):
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.SET_NULL,
        related_name='orcamento_items',
        null=True,
        blank=True
    )
    peca = models.ForeignKey(
        Pecas,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    quantidade = models.IntegerField()
    preco_orcamento = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return f'{self.pk} - {self.orcamento.pk} - {self.peca}'
