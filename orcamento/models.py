from decimal import Decimal

from django.db import models
from peca.models import Pecas
from cliente.models import Cliente
from colaborador.models import Colaborador
from django.contrib.auth.models import User
from financeiro.models import CardMachine


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
        (FIADO, 'Fiado a receber')
    ]
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    celular = models.CharField(max_length=90)
    data_entrega = models.DateField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    status = models.CharField(choices=STATUS, max_length=21)
    observacao = models.TextField(null=True, blank=True)
    tecnico = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    desconto = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    forma_pagamento = models.CharField(choices=FORMA_PAGAMENTO, max_length=21, default=PIX)
    data_vencimento = models.DateField(null=True, blank=True)
    qtd_parcela = models.IntegerField(null=True, blank=True)
    valor_entrada = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    card_machine = models.ForeignKey(CardMachine, on_delete=models.PROTECT, null=True, blank=True)
    card_payment_type = models.CharField(max_length=10, null=True, blank=True)
    card_installments = models.PositiveSmallIntegerField(null=True, blank=True)
    card_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    card_fee_amount = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    card_base_amount = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    card_final_amount = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    pass_card_fee_to_customer = models.BooleanField(default=False)


    
    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return self.cliente

    def total(self):
        if self.card_final_amount is not None:
            return self.card_final_amount
        desconto = self.desconto or Decimal('0.00')
        itens = self.orcamento_items.values_list('preco_orcamento', 'quantidade')
        total = sum(preco * qtd for preco, qtd in itens)
        return total - desconto

    def total_sem_desconto(self):
        itens = self.orcamento_items.values_list('preco_orcamento', 'quantidade')
        return sum(preco * qtd for preco, qtd in itens)

    def custo_total(self):
        return sum(
            (item.peca.preco_de_custo or Decimal('0.00')) * item.quantidade
            for item in self.orcamento_items.select_related('peca').all()
            if item.peca_id
        )

    def lucro_total(self):
        desconto = self.desconto or Decimal('0.00')
        lucro_itens = Decimal('0.00')

        for item in self.orcamento_items.select_related('peca').all():
            if item.peca_id:
                custo = item.peca.preco_de_custo or Decimal('0.00')
                lucro_itens += (item.preco_orcamento - custo) * item.quantidade
            else:
                lucro_itens += item.preco_orcamento * item.quantidade

        return Decimal(lucro_itens - desconto).quantize(Decimal('0.01'))

    def valor_a_receber(self):
        entrada = self.valor_entrada or Decimal('0.00')
        return self.total() - entrada


class OrcamentoSubmissionToken(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    finalidade = models.CharField(max_length=40)
    data_criacao = models.DateTimeField(auto_now_add=True)
    usado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'finalidade', 'usado_em']),
        ]


class Servico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    servico = models.CharField(max_length=100)

    def __str__(self):
        return self.servico




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
        null=True,
        blank=True,
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
    
    def save(self, *args, **kwargs):
        if self.peca_id and self.peca:
            self.peca.quantidade -= self.quantidade
            self.peca.save()
        super(ItemsOrcamento, self).save(*args, **kwargs)

