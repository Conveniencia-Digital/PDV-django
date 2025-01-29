from django.contrib.auth.models import User
from django.db import models

from cliente.models import Cliente
from colaborador.models import Colaborador
from produto.models import Produto


class Vendas(models.Model):
    ENTREGUE = 'Entregue'
    CANCELADA = 'Cancelada'
    TROCA = 'Troca de produto'
    RETORNO_GARANTIA = 'Retorno garantia'
    STATUS = [
        (ENTREGUE, 'Concluida e entregue'),
        (CANCELADA, 'Cancelada e estornada'),
        (TROCA, 'Troca de produto'),
        (RETORNO_GARANTIA, 'Retorno para garantia'),
    ]
    PIX = 'Pix'
    CARTAO_CREDITO = 'Cartāo de credito'
    CARTAO_DEBITO = 'Cartāo de debito'
    DINHEIRO = 'Dinheiro'
    FIADO = 'Fiado a receber'
    FORMA_PAGAMENTO = [
        (PIX, 'Pix'),
        (CARTAO_CREDITO, 'Cartāo de credito'),
        (CARTAO_DEBITO, 'Cartāo de debito'),
        (DINHEIRO, 'Dinheiro'),
        (FIADO, 'Fiado a receber'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    desconto = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=20, default=PIX)
    observacao = models.TextField(null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=20, default=ENTREGUE)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.cliente, self.vendedor

    def total(self):
        qs = self.vendas_items.filter(vendas=self.pk).values_list('preco', 'quantidade') or 0
        t = 0 if isinstance(qs, int) else sum(map(lambda q: q[0] * q[1], qs))
        desc = t - self.desconto
        return desc

    def valor_a_receber(self):
        qs = self.vendas_items.filter(vendas=self.pk).values_list('preco', 'quantidade') or 0
        t = 0 if isinstance(qs, int) else sum(map(lambda q: q[0] * q[1], qs))
        desc = t - self.desconto
        return desc - self.valor_entrada


class ItemsVenda(models.Model):
    vendas = models.ForeignKey(
        Vendas,
        on_delete=models.SET_NULL,
        related_name='vendas_items',
        blank=True,
        null=True,
    )
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return f'{self.pk} - {self.vendas.pk} - {self.produto}'

    def subtotal(self):
        return self.quantidade * self.preco

    def save(self, *args, **kwargs):
        self.produto.quantidade -= self.quantidade
        self.produto.save()
        super(ItemsVenda, self).save(*args, **kwargs)
