from django.db import models
from django.db.models.aggregates import Count
from peca.models import Pecas
from cliente.models import Cliente
from servico.models import Servico
from colaborador.models import Colaborador


class Orcamento(models.Model):
    ANALISE = 'Em analise'
    PASSAR_ORCAMENTO = 'Passar orçamento'
    AGUARDANDO_LIBERACAO = 'Aguardando liberaçāo'
    LIBERADO = 'Liberado'
    EM_REPARO = 'Em reparo'
    FINALIZADO = 'Finalizado'
    FINALIZADO_ENTREGUE = 'Finalizado e entregue'
    GARANTIA_ENCERRADA = 'Garantia encerrada'
    RETORNO_GARANTIA = 'Retorno garantia'
    CANCELADO = 'Cancelado'
    CANCELADO_ENTREGUE = 'Cancelado e entregue'
   
    STATUS = [

        (ANALISE, 'Em analise'),
        (PASSAR_ORCAMENTO, 'Passar orçamento'),
        (AGUARDANDO_LIBERACAO, 'Aguardando liberaçāo'),
        (LIBERADO,'Liberado'),
        (EM_REPARO, 'Em reparo'),
        (FINALIZADO, 'Finalizado'),
        (FINALIZADO_ENTREGUE, 'Finalizado e entregue'),
        (GARANTIA_ENCERRADA, 'Garantia encerrada'),
        (RETORNO_GARANTIA, 'Retorno garantia'),
        (CANCELADO, 'Cancelado'),
        (CANCELADO_ENTREGUE, 'Cancelado e entregue')

    ]
    PIX = 'PX'
    CARTAO_CREDITO = 'CC'
    CARTAO_DEBITO = 'CD'
    DINHEIRO = 'DN'
    FIADO = 'FD'
    FORMA_PAGAMENTO = [
        (PIX, 'Pix'),
        (CARTAO_CREDITO, 'Cartāo de credito'),
        (CARTAO_DEBITO, 'Cartāo de debito'),
        (DINHEIRO, 'Dinheiro'),
        (FIADO, 'Fiado')
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    celular = models.CharField(max_length=90)
    data_entrega = models.DateTimeField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    status = models.CharField(choices=STATUS, max_length=21)
    observacao = models.TextField(null=True, blank=True)
    tecnico = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    desconto = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=2, default=PIX)

    
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
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
   
    quantidade = models.IntegerField()
    preco_orcamento = models.DecimalField(max_digits=9, decimal_places=2)
   

    class Meta:
        ordering = ('pk',)

    @property
    def __str__(self):
        return f'{self.pk} - {self.orcamento.pk} - {self.peca} - {self.servico}'

    def subtotal(self):
        return self.preco_orcamento * (self.quantidade or 0)

