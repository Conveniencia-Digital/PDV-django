from django.db import models
from produto.models import Produto
from cliente.models import Cliente



class Vendas(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.cliente
    
    def total(self):
        qs = self.vendas_items.filter(vendas=self.pk).values_list(
            'preco', 'quantidade') or 0
        t = 0 if isinstance(qs, int) else sum(map(lambda q: q[0] * q[1], qs))
        return t


class ItemsVenda(models.Model):
    vendas = models.ForeignKey(Vendas,
                               on_delete=models.SET_NULL,
                               related_name='vendas_items',
                               blank=True,
                               null=True,
                               )
    produto = models.ForeignKey(Produto,
                                on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return f' {self.pk} - {self.vendas.pk} - {self.produto}'

    def subtotal(self):
        return self.quantidade * self.preco
