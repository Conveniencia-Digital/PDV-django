from produto.models import Produto
from django.db import models


class Vendas(models.Model):
    nf = models.IntegerField()

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.nf


class ItemsVenda(models.Model):
    vendas = models.ForeignKey(Vendas, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='vendas')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return f' {self.pk} - {self.vendas.pk} - {self.produto}'









