from django.db import models
from django.db.models.aggregates import Count
from peca.models import Pecas
from cliente.models import Cliente
from servico.models import Servico


class Orcamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    celular = models.CharField(max_length=90)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.cliente

    def total(self):
        qs = self.orcamento_items.filter(orcamento=self.pk).values_list(
            'preco_orcamento', 'quantidade') or 0
        t = 0 if isinstance(qs, int) else sum(map(lambda q: q[0] * q[1], qs))
        return t


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
        on_delete=models.CASCADE,
    )
    quantidade = models.IntegerField()
    preco_orcamento = models.DecimalField(max_digits=9, decimal_places=2)
   

    class Meta:
        ordering = ('pk',)

    @property
    def __str__(self):
        return f'{self.pk} - {self.orcamento.pk} - {self.peca}'

    def subtotal(self):
        return self.preco_orcamento * (self.quantidade or 0)
